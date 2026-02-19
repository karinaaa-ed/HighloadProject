import os
import pickle
from heapq import heappush, heappop
from urllib.parse import unquote, urlparse

import bs4
import requests
import scipy.sparse
import scipy.spatial

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from main.models import Article, MLTask
from main.tasks import train_model_task, inference_task


WIKIPEDIA_HEADERS = {
    "User-Agent": "HighloadProjectBot/1.0 (+https://localhost)"
}

def _extract_title_from_url(source_url):
    path = urlparse(source_url).path
    slug = path.rsplit('/', 1)[-1] if path else ''
    slug = unquote(slug).replace('_', ' ').strip()
    return slug or "Unknown title"


def _build_query_content(source_url):
    fallback_title = _extract_title_from_url(source_url)

    try:
        response = requests.get(source_url, timeout=10, headers=WIKIPEDIA_HEADERS)
        response.raise_for_status()
        html = bs4.BeautifulSoup(response.text, "html.parser")
        heading = html.select_one("#firstHeading")
        query_film = heading.text.strip() if heading else fallback_title

        paragraphs = [p.get_text(" ", strip=True) for p in html.select("#mw-content-text p") if p.get_text(strip=True)]
        content = " ".join(paragraphs[:25]).strip()
        if not content:
            content = query_film

        return query_film, content
    except Exception:
        return fallback_title, fallback_title


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

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "task_id": async_task.id,
            "status": "PENDING",
            "message": "Задача обучения отправлена в очередь"
        })

    return render(request, "main/train_status.html", {"task_id": async_task.id})


@require_http_methods(["GET"])
def get_similar(request):
    source_url = request.GET.get("url")
    limit = int(request.GET.get("cnt", 5))

    if not source_url:
        return render(request, "main/index.html", {
            "error_message": "Введите ссылку на статью Wikipedia."
        })

    try:
        query_film, content = _build_query_content(source_url)

        with open("model.pickle", "rb") as f:
            model = pickle.load(f)

        data = scipy.sparse.load_npz("data.npz")
        query_vec = model.transform([content]).toarray()

        top = []
        for i, row in enumerate(data):
            dist = scipy.spatial.distance.euclidean(
                row.toarray().reshape(-1),
                query_vec.reshape(-1)
            )
            heappush(top, (-dist, i))
            if len(top) > limit:
                heappop(top)

        result_ids = [num for _, num in sorted(top, reverse=True)]
        films_by_number = {film.number: film for film in Article.objects.filter(number__in=result_ids)}
        films = [films_by_number[number] for number in result_ids if number in films_by_number]

        if not films:
            return render(request, "main/index.html", {
                "error_message": "Похожие фильмы не найдены. Попробуйте переобучить модель и повторить запрос."
            })

        return render(request, "main/get_similar.html", {
            "query_film": query_film,
            "films": films,
        })
    except Exception as exc:
        return render(request, "main/index.html", {
            "error_message": f"Не удалось получить похожие фильмы: {exc}"
        })


@require_http_methods(["GET"])
def get_similar_async(request):
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
