FROM python:3.9.6-slim-buster

LABEL maintainer="Vasco Monteiro <vmnokk@gmail.com>"

ENV BUILD_ONLY_PACKAGES='wget' \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.1.5 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PATH="$PATH:/root/.poetry/bin"

WORKDIR /app

# System deps:
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    bash \
    build-essential \
    curl \
#    libpq-dev \
    # Defining build-time-only dependencies:
    $BUILD_ONLY_PACKAGES \
  # Installing `poetry` package manager:
  # https://github.com/python-poetry/poetry
  && curl -sSL 'https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py' | python \
  && poetry --version \
  # Removing build-time-only dependencies:
  && apt-get remove -y $BUILD_ONLY_PACKAGES \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
#  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*


COPY ./pyproject.toml ./poetry.lock* /app/


# Project initialization:
RUN poetry install --no-dev --no-interaction --no-ansi \
  # Upgrading pip, it is insecure, remove after `pip@21.1`
  && poetry run pip install -U pip \
  # Cleaning poetry installation's cache for production:
  && rm -rf "$POETRY_CACHE_DIR"

EXPOSE 8080
EXPOSE 5432
COPY . /app/
ENV PYTHONPATH=/app

CMD uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 --workers 2
