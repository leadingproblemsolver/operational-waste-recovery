FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir .
RUN useradd --create-home owrp && mkdir -p /app/data /app/reports /app/logs && chown -R owrp:owrp /app
USER owrp
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=2)" || exit 1
CMD ["owrp", "--root", "/app", "serve", "--host", "0.0.0.0", "--port", "8787"]
