FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN mkdir -p /app/db

RUN apk add --no-cache \
    wget \
    gnupg \
    ca-certificates \
    tzdata \
    libstdc++ \
    musl \
    libgcc \
    chromium \
    chromium-chromedriver \
    && rm -rf /var/cache/apk/*

COPY pyproject.toml ./
RUN pip install uv && uv sync

COPY app ./app
COPY templates ./templates
COPY static ./static
COPY wsgi.py ./
COPY .env.example ./
COPY Makefile ./
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 5000

CMD ["./start.sh"]
