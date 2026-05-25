import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    # accept() waits for a client to connect. 
    # 'conn' is the new socket we use to talk back to this specific client.
    # 'addr' is the client's IP address and port.
    conn, addr = server_socket.accept() 

    # Send the HTTP response.
    # The 'b' makes it a byte-string (since sockets send raw bytes, not Python strings).
    # HTTP requires lines to end with \r\n, and the response headers must end with a blank line (\r\n\r\n).
    conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")


if __name__ == "__main__":
    main()
