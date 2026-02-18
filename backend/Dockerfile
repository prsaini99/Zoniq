FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /usr/backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

EXPOSE 8000

RUN apt-get update \
  && apt-get -y install netcat-openbsd gcc libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY ./requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . .

COPY ./entrypoint.sh .
RUN chmod +x /usr/backend/entrypoint.sh

ENTRYPOINT ["/usr/backend/entrypoint.sh"]

CMD uvicorn src.main:backend_app --host 0.0.0.0 --port 8000 --workers ${BACKEND_SERVER_WORKERS:-4}
