FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y --no-install-recommends git

COPY requirements.txt requirements.txt
RUN python -m pip --disable-pip-version-check --no-cache-dir install -r requirements.txt \ 
    && rm -rf requirements.txt

RUN apt-get remove -y git && apt-get -y autoremove

COPY ["RSS/models.py", "RSS/utils.py", "RSS/"]
COPY ["RSS/client/__main__.py", "RSS/client/__main__.py"]
COPY ["RSS/webhooks/", "RSS/webhooks/"]
COPY ["RSS/server/__main__.py", "RSS/server/feed_generator.py", "RSS/server/"]

ENTRYPOINT [ "python", "-m", "RSS.server"]
