# Python HTTP Server

A custom HTTP server built from scratch in Python using only the standard `socket` library. This project aims to demonstrate a deep understanding of networking protocols, socket programming, and the HTTP/1.1 specification.

## Features Currently Implemented
- [x] TCP Socket binding and listening
- [x] Responding with valid HTTP `200 OK`
- [x] Extracting URL paths from incoming HTTP Request strings
- [x] Responding with conditional HTTP `404 Not Found`

## How to Run

1. Start the server:
```bash
python app/main.py
```

2. Open a new terminal and test it using cURL:

Test the root path (Should return 200 OK):
```bash
curl -v http://localhost:4221/
```

Test a random path (Should return 404 Not Found):
```bash
curl -v http://localhost:4221/notfound
```
