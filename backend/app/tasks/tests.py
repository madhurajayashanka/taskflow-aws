from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task


class TaskModelTest(TestCase):
    """Tests for the Task model."""

    def test_create_task_defaults(self):
        task = Task.objects.create(title='Test Task')
        self.assertEqual(task.status, 'todo')
        self.assertEqual(task.description, '')
        self.assertIsNone(task.attachment.name)
        self.assertIsNotNone(task.created_at)

    def test_str_representation(self):
        task = Task.objects.create(title='My Task', status='in_progress')
        self.assertIn('In Progress', str(task))
        self.assertIn('My Task', str(task))


class TaskAPITest(TestCase):
    """Tests for the Task API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.task_data = {
            'title': 'Test Task',
            'description': 'A task for testing',
            'status': 'todo',
        }
        self.task = Task.objects.create(**self.task_data)

    def test_list_tasks(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_task(self):
        data = {'title': 'New Task', 'description': 'New description'}
        response = self.client.post('/api/tasks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Task')
        self.assertEqual(response.data['status'], 'todo')

    def test_create_task_without_title_fails(self):
        response = self.client.post('/api/tasks/', {'description': 'No title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_task(self):
        response = self.client.get(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Task')

    def test_update_task(self):
        data = {'title': 'Updated Task', 'description': 'Updated', 'status': 'done'}
        response = self.client.put(
            f'/api/tasks/{self.task.id}/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['status'], 'done')

    def test_partial_update_task(self):
        response = self.client.patch(
            f'/api/tasks/{self.task.id}/',
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_delete_task(self):
        response = self.client.delete(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_get_nonexistent_task(self):
        response = self.client.get('/api/tasks/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_tasks_by_status(self):
        Task.objects.create(title='Done Task', status='done')
        response = self.client.get('/api/tasks/?status=done')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_task_with_all_fields(self):
        data = {
            'title': 'Full Task',
            'description': 'Desc',
            'status': 'in_progress',
        }
        response = self.client.post('/api/tasks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'in_progress')


class TaskFileUploadTest(TestCase):
    """Tests for the file upload endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.task = Task.objects.create(title='Upload Test Task')

    def test_upload_file(self):
        """POST /api/tasks/{id}/upload/ with a file attachment."""
        file = SimpleUploadedFile(
            'testfile.txt', b'file content here', content_type='text/plain'
        )
        response = self.client.post(
            f'/api/tasks/{self.task.id}/upload/',
            {'attachment': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', response.data)
        self.assertIsNotNone(response.data['attachment'])

    def test_upload_without_file_fails(self):
        """POST /api/tasks/{id}/upload/ without a file returns 400."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/upload/',
            {},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_replaces_existing_file(self):
        """Uploading a new file replaces the old attachment."""
        file1 = SimpleUploadedFile('file1.txt', b'first', content_type='text/plain')
        self.client.post(
            f'/api/tasks/{self.task.id}/upload/',
            {'attachment': file1},
            format='multipart',
        )
        file2 = SimpleUploadedFile('file2.txt', b'second', content_type='text/plain')
        response = self.client.post(
            f'/api/tasks/{self.task.id}/upload/',
            {'attachment': file2},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('file2', response.data['attachment'])

    def test_upload_to_nonexistent_task(self):
        """Upload to a task that doesn't exist returns 404."""
        file = SimpleUploadedFile('test.txt', b'data', content_type='text/plain')
        response = self.client.post(
            '/api/tasks/9999/upload/',
            {'attachment': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HealthCheckTest(TestCase):
    """Tests for the health check endpoint."""

    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['db'], 'connected')
