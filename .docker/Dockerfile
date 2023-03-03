FROM python:3.11-slim as base

COPY requirements.txt requirements.txt
RUN python -m pip --disable-pip-version-check --no-cache-dir install -r requirements.txt \ 
    && rm -rf requirements.txt

COPY ["models.py", "utils.py", "database.py", "rss/"]
COPY ["client/__main__.py", "rss/client/__main__.py"]
COPY ["server/__main__.py", "server/feed_generator.py", "rss/server/"]

ENTRYPOINT [ "python", "-m", "rss.server"]
