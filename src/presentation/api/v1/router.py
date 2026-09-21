# src/presentation/api/v1/router.py
from fastapi import APIRouter

from src.presentation.api.v1.routers import auth

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
