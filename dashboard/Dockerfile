FROM python:3.12-slim
WORKDIR /app
COPY dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard/app.py ./app.py
COPY data/validation/market_returns_validation.csv ./data/market_returns_validation.csv
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
