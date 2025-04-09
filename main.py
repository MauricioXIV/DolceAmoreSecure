from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from routers import login
from starlette.middleware.sessions import SessionMiddleware
from routers.login import SECRET
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET, )
app.include_router(login.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")