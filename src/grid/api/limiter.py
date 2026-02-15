from slowapi import Limiter
from slowapi.util import get_remote_address

from ..core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/minute"]
)
