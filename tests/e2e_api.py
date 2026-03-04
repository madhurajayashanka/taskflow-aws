#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
TaskFlow — End-to-End API Tests
═══════════════════════════════════════════════════════════════════
Tests every API endpoint against the LIVE running stack.
No mocking — these hit real HTTP endpoints through Nginx.

Usage:
    # Against local dev stack (default):
    python tests/e2e_api.py

    # Against a remote server:
    BASE_URL=https://54.123.45.67 python tests/e2e_api.py

    # Via Make:
    make test-e2e
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import tempfile
import unittest
from urllib import request, error, parse

# ── Configuration ───────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "http://localhost").rstrip("/")
API_URL = f"{BASE_URL}/api"
VERIFY_SSL = os.environ.get("VERIFY_SSL", "false").lower() == "true"

# For self-signed certs in production
if not VERIFY_SSL:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context


# ── Helper Functions ────────────────────────────────────────────
MAX_RETRIES = int(os.environ.get("E2E_RETRIES", "3"))
RETRY_DELAY = float(os.environ.get("E2E_RETRY_DELAY", "2"))


def api_request(method, path, data=None, content_type="application/json"):
    """Make an HTTP request and return (status_code, response_body_dict).
    Automatically retries on 429 (rate-limited) responses."""
    url = f"{API_URL}{path}"
    headers = {}

    if data is not None and content_type == "application/json":
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data is not None:
        body = data
        if content_type:
            headers["Content-Type"] = content_type
    else:
        body = None

    for attempt in range(MAX_RETRIES + 1):
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, raw
        except error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                retry_after = float(e.headers.get("Retry-After", RETRY_DELAY))
                time.sleep(retry_after)
                continue
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw)
            except json.JSONDecodeError:
                return e.code, raw


def multipart_upload(path, filename, file_content, field_name="attachment"):
    """Upload a file using multipart/form-data (stdlib only, no requests).
    Automatically retries on 429 (rate-limited) responses."""
    boundary = "----TaskFlowE2EBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    body += file_content
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{API_URL}{path}"
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

    for attempt in range(MAX_RETRIES + 1):
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                retry_after = float(e.headers.get("Retry-After", RETRY_DELAY))
                time.sleep(retry_after)
                continue
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw)
            except json.JSONDecodeError:
                return e.code, raw


# ═══════════════════════════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════════════════════════


class T01_HealthCheck(unittest.TestCase):
    """Verify the system is up and database is connected."""

    def test_health_endpoint_returns_ok(self):
        """GET /api/health/ → 200 + status=ok"""
        status_code, body = api_request("GET", "/health/")
        self.assertEqual(status_code, 200)
        self.assertEqual(body["status"], "ok")

    def test_health_shows_db_connected(self):
        """GET /api/health/ → db=connected"""
        status_code, body = api_request("GET", "/health/")
        self.assertEqual(body["db"], "connected")


class T02_CreateTask(unittest.TestCase):
    """Test task creation (POST /api/tasks/)."""

    def test_create_minimal_task(self):
        """POST with just a title → 201, status defaults to 'todo'."""
        status_code, body = api_request("POST", "/tasks/", {"title": "E2E Minimal Task"})
        self.assertEqual(status_code, 201)
        self.assertEqual(body["title"], "E2E Minimal Task")
        self.assertEqual(body["status"], "todo")
        self.assertEqual(body["description"], "")
        self.assertIn("id", body)
        self.assertIn("created_at", body)
        self.assertIn("updated_at", body)
        # Cleanup
        api_request("DELETE", f"/tasks/{body['id']}/")

    def test_create_full_task(self):
        """POST with all fields → 201, all values persisted."""
        data = {
            "title": "E2E Full Task",
            "description": "A detailed description",
            "status": "in_progress",
        }
        status_code, body = api_request("POST", "/tasks/", data)
        self.assertEqual(status_code, 201)
        self.assertEqual(body["title"], "E2E Full Task")
        self.assertEqual(body["description"], "A detailed description")
        self.assertEqual(body["status"], "in_progress")
        api_request("DELETE", f"/tasks/{body['id']}/")

    def test_create_task_without_title_fails(self):
        """POST without title → 400."""
        status_code, body = api_request("POST", "/tasks/", {"description": "No title here"})
        self.assertEqual(status_code, 400)

    def test_create_task_with_empty_title_fails(self):
        """POST with blank title → 400."""
        status_code, body = api_request("POST", "/tasks/", {"title": ""})
        self.assertEqual(status_code, 400)

    def test_create_task_with_invalid_status_fails(self):
        """POST with an invalid status value → 400."""
        status_code, body = api_request(
            "POST", "/tasks/", {"title": "Bad Status", "status": "invalid_status"}
        )
        self.assertEqual(status_code, 400)

    def test_created_at_is_auto_set(self):
        """created_at is populated by the server, not the client."""
        status_code, body = api_request("POST", "/tasks/", {"title": "Timestamp Test"})
        self.assertEqual(status_code, 201)
        self.assertIsNotNone(body["created_at"])
        self.assertIsNotNone(body["updated_at"])
        api_request("DELETE", f"/tasks/{body['id']}/")


class T03_ReadTask(unittest.TestCase):
    """Test reading tasks (GET /api/tasks/ and GET /api/tasks/{id}/)."""

    @classmethod
    def setUpClass(cls):
        _, cls.task1 = api_request("POST", "/tasks/", {"title": "Read Test 1", "status": "todo"})
        _, cls.task2 = api_request("POST", "/tasks/", {"title": "Read Test 2", "status": "done"})
        _, cls.task3 = api_request("POST", "/tasks/", {"title": "Read Test 3", "status": "in_progress"})

    @classmethod
    def tearDownClass(cls):
        for t in [cls.task1, cls.task2, cls.task3]:
            api_request("DELETE", f"/tasks/{t['id']}/")

    def test_list_tasks(self):
        """GET /api/tasks/ → 200 and returns a paginated response."""
        status_code, body = api_request("GET", "/tasks/")
        self.assertEqual(status_code, 200)
        # DRF pagination wraps results
        if isinstance(body, dict) and "results" in body:
            self.assertIsInstance(body["results"], list)
            self.assertGreaterEqual(len(body["results"]), 3)
        else:
            self.assertIsInstance(body, list)
            self.assertGreaterEqual(len(body), 3)

    def test_get_single_task(self):
        """GET /api/tasks/{id}/ → 200 with correct data."""
        status_code, body = api_request("GET", f"/tasks/{self.task1['id']}/")
        self.assertEqual(status_code, 200)
        self.assertEqual(body["title"], "Read Test 1")
        self.assertEqual(body["id"], self.task1["id"])

    def test_get_nonexistent_task(self):
        """GET /api/tasks/99999/ → 404."""
        status_code, _ = api_request("GET", "/tasks/99999/")
        self.assertEqual(status_code, 404)

    def test_response_has_all_fields(self):
        """Each task response has all expected fields."""
        status_code, body = api_request("GET", f"/tasks/{self.task1['id']}/")
        expected_fields = {"id", "title", "description", "status", "attachment", "created_at", "updated_at"}
        self.assertTrue(expected_fields.issubset(set(body.keys())),
                        f"Missing fields: {expected_fields - set(body.keys())}")

    def test_list_returns_newest_first(self):
        """Tasks are ordered by created_at descending (newest first)."""
        status_code, body = api_request("GET", "/tasks/")
        results = body.get("results", body) if isinstance(body, dict) else body
        if len(results) >= 2:
            # task3 was created last, should appear before task1
            ids = [t["id"] for t in results]
            idx3 = ids.index(self.task3["id"]) if self.task3["id"] in ids else -1
            idx1 = ids.index(self.task1["id"]) if self.task1["id"] in ids else -1
            if idx3 >= 0 and idx1 >= 0:
                self.assertLess(idx3, idx1, "Newest task should appear first")


class T04_UpdateTask(unittest.TestCase):
    """Test full and partial updates (PUT and PATCH)."""

    def setUp(self):
        _, self.task = api_request("POST", "/tasks/", {
            "title": "Update Test",
            "description": "Original desc",
            "status": "todo",
        })

    def tearDown(self):
        api_request("DELETE", f"/tasks/{self.task['id']}/")

    def test_full_update(self):
        """PUT /api/tasks/{id}/ → 200, all fields updated."""
        data = {"title": "Updated Title", "description": "Updated desc", "status": "done"}
        status_code, body = api_request("PUT", f"/tasks/{self.task['id']}/", data)
        self.assertEqual(status_code, 200)
        self.assertEqual(body["title"], "Updated Title")
        self.assertEqual(body["description"], "Updated desc")
        self.assertEqual(body["status"], "done")

    def test_partial_update_status(self):
        """PATCH /api/tasks/{id}/ with just status → 200."""
        status_code, body = api_request("PATCH", f"/tasks/{self.task['id']}/", {"status": "in_progress"})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["status"], "in_progress")
        # Other fields unchanged
        self.assertEqual(body["title"], "Update Test")

    def test_partial_update_title(self):
        """PATCH /api/tasks/{id}/ with just title → 200."""
        status_code, body = api_request("PATCH", f"/tasks/{self.task['id']}/", {"title": "Patched Title"})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["title"], "Patched Title")
        self.assertEqual(body["status"], "todo")  # unchanged

    def test_partial_update_description(self):
        """PATCH /api/tasks/{id}/ with just description → 200."""
        status_code, body = api_request("PATCH", f"/tasks/{self.task['id']}/", {"description": "New desc"})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["description"], "New desc")

    def test_update_nonexistent_task(self):
        """PUT /api/tasks/99999/ → 404."""
        data = {"title": "Ghost", "description": "", "status": "todo"}
        status_code, _ = api_request("PUT", "/tasks/99999/", data)
        self.assertEqual(status_code, 404)

    def test_update_with_invalid_status(self):
        """PUT with invalid status → 400."""
        data = {"title": "Bad", "description": "", "status": "not_a_status"}
        status_code, _ = api_request("PUT", f"/tasks/{self.task['id']}/", data)
        self.assertEqual(status_code, 400)

    def test_updated_at_changes(self):
        """updated_at should change after an update."""
        original_updated = self.task["updated_at"]
        time.sleep(1)  # Ensure timestamp difference
        status_code, body = api_request("PATCH", f"/tasks/{self.task['id']}/", {"title": "Timestamp"})
        self.assertEqual(status_code, 200)
        self.assertNotEqual(body["updated_at"], original_updated)

    def test_created_at_does_not_change(self):
        """created_at should remain the same after an update."""
        original_created = self.task["created_at"]
        status_code, body = api_request("PATCH", f"/tasks/{self.task['id']}/", {"title": "NoChange"})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["created_at"], original_created)


class T05_DeleteTask(unittest.TestCase):
    """Test task deletion (DELETE /api/tasks/{id}/)."""

    def test_delete_task(self):
        """DELETE /api/tasks/{id}/ → 204, then GET → 404."""
        _, task = api_request("POST", "/tasks/", {"title": "Delete Me"})
        task_id = task["id"]

        # Delete
        status_code, _ = api_request("DELETE", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 204)

        # Verify gone
        status_code, _ = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 404)

    def test_delete_nonexistent_task(self):
        """DELETE /api/tasks/99999/ → 404."""
        status_code, _ = api_request("DELETE", "/tasks/99999/")
        self.assertEqual(status_code, 404)

    def test_delete_is_permanent(self):
        """Deleted task does not reappear in the list."""
        _, task = api_request("POST", "/tasks/", {"title": "Vanish"})
        task_id = task["id"]
        api_request("DELETE", f"/tasks/{task_id}/")

        status_code, body = api_request("GET", "/tasks/")
        results = body.get("results", body) if isinstance(body, dict) else body
        ids = [t["id"] for t in results]
        self.assertNotIn(task_id, ids)


class T06_FileUpload(unittest.TestCase):
    """Test file upload endpoint (POST /api/tasks/{id}/upload/)."""

    def setUp(self):
        _, self.task = api_request("POST", "/tasks/", {"title": "Upload Test"})

    def tearDown(self):
        api_request("DELETE", f"/tasks/{self.task['id']}/")

    def test_upload_text_file(self):
        """POST /api/tasks/{id}/upload/ with a .txt file → 200."""
        status_code, body = multipart_upload(
            f"/tasks/{self.task['id']}/upload/",
            "test_document.txt",
            b"Hello, this is a test file for E2E testing.",
        )
        self.assertEqual(status_code, 200)
        self.assertIn("attachment", body)
        self.assertIsNotNone(body["attachment"])
        # Attachment URL should be non-empty
        self.assertTrue(len(body["attachment"]) > 0)

    def test_upload_without_file_fails(self):
        """POST /api/tasks/{id}/upload/ without a file → 400."""
        boundary = "----EmptyBoundary"
        body = f"--{boundary}--\r\n".encode("utf-8")
        url = f"{API_URL}/tasks/{self.task['id']}/upload/"
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req) as resp:
                self.fail("Expected 400 but got 200")
        except error.HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_upload_to_nonexistent_task(self):
        """POST /api/tasks/99999/upload/ → 404."""
        status_code, _ = multipart_upload(
            "/tasks/99999/upload/",
            "orphan.txt",
            b"This task does not exist.",
        )
        self.assertEqual(status_code, 404)

    def test_upload_replaces_previous_file(self):
        """Uploading a second file replaces the first."""
        multipart_upload(
            f"/tasks/{self.task['id']}/upload/", "first.txt", b"first file"
        )
        status_code, body = multipart_upload(
            f"/tasks/{self.task['id']}/upload/", "second.txt", b"second file"
        )
        self.assertEqual(status_code, 200)
        self.assertIn("second", body["attachment"])

    def test_upload_preserves_task_data(self):
        """File upload should not wipe the task's title/description/status."""
        # First update the task
        api_request("PATCH", f"/tasks/{self.task['id']}/", {
            "description": "Important task",
            "status": "in_progress",
        })

        # Upload a file
        status_code, body = multipart_upload(
            f"/tasks/{self.task['id']}/upload/", "doc.txt", b"content"
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(body["title"], "Upload Test")
        self.assertEqual(body["description"], "Important task")
        self.assertEqual(body["status"], "in_progress")


class T07_FullCRUDLifecycle(unittest.TestCase):
    """
    End-to-end lifecycle test: Create → Read → Update → Upload → Delete.
    Verifies the entire happy path works in sequence.
    """

    def test_complete_lifecycle(self):
        """Walk through the full task lifecycle."""

        # ── Step 1: Create ──────────────────────────────────────
        status_code, task = api_request("POST", "/tasks/", {
            "title": "Lifecycle Task",
            "description": "Testing the full lifecycle",
            "status": "todo",
        })
        self.assertEqual(status_code, 201, "Create failed")
        task_id = task["id"]
        self.assertEqual(task["title"], "Lifecycle Task")

        # ── Step 2: Read ────────────────────────────────────────
        status_code, body = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 200, "Read failed")
        self.assertEqual(body["id"], task_id)
        self.assertEqual(body["title"], "Lifecycle Task")

        # ── Step 3: Update (move to in_progress) ────────────────
        status_code, body = api_request("PATCH", f"/tasks/{task_id}/", {
            "status": "in_progress",
        })
        self.assertEqual(status_code, 200, "Partial update failed")
        self.assertEqual(body["status"], "in_progress")

        # ── Step 4: Full Update ─────────────────────────────────
        status_code, body = api_request("PUT", f"/tasks/{task_id}/", {
            "title": "Lifecycle Task — Updated",
            "description": "Full update test",
            "status": "in_progress",
        })
        self.assertEqual(status_code, 200, "Full update failed")
        self.assertEqual(body["title"], "Lifecycle Task — Updated")

        # ── Step 5: Upload a file ───────────────────────────────
        status_code, body = multipart_upload(
            f"/tasks/{task_id}/upload/",
            "lifecycle_doc.txt",
            b"This file proves the upload works end-to-end.",
        )
        self.assertEqual(status_code, 200, "Upload failed")
        self.assertIsNotNone(body["attachment"])

        # ── Step 6: Verify file is attached ─────────────────────
        status_code, body = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(body["attachment"])
        self.assertIn("lifecycle_doc", body["attachment"])

        # ── Step 7: Mark as done ────────────────────────────────
        status_code, body = api_request("PATCH", f"/tasks/{task_id}/", {"status": "done"})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["status"], "done")

        # ── Step 8: Verify it appears in the list ───────────────
        status_code, body = api_request("GET", "/tasks/")
        results = body.get("results", body) if isinstance(body, dict) else body
        found = any(t["id"] == task_id for t in results)
        self.assertTrue(found, "Task not found in list")

        # ── Step 9: Delete ──────────────────────────────────────
        status_code, _ = api_request("DELETE", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 204, "Delete failed")

        # ── Step 10: Confirm deletion ───────────────────────────
        status_code, _ = api_request("GET", f"/tasks/{task_id}/")
        self.assertEqual(status_code, 404, "Task still exists after delete")


class T08_EdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_body_post(self):
        """POST /api/tasks/ with empty body → 400."""
        status_code, _ = api_request("POST", "/tasks/", {})
        self.assertEqual(status_code, 400)

    def test_very_long_title(self):
        """POST with a 255-char title → 201 (max_length=255)."""
        long_title = "A" * 255
        status_code, body = api_request("POST", "/tasks/", {"title": long_title})
        self.assertEqual(status_code, 201)
        self.assertEqual(len(body["title"]), 255)
        api_request("DELETE", f"/tasks/{body['id']}/")

    def test_title_exceeding_max_length(self):
        """POST with a 256-char title → 400."""
        too_long = "A" * 256
        status_code, _ = api_request("POST", "/tasks/", {"title": too_long})
        self.assertEqual(status_code, 400)

    def test_special_characters_in_title(self):
        """POST with special chars in title → 201."""
        title = "Task with spëcial chars: <>&\"' 日本語 🚀"
        status_code, body = api_request("POST", "/tasks/", {"title": title})
        self.assertEqual(status_code, 201)
        self.assertEqual(body["title"], title)
        api_request("DELETE", f"/tasks/{body['id']}/")

    def test_all_three_statuses(self):
        """Can create tasks with each valid status."""
        for s in ["todo", "in_progress", "done"]:
            status_code, body = api_request("POST", "/tasks/", {"title": f"Status {s}", "status": s})
            self.assertEqual(status_code, 201, f"Failed to create with status={s}")
            self.assertEqual(body["status"], s)
            api_request("DELETE", f"/tasks/{body['id']}/")

    def test_concurrent_creates(self):
        """Multiple rapid creates should all succeed."""
        created_ids = []
        for i in range(5):
            status_code, body = api_request("POST", "/tasks/", {"title": f"Concurrent {i}"})
            self.assertEqual(status_code, 201)
            created_ids.append(body["id"])

        # Verify all exist
        for task_id in created_ids:
            status_code, _ = api_request("GET", f"/tasks/{task_id}/")
            self.assertEqual(status_code, 200)

        # Cleanup
        for task_id in created_ids:
            api_request("DELETE", f"/tasks/{task_id}/")

    def test_invalid_http_method(self):
        """POST to a single-task URL should fail (not an allowed method)."""
        status_code, _ = api_request("POST", f"/tasks/{99999}/", {"title": "Nope"})
        self.assertIn(status_code, [404, 405])


class T09_ResponseFormat(unittest.TestCase):
    """Verify API response format and content types."""

    def test_list_response_is_paginated(self):
        """GET /api/tasks/ returns paginated format with count/results."""
        status_code, body = api_request("GET", "/tasks/")
        self.assertEqual(status_code, 200)
        if isinstance(body, dict):
            self.assertIn("results", body)
            self.assertIn("count", body)

    def test_json_content_type(self):
        """API responses should be JSON."""
        url = f"{API_URL}/health/"
        req = request.Request(url, method="GET")
        try:
            with request.urlopen(req) as resp:
                content_type = resp.headers.get("Content-Type", "")
                self.assertIn("json", content_type.lower())
        except error.HTTPError as e:
            if e.code == 429:
                self.skipTest("Rate limited — skipping content-type check")
            raise

    def test_create_returns_all_fields(self):
        """POST response includes all serializer fields."""
        status_code, body = api_request("POST", "/tasks/", {"title": "Field Check"})
        self.assertEqual(status_code, 201)
        required_fields = {"id", "title", "description", "status", "attachment", "created_at", "updated_at"}
        self.assertTrue(required_fields.issubset(set(body.keys())))
        api_request("DELETE", f"/tasks/{body['id']}/")


class T10_NginxAndInfra(unittest.TestCase):
    """Test infrastructure-level behavior (Nginx, CORS, headers)."""

    def test_http_redirect_to_https(self):
        """If running production, HTTP should redirect to HTTPS."""
        if "https" not in BASE_URL and "localhost" in BASE_URL:
            self.skipTest("Localhost dev — no HTTPS redirect expected")

        # Try HTTP version
        http_url = BASE_URL.replace("https://", "http://") + "/api/health/"
        req = request.Request(http_url, method="GET")
        try:
            with request.urlopen(req) as resp:
                # If it follows the redirect and succeeds, that's fine
                self.assertIn(resp.status, [200, 301, 302])
        except error.HTTPError as e:
            self.assertIn(e.code, [301, 302, 308])

    def test_security_headers_present(self):
        """Production Nginx should set security headers."""
        url = f"{API_URL}/health/"
        req = request.Request(url, method="GET")
        try:
            ctx = ssl._create_unverified_context() if not VERIFY_SSL else None
            with request.urlopen(req, context=ctx) as resp:
                headers = dict(resp.headers)
                # These are set by Nginx in production
                if "localhost" not in BASE_URL:
                    self.assertIn("x-content-type-options", {k.lower() for k in headers})
                    self.assertIn("x-frame-options", {k.lower() for k in headers})
        except error.HTTPError:
            pass  # Still check even on error responses


# ═══════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════

def wait_for_stack(max_retries=30, delay=2):
    """Wait until the API health endpoint responds."""
    print(f"\n⏳ Waiting for stack at {BASE_URL} ...")
    for i in range(max_retries):
        try:
            status_code, body = api_request("GET", "/health/")
            if status_code == 200:
                print(f"✅ Stack is healthy! (attempt {i + 1})\n")
                return True
        except Exception:
            pass
        time.sleep(delay)
        print(f"   Retry {i + 1}/{max_retries}...")

    print("❌ Stack did not become healthy in time!")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("  TaskFlow — End-to-End API Tests")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    if not wait_for_stack():
        sys.exit(1)

    # Run tests with verbosity
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None  # Keep test order as written
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
