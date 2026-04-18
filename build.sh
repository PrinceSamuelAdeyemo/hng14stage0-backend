#!/bin/bash
set -e

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔄 Collecting static files..."
python manage.py collectstatic --no-input --clear || true

echo "🗄️  Running database migrations..."
python manage.py migrate --no-input

echo "✅ Build completed successfully"
