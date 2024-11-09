FROM cgr.dev/chainguard/python:latest-dev AS dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONBUFFERED=1

WORKDIR /app

RUN python -m venv /app/.venv
COPY requirements.txt ./
RUN python -m pip --disable-pip-version-check --no-cache-dir install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONBUFFERED=1

COPY --from=dev /app/.venv /app/.venv
WORKDIR /app

COPY ["RSS/models.py", "RSS/utils.py", "RSS/"]
COPY ["RSS/client/__main__.py", "RSS/client/__main__.py"]
COPY ["RSS/webhooks/", "RSS/webhooks/"]
COPY ["RSS/server/__main__.py", "RSS/server/feed_generator.py", "RSS/server/"]

ENTRYPOINT [ "python", "-m", "RSS.server"]
