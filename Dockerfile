FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY token_forecast/ token_forecast/
COPY sample_data/ sample_data/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["token-forecast"]
