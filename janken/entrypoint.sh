#!/bin/sh

python /app/init_db.py

gunicorn -b 0.0.0.0:5000 app:app