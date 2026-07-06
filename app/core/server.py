import socket
import selectors
import threading
from concurrent.futures import ThreadPoolExecutor
from app.core.request import HTTPRequest
from app.core.response import HTTPResponse
from app.middleware.base import MiddlewarePipeline
from app.routing.router import Router

class HTTPServer:
    """
    Core Server orchestrating sockets, selectors event loop, thread pools,
    routing, and middleware pipeline.
    Adheres to SOLID Single Responsibility and Open/Closed Principles.
    """
    def __init__(self, host: str = "0.0.0.0", port: int = 4221, max_workers: int = 10):
        self.host = host
        self.port = port
        self.selector = selectors.DefaultSelector()
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.router = Router()
        self.pipeline = MiddlewarePipeline()
        self.sessions = {}  # Thread-safe guarded client state
        self.lock = threading.Lock()
        self.running = False
        self.server_socket = None

    def start(self):
        """
        Binds to socket and starts the asynchronous selectors event loop.
        """
        self.server_socket = socket.create_server((self.host, self.port), reuse_port=True)
        self.server_socket.setblocking(False)
        self.selector.register(self.server_socket, selectors.EVENT_READ, self._accept)
        
        self.running = True
        print(f"Server started on http://{self.host}:{self.port} using hybrid Async + Thread Pool concurrency model...")
        
        try:
            while self.running:
                # 0.5s timeout allows safe thread registrations and loop checks
                events = self.selector.select(timeout=0.5)
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.stop()

    def stop(self):
        """
        Closes all sockets and shuts down the thread pool.
        """
        self.running = False
        with self.lock:
            for conn in list(self.sessions.keys()):
                self._close_connection(conn)
            if self.server_socket:
                self.selector.unregister(self.server_socket)
                self.server_socket.close()
            self.selector.close()
        self.thread_pool.shutdown(wait=False)

    def _accept(self, server_socket, mask):
        """Accepts incoming TCP connection and registers it for reading."""
        conn, addr = server_socket.accept()
        conn.setblocking(False)
        
        with self.lock:
            self.sessions[conn] = {
                "buffer": b"",
                "content_length": None,
                "headers_part": None,
                "body_part": None,
                "client_addr": addr
            }
            self.selector.register(conn, selectors.EVENT_READ, self._read)

    def _read(self, conn, mask):
        """Reads non-blocking chunks into connection session buffers."""
        with self.lock:
            session = self.sessions.get(conn)
            if not session:
                return

        try:
            chunk = conn.recv(4096)
            if not chunk:
                self._close_connection(conn)
                return

            with self.lock:
                session["buffer"] += chunk
                
                # 1. Parse headers if not already completed
                if session["content_length"] is None and b"\r\n\r\n" in session["buffer"]:
                    headers_part, body_part = session["buffer"].split(b"\r\n\r\n", 1)
                    session["content_length"] = self._parse_content_length(headers_part)
                    session["headers_part"] = headers_part
                    session["body_part"] = body_part
                elif session["content_length"] is not None:
                    session["body_part"] += chunk

                # 2. Check if the full request body is read
                if session["content_length"] is not None:
                    if len(session["body_part"]) >= session["content_length"]:
                        body = session["body_part"][:session["content_length"]]
                        leftover = session["body_part"][session["content_length"]:]
                        headers_to_process = session["headers_part"]
                        addr = session["client_addr"]

                        # Reset session state for subsequent pipelined requests
                        session["buffer"] = leftover
                        session["content_length"] = None
                        session["headers_part"] = None
                        session["body_part"] = None

                        # Temporarily unregister read interest while thread pool processes
                        self.selector.unregister(conn)
                        
                        # Dispatch work task to the Thread Pool thread
                        self.thread_pool.submit(self._process_request, conn, addr, headers_to_process, body)

        except Exception as e:
            print(f"Error reading socket: {e}")
            self._close_connection(conn)

    def _process_request(self, conn, addr, headers_part: bytes, body_part: bytes):
        """Executes the middleware chain and routing logic inside a Thread Pool worker thread."""
        try:
            request = HTTPRequest.parse(headers_part, body_part)
            request.client_addr = addr

            # Router handler wrapped in middleware pipeline
            def final_handler(req: HTTPRequest) -> HTTPResponse:
                handler, params = self.router.match(req.method, req.path)
                if handler:
                    req.path_params = params
                    return handler(req)
                return HTTPResponse(status=404, headers={"Content-Type": "text/plain"}, body=b"Not Found")

            # Execute pipeline
            response = self.pipeline.execute(request, final_handler)

            # Send serialized response bytes
            supports_gzip = "gzip" in request.get_header("accept-encoding")
            conn.sendall(response.to_bytes(supports_gzip))

            # Persistent Connection logic
            # HTTP/1.1 defaults to keep-alive. HTTP/1.0 defaults to close.
            conn_header = request.get_header("connection").lower()
            is_keep_alive = (request.version == "HTTP/1.1" and conn_header != "close") or (conn_header == "keep-alive")

            if not is_keep_alive:
                self._close_connection(conn)
            else:
                # Re-register for reading future pipelined requests
                with self.lock:
                    if conn in self.sessions:
                        self.selector.register(conn, selectors.EVENT_READ, self._read)
                # Check if pipelined request is already in buffer
                self._check_buffered_request(conn)

        except Exception as e:
            print(f"Error processing client task: {e}")
            self._close_connection(conn)

    def _check_buffered_request(self, conn):
        """Checks if session buffer contains a complete HTTP request. Dispatches immediately if so."""
        with self.lock:
            session = self.sessions.get(conn)
            if not session:
                return

            if session["content_length"] is None and b"\r\n\r\n" in session["buffer"]:
                headers_part, body_part = session["buffer"].split(b"\r\n\r\n", 1)
                session["content_length"] = self._parse_content_length(headers_part)
                session["headers_part"] = headers_part
                session["body_part"] = body_part

            if session["content_length"] is not None:
                if len(session["body_part"]) >= session["content_length"]:
                    body = session["body_part"][:session["content_length"]]
                    leftover = session["body_part"][session["content_length"]:]
                    headers_to_process = session["headers_part"]
                    addr = session["client_addr"]

                    session["buffer"] = leftover
                    session["content_length"] = None
                    session["headers_part"] = None
                    session["body_part"] = None

                    try:
                        self.selector.unregister(conn)
                    except KeyError:
                        pass
                    
                    self.thread_pool.submit(self._process_request, conn, addr, headers_to_process, body)

    def _parse_content_length(self, headers_part: bytes) -> int:
        headers_decoded = headers_part.decode("utf-8", errors="ignore")
        for line in headers_decoded.split("\r\n"):
            if line.lower().startswith("content-length:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    return 0
        return 0

    def _close_connection(self, conn):
        """Cleans up selector registries and closes client socket descriptors."""
        with self.lock:
            if conn in self.sessions:
                del self.sessions[conn]
                try:
                    self.selector.unregister(conn)
                except KeyError:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
