import datetime
import stripe
import jwt
import hashlib
import os
from fastapi import FastAPI, Query, HTTPException, Security, status, APIRouter, Depends, BackgroundTasks
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from database import get_db_connection

# Stripe Setup (Optionally set STRIPE_SECRET_KEY in your env)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_key_2026")
stripe.api_key = STRIPE_SECRET_KEY

# Define the header name and our mock secret token
API_KEY_NAME = "X-API-Key"
API_KEY = "NectarPlatformSecretToken2026"  # Mock secure token
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
security_scheme = HTTPBearer()

app = FastAPI(
    title="Tenant Inc. - Nectar Integration Platform API",
    description="API-first storage inventory and facility tracking service simulator with automated payments.",
    version="1.1.0"
)

# Setup JWT Metadata
JWT_SECRET = "ChangeThisToALongSecretKeyInProduction2026"
JWT_ALGORITHM = "HS256"

# Pydantic models for authentication request validation
class CustomerRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str

# Pydantic model for incoming booking requests
class BookingCreate(BaseModel):
    unit_id: int
    days_duration: int = 30  # Default rental period

# Pydantic models for payment processing
class ProcessPaymentRequest(BaseModel):
    booking_id: int
    payment_method_token: str  # Token generated via Stripe or tokenized gateway (e.g. "pm_card_visa")
    card_brand: str = "Visa"
    card_last4: str = "4242"

class SavePaymentMethodRequest(BaseModel):
    payment_method_token: str
    card_brand: str
    card_last4: str
    exp_month: int
    exp_year: int

# Native Python helper security functions
def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a unique random salt."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify an incoming password against the stored salt and hash."""
    try:
        salt, stored_hash = hashed_password.split(":")
        computed_hash = hashlib.sha256((plain_password + salt).encode('utf-8')).hexdigest()
        return computed_hash == stored_hash
    except ValueError:
        return False

def create_access_token(customer_id: int, email: str) -> str:
    payload = {
        "customer_id": customer_id,
        "email": email,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_api_key(header_key: str = Security(api_key_header)):
    """Dependency function to validate incoming X-API-Key headers."""
    if header_key == API_KEY:
        return header_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key. Access Denied."
    )

def get_current_customer_id(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> int:
    """Extracts and verifies the customer_id from the incoming JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        customer_id: int = payload.get("customer_id")
        if customer_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload: Missing customer ID.")
        return customer_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

# --- Mock Notification Dispatch Service ---

def dispatch_booking_confirmation_email(email: str, first_name: str, booking_id: int, unit_size: str, initial_charge: float):
    """
    Simulates an asynchronous SMTP handshake and dispatch pipeline 
    to handle automated customer rental confirmation notifications.
    """
    print("\n" + "="*60)
    print("📢 DISPATCHING AUTOMATED NOTIFICATION SYSTEM")
    print(f"📧 Outbound Target: {email}")
    print(f"👤 Recipient Name: {first_name}")
    print(f"📝 Confirmation ID: #{booking_id}")
    print(f"📦 Storage Unit Tier: {unit_size}")
    print(f"💳 First Statement Invoice Generated: ${initial_charge:.2f}")
    print("✅ SMTP Status 250: Message successfully buffered and delivered.")
    print("="*60 + "\n")

# --- Authentication Endpoints ---

@app.post("/api/v1/auth/register", tags=["Authentication"])
def register_customer(user: CustomerRegister):
    """Registers a brand new customer account into the database securely."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM customers WHERE email = %s;", (user.email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed = hash_password(user.password)
        cur.execute(
            """INSERT INTO customers (first_name, last_name, email, hashed_password) 
               VALUES (%s, %s, %s, %s) RETURNING id;""",
            (user.first_name, user.last_name, user.email, hashed)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        conn.close()
        return {"status": "success", "message": "Customer created successfully", "customer_id": new_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Insertion Error: {str(e)}")

@app.post("/api/v1/auth/login", tags=["Authentication"])
def login_customer(user: CustomerLogin):
    """Authenticates credentials and returns a secure JWT login token."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, hashed_password FROM customers WHERE email = %s;", (user.email,))
        record = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not record or not verify_password(user.password, record[1]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        token = create_access_token(record[0], user.email)
        return {"status": "success", "access_token": token, "token_type": "bearer"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication Error: {str(e)}")

# --- Customer Profile Endpoints ---

@app.get("/api/v1/customers/me", tags=["Customers"])
def get_customer_profile(current_customer_id: int = Depends(get_current_customer_id)):
    """Fetches the authenticated customer's full profile details."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """SELECT id, first_name, last_name, email, created_at 
               FROM customers WHERE id = %s;""", 
            (current_customer_id,)
        )
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Customer profile not found.")
            
        return {
            "status": "success",
            "data": {
                "customer_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "email": row[3],
                "created_at": row[4]
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Retrieval Error: {str(e)}")

# --- Bookings Endpoints ---

@app.get("/api/v1/bookings/me", tags=["Bookings"])
def get_customer_bookings(current_customer_id: int = Depends(get_current_customer_id)):
    """Fetches all active and past storage unit bookings for the authenticated customer."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT b.id, b.unit_id, u.size, u.price_monthly, b.start_date, b.end_date, b.status
            FROM bookings b
            JOIN units u ON b.unit_id = u.id
            WHERE b.customer_id = %s
            ORDER BY b.start_date DESC;
        """
        
        cur.execute(query, (current_customer_id,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        results = [
            {
                "booking_id": r[0],
                "unit_id": r[1],
                "size": r[2],
                "price_monthly": float(r[3]),
                "start_date": r[4].strftime("%Y-%m-%d") if r[4] else None,
                "end_date": r[5].strftime("%Y-%m-%d") if r[5] else None,
                "status": r[6]
            }
            for r in rows
        ]
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Booking Retrieval Error: {str(e)}")

@app.post("/api/v1/bookings", status_code=201, tags=["Bookings"])
def create_booking(
    booking_data: BookingCreate, 
    background_tasks: BackgroundTasks,
    current_customer_id: int = Depends(get_current_customer_id)
):
    """
    Creates a new rental contract, updates the storage unit to 'Rented',
    initiates the initial statement charge inside the payments table,
    and queues up an automated booking email confirmation.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Check unit availability
        cur.execute("SELECT price_monthly, status, size FROM units WHERE id = %s;", (booking_data.unit_id,))
        unit = cur.fetchone()
        
        if not unit:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Storage unit not found.")
            
        if unit[1] != 'Available':
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Storage unit is no longer available for rent.")
            
        price_monthly = float(unit[0])
        unit_size = unit[2]
        
        # 2. Fetch Customer details
        cur.execute("SELECT email, first_name FROM customers WHERE id = %s;", (current_customer_id,))
        customer = cur.fetchone()
        customer_email, customer_name = customer[0], customer[1]
        
        # 3. Calculate dates
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=booking_data.days_duration)
        
        # 4. Insert booking
        cur.execute(
            """INSERT INTO bookings (customer_id, unit_id, start_date, end_date, status)
               VALUES (%s, %s, %s, %s, 'Active') RETURNING id;""",
            (current_customer_id, booking_data.unit_id, start_date, end_date)
        )
        booking_id = cur.fetchone()[0]
        
        # 5. Update unit status
        cur.execute("UPDATE units SET status = 'Rented' WHERE id = %s;", (booking_data.unit_id,))
        
        # 6. Insert initial pending invoice
        cur.execute(
            """INSERT INTO payments (booking_id, amount, payment_date, status)
               VALUES (%s, %s, %s, 'Pending');""",
            (booking_id, price_monthly, datetime.datetime.now(datetime.timezone.utc))
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        # 7. Queue background mail job
        background_tasks.add_task(
            dispatch_booking_confirmation_email,
            email=customer_email,
            first_name=customer_name,
            booking_id=booking_id,
            unit_size=unit_size,
            initial_charge=price_monthly
        )
        
        return {
            "status": "success",
            "message": "Storage unit rented successfully. Confirmation email queued.",
            "booking_id": booking_id,
            "initial_charge": price_monthly
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking Processing Error: {str(e)}")

# --- Payments & Checkout Endpoints ---

@app.get("/api/v1/payments/me", tags=["Payments"])
def get_customer_payments(current_customer_id: int = Depends(get_current_customer_id)):
    """Fetches all billing and payment transaction records for the authenticated customer."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT p.id, p.booking_id, p.amount, p.payment_date, p.status
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            WHERE b.customer_id = %s
            ORDER BY p.payment_date DESC;
        """
        
        cur.execute(query, (current_customer_id,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        results = [
            {
                "payment_id": r[0],
                "booking_id": r[1],
                "amount": float(r[2]),
                "payment_date": r[3].strftime("%Y-%m-%d %H:%M:%S") if r[3] else None,
                "status": r[4]
            }
            for r in rows
        ]
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Payment Retrieval Error: {str(e)}")

@app.post("/api/v1/payments/checkout", tags=["Payments"])
def process_booking_payment(
    payment_data: ProcessPaymentRequest,
    current_customer_id: int = Depends(get_current_customer_id)
):
    """
    Processes a payment for an active booking or invoice statement using a tokenized card token.
    Updates payment records from 'Pending' to 'Paid' without exposing sensitive raw PCI card data.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Verify booking ownership
        cur.execute(
            """SELECT b.id, p.id, p.amount, p.status 
               FROM bookings b
               JOIN payments p ON p.booking_id = b.id
               WHERE b.id = %s AND b.customer_id = %s
               ORDER BY p.payment_date DESC LIMIT 1;""",
            (payment_data.booking_id, current_customer_id)
        )
        record = cur.fetchone()

        if not record:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="No billing invoice found matching this booking ID for your profile.")

        booking_id, payment_id, amount, payment_status = record[0], record[1], float(record[2]), record[3]

        # 2. Tokenized payment execution wrapper
        transaction_reference = f"txn_{os.urandom(8).hex()}"
        
        if not STRIPE_SECRET_KEY.startswith("sk_test_mock"):
            try:
                # Actual Stripe Charge Execution if a real key is present
                charge = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Amount in cents
                    currency="usd",
                    payment_method=payment_data.payment_method_token,
                    confirm=True,
                    description=f"Rent Payment for Booking #{booking_id}"
                )
                transaction_reference = charge.id
            except stripe.error.StripeError as se:
                cur.close()
                conn.close()
                raise HTTPException(status_code=400, detail=f"Payment Gateway Error: {str(se)}")

        # 3. Mark invoice as paid in PostgreSQL
        cur.execute(
            """UPDATE payments 
               SET status = 'Paid', payment_date = %s 
               WHERE id = %s;""",
            (datetime.datetime.now(datetime.timezone.utc), payment_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "message": "Payment processed successfully.",
            "transaction_id": transaction_reference,
            "amount_paid": amount,
            "card_summary": f"{payment_data.card_brand} ending in {payment_data.card_last4}"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout Processing Error: {str(e)}")

# --- Inventory Endpoints ---

@app.get("/api/v1/inventory/search", tags=["Inventory"])
def search_inventory(
    size: str = Query(None, description="Dimensions to filter by, e.g., '5x10'"),
    facility: str = Query(None, description="City or facility name keyword, e.g., 'San Diego'"),
    api_key: str = Security(get_current_api_key)
):
    """
    REST Endpoint to fetch live, available storage unit inventory.
    Requires a valid X-API-Key header to authenticate.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT u.id, f.name, u.size, u.price_monthly 
            FROM units u 
            JOIN facilities f ON u.facility_id = f.id 
            WHERE u.status = 'Available'
        """
        params = []
        
        if size:
            query += " AND u.size ILIKE %s"
            params.append(f"%{size}%")
        if facility:
            query += " AND f.name ILIKE %s"
            params.append(f"%{facility}%")
            
        query += " LIMIT 500;"
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        results = [
            {"unit_id": r[0], "facility_name": r[1], "size": r[2], "price_monthly": float(r[3])}
            for r in rows
        ]
        
        return {"status": "success", "count": len(results), "data": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# --- Administrative Endpoints ---

@app.get("/api/v1/customers/count", tags=["Administration"])
def get_customer_count(api_key: str = Security(get_current_api_key)):
    """Administrative metric route to retrieve total number of registered customer profiles."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"status": "success", "total_customers": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics Evaluation Error: {str(e)}")