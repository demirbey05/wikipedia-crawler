FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync

COPY main.py .

RUN mkdir -p data

CMD ["uv", "run", "python", "main.py"]