"""Register all routers."""

from aiogram import Router

from handlers.start import router as start_router
from handlers.store import router as store_router
from handlers.penalties import router as penalties_router
from handlers.admin import router as admin_router


def setup_routers() -> Router:
    """Create and return main router with all sub-routers."""
    main_router = Router()
    main_router.include_router(admin_router)  # admin first (has filters)
    main_router.include_router(start_router)
    main_router.include_router(store_router)
    main_router.include_router(penalties_router)
    return main_router
