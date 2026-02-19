import pickle
import scipy.sparse
import scipy.spatial
import pandas as pd
import requests
import bs4
from heapq import heappush, heappop
from urllib.parse import unquote, urlparse

from celery import shared_task
from sklearn.feature_extraction.text import TfidfVectorizer

from main.models import Article, MLTask


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
        title = heading.text.strip() if heading else fallback_title

        paragraphs = [p.get_text(" ", strip=True) for p in html.select("#mw-content-text p") if p.get_text(strip=True)]
        content = " ".join(paragraphs[:25]).strip()
        if not content:
            content = title

        return content
    except Exception:
        return fallback_title


# Training
@shared_task(bind=True)
def train_model_task(self, num_articles):
    task = MLTask.objects.get(task_id=self.request.id)
    task.status = "STARTED"
    task.save()

    try:
        max_articles_train = int(num_articles)

        Article.objects.all().delete()
        data = pd.read_csv("wiki_movie_plots_deduped.csv").sample(max_articles_train)

        text_corpus = list(data.Plot)

        articles = [
            Article(
                number=i,
                title=data.iloc[i].Title[:100],
                url=data.iloc[i]["Wiki Page"][:100],
                summary=data.iloc[i].Plot[:4000],
            )
            for i in range(data.shape[0])
        ]
        Article.objects.bulk_create(articles)

        model = TfidfVectorizer(
            analyzer="word",
            stop_words="english",
            strip_accents="ascii",
        )
        matrix = model.fit_transform(text_corpus)

        with open("model.pickle", "wb") as f:
            pickle.dump(model, f)

        scipy.sparse.save_npz("data.npz", matrix)

        task.status = "SUCCESS"

    except Exception as e:
        task.status = "FAILURE"
        task.result = str(e)

    task.save()

# Inference
@shared_task(bind=True)
def inference_task(self, url, cnt):
    task = MLTask.objects.get(task_id=self.request.id)
    task.status = "STARTED"
    task.save()

    try:
        content = _build_query_content(url)

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
            if len(top) > cnt:
                heappop(top)

        result_ids = [num for _, num in sorted(top, reverse=True)]
        task.result = ",".join(map(str, result_ids))
        task.status = "SUCCESS"

    except Exception as e:
        task.status = "FAILURE"
        task.result = str(e)

    task.save()
