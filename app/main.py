from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .controllers.login import router as login_router
from .controllers.student import router as student_router

app = FastAPI()

origins = [
    "http://localhost:8080",
]

app.include_router(login_router)
app.include_router(student_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse("/login")
