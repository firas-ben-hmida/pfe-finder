from fastapi import Request
from slowapi import Limiter


def client_ip(request: Request) -> str:
    """IP du client (X-Forwarded-For derrière Render). Protège le quota gratuit, pas une barrière de sécurité."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, default_limits=["120/minute"])
