import socket  # noqa: F401


def main():
    print("Logs from your program will appear here!")

    # 1. Bind to port 4221
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    # 2. Wait for a client connection
    conn, addr = server_socket.accept() 

    # 3. Read and decode the request data
    request_data = conn.recv(1024).decode("utf-8")
    
    # 4. Split request into lines to easily read headers and the request line
    lines = request_data.split("\r\n")
    request_line = lines[0]
    
    # 5. Extract the path from the request line (e.g. "GET /path HTTP/1.1")
    parts = request_line.split(" ")
    if len(parts) > 1:
        path = parts[1]
    else:
        path = "/"

    # 6. Route the request based on the path
    if path == "/":
        # Root path -> Return 200 OK
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

    elif path.startswith("/echo/"):
        # Echo path -> Extract the string and return it in the body
        echo_string = path[6:]
        response_body = echo_string.encode("utf-8")
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(echo_string)}\r\n"
            f"\r\n"
        ).encode("utf-8") + response_body
        conn.sendall(response)

    elif path == "/user-agent":
        # User-Agent path -> Find the User-Agent header and return it in the body
        for l in lines:
            if l.startswith("User-Agent: "):
                user_agent = l[12:]
                response_body = user_agent.encode("utf-8")
                response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/plain\r\n"
                    f"Content-Length: {len(user_agent)}\r\n"
                    f"\r\n"
                ).encode("utf-8") + response_body
                conn.sendall(response)
                break
    
    else:
        # Unknown path -> Return 404 Not Found
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
