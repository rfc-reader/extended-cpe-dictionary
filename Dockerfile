FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./

# Install dependencies first for better Docker layer caching.
RUN uv sync --no-dev

# Copy application source.
COPY ./application ./application
COPY ./extended_cpe_dictionary ./extended_cpe_dictionary
COPY ./manage.py ./manage.py
COPY ./README.md ./README.md
COPY ./UNLICENSE ./UNLICENSE

# Run initial migration
RUN uv run python manage.py makemigrations && uv run python manage.py migrate --noinput

RUN uv run python manage.py collectstatic


EXPOSE 8000
CMD ["uv", "run", "gunicorn", "extended_cpe_dictionary.wsgi:application", "--bind", "0.0.0.0:8000"]
