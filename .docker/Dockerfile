FROM python:3.11-slim as base

COPY requirements.txt requirements.txt
RUN python -m pip --disable-pip-version-check --no-cache-dir install -r requirements.txt \ 
    && rm -rf requirements.txt

COPY ["RSS/models.py", "RSS/utils.py", "RSS/"]
COPY ["RSS/client/__main__.py", "RSS/client/__main__.py"]
COPY ["RSS/server/__main__.py", "RSS/server/feed_generator.py", "RSS/server/"]

ENTRYPOINT [ "python", "-m", "RSS.server"]
