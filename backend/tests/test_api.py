from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}


def test_black_scholes_endpoint():
    r = client.post('/pricing/black-scholes', json={
        'spot': 100,
        'strike': 100,
        'rate': 0.05,
        'volatility': 0.20,
        'maturity': 1.0,
        'dividend_yield': 0.0,
        'option_type': 'call',
    })
    assert r.status_code == 200
    body = r.json()
    assert abs(body['price'] - 10.4506) < 0.001
    assert 'delta' in body['greeks']
