import tempfile
from pathlib import Path

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_health_check_is_public_and_available(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])


class FrontendAppTests(APITestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.dist_dir = Path(temp_dir.name)

    def test_client_side_routes_return_react_index(self):
        (self.dist_dir / "index.html").write_text("<div id='root'></div>")

        with override_settings(FRONTEND_DIST_DIR=self.dist_dir):
            response = self.client.get("/student/login")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"id='root'", b"".join(response.streaming_content))

    def test_college_admin_portal_routes_return_react_index(self):
        (self.dist_dir / "index.html").write_text("<div id='root'></div>")

        with override_settings(FRONTEND_DIST_DIR=self.dist_dir):
            response = self.client.get("/admin/companies")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"id='root'", b"".join(response.streaming_content))

    def test_django_admin_site_is_not_served_by_frontend(self):
        (self.dist_dir / "index.html").write_text("<div id='root'></div>")

        with override_settings(FRONTEND_DIST_DIR=self.dist_dir):
            response = self.client.get("/django-admin/login/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Django")

    def test_missing_build_returns_not_found(self):
        with override_settings(FRONTEND_DIST_DIR=self.dist_dir):
            response = self.client.get("/student/login")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_api_paths_are_not_served_by_frontend(self):
        (self.dist_dir / "index.html").write_text("<div id='root'></div>")

        with override_settings(FRONTEND_DIST_DIR=self.dist_dir):
            response = self.client.get("/api/does-not-exist/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
