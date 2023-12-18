# Template API 

## Features

- FastAPI
- PostgreSQL on dev/prd
- SQLite for testing
- Localstack with ES and SQS
- Alembic migrations
- Black formatting
- Pytest
- [WebAPI docs](http://localhost:5000/docs)
- [WebAPI redoc](http://localhost:5000/redoc)
- [OpenAPI spec](http://localhost:5000/openapi.json)
- [WDB debugging](http://localhost:1984)
- VSCode support (.devcontainer)

## Development

- Run tests: `./scripts/test.sh`
- Run black: `./scripts/black.sh`
- Build dev: `docker-compose build api`
- Run dev: `docker-compose up api`

## Production

- Build prd: `docker build . -f docker/api/Dockerfile --no-cache -t api`
- Run prd: `docker run -d -p 5000:5000 --name api api`

## Required

- ES_HOST
- ES_PORT
- ES_USE_SSL ('true')
- ES_AWS_REGION
- ES_AWS_ACCESS_KEY
- ES_AWS_SECRET_KEY



WORKDIR /app

## Run With Docker

```
docker build -t customer-api . &&\
	docker kill customer-api-server;
	docker rm customer-api-server;
	docker run -p 8000:8000 --name customer-api-server customer-api 
```

## Test it
curl localhost:8000
