from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from app.db import init_db
from app.db.exceptions import UsernameAlreadyInUseError


app = FastAPI(
    title="crud-user-api-test",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = perf_counter() * 1000
    response = await call_next(request)
    process_time = perf_counter() * 1000 - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(UsernameAlreadyInUseError)
async def unicorn_exception_handler(
    request: Request, exc: UsernameAlreadyInUseError
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.msg},
    )


@app.get("/")
def index():
    return RedirectResponse(
        url="/api/users", status_code=status.HTTP_303_SEE_OTHER
    )


app.include_router(api_router, prefix=settings.API_PREFIX)

init_db(app=app)
