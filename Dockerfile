FROM python:3.12-slim

WORKDIR /cloudpilot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps ./apps

RUN useradd --uid 10001 --create-home cloudpilot \
    && mkdir -p /cloudpilot/data \
    && chown -R cloudpilot:cloudpilot /cloudpilot/data
ENV CLOUDPILOT_DB_PATH=/cloudpilot/data/cloudpilot.db
USER 10001:10001

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
