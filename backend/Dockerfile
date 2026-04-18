#Base image
FROM python:3.12-slim

#Metadata
LABEL maintainer="BookingSystem"
LABEL description="booking system for salon"

#PYTHONUNBUFFERED=1 — Python логтарын бірден экранға шығарады (буферлемейді)
#PYTHONDONTWRITEBYTECODE=1 — .pyc файлдар жасамайды (контейнерде қажет емес)
#PIP_NO_CACHE_DIR=1 — pip кэш сақтамайды (образ кішірейеді)
#PIP_DISABLE_PIP_VERSION_CHECK=1 — pip version тексермейді (жылдамырақ)

#Set enviroment variables 
ENV PYTHONUNBUFFERED=1 \ 
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

#Жүйелік зависимостілер
RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

RUN useradd -m -u 1000 appuser && \ 
    mkdir -p /app/staticfiles /app/media /app/db && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh 

USER appuser

ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000" ]

