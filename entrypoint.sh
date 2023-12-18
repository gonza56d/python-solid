#!/usr/bin/env bash

alembic upgrade head &&\
	uvicorn users.api.run:app --proxy-headers --host 0.0.0.0 --port $1
