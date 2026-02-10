#!/usr/bin/env bash
# Start script for Render — runs bot in background + gunicorn web server

echo "🦅 Starting Eagles View Bot in background..."
python manage.py runbot &

echo "🌐 Starting Gunicorn web server..."
gunicorn EaglesViewTGBot.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
