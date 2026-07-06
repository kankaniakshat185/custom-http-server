class MiddlewarePipeline:
    """
    Manages and executes a pipeline of HTTP middlewares wrapping a final route handler.
    Implements Chain of Responsibility pattern.
    """
    def __init__(self):
        self.middlewares = []

    def use(self, middleware_func):
        """
        Adds a middleware function to the pipeline.
        The middleware function signature must be:
        def middleware(request: HTTPRequest, next_handler: Callable) -> HTTPResponse
        """
        self.middlewares.append(middleware_func)

    def execute(self, request, final_handler):
        """
        Runs the request through the middleware chain, ending with final_handler.
        """
        def dispatch(index):
            if index < len(self.middlewares):
                middleware = self.middlewares[index]
                return middleware(request, lambda req: dispatch(index + 1))
            return final_handler(request)
            
        return dispatch(0)
