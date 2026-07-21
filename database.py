# database.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "tenant_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def init_db():
    """
    Initializes database tables automatically on startup.
    Creates the payments table along with primary foreign key tables if they do not exist.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL execution block creating the payments ledger table
        create_payments_table_query = """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id SERIAL PRIMARY KEY,
            booking_id INT REFERENCES bookings(booking_id),
            stripe_customer_id VARCHAR(255),
            stripe_payment_method_id VARCHAR(255),
            card_brand VARCHAR(50),
            card_last4 VARCHAR(4),
            amount DECIMAL(10, 2),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(create_payments_table_query)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database schema synchronized: 'payments' table initialized.")
    except Exception as e:
        print(f"⚠️ Error initializing database tables: {e}")

def check_unit_availability(size: str = None, facility_keyword: str = None) -> str:
    """
    Queries the database for live storage unit inventory. 
    Can filter by size (e.g., '5x10') and/or facility location keyword (e.g., 'San Diego', 'Irvine').
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Base query joining units to their specific facilities
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
        if facility_keyword:
            query += " AND f.name ILIKE %s"
            params.append(f"%{facility_keyword}%")
            
        query += " LIMIT 10;" # Limit results so the LLM context isn't overwhelmed
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            return f"I checked our storage systems, and we currently have no vacant units matching those criteria."
        
        units_list = [f"ID: {r[0]} | Location: {r[1]} | Size: {r[2]} | Price: ${r[3]}/mo" for r in rows]
        return "Found the following matching available units:\n" + "\n".join(units_list)
    except Exception as e:
        return f"Database operational error: {str(e)}"

if __name__ == "__main__":
    init_db()