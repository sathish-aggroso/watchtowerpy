import pytest
from unittest.mock import MagicMock, patch


class TestMainRoutes:
    def test_index_route(self, client):
        with (
            patch("app.services.link_service.LinkService.get_all_links") as mock_links,
            patch(
                "app.services.project_service.ProjectService.get_all_projects"
            ) as mock_projects,
            patch(
                "app.services.health_service.HealthService.get_status"
            ) as mock_health,
        ):
            mock_links.return_value = []
            mock_projects.return_value = []
            mock_health.return_value = {"status": "healthy"}

            response = client.get("/")

            assert response.status_code == 200

    def test_index_with_project_filter(self, client):
        with (
            patch("app.services.link_service.LinkService.get_all_links") as mock_links,
            patch(
                "app.services.project_service.ProjectService.get_all_projects"
            ) as mock_projects,
            patch("app.services.health_service.HealthService.get_status"),
        ):
            mock_links.return_value = []
            mock_projects.return_value = []

            response = client.get("/?project=1")

            assert response.status_code == 200

    def test_status_route(self, client):
        with patch(
            "app.services.health_service.HealthService.get_status"
        ) as mock_health:
            mock_health.return_value = {"status": "healthy"}

            response = client.get("/status")

            assert response.status_code == 200

    def test_add_link_no_url(self, client):
        response = client.post(
            "/add", data={"url": "", "title": "Test"}, follow_redirects=True
        )

        assert response.status_code == 200

    def test_add_link_invalid_url(self, client):
        response = client.post(
            "/add", data={"url": "not-a-url", "title": "Test"}, follow_redirects=True
        )

        assert response.status_code == 200

    def test_add_link_invalid_scheme(self, client):
        response = client.post(
            "/add",
            data={"url": "httpexample.com", "title": "Test"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_add_link_success(self, client):
        with patch("app.services.link_service.LinkService.create_link") as mock_create:
            mock_create.return_value = {"id": 1}

            response = client.post(
                "/add",
                data={"url": "https://example.com", "title": "Example"},
                follow_redirects=True,
            )

            assert response.status_code == 200

    def test_add_link_auto_https(self, client):
        with patch("app.services.link_service.LinkService.create_link") as mock_create:
            mock_create.return_value = {"id": 1}

            response = client.post(
                "/add",
                data={"url": "example.com", "title": "Example"},
                follow_redirects=True,
            )

            assert response.status_code == 200

    def test_delete_link(self, client):
        with patch("app.services.link_service.LinkService.delete_link") as mock_delete:
            mock_delete.return_value = True

            response = client.get("/delete/1", follow_redirects=True)

            assert response.status_code == 200

    def test_check_link_success(self, client):
        with patch("app.services.check_service.CheckService.check_link") as mock_check:
            mock_check.return_value = {"success": True, "summary": "Content changed"}

            response = client.get("/check/1", follow_redirects=True)

            assert response.status_code == 200

    def test_check_link_failure(self, client):
        with patch("app.services.check_service.CheckService.check_link") as mock_check:
            mock_check.return_value = {"success": False, "error": "Connection failed"}

            response = client.get("/check/1", follow_redirects=True)

            assert response.status_code == 200

    def test_view_link_not_found(self, client):
        with patch("app.services.link_service.LinkService.get_link") as mock_get:
            mock_get.return_value = None

            response = client.get("/link/999")

            assert response.status_code == 302

    def test_view_link_success(self, client):
        with (
            patch("app.services.link_service.LinkService.get_link") as mock_link,
            patch(
                "app.repositories.diff_repository.InitialPageRepository.get_by_link"
            ) as mock_initial,
            patch(
                "app.repositories.diff_repository.DiffRepository.get_by_link"
            ) as mock_diffs,
            patch("app.services.health_service.HealthService.get_status"),
        ):
            mock_link.return_value = {"id": 1, "url": "https://example.com"}
            mock_initial.return_value = None
            mock_diffs.return_value = []
            mock_health = MagicMock()

            response = client.get("/link/1")

            assert response.status_code == 200

    def test_view_diff_not_found(self, client):
        with patch(
            "app.repositories.diff_repository.DiffRepository.get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            response = client.get("/diff/999")

            assert response.status_code == 302

    def test_view_diff_success(self, client):
        with (
            patch(
                "app.repositories.diff_repository.DiffRepository.get_by_id"
            ) as mock_diff,
            patch("app.services.link_service.LinkService.get_link") as mock_link,
            patch(
                "app.repositories.diff_repository.DiffRepository.get_previous"
            ) as mock_prev,
            patch(
                "app.repositories.diff_repository.InitialPageRepository.get_by_link"
            ) as mock_initial,
            patch(
                "app.services.check_service.CheckService._extract_price"
            ) as mock_price,
            patch("app.services.check_service.CheckService._compute_html_diff"),
        ):
            mock_diff.return_value = {
                "id": 1,
                "link_id": 1,
                "full_content": "<html><body>New</body></html>",
            }
            mock_link.return_value = {"id": 1, "url": "https://example.com"}
            mock_prev.return_value = {"full_content": "<html><body>Old</body></html>"}
            mock_initial.return_value = None
            mock_price.return_value = None

            response = client.get("/diff/1")

            assert response.status_code == 200

    def test_view_initial_not_found(self, client):
        with patch(
            "app.repositories.diff_repository.InitialPageRepository.get_by_link"
        ) as mock_get:
            mock_get.return_value = None

            response = client.get("/initial/999")

            assert response.status_code == 302

    def test_view_initial_success(self, client):
        with (
            patch(
                "app.repositories.diff_repository.InitialPageRepository.get_by_link"
            ) as mock_initial,
            patch("app.services.link_service.LinkService.get_link") as mock_link,
            patch("app.services.health_service.HealthService.get_status"),
        ):
            mock_initial.return_value = {
                "id": 1,
                "link_id": 1,
                "screenshot": None,
            }
            mock_link.return_value = {"id": 1, "url": "https://example.com"}

            response = client.get("/initial/1")

            assert response.status_code == 200

    def test_add_project_no_name(self, client):
        response = client.post(
            "/project/add",
            data={"name": "", "description": "Test"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_add_project_success(self, client):
        with patch(
            "app.services.project_service.ProjectService.create_project"
        ) as mock_create:
            mock_create.return_value = {"id": 1}

            response = client.post(
                "/project/add",
                data={"name": "Test Project", "description": "Test"},
                follow_redirects=True,
            )

            assert response.status_code == 200

    def test_delete_project(self, client):
        with patch(
            "app.services.project_service.ProjectService.delete_project"
        ) as mock_delete:
            mock_delete.return_value = True

            response = client.get("/project/delete/2", follow_redirects=True)

            assert response.status_code == 200

    def test_set_timezone(self, client):
        response = client.post(
            "/set-timezone",
            data={"timezone": "America/New_York"},
            follow_redirects=True,
        )

        assert response.status_code == 200


class TestApiRoutes:
    def test_health_endpoint(self, client):
        with patch(
            "app.services.health_service.HealthService.get_status"
        ) as mock_health:
            mock_health.return_value = {"status": "healthy"}

            response = client.get("/api/health")

            assert response.status_code == 200
            assert response.json["status"] == "healthy"

    def test_check_endpoint_success(self, client):
        with patch("app.services.check_service.CheckService.check_link") as mock_check:
            mock_check.return_value = {"success": True, "summary": "Changed"}

            response = client.get("/api/check/1")

            assert response.status_code == 200

    def test_check_endpoint_failure(self, client):
        with patch("app.services.check_service.CheckService.check_link") as mock_check:
            mock_check.return_value = {"success": False, "error": "Failed"}

            response = client.get("/api/check/1")

            assert response.status_code == 400

    def test_check_endpoint_with_screenshot(self, client):
        with patch("app.services.check_service.CheckService.check_link") as mock_check:
            mock_check.return_value = {"success": True, "summary": "Changed"}

            response = client.get("/api/check/1?screenshot=true")

            assert response.status_code == 200
