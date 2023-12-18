FROM python:3.8.5

ENV PYTHONPATH=/app

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN chmod u+x /app/entrypoint.sh
ENTRYPOINT /app/entrypoint.sh $PORT
