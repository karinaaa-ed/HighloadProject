import os
import pickle
import uuid
from heapq import heappush, heappop

import bs4
import wikipedia
import requests
import scipy.sparse
import pandas as pd

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from main.models import Article, MLTask
from main.tasks import train_model_task, inference_task


def index(request):
    model_ready = os.path.exists("model.pickle") and os.path.exists("data.npz")
    template = "main/index.html" if model_ready else "main/need_train.html"
    return render(request, template)


@require_http_methods(["POST", "GET"])
def train(request):
    if request.method == "GET":
        return render(request, "main/train_form.html")

    num_articles = int(request.POST.get("num_articles", 20000))

    async_task = train_model_task.delay(num_articles)

    MLTask.objects.create(
        task_id=async_task.id,
        task_type="train",
        status="PENDING"
    )

    return JsonResponse({
        "task_id": async_task.id,
        "status": "PENDING",
        "message": "Задача обучения отправлена в очередь"
    })


@require_http_methods(["POST", "GET"])
def train(request):
    if request.method == "GET":
        return render(request, "main/train_form.html")

    num_articles = int(request.POST.get("num_articles", 20000))

    async_task = train_model_task.delay(num_articles)

    MLTask.objects.create(
        task_id=async_task.id,
        task_type="train",
        status="PENDING"
    )

    return JsonResponse({
        "task_id": async_task.id,
        "status": "PENDING",
        "message": "Задача обучения отправлена в очередь"
    })


@require_http_methods(["GET"])
def get_similar(request):
    source_url = request.GET.get("url")
    limit = int(request.GET.get("cnt", 5))

    async_task = inference_task.delay(source_url, limit)

    MLTask.objects.create(
        task_id=async_task.id,
        task_type="infer",
        status="PENDING"
    )

    return JsonResponse({
        "task_id": async_task.id,
        "status": "PENDING"
    })


def task_status(request, task_id):
    try:
        task = MLTask.objects.get(task_id=task_id)
    except MLTask.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    payload = {
        "task_id": task.task_id,
        "type": task.task_type,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }

    if task.result:
        payload["result"] = task.result

    return JsonResponse(payload)


def tasks_overview(request):
    tasks = MLTask.objects.order_by("-created_at")[:50]

    return JsonResponse({
        "count": tasks.count(),
        "tasks": [
            {
                "task_id": t.task_id,
                "type": t.task_type,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    })
