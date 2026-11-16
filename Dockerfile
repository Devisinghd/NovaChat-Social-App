
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && \ 
    pip install -r requirements.txt 

COPY . /app/

RUN mkdir -p /app/staticfiles /app/media

RUN DJANGO_SECRET_KEY=build-only-not-for-runtime ALLOW_SQLITE=True ALLOWED_HOST=localhost EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", " python manage.py migrate && daphne -b 0.0.0.0 -p 8000 Novachat.asgi:application" ]

