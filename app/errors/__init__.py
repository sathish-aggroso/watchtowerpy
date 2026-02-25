from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return jsonify(
            {
                "error": {
                    "code": e.name.upper().replace(" ", "_"),
                    "message": e.description,
                }
            }
        ), e.code

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        from flask import current_app

        if current_app.config.get("DEBUG"):
            raise e

        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            }
        ), 500
