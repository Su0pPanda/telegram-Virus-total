from aiogram import Router

from src.bot.handlers.files import router as files_router
from src.bot.handlers.lookups import router as lookups_router
from src.bot.handlers.start import router as start_router
from src.bot.middleware.rate_limit import RateLimitMiddleware
from src.services.rate_limiter import RateLimiter


def build_router(rate_limiter: RateLimiter | None = None) -> Router:
    root = Router(name="root")
    root.include_router(start_router)
    if rate_limiter is not None:
        files_router.message.middleware(RateLimitMiddleware(rate_limiter))
        lookups_router.message.middleware(RateLimitMiddleware(rate_limiter))
    root.include_router(files_router)
    root.include_router(lookups_router)
    return root
