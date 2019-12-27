#!/bin/sh
export FLASK_APP=./src/auth0.py
source $(pipenv --venv)/bin/activate
export $(cat .env | xargs) && flask run -h localhost
