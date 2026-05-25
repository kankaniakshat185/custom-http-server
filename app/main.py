import socket  # noqa: F401
import threading
import sys
import os
import gzip



def handle_connection(conn, directory):
    # 3. Read and decode the request data
    request_data = conn.recv(1024).decode("utf-8")
    
    # 4. Split request into lines to easily read headers and the request line
    lines = request_data.split("\r\n")
    request_line = lines[0]
    
    # Check if client supports gzip
    supports_gzip = False
    for l in lines:
        if l.startswith("Accept-Encoding: "):
            encodings = l[17:]
            encoding_list = [e.strip() for e in encodings.split(",")]
            if "gzip" in encoding_list:
                supports_gzip = True
    
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
        
        if supports_gzip:
            compressed_body = gzip.compress(response_body)
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Encoding: gzip\r\n"
                f"Content-Length: {len(compressed_body)}\r\n"
                f"\r\n"
            ).encode("utf-8") + compressed_body
        else:
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
    elif path.startswith("/files/"):
        filename = path[7:]
        filepath = os.path.join(directory, filename)

        if parts[0] == "GET":
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read()
                    response_body = content.encode("utf-8")
                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(content)}\r\n"
                        f"\r\n"
                    ).encode("utf-8") + response_body
                    conn.sendall(response)
            else:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

        elif parts[0] == "POST":
            body = request_data.split("\r\n\r\n")[1] 
            with open(filepath, "w") as f:
                f.write(body)
            conn.sendall(b"HTTP/1.1 201 Created\r\n\r\n")

    else:
        # Unknown path -> Return 404 Not Found
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    conn.close()

def main():
    print("Logs from your program will appear here!")

    directory = ""
    if len(sys.argv) == 3 and sys.argv[1] == "--directory":
        directory = sys.argv[2]
    
    # 1. Bind to port 4221
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    while True:
    # 2. Wait for a client connection
        conn, addr = server_socket.accept() 
    
        client_thread = threading.Thread(target=handle_connection, args=(conn, directory))
        client_thread.start()
    


if __name__ == "__main__":
    main()
