FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
COPY singapore_transport ./singapore_transport
COPY scripts ./scripts

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "singapore_transport.api:app", "--host", "0.0.0.0", "--port", "8000"]
