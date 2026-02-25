import pytest
from unittest.mock import MagicMock, patch


class TestExtensions:
    def test_init_extensions(self):
        from flask import Flask
        from app import extensions

        app = Flask(__name__)
        app.config["DATABASE_PATH"] = ":memory:"

        with (
            patch.object(extensions, "create_engine") as mock_engine,
            patch.object(extensions, "_seed_default_project"),
        ):
            mock_engine.return_value = MagicMock()
            extensions.init_extensions(app)

            assert extensions._engine is not None

    def test_check_database_health_success(self):
        from app.extensions import check_database_health

        with patch("app.extensions._Session") as mock_session:
            mock_execute = MagicMock()
            mock_session.return_value.execute.return_value = mock_execute
            mock_session.return_value.close = MagicMock()

            result = check_database_health()

            assert result is True

    def test_check_database_health_failure(self):
        from app.extensions import check_database_health

        with patch("app.extensions._Session") as mock_session:
            mock_session.return_value.execute.side_effect = Exception("DB Error")

            result = check_database_health()

            assert result is False


class TestErrors:
    def test_http_exception_handler(self, app):
        from werkzeug.exceptions import NotFound

        with app.test_request_context():
            from app.errors import register_error_handlers

            @app.route("/notfound")
            def test_route():
                raise NotFound("Not found")

    def test_register_error_handlers(self, app):
        from flask import jsonify
        from werkzeug.exceptions import HTTPException

        with patch("app.errors.jsonify") as mock_jsonify:
            from app.errors import register_error_handlers

            register_error_handlers(app)

            assert True


class TestApp:
    def test_create_app(self):
        from app import create_app

        with (
            patch("app.extensions.init_extensions"),
            patch("app.routes.register_blueprints"),
            patch("app.errors.register_error_handlers"),
        ):
            app = create_app("app.config.Config")

            assert app is not None
            assert app.config is not None

    def test_register_template_filters(self):
        from flask import Flask
        from app import _register_template_filters

        app = Flask(__name__)

        _register_template_filters(app)

        assert "localtime" in app.jinja_env.filters
        assert "relativetime" in app.jinja_env.filters


class TestRoutesInit:
    def test_register_blueprints(self):
        from flask import Flask
        from app.routes import register_blueprints

        app = Flask(__name__)

        with patch("app.routes.main.main_bp"), patch("app.routes.api.api_bp"):
            register_blueprints(app)

            assert True
