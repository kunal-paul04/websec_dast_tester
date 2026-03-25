from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.request_id import RequestIDMiddleware
from app.api.routes import router

app = FastAPI()

app.add_middleware(RequestIDMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)