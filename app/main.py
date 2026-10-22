"""FastAPI application factory: mounts routers, templates, static files and test-only routes.

Run with `python -m uvicorn app.main:app`. The database is created and seeded on first start.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import api, auth, dashboard, db, errors, faults
from app.seed import reset_database
from app.settings import settings
from app.web import APP_DIR

log = logging.getLogger("testmu")


def health() -> JSONResponse:
    database = "ok"
    try:
        conn = db.connect()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        database = "fail"
    ok = database == "ok" and not faults.is_active("ENV_HEALTH_FAILING")
    body = {"status": "ok" if ok else "fail", "checks": {"database": database}}
    return JSONResponse(body, status_code=200 if ok else 503)


def create_app() -> FastAPI:
    if not settings.db_path.exists():
        reset_database()

    app = FastAPI(title="TestMu Lite", version="1.0.0")
    errors.register(app)

    @app.exception_handler(auth.LoginRequired)
    async def _login_required(_: Request, exc: auth.LoginRequired) -> RedirectResponse:
        return auth.login_redirect(exc.reason)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/dashboard", status_code=303)

    app.add_api_route("/health", health, methods=["GET"], tags=["health"])
    app.include_router(auth.router)
    app.include_router(dashboard.page_router)
    app.include_router(dashboard.widget_router)
    app.include_router(api.router)
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

    if settings.test_mode:
        from app import testing

        app.include_router(testing.router)
        log.warning("TEST_MODE=1: test-only endpoints under /_test are enabled")
    if faults.active():
        log.warning("Faults active at startup: %s", ", ".join(faults.active()))
    return app


app = create_app()
