import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())

        # Attach to request state
        request.state.request_id = request_id

        response = await call_next(request)

        # Attach to response header
        response.headers["X-Request-ID"] = request_id

        return response