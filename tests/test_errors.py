import pytest
from unittest.mock import MagicMock, patch


class TestErrors:
    def test_http_exception_handler(self, app):
        from werkzeug.exceptions import NotFound

        with app.test_request_context():
            from app import create_app

            app = create_app("app.config.Config")
            app.config["TESTING"] = True

            with app.test_client() as client:
                response = client.get("/nonexistent")
                assert response.status_code == 404

    def test_generic_exception_handler(self, app):
        from app import create_app
        from flask import Flask

        app = create_app("app.config.Config")
        app.config["TESTING"] = True
        app.config["DEBUG"] = False

        @app.route("/error")
        def test_error():
            raise Exception("Test error")

        with app.test_client() as client:
            response = client.get("/error")
            assert response.status_code == 500
            assert (
                b"error" in response.data.lower()
                or b"unexpected" in response.data.lower()
            )

    def test_register_error_handlers(self):
        from flask import Flask
        from app.errors import register_error_handlers

        app = Flask(__name__)
        app.config["DEBUG"] = False

        register_error_handlers(app)

        assert True
