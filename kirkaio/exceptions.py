class KirkaError(Exception):
    """Base exception for all kirkaio errors."""
    pass


class AuthenticationError(KirkaError):
    """Raised when the API key is missing or invalid."""
    pass


class NotFoundError(KirkaError):
    """Raised when a resource is not found (404)."""
    pass


class RateLimitError(KirkaError):
    """Raised when the rate limit is exceeded (429)."""
    pass


class RouteDisabledError(KirkaError):
    """Raised when a route is disabled for public access (403)."""
    pass


class ValidationError(KirkaError):
    """Raised when the request payload fails validation (400)."""
    pass


class ServerError(KirkaError):
    """Raised on unexpected server errors (500)."""
    pass