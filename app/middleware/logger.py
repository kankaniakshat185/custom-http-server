import datetime
from app.core.response import HTTPResponse

def logger_middleware(request, next_handler) -> HTTPResponse:
    """
    Middleware that captures request metrics, handles uncaught route exceptions,
    and prints thread-safe console logs.
    """
    client_ip, client_port = getattr(request, "client_addr", ("unknown", 0))
    
    try:
        response = next_handler(request)
    except Exception as e:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {client_ip}:{client_port} - {request.method} {request.path} -> Crash: {e}")
        response = HTTPResponse(
            status=500, 
            headers={"Content-Type": "text/plain"}, 
            body=f"Internal Server Error: {e}".encode("utf-8")
        )
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_str = HTTPResponse.STATUS_MAP.get(response.status, str(response.status))
    print(f"[{timestamp}] {client_ip}:{client_port} - {request.method} {request.path} -> {status_str}")
    return response
