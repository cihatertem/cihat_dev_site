FROM python:3.11-bullseye

LABEL maintainer="Cihat Ertem <cihatertem@gmail.com>"

ENV PYTHONUNBUFFERED=1

RUN groupadd -r django && useradd --no-log-init -r -g django django

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt clean -y \
    && apt autopurge -y

COPY requirements.txt /tmp

RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade --no-cache-dir pip \
    && /venv/bin/pip install --upgrade --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

ENV PATH="/venv/bin:$PATH"

WORKDIR /app

COPY . .

RUN chown -R django:django /app

USER django

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "2", "cihat_dev.wsgi:application"]