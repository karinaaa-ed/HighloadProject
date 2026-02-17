from django.db import models


class Article(models.Model):
    number = models.IntegerField()
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    summary = models.CharField(max_length=5000)


class MLTask(models.Model):
    TASK_TYPES = (
        ("train", "Training"),
        ("infer", "Inference"),
    )

    task_id = models.CharField(max_length=255, unique=True)
    task_type = models.CharField(max_length=10, choices=TASK_TYPES)
    status = models.CharField(max_length=20)
    result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)