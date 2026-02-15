# Python review 2 Django web service

## Описание
Проект представляет собой Django-сервис для поиска похожих фильмов по статье в Wikipedia.

## Требования
* Python 3.11+
* Docker (для контейнерного запуска)

## Запуск без Docker
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Примените миграции:
   ```bash
   python manage.py migrate
   ```
3. Запустите сервер:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
4. Откройте в браузере: `http://localhost:8000/`.

## Запуск в Docker
### Сборка образа
```bash
docker build -t highload-project .
```

### Запуск контейнера
```bash
docker run --rm -p 8000:8000 highload-project
```
Контейнер при старте автоматически выполняет `python manage.py migrate`.
После запуска сервис будет доступен по адресу: `http://localhost:8000/`.

### Остановка и удаление контейнера
Если контейнер запускался в фоне, используйте точные команды:
```bash
docker run -d --name highload-project -p 8000:8000 highload-project
docker stop highload-project
docker rm highload-project
```
Если контейнер запускался с `--rm`, он удалится автоматически после остановки.

### Проверка функционала
После запуска контейнера убедитесь, что сервис отвечает:
```bash
curl -f http://localhost:8000/
```
Для проверки страницы обучения (при наличии CSV-файла):
```bash
curl -f http://localhost:8000/train/
```

## Запуск через docker-compose (PostgreSQL)
1. Соберите и запустите сервисы:
   ```bash
   docker-compose up --build
   ```
2. Откройте в браузере: `http://localhost:8000/` (запросы идут через frontend на backend).
3. Остановить и удалить контейнеры и данные:
   ```bash
   docker-compose down -v
   ```
4. Инициализация базы данных выполняется автоматически при первом запуске:
   ```bash
   ls docker/db/init
   ```
   Файлы из `docker/db/init` монтируются в `/docker-entrypoint-initdb.d`.

### Обучение модели
Страница `/train` требует файл `wiki_movie_plots_deduped.csv` в корне проекта.
Если вы хотите обучать модель внутри контейнера, передайте файл через volume:
```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/wiki_movie_plots_deduped.csv:/app/wiki_movie_plots_deduped.csv" \
  -e num_articles=1000 \
  highload-project
```
Параметр `num_articles` задаёт количество фильмов для обучения (по умолчанию 1000).

## Функционал сервиса
* `/` — форма для ввода ссылки на статью о фильме в Википедии и количества похожих фильмов.
* `/train` — обучение модели (требует CSV-файл с описаниями фильмов).

После обучения модель сохраняется в `model.pickle` и `data.npz` и используется для поиска похожих фильмов.
