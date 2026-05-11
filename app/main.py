from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .controllers.login import router as login_router

app = FastAPI()

app.include_router(login_router)


@app.get("/")
async def root():
    return RedirectResponse("/login")
