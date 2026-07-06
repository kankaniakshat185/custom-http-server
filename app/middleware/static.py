import os
import mimetypes
from app.core.response import HTTPResponse

class StaticFilesMiddleware:
    """
    Middleware that intercepts requests to a path prefix and serves/saves files on disk.
    Implements security validation to prevent Directory Traversal attacks.
    Adheres to SOLID Single Responsibility Principle.
    """
    def __init__(self, path_prefix: str, directory: str):
        self.path_prefix = path_prefix
        # Resolve to absolute path to guarantee secure traversal checks
        self.directory = os.path.realpath(directory if directory else ".")

    def __call__(self, request, next_handler) -> HTTPResponse:
        if not request.path.startswith(self.path_prefix):
            return next_handler(request)

        # Extract filename and construct resolved target filepath
        filename = request.path[len(self.path_prefix):]
        filepath = os.path.join(self.directory, filename)
        resolved_filepath = os.path.realpath(filepath)

        # 1. Path Traversal Validation
        if not resolved_filepath.startswith(self.directory):
            return HTTPResponse(
                status=403, 
                headers={"Content-Type": "text/plain"}, 
                body=b"Forbidden"
            )

        # 2. Method Routing
        if request.method == "GET":
            if os.path.exists(filepath) and os.path.isfile(filepath):
                try:
                    with open(filepath, "rb") as f:
                        response_body = f.read()
                    
                    mime_type, _ = mimetypes.guess_type(filepath)
                    if mime_type is None:
                        mime_type = "application/octet-stream"
                    
                    return HTTPResponse(
                        status=200,
                        headers={"Content-Type": mime_type},
                        body=response_body
                    )
                except Exception as e:
                    return HTTPResponse(
                        status=500,
                        headers={"Content-Type": "text/plain"},
                        body=f"Error reading file: {e}".encode("utf-8")
                    )
            else:
                return HTTPResponse(status=404)

        elif request.method == "POST":
            try:
                with open(filepath, "wb") as f:
                    f.write(request.body)
                return HTTPResponse(status=201)
            except Exception as e:
                return HTTPResponse(
                    status=500,
                    headers={"Content-Type": "text/plain"},
                    body=f"Error writing file: {e}".encode("utf-8")
                )

        elif request.method == "DELETE":
            if os.path.exists(filepath) and os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    return HTTPResponse(status=204)
                except Exception as e:
                    return HTTPResponse(
                        status=500,
                        headers={"Content-Type": "text/plain"},
                        body=f"Error deleting file: {e}".encode("utf-8")
                    )
            else:
                return HTTPResponse(status=404)

        else:
            return HTTPResponse(status=405)
