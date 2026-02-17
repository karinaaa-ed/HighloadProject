import os
import pickle
import scipy.sparse
import scipy.spatial
import pandas as pd
import wikipedia
import requests
import bs4
from heapq import heappush, heappop

from celery import shared_task
from sklearn.feature_extraction.text import TfidfVectorizer

from main.models import Article, MLTask

# Training
@shared_task(bind=True)
def train_model_task(self):
    task = MLTask.objects.get(task_id=self.request.id)
    task.status = "STARTED"
    task.save()

    try:
        max_articles_train = int(os.environ.get("num_articles", 1000))

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
        response = requests.get(url, timeout=10)
        html = bs4.BeautifulSoup(response.text, "html.parser")
        title = html.select("#firstHeading")[0].text

        page = wikipedia.page(title)
        content = page.content

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
