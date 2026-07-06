class HTTPRequest:
    """
    Represents an HTTP request parsing raw socket bytes into an object-oriented structure.
    Adheres to SOLID Single Responsibility Principle by only managing request parsing.
    """
    def __init__(self, method: str, path: str, headers: dict, body: bytes, query_params: dict = None, version: str = "HTTP/1.1"):
        self.method = method.upper()
        self.path = path
        self.headers = headers  # Case-insensitive keys
        self.body = body
        self.query_params = query_params or {}
        self.path_params = {}  # Set later by the Router during route matching
        self.version = version

    @classmethod
    def parse(cls, headers_part: bytes, body_part: bytes) -> 'HTTPRequest':
        """
        Factory method to parse raw request bytes.
        """
        headers_decoded = headers_part.decode("utf-8", errors="ignore")
        lines = headers_decoded.split("\r\n")
        
        if not lines or not lines[0]:
            raise ValueError("Empty request line")
            
        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) < 3:
            raise ValueError("Malformed HTTP request line")
            
        method = parts[0]
        full_path = parts[1]
        version = parts[2]
        
        # 1. Parse path and query parameters
        path = full_path
        query_params = {}
        if "?" in full_path:
            path, query_string = full_path.split("?", 1)
            for param in query_string.split("&"):
                if not param:
                    continue
                if "=" in param:
                    k, v = param.split("=", 1)
                    query_params[k] = v
                else:
                    query_params[param] = ""
                    
        # 2. Parse headers case-insensitively
        headers = {}
        for line in lines[1:]:
            if not line:
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()
                
        return cls(
            method=method,
            path=path,
            headers=headers,
            body=body_part,
            query_params=query_params,
            version=version
        )

    def get_header(self, name: str, default: str = "") -> str:
        """Helper to get a header case-insensitively."""
        return self.headers.get(name.lower(), default)
