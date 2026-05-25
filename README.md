# Python HTTP Server

A custom HTTP server built from scratch in Python using only the standard `socket` library. This project aims to demonstrate a deep understanding of networking protocols, socket programming, and the HTTP/1.1 specification.

## Features Currently Implemented
- [x] TCP Socket binding and listening
- [x] Responding with valid HTTP `200 OK`
- [x] Extracting URL paths from incoming HTTP Request strings
- [x] Responding with conditional HTTP `404 Not Found`
- [x] Responding with HTTP message bodies (`Content-Type` and `Content-Length`)
- [x] Parsing and extracting HTTP Headers (e.g., `User-Agent`)
- [x] Handling concurrent client connections using Python `threading`
- [x] Reading command-line arguments to configure server state
- [x] Returning file contents from disk (`application/octet-stream`)
- [x] Receiving and saving files to disk (Parsing `POST` request bodies)
- [x] Parsing `Accept-Encoding` headers to support `gzip` compression
- [x] Compressing HTTP response bodies using the `gzip` library

## How to Run

1. Start the server (it will run indefinitely and can handle multiple connections at once):
```bash
python app/main.py
```

2. Open a new terminal and test it using cURL. You do not need to restart the server between tests!

Test the root path (Returns `200 OK`):
```bash
curl -v http://localhost:4221/
```

Test the echo path (Returns your string in the body):
```bash
curl -v http://localhost:4221/echo/hello_world
```

Test the user-agent path (Returns your client's software name):
```bash
curl -v http://localhost:4221/user-agent
```

Test an unknown path (Returns `404 Not Found`):
```bash
curl -v http://localhost:4221/doesnotexist
```
