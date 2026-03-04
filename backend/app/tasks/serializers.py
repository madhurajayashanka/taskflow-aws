from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for the Task model — handles all CRUD fields."""

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'attachment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
