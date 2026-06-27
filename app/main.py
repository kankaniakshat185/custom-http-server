import socket  # noqa: F401
import threading
import sys
import os
import gzip
import mimetypes
import datetime


def handle_connection(conn, addr, directory):
    # Buffer to hold incoming bytes
    request_buffer = b""
    
    try:
        while True:
            # 1. Read request headers (until we find double CRLF)
            while b"\r\n\r\n" not in request_buffer:
                chunk = conn.recv(4096)
                if not chunk:
                    # Client disconnected, break persistent connection loop
                    return
                request_buffer += chunk
            
            # Split headers from the body portion
            headers_part, body_part = request_buffer.split(b"\r\n\r\n", 1)
            
            # Parse request line & headers
            headers_decoded = headers_part.decode("utf-8", errors="ignore")
            lines = headers_decoded.split("\r\n")
            if not lines or not lines[0]:
                return
            
            request_line = lines[0]
            parts = request_line.split(" ")
            if len(parts) < 3:
                # Malformed request line
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
                return
            
            method = parts[0]
            path = parts[1]
            # http_version = parts[2]
            
            # Parse headers case-insensitively
            headers = {}
            for line in lines[1:]:
                if not line:
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    headers[key.strip().lower()] = val.strip()
            
            # Determine content length for body
            content_length = 0
            if "content-length" in headers:
                try:
                    content_length = int(headers["content-length"])
                except ValueError:
                    conn.sendall(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
                    return
            
            # 2. Read request body based on Content-Length
            while len(body_part) < content_length:
                chunk = conn.recv(4096)
                if not chunk:
                    # Client hung up prematurely
                    return
                body_part += chunk
            
            # Slice request body matching content_length exactly
            body = body_part[:content_length]
            
            # Keep leftover bytes for the next request in the same connection
            request_buffer = body_part[content_length:]
            
            # Check if client supports gzip
            supports_gzip = False
            if "accept-encoding" in headers:
                encodings = [e.strip() for e in headers["accept-encoding"].split(",")]
                if "gzip" in encodings:
                    supports_gzip = True
            
            # Connection keep-alive/close checks
            # HTTP/1.1 uses persistent connections by default unless Connection header says 'close'
            close_connection = (headers.get("connection", "").lower() == "close")
            conn_header = "Connection: close\r\n" if close_connection else ""
            
            # Define response placeholders
            status_code = "200 OK"
            response_headers = []
            response_body = b""
            
            # 3. Routing
            if path == "/":
                status_code = "200 OK"
            
            elif path.startswith("/echo/"):
                echo_string = path[6:]
                response_body = echo_string.encode("utf-8")
                response_headers.append(("Content-Type", "text/plain"))
                
                if supports_gzip:
                    response_body = gzip.compress(response_body)
                    response_headers.append(("Content-Encoding", "gzip"))
                
                status_code = "200 OK"
            
            elif path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                response_body = user_agent.encode("utf-8")
                response_headers.append(("Content-Type", "text/plain"))
                status_code = "200 OK"
            
            elif path.startswith("/files/"):
                filename = path[7:]
                filepath = os.path.join(directory, filename)
                
                # Dynamic path validation to prevent Directory Traversal
                target_dir = os.path.realpath(directory if directory else ".")
                resolved_filepath = os.path.realpath(filepath)
                if not resolved_filepath.startswith(target_dir):
                    status_code = "403 Forbidden"
                    response_body = b"Forbidden"
                    response_headers.append(("Content-Type", "text/plain"))
                
                elif method == "GET":
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        try:
                            with open(filepath, "rb") as f:
                                response_body = f.read()
                            
                            # Dynamic MIME type detection
                            mime_type, _ = mimetypes.guess_type(filepath)
                            if mime_type is None:
                                mime_type = "application/octet-stream"
                            
                            response_headers.append(("Content-Type", mime_type))
                            status_code = "200 OK"
                        except Exception as e:
                            status_code = "500 Internal Server Error"
                            response_body = f"Error reading file: {e}".encode("utf-8")
                            response_headers.append(("Content-Type", "text/plain"))
                    else:
                        status_code = "404 Not Found"
                
                elif method == "POST":
                    try:
                        # Write the payload in binary mode
                        with open(filepath, "wb") as f:
                            f.write(body)
                        status_code = "201 Created"
                    except Exception as e:
                        status_code = "500 Internal Server Error"
                        response_body = f"Error writing file: {e}".encode("utf-8")
                        response_headers.append(("Content-Type", "text/plain"))
                
                elif method == "DELETE":
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        try:
                            os.remove(filepath)
                            status_code = "204 No Content"
                        except Exception as e:
                            status_code = "500 Internal Server Error"
                            response_body = f"Error deleting file: {e}".encode("utf-8")
                            response_headers.append(("Content-Type", "text/plain"))
                    else:
                        status_code = "404 Not Found"
                
                else:
                    status_code = "405 Method Not Allowed"
            
            else:
                status_code = "404 Not Found"
            
            # 4. Construct and send response
            response_headers.append(("Content-Length", str(len(response_body))))
            
            headers_str = f"HTTP/1.1 {status_code}\r\n"
            if conn_header:
                headers_str += conn_header
            for k, v in response_headers:
                headers_str += f"{k}: {v}\r\n"
            headers_str += "\r\n"
            
            full_response = headers_str.encode("utf-8") + response_body
            conn.sendall(full_response)
            
            # Print log in thread-safe console output (single write)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {addr[0]}:{addr[1]} - {method} {path} -> {status_code}")
            
            if close_connection:
                break
                
    except Exception as e:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {addr[0]}:{addr[1]} - Error handling connection: {e}")
        try:
            conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n")
        except Exception:
            pass
    finally:
        conn.close()


def main():
    print("Logs from your program will appear here!")

    directory = ""
    if len(sys.argv) >= 3 and sys.argv[1] == "--directory":
        directory = sys.argv[2]
    
    # 1. Bind to port 4221
    server_socket = socket.create_server(("0.0.0.0", 4221), reuse_port=True)
    
    while True:
        # 2. Wait for a client connection
        conn, addr = server_socket.accept() 
        client_thread = threading.Thread(target=handle_connection, args=(conn, addr, directory))
        client_thread.start()


if __name__ == "__main__":
    main()
