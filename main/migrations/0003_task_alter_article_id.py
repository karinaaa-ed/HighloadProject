import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_article_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("train", "Train model"),
                            ("infer", "Infer similar films"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                (
                    "queue",
                    models.CharField(
                        choices=[("heavy", "Heavy"), ("light", "Light")], max_length=16
                    ),
                ),
                ("priority", models.IntegerField(default=0)),
                ("payload", models.JSONField(default=dict)),
                ("result", models.JSONField(default=dict)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name="article",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]