from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin_api", tags=["admin_api"])


@router.get("/health")
def health_check() -> dict[str, bool]:
    return {"ok": True}
