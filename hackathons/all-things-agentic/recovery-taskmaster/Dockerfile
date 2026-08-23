FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 taskmaster \
    && mkdir -p /tmp/recovery-taskmaster \
    && chown -R taskmaster:taskmaster /app /tmp/recovery-taskmaster

USER taskmaster
ENV PORT=8080
ENV RECOVERY_TASKMASTER_ROOT=/tmp/recovery-taskmaster

EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
