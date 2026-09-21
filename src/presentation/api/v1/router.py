# src/presentation/api/v1/router.py
from fastapi import APIRouter

from src.presentation.api.v1.routers import auth, me, sessions

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(me.router)
router.include_router(sessions.router)
