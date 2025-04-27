FROM python:3.12.2-alpine3.19

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./ .

CMD alembic upgrade head & python -m app.main
