# Imagen del backend para Render. WeasyPrint (PDF) necesita Pango, que no
# viene en las imágenes de Python "slim".
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .
ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    PYTHONUNBUFFERED=1

# Los estáticos se juntan al construir; las variables son de relleno, solo
# para que Django arranque (los valores reales llegan al ejecutar).
RUN SECRET_KEY=solo-para-construir ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://u:p@localhost/db python manage.py collectstatic --noinput

# Aplica las migraciones al arrancar (el plan gratuito no tiene "pre-deploy").
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120"]
