#!/bin/sh
# Startup script for Fly.io deployment

echo "Starting Coupang Wing CS Backend..."

# Run database migration (ignore errors to allow server to start)
echo "Running database migration..."
python add_receiver_columns.py || echo "Migration 1 skipped"
python migrate_account_sets_table.py || echo "Migration 2 skipped"
python migrate_coupon_tables.py || echo "Migration 3 skipped"

# Start Xvfb for headless Chrome
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x16 &

# Wait for Xvfb to start
sleep 2

# Start uvicorn
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
