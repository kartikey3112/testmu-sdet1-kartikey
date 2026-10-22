"""Shared Jinja2 template setup for the HTML pages."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).parent

templates = Jinja2Templates(directory=APP_DIR / "templates")
