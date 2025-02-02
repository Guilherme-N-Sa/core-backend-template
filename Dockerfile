FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  gcc \
  postgresql-client \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --no-cache-dir setuptools gunicorn uvicorn \
  && curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY ./src .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD [ \
  "gunicorn", \
  "core.asgi:application", \
  "--workers", "4", \
  "--worker-class", "uvicorn.workers.UvicornWorker", \
  "--bind", "0.0.0.0:8000" \
  ]
