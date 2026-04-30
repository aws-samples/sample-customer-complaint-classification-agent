FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
COPY shared/ ./shared/
COPY config/ ./config/
COPY agent.py .

RUN pip install --no-cache-dir --user .

FROM python:3.12-slim

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/ ./

ENV PYTHONPATH=/app/src:/app
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

RUN chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "from bedrock_agentcore import BedrockAgentCoreApp" || exit 1

CMD ["python3", "agent.py"]
