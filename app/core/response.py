import gzip

class HTTPResponse:
    """
    Represents an HTTP response. Encapsulates status codes, headers, and bodies.
    Adheres to SOLID Single Responsibility Principle by only managing response formatting.
    """
    STATUS_MAP = {
        200: "200 OK",
        201: "201 Created",
        204: "204 No Content",
        400: "400 Bad Request",
        403: "403 Forbidden",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
        500: "500 Internal Server Error"
    }

    def __init__(self, status: int = 200, headers: dict = None, body: bytes = b""):
        self.status = status
        self.headers = headers or {}
        self.body = body

    def to_bytes(self, client_supports_gzip: bool = False) -> bytes:
        """
        Serializes the response into raw HTTP/1.1 network bytes.
        Handles dynamic gzip compression based on client capability.
        """
        response_body = self.body
        resp_headers = {k.lower(): v for k, v in self.headers.items()}
        
        # Check if gzip compression is negotiated
        if client_supports_gzip and len(response_body) > 0 and "content-encoding" not in resp_headers:
            response_body = gzip.compress(response_body)
            resp_headers["content-encoding"] = "gzip"

        resp_headers["content-length"] = str(len(response_body))

        # Construct HTTP/1.1 format
        status_str = self.STATUS_MAP.get(self.status, f"{self.status} Unknown")
        status_line = f"HTTP/1.1 {status_str}\r\n"
        
        headers_str = ""
        for k, v in resp_headers.items():
            header_name = "-".join(part.capitalize() for part in k.split("-"))
            headers_str += f"{header_name}: {v}\r\n"
        headers_str += "\r\n"

        return status_line.encode("utf-8") + headers_str.encode("utf-8") + response_body
