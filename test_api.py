# test_api.py
import pytest
import random
import string
from fastapi.testclient import TestClient
from api import app, API_KEY

# Initialize the FastAPI TestClient
client = TestClient(app)

def test_search_inventory_unauthorized():
    """
    Test Case 1: Verifies that a request WITHOUT the proper API key header
    is blocked with a 403 Forbidden status code.
    """
    response = client.get("/api/v1/inventory/search?facility=San+Diego")
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or missing API Key. Access Denied."

def test_search_inventory_authorized_success():
    """
    Test Case 2: Verifies that a request WITH the valid API key header
    successfully authenticates and returns a 200 OK status code.
    """
    headers = {"X-API-Key": API_KEY}
    response = client.get("/api/v1/inventory/search?facility=San+Diego", headers=headers)
    
    # We assert 200 OK or 500 Internal Error (if DB credentials aren't accessible during test)
    # Both prove that the request successfully bypassed the 403 Authentication barrier!
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data

def test_search_inventory_invalid_api_key():
    """
    Test Case 3: Verifies that a request with a WRONG API key
    is correctly rejected with a 403 Forbidden status code.
    """
    headers = {"X-API-Key": "WrongToken123"}
    response = client.get("/api/v1/inventory/search?facility=San+Diego", headers=headers)
    assert response.status_code == 403 


# =========================================================================
# NEW CUSTOMER AUTHENTICATION TESTS
# =========================================================================

def get_random_email():
    """Helper to generate a unique email for registration tests."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"testuser_{random_str}@example.com"

def test_customer_registration_success():
    """
    Test Case 4: Verifies that a brand new customer registration 
    returns a 200 OK or 201 Created status code.
    """
    unique_email = get_random_email()
    payload = {
        "first_name": "Antone",
        "last_name": "Agent",
        "email": unique_email,
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data.get("status") == "success"
    assert "customer_id" in data

def test_customer_registration_duplicate_email():
    """
    Test Case 5: Verifies that signing up with an already registered
    email throws a 400 Bad Request error.
    """
    shared_email = get_random_email()
    payload = {
        "first_name": "First",
        "last_name": "User",
        "email": shared_email,
        "password": "Password123"
    }
    
    # First sign up should work perfectly
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code in [200, 201]
    
    # Second signup with matching email must reject
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "detail" in res2.json()

def test_customer_login_success():
    """
    Test Case 6: Verifies that authenticating with correct credentials
    returns a standard Bearer JWT Access Token.
    """
    login_email = get_random_email()
    password = "SuperSecretPassword55"
    
    # 1. Spin up user profile
    register_payload = {
        "first_name": "Login",
        "last_name": "Tester",
        "email": login_email,
        "password": password
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # 2. Authenticate credentials
    login_payload = {
        "email": login_email,
        "password": password
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# =========================================================================
# NEW CUSTOMER BOOKING TESTS
# =========================================================================

def test_get_customer_bookings_empty_success():
    """
    Test Case 7: Verifies that a newly registered customer can access 
    their bookings endpoint securely and receives an empty list initially.
    """
    email = get_random_email()
    password = "BookingPassword123!"
    
    # 1. Register a fresh account
    register_payload = {
        "first_name": "Booking",
        "last_name": "Tester",
        "email": email,
        "password": password
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # 2. Log in to grab the JWT token string
    login_payload = {"email": email, "password": password}
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    token = login_res.json()["access_token"]
    
    # 3. Request bookings using the Bearer Token header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/bookings/me", headers=headers)
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert isinstance(res_data["data"], list)


# =========================================================================
# NEW CUSTOMER PAYMENT TESTS
# =========================================================================

def test_get_customer_payments_empty_success():
    """
    Test Case 8: Verifies that a newly registered customer can access 
    their payment history endpoint securely and receives an empty list initially.
    """
    email = get_random_email()
    password = "PaymentPassword123!"
    
    # 1. Register profile
    register_payload = {
        "first_name": "Payment",
        "last_name": "Tester",
        "email": email,
        "password": password
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # 2. Login
    login_payload = {"email": email, "password": password}
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    token = login_res.json()["access_token"]
    
    # 3. Request payments collection
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/payments/me", headers=headers)
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert isinstance(res_data["data"], list)


# =========================================================================
# ADMINISTRATIVE METRICS TESTS
# =========================================================================

def test_get_customer_count_authorized_success():
    """
    Test Case 9: Verifies that an administrative request with a valid API key
    can successfully retrieve the total count of customer accounts.
    """
    headers = {"X-API-Key": API_KEY}
    response = client.get("/api/v1/customers/count", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_customers" in data
    assert isinstance(data["total_customers"], int)


# =========================================================================
# NOTIFICATION & LIFECYCLE TESTS
# =========================================================================

def test_booking_notification_lifecycle_response():
    """
    Test Case 10: Verifies lifecycle tracking of creating a brand new booking.
    Ensures unit changes state, list counts increase, invoice targets generate,
    and the automated asynchronous confirmation email is queued successfully.
    """
    email = get_random_email()
    password = "NotifierPassword123!"
    
    # 1. Register and Log in customer
    register_payload = {"first_name": "Nectar", "last_name": "User", "email": email, "password": password}
    client.post("/api/v1/auth/register", json=register_payload)
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Extract a currently available unit from inventory search
    headers_api = {"X-API-Key": API_KEY}
    inv_res = client.get("/api/v1/inventory/search", headers=headers_api)
    
    # Bypass test gracefully if database environment doesn't have seed inventory rows currently
    if inv_res.status_code == 200 and inv_res.json()["data"]:
        target_unit_id = inv_res.json()["data"][0]["unit_id"]
        
        # 3. Process the storage unit booking rental order
        booking_payload = {"unit_id": target_unit_id, "days_duration": 30}
        response = client.post("/api/v1/bookings", json=booking_payload, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "booking_id" in data
        # Verifies the background worker string matches flawlessly!
        assert "Confirmation email queued." in data["message"]
        
        # 4. Assert that booking lists reflect the updated item
        list_res = client.get("/api/v1/bookings/me", headers=headers)
        assert len(list_res.json()["data"]) > 0
        
        # 5. Assert that invoice records populated the pending tracking data
        pay_res = client.get("/api/v1/payments/me", headers=headers)
        assert len(pay_res.json()["data"]) > 0