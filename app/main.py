import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    # accept() waits for a client to connect. 
    # 'conn' is the new socket we use to talk back to this specific client.
    # 'addr' is the client's IP address and port.
    conn, addr = server_socket.accept() 

    # 1. Read the HTTP request data sent by the client. 
    # recv(1024) reads up to 1024 bytes. We decode it from bytes to a regular string.
    request_data = conn.recv(1024).decode("utf-8")
    
    # 2. An HTTP request starts with a "Request Line" like: "GET / HTTP/1.1"
    # The lines are separated by \r\n, so let's split the text into lines.
    lines = request_data.split("\r\n")
    request_line = lines[0] # The first line is "GET /path HTTP/1.1"
    
    # 3. Split the request line by spaces to extract the path
    # Example: ["GET", "/abcdefg", "HTTP/1.1"]
    parts = request_line.split(" ")
    if len(parts) > 1:
        path = parts[1]
    else:
        path = "/"

    # 4. Check the path and send the appropriate response
    # If the path is exactly "/", we return 200 OK. Otherwise, 404 Not Found.
    if path == "/":
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif path.startswith("/echo/"):
        echo_string = path[6:]
        response_body = echo_string.encode("utf-8")
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(echo_string)}\r\n"
            f"\r\n"
        ).encode("utf-8") + response_body
        conn.sendall(response)
    else:
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
