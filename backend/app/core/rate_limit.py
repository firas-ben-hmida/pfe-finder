from fastapi import Request
from slowapi import Limiter


def client_ip(request: Request) -> str:
    """IP du client. Derrière le proxy de Render, elle est dans X-Forwarded-For.

    Cet en-tête peut être falsifié : la limite protège le quota gratuit,
    ce n'est pas une barrière de sécurité.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, default_limits=["120/minute"])
