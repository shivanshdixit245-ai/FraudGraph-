@echo off
set PYTHONUNBUFFERED=1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010 --ws websockets
