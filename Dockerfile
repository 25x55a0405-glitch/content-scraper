# Report Desk — one container, one persistent volume mounted at /data.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    REPORT_DESK_HOME=/data REPORT_DESK_SECURE_COOKIES=1
WORKDIR /app
COPY agency_report_agent/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*
COPY agency_report_agent ./agency_report_agent
RUN useradd -m app && mkdir -p /data && chown -R app /data /opt/pw-browsers
USER app
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz')"
# REPORT_DESK_PASSWORD must be set; the app refuses to listen on the network without it.
CMD ["python", "-m", "agency_report_agent.web", "--host", "0.0.0.0", "--port", "8000"]
