FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Override with a closer PyPI mirror when the default one is slow from the build host.
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir --index-url ${PIP_INDEX_URL} -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
