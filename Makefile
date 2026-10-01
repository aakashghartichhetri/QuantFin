.PHONY: test validate reports run-api run-dashboard up down

test:
	cd backend && PYTHONPATH=. pytest -q

validate:
	python scripts/run_model_validation.py

reports:
	python scripts/generate_analytics_reports.py

run-api:
	cd backend && uvicorn app.main:app --reload --port 8000

run-dashboard:
	cd dashboard && API_URL=http://localhost:8000 VALIDATION_DATA=../data/validation/market_returns_validation.csv streamlit run app.py

up:
	docker compose up --build

down:
	docker compose down
