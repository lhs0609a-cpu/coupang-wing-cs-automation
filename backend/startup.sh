#!/bin/sh
# Startup script for Fly.io deployment

echo "Starting Coupang Wing CS Backend..."

# Run database migration
echo "Running database migration..."
python add_receiver_columns.py
python migrate_account_sets_table.py
python migrate_coupon_tables.py

# Start Xvfb for headless Chrome
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x16 &

# Wait for Xvfb to start
sleep 2

# Start uvicorn
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
