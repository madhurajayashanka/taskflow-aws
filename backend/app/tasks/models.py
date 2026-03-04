from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


def validate_file_size(value):
    """Restrict file uploads to 10MB maximum."""
    max_size = 10 * 1024 * 1024  # 10MB
    if value.size > max_size:
        raise ValidationError(
            f'File size {value.size / (1024*1024):.1f}MB exceeds the 10MB limit.'
        )


class Task(models.Model):
    """A single task in the TaskFlow application."""

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    ALLOWED_EXTENSIONS = [
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'doc', 'docx',
        'xls', 'xlsx', 'csv', 'zip', 'tar', 'gz',
    ]

    title = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
    )
    attachment = models.FileField(
        upload_to='attachments/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=[
                'pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'doc', 'docx',
                'xls', 'xlsx', 'csv', 'zip', 'tar', 'gz',
            ]),
            validate_file_size,
        ],
        help_text='Allowed: PDF, images, text, docs, spreadsheets, archives. Max 10MB.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"
