from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Task objects.

    list:    GET    /api/tasks/
    create:  POST   /api/tasks/
    read:    GET    /api/tasks/{id}/
    update:  PUT    /api/tasks/{id}/
    partial: PATCH  /api/tasks/{id}/
    delete:  DELETE /api/tasks/{id}/
    upload:  POST   /api/tasks/{id}/upload/
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(
        detail=True,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        url_path='upload',
    )
    def upload(self, request, pk=None):
        """Upload a file attachment to an existing task."""
        task = self.get_object()
        file = request.FILES.get('attachment')

        if not file:
            return Response(
                {'error': 'No file provided. Send as "attachment" field.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete old attachment if it exists
        if task.attachment:
            task.attachment.delete(save=False)

        task.attachment = file
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for Docker / load balancer probes.
    Returns DB connectivity status.
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        return Response({'status': 'ok', 'db': 'connected'})
    except Exception:
        return Response(
            {'status': 'error', 'db': 'disconnected'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
