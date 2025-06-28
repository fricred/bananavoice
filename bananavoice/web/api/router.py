from fastapi.routing import APIRouter

from bananavoice.web.api import docs, monitoring, users, voice

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(users.router)
api_router.include_router(docs.router)
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
