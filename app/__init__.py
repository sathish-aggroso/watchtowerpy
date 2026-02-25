import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def create_app(config_object: str = "app.config.Config"):
    from flask import Flask

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_object)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    logging.root.addHandler(root_handler)
    logging.root.setLevel(logging.DEBUG)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.handlers = [root_handler]

    from app import extensions
    from app import models
    from app.routes import register_blueprints
    from app.errors import register_error_handlers

    extensions.init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    _register_template_filters(app)

    return app


def _register_template_filters(app: "Flask") -> None:
    from datetime import datetime
    import markdown

    @app.template_filter("markdown")
    def markdown_filter(text):
        if not text:
            return ""
        return markdown.markdown(text, extensions=["fenced_code", "tables"])

    @app.template_filter("localtime")
    def localtime_filter(utc_str, fmt="%Y-%m-%d %H:%M:%S %Z"):
        if not utc_str:
            return ""
        try:
            if isinstance(utc_str, str):
                utc_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            else:
                utc_dt = utc_str
            from app.utils import format_local_time

            return format_local_time(utc_dt)
        except Exception:
            return utc_str

    @app.template_filter("relativetime")
    def relativetime_filter(utc_str):
        if not utc_str:
            return ""
        try:
            if isinstance(utc_str, str):
                utc_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            else:
                utc_dt = utc_str
            from app.utils import relative_time

            return relative_time(utc_dt)
        except Exception:
            return utc_str
