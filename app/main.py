from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.basic_auth import basic_auth_challenge, is_basic_auth_allowed

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    if is_basic_auth_allowed(request):
        return await call_next(request)
    return basic_auth_challenge()

app.include_router(router, prefix="/api")
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
