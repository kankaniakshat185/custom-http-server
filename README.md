# Python HTTP Server & Web Framework

A lightweight, robust, and highly modular custom-built HTTP/1.1 server and web framework written entirely from scratch in Python. 

Built exclusively using standard libraries (`socket`, `selectors`, `threading`, `gzip`), this project demonstrates high-performance concurrency concepts including **non-blocking I/O multiplexing (`epoll`/`kqueue`)** and a **worker Thread Pool** combined with an Express-style routing and middleware engine.

---

## Features

- **Asynchronous Event Loop**: Uses `selectors` (`epoll` on Linux, `kqueue` on macOS) for non-blocking network socket polling.
- **Pre-allocated Thread Pool**: Offloads routing and blocking disk I/O operations to worker threads, preventing network loops from blocking.
- **Express-style Middlewares**: Onion-style recursive middleware execution pipeline (`request, next_handler`).
- **Dynamic Variable Routing**: Register patterns with dynamic path parameters (e.g., `/echo/:string`).
- **Persistent Connections**: Full support for HTTP/1.1 `Connection: Keep-Alive` pipelined socket reuse.
- **Content Negotiation**: Dynamic GZIP compression for optimized body payloads.
- **Directory Traversal Protection**: Validation via canonical filesystem path checks (`os.path.realpath`) to lock files in a sandbox folder.
- **MIME-Type Resolution**: Automatic file content detection via Python's standard `mimetypes` library.
- **Thread-Safe Access Logging**: Logger middleware printing formatted console logs.

---

## Codebase Modular Structure

The codebase is split into distinct modules following OOP and SOLID principles:
- `core/server.py`: Manages socket bindings, selectors loop, and thread pool dispatching.
- `core/request.py` & `core/response.py`: Data models encapsulating HTTP states.
- `routing/router.py`: Handles dynamic route registries.
- `middleware/`: Pipeline base interface and built-in middlewares (logger, static files).

---

## How to Run

### Method 1: Running Locally
Since the server uses a modular package structure, set the `PYTHONPATH` when launching the server:
```bash
mkdir -p sandbox
PYTHONPATH=. python3 app/main.py --directory ./sandbox
```

### Method 2: Running with Docker
You can run the server inside an isolated container:
```bash
# Build and start in foreground
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d

# Shutdown and cleanup containers
docker-compose down
```

---

## How to Use as a Web Framework

Other developers can use this project as a reusable micro-framework. Simply write a custom python script and import our components:

```python
from app.core.server import HTTPServer
from app.core.response import HTTPResponse

# Initialize server
server = HTTPServer(host="0.0.0.0", port=4221, max_workers=10)

# 1. Register middlewares
def custom_middleware(request, next_handler):
    print(f"Request intercepted: {request.path}")
    return next_handler(request)

server.pipeline.use(custom_middleware)

# 2. Register dynamic routes
def hello_handler(request):
    name = request.path_params.get("name", "World")
    return HTTPResponse(status=200, body=f"Hello, {name}!".encode("utf-8"))

server.router.add_route("GET", "/hello/:name", hello_handler)

# 3. Start Event Loop
server.start()
```

---

## Benchmarking Guide (Comparing with Flask)

You can benchmark this server against a standard Python Flask application using load-testing tools like **Apache Bench (`ab`)** or **`wrk`**.

### 1. Test Setup
Start both servers on different ports (e.g. our custom server on `:4221` and a basic Flask app on `:5000`).

### 2. Running Benchmarks

#### Using Apache Bench (`ab`)
Send 10,000 requests with a concurrency of 100 requests at the `/` endpoint:
```bash
# Benchmark our Custom Server
ab -n 10000 -c 100 http://localhost:4221/

# Benchmark Flask
ab -n 10000 -c 100 http://localhost:5000/
```

#### Using `wrk`
Run a 30-second benchmark using 8 threads and 200 concurrent connections:
```bash
wrk -t8 -c200 -d30s http://localhost:4221/
```

### 3. Comparing Results
Compare the following key metrics in the benchmark reports:
- **Requests per Second (RPS)**: The throughput of requests the server handles.
- **Latency (ms)**: The average roundtrip time for a request. Our async loop + thread pool is designed to maintain lower latency under heavy concurrency.

---

## Testing Endpoints

#### 1. Root Path
```bash
curl -v http://localhost:4221/
```

#### 2. Echo with Gzip Decompression
```bash
curl -v http://localhost:4221/echo/hello_world --compressed
```

#### 3. Fetch User-Agent
```bash
curl -v http://localhost:4221/user-agent -H "User-Agent: my-custom-agent"
```

#### 4. File Actions (POST, GET, DELETE)
```bash
# Upload
curl -v -X POST http://localhost:4221/files/hello.txt -d "Written through custom server"
# Download
curl -v http://localhost:4221/files/hello.txt
# Delete
curl -v -X DELETE http://localhost:4221/files/hello.txt
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](file:///Users/akshatkankani/Desktop/Github/custom-http-server/LICENSE) file for details.
