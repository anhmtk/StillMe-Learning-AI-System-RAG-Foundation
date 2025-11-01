# Procfile for Heroku (optional - if you want to use Heroku)
# Heroku auto-detects this file

web: python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
dashboard: streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless=true

