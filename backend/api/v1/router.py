from fastapi import APIRouter

from api.v1 import health, ingest, query, documents, admin

v1_router = APIRouter()

v1_router.include_router(health.router)
v1_router.include_router(ingest.router)
v1_router.include_router(query.router)
v1_router.include_router(documents.router)
v1_router.include_router(admin.router)
