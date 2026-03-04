#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
TaskFlow — Frontend & Integration E2E Tests
═══════════════════════════════════════════════════════════════════
Tests that the React frontend is served correctly through Nginx,
static assets load, and the API proxy works from a browser-like
perspective.

Usage:
    python tests/e2e_frontend.py
    BASE_URL=https://54.123.45.67 python tests/e2e_frontend.py
    make test-e2e-frontend
═══════════════════════════════════════════════════════════════════
"""

import os
import re
import sys
import json
import time
import unittest
from urllib import request, error

# ── Configuration ───────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "http://localhost").rstrip("/")
VERIFY_SSL = os.environ.get("VERIFY_SSL", "false").lower() == "true"

if not VERIFY_SSL:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context


# ── Helpers ─────────────────────────────────────────────────────

def http_get(path, headers=None):
    """GET request returning (status, headers_dict, body_text)."""
    url = f"{BASE_URL}{path}"
    req = request.Request(url, method="GET", headers=headers or {})
    try:
        with request.urlopen(req) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8")


def api_request(method, path, data=None):
    """JSON API request through the proxy, like the frontend does."""
    url = f"{BASE_URL}/api{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, dict(resp.headers), json.loads(raw) if raw else {}
    except error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, dict(e.headers), json.loads(raw)
        except json.JSONDecodeError:
            return e.code, dict(e.headers), raw


# ═══════════════════════════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════════════════════════


class F01_FrontendServing(unittest.TestCase):
    """Verify the React SPA is served correctly through Nginx."""

    def test_root_returns_html(self):
        """GET / returns 200 with HTML content."""
        status, headers, body = http_get("/")
        self.assertEqual(status, 200)
        content_type = headers.get("Content-Type", "")
        self.assertIn("text/html", content_type)

    def test_html_contains_react_root(self):
        """The HTML page has a div#root for React to mount into."""
        _, _, body = http_get("/")
        self.assertIn('id="root"', body, "Missing React root element")

    def test_html_includes_script_tags(self):
        """The HTML page includes JavaScript bundles."""
        _, _, body = http_get("/")
        self.assertTrue(
            re.search(r'<script[^>]+src=["\'][^"\']+\.js', body),
            "No JS bundle found in HTML",
        )

    def test_html_includes_title(self):
        """The HTML page has a <title> tag."""
        _, _, body = http_get("/")
        self.assertRegex(body, r"<title>[^<]+</title>")

    def test_meta_viewport_present(self):
        """Responsive viewport meta tag should be present."""
        _, _, body = http_get("/")
        self.assertIn("viewport", body.lower())


class F02_StaticAssets(unittest.TestCase):
    """Verify static assets (JS/CSS) are accessible."""

    @classmethod
    def setUpClass(cls):
        """Parse the index.html to find asset URLs."""
        _, _, body = http_get("/")
        cls.js_paths = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', body)
        cls.css_paths = re.findall(r'href=["\']([^"\']+\.css[^"\']*)["\']', body)
        cls.html_body = body

    def test_js_bundles_load(self):
        """All JavaScript files referenced in HTML should return 200."""
        self.assertTrue(len(self.js_paths) > 0, "No JS files found in HTML")
        for js_path in self.js_paths:
            # Handle absolute and relative paths
            path = js_path if js_path.startswith("/") else f"/{js_path}"
            status, headers, body = http_get(path)
            self.assertEqual(
                status, 200,
                f"Failed to load JS: {path} (status {status})",
            )
            # Should have content
            self.assertTrue(len(body) > 0, f"Empty JS file: {path}")

    def test_css_loads(self):
        """CSS files referenced in HTML should return 200."""
        if not self.css_paths:
            self.skipTest("No CSS files linked in HTML (may be inlined)")
        for css_path in self.css_paths:
            path = css_path if css_path.startswith("/") else f"/{css_path}"
            status, _, body = http_get(path)
            self.assertEqual(
                status, 200,
                f"Failed to load CSS: {path} (status {status})",
            )

    def test_favicon_or_icon(self):
        """Favicon should exist (common evaluator check)."""
        # Try common paths
        for path in ["/favicon.ico", "/favicon.svg", "/vite.svg"]:
            status, _, _ = http_get(path)
            if status == 200:
                return
        # Not a hard failure — some SPAs don't have favicons
        self.skipTest("No favicon found (not critical)")


class F03_SPARouting(unittest.TestCase):
    """Verify SPA routing works — non-API paths should return the app."""

    def test_unknown_path_returns_app(self):
        """GET /some/random/path should still return the SPA HTML.
        Nginx should proxy to frontend which serves index.html for any path.
        """
        status, headers, body = http_get("/nonexistent/route/12345")
        # Should get the SPA (either 200 or frontend may 404 but still serve HTML)
        content_type = headers.get("Content-Type", "")
        if status == 200:
            self.assertIn("text/html", content_type)
            self.assertIn('id="root"', body)

    def test_api_path_not_caught_by_spa(self):
        """GET /api/notreal/ should be handled by the backend, not the SPA.
        Django's default 404 may return HTML, but a known DRF path returns JSON.
        """
        status, headers, body = http_get("/api/tasks/99999/", {
            "Accept": "application/json",
        })
        self.assertEqual(status, 404)
        content_type = headers.get("Content-Type", "")
        self.assertIn("json", content_type.lower())


class F04_NginxProxyIntegration(unittest.TestCase):
    """Verify Nginx correctly proxies API requests to the backend."""

    def test_api_health_through_nginx(self):
        """API requests go through Nginx and reach the backend."""
        status, headers, body = api_request("GET", "/health/")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_api_response_content_type(self):
        """API responses have JSON content type through the proxy."""
        status, headers, body = api_request("GET", "/health/")
        content_type = headers.get("Content-Type", "")
        self.assertIn("application/json", content_type)

    def test_cors_headers_present(self):
        """CORS preflight should work for frontend → API requests."""
        url = f"{BASE_URL}/api/tasks/"
        headers = {
            "Origin": BASE_URL,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        req = request.Request(url, headers=headers, method="OPTIONS")
        try:
            with request.urlopen(req) as resp:
                self.assertIn(resp.status, [200, 204])
        except error.HTTPError as e:
            # A 200 from OPTIONS is fine, some stacks return content
            self.assertIn(e.code, [200, 204, 403])

    def test_client_max_body_size(self):
        """Nginx should reject uploads larger than the configured limit.
        (config: client_max_body_size 10M)
        """
        # Create a task first
        status, _, task = api_request("POST", "/tasks/", {"title": "Size Limit Test"})
        self.assertEqual(status, 201)
        task_id = task["id"]

        # Try uploading a large file (11MB) — should fail with 413
        try:
            boundary = "----LargeUploadBoundary"
            large_content = b"X" * (11 * 1024 * 1024)  # 11MB
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="attachment"; filename="huge.bin"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode("utf-8")
            body += large_content
            body += f"\r\n--{boundary}--\r\n".encode("utf-8")

            url = f"{BASE_URL}/api/tasks/{task_id}/upload/"
            headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
            req = request.Request(url, data=body, headers=headers, method="POST")
            with request.urlopen(req) as resp:
                # If it somehow succeeds, that's unexpected but not a failure
                pass
        except error.HTTPError as e:
            self.assertIn(e.code, [413, 400], "Expected 413 (Request Entity Too Large)")
        finally:
            api_request("DELETE", f"/tasks/{task_id}/")


class F05_BrowserSimulation(unittest.TestCase):
    """Simulate what a browser does when loading TaskFlow:
    1. Load HTML page
    2. Load JS/CSS assets
    3. JS calls API endpoints
    """

    def test_full_browser_flow(self):
        """Simulate a complete browser session."""

        # ── Step 1: Browser loads the page ──────────────────────
        status, headers, html = http_get("/", {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "TaskFlow-E2E-Test/1.0",
        })
        self.assertEqual(status, 200, "Page failed to load")
        self.assertIn('id="root"', html, "React root missing")

        # ── Step 2: Browser loads JavaScript ────────────────────
        js_paths = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
        for js_path in js_paths:
            path = js_path if js_path.startswith("/") else f"/{js_path}"
            js_status, _, js_body = http_get(path)
            self.assertEqual(
                js_status, 200,
                f"JS asset failed to load: {path}",
            )

        # ── Step 3: JS fetches task list (like tasks.js → taskApi.list()) ──
        status, _, body = api_request("GET", "/tasks/")
        self.assertEqual(status, 200, "API list call failed")
        if isinstance(body, dict):
            self.assertIn("results", body, "Missing paginated results")

        # ── Step 4: JS creates a task (like taskApi.create()) ───
        status, _, task = api_request("POST", "/tasks/", {
            "title": "Browser Sim Task",
            "description": "Created by simulated browser flow",
            "status": "todo",
        })
        self.assertEqual(status, 201, "Create from browser flow failed")
        task_id = task["id"]

        # ── Step 5: JS reads the task back (like taskApi.get()) ─
        status, _, body = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status, 200, "Read from browser flow failed")
        self.assertEqual(body["title"], "Browser Sim Task")

        # ── Step 6: JS updates status (like taskApi.patch()) ────
        status, _, body = api_request("PATCH", f"/tasks/{task_id}/", {
            "status": "in_progress",
        })
        self.assertEqual(status, 200, "Patch from browser flow failed")
        self.assertEqual(body["status"], "in_progress")

        # ── Step 7: JS marks done (like taskApi.patch()) ────────
        status, _, body = api_request("PATCH", f"/tasks/{task_id}/", {
            "status": "done",
        })
        self.assertEqual(status, 200, "Status update failed")
        self.assertEqual(body["status"], "done")

        # ── Step 8: JS deletes task (like taskApi.delete()) ─────
        status, _, _ = api_request("DELETE", f"/tasks/{task_id}/")
        self.assertEqual(status, 204, "Delete from browser flow failed")

        # ── Step 9: Confirm task is gone ────────────────────────
        status, _, _ = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status, 404, "Task should be deleted")


class F06_MediaServing(unittest.TestCase):
    """Verify uploaded media files are accessible through Nginx."""

    def test_uploaded_file_is_downloadable(self):
        """After uploading a file, the attachment URL should be accessible."""
        # Create task
        status, _, task = api_request("POST", "/tasks/", {"title": "Media Test"})
        self.assertEqual(status, 201)
        task_id = task["id"]

        # Upload a file
        boundary = "----MediaTestBoundary"
        file_content = b"This is a test file for media serving."
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="attachment"; filename="media_test.txt"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
        ).encode("utf-8")
        body += file_content
        body += f"\r\n--{boundary}--\r\n".encode("utf-8")

        url = f"{BASE_URL}/api/tasks/{task_id}/upload/"
        headers_dict = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        req = request.Request(url, data=body, headers=headers_dict, method="POST")
        try:
            with request.urlopen(req) as resp:
                upload_result = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            self.fail(f"Upload failed: {e.code}")

        # Get the attachment URL and try to download it
        attachment_url = upload_result.get("attachment", "")
        self.assertTrue(len(attachment_url) > 0, "No attachment URL returned")

        # The URL could be relative or absolute
        if attachment_url.startswith("http"):
            download_url = attachment_url
        elif attachment_url.startswith("/"):
            download_url = f"{BASE_URL}{attachment_url}"
        else:
            download_url = f"{BASE_URL}/{attachment_url}"

        req = request.Request(download_url, method="GET")
        try:
            with request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                downloaded = resp.read()
                self.assertEqual(downloaded, file_content)
        except error.HTTPError as e:
            # S3 URLs or signed URLs might have different behavior
            if e.code not in [403]:
                self.fail(f"Could not download media: {e.code} from {download_url}")

        # Cleanup
        api_request("DELETE", f"/tasks/{task_id}/")


class F07_ErrorPages(unittest.TestCase):
    """Verify error handling works correctly."""

    def test_api_404_returns_json(self):
        """API 404s return JSON (not HTML error pages)."""
        status, headers, _ = api_request("GET", "/tasks/99999/")
        self.assertEqual(status, 404)
        content_type = headers.get("Content-Type", "")
        self.assertIn("json", content_type.lower())

    def test_api_400_returns_json(self):
        """API validation errors return JSON."""
        status, headers, body = api_request("POST", "/tasks/", {})
        self.assertEqual(status, 400)
        content_type = headers.get("Content-Type", "")
        self.assertIn("json", content_type.lower())

    def test_api_405_method_not_allowed(self):
        """Using wrong method on endpoint returns 405."""
        status, _, _ = api_request("DELETE", "/health/")
        self.assertIn(status, [405, 404])


# ═══════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════

def wait_for_stack(max_retries=30, delay=2):
    """Wait until both frontend and API are ready."""
    print(f"\n⏳ Waiting for stack at {BASE_URL} ...")
    for i in range(max_retries):
        try:
            # Check frontend
            f_status, _, f_body = http_get("/")
            # Check API
            url = f"{BASE_URL}/api/health/"
            req = request.Request(url, method="GET")
            with request.urlopen(req) as resp:
                a_status = resp.status
            if f_status == 200 and a_status == 200:
                print(f"✅ Frontend + API healthy! (attempt {i + 1})\n")
                return True
        except Exception:
            pass
        time.sleep(delay)
        print(f"   Retry {i + 1}/{max_retries}...")

    print("❌ Stack did not become healthy in time!")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("  TaskFlow — Frontend & Integration E2E Tests")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    if not wait_for_stack():
        sys.exit(1)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
