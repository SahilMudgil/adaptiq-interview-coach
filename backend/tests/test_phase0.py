from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal, is_postgres
from backend.app.models.all_models import User

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data["status"] == "healthy"
    print("Health check endpoint passed!")
    print(f"  Database type: {data['database']['type']}")

def test_auth_flow():
    test_email = "tester_phase0@example.com"
    test_password = "securePassword123!"
    test_name = "Phase0 Tester"

    # Clean up if exists
    db = SessionLocal()
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    # Signup
    signup_res = client.post("/api/v1/auth/signup", json={
        "name": test_name,
        "email": test_email,
        "password": test_password
    })
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    signup_data = signup_res.json()
    assert "access_token" in signup_data
    token = signup_data["access_token"]
    print("Signup endpoint passed! Received valid JWT access token.")

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    assert "access_token" in login_data
    print("Login endpoint passed!")

    # Profile via Token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200, f"Me endpoint failed: {me_res.text}"
    assert me_res.json()["email"] == test_email
    print("Protected /auth/me endpoint passed!")

if __name__ == "__main__":
    print("--- Running Phase 0 Verification Tests ---")
    test_health()
    test_auth_flow()
    print("--- ALL PHASE 0 TESTS PASSED CLEANLY! ---")
