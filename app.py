# app.py
import os
import streamlit as st
import requests
from google import genai

# Dynamically pull the backend URL or fall back to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
ADMIN_API_KEY = "NectarPlatformSecretToken2026"

st.set_page_config(
    page_title="Antone AI - Tenant Inc",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection for layout styling
st.markdown(
    """
    <style>
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
    """, 
    unsafe_allow_html=True
)

# Initialize persistent session states
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "customer_name" not in st.session_state:
    st.session_state["customer_name"] = ""
if "show_login_prompt" not in st.session_state:
    st.session_state["show_login_prompt"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I am Antone. How can I help you optimize or reserve your storage space today?"}
    ]

## --- Endpoints Dynamic Headers ---
def HTTP_headers():
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}

def API_key_headers():
    return {"X-API-Key": ADMIN_API_KEY}

## --- Fetch Unique Cities From Catalog ---
def get_available_cities():
    """Queries the catalog to extract unique facility locations or falls back to mock data if offline."""
    try:
        res = requests.get(f"{API_BASE_URL}/inventory/search", headers=API_key_headers(), timeout=2)
        if res.status_code == 200:
            units = res.json().get("data", [])
            city_counts = {}
            total_available = len(units)
            
            for u in units:
                name = u.get("facility_name", "")
                city = name.split(" - ")[-1].strip() if " - " in name else name.strip()
                city_counts[city] = city_counts.get(city, 0) + 1
            
            options = [f"All Cities ({total_available} units available)"]
            for city in sorted(city_counts.keys()):
                options.append(f"{city} ({city_counts[city]} units available)")
                
            return options
    except Exception:
        pass
    
    # Cloud demo mode fallback
    return ["All Cities (12 units available)", "Irvine (5 units available)", "San Diego (7 units available)"]


# =========================================================================
# SIDEBAR: NAVIGATION PANEL & SESSION METRICS
# =========================================================================
with st.sidebar:
    st.title("🔑 Tenant Space Control")
    st.caption("⚡ Run locally via Docker or browse online demo mode")
    st.write("---")
    
    if not st.session_state["access_token"]:
        page_route = st.selectbox("Navigate Portal Pages", ["🔑 Login to Account", "✨ Register Profile"])
        st.write("---")
        
        if page_route == "🔑 Login to Account":
            st.subheader("Login Portal")
            login_email = st.text_input("Email Address", placeholder="name@example.com", key="login_email")
            login_password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            st.write("")
            
            if st.button("Secure Login 🔓", width="stretch", type="primary"):
                payload = {"email": login_email, "password": login_password}
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/login", json=payload, timeout=2)
                    if res.status_code == 200:
                        st.session_state["access_token"] = res.json()["access_token"]
                        profile_res = requests.get(f"{API_BASE_URL}/customers/me", headers=HTTP_headers(), timeout=2)
                        if profile_res.status_code == 200:
                            st.session_state["customer_name"] = profile_res.json()["data"]["first_name"]
                        st.session_state["show_login_prompt"] = False
                        st.toast("Welcome back! Control center unlocked.", icon="🔓")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Invalid email or password."))
                except Exception:
                    # Cloud Demo Mock Login bypass
                    st.session_state["access_token"] = "mock_cloud_jwt_token"
                    st.session_state["customer_name"] = "Guest Demo User"
                    st.session_state["show_login_prompt"] = False
                    st.toast("Logged into Cloud Demo Mode!", icon="☁️")
                    st.rerun()
                    
        elif page_route == "✨ Register Profile":
            st.subheader("Registration Portal")
            reg_first_name = st.text_input("First Name", placeholder="John")
            reg_last_name = st.text_input("Last Name", placeholder="Doe")
            reg_email = st.text_input("Email Address", placeholder="name@example.com")
            reg_password = st.text_input("Password", type="password", placeholder="••••••••")
            st.write("")
            
            if st.button("Create Account 📝", width="stretch", type="primary"):
                payload = {"first_name": reg_first_name, "last_name": reg_last_name, "email": reg_email, "password": reg_password}
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/register", json=payload, timeout=2)
                    if res.status_code == 200:
                        st.success("Account created successfully! Select 'Login to Account' from the dropdown to access your portal.")
                    else:
                        st.error(res.json().get("detail", "Registration rejected."))
                except Exception:
                    st.success("Demo Registration Successful! You can now log in using any dummy credentials.")

    else:
        st.subheader(f"Welcome back, {st.session_state['customer_name']}! 👋")
        st.caption("Session Status: Authenticated Session")
        st.write("---")
        
        try:
            bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers(), timeout=2)
            if bk_res.status_code == 200:
                active_count = bk_res.json().get("count", 0)
                st.metric(label="Your Subleased Units", value=active_count)
            else:
                raise Exception()
        except Exception:
            st.metric(label="Your Subleased Units (Demo)", value=2)
            
        st.write("---")
        if st.button("Log Out Session 🚪", width="stretch"):
            st.session_state["access_token"] = None
            st.session_state["customer_name"] = ""
            st.session_state["show_login_prompt"] = False
            st.rerun()


# =========================================================================
# MAIN SCREEN VIEWS DESIGNATOR
# =========================================================================
if st.session_state["access_token"]:
    col_chat, col_dash = st.columns([1.3, 1], gap="large")
else:
    col_chat = st.container()
    col_dash = None

# LEFT SIDE / FULL SCREEN: THE ANTONE AI CONVERSATION WINDOW
with col_chat:
    st.title("Meet Antone")
    st.caption("AI-Powered Real-Time Chat Assistant for Storage Operators")
    st.write("")
    
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if st.session_state["show_login_prompt"] and not st.session_state["access_token"]:
        st.info("💡 **Account Access Required** — Please use the credentials fields inside the sidebar component to sign in. Once validated, your interactive ledger details will open right here on the layout.")
            
    if prompt := st.chat_input("Ask Antone about unit availability..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        profile_flagged_keywords = ["my unit", "my booking", "my statement", "my bill", "my payment", "balance", "sublease", "invoice", "rent unit", "ledger", "details", "pay"]
        requires_profile_context = any(word in prompt.lower() for word in profile_flagged_keywords)
        
        if requires_profile_context and not st.session_state["access_token"]:
            st.session_state["show_login_prompt"] = True
            ai_response = "I can definitely help locate that layout detail for you, but those metrics contain personal profile information! Please use the sidebar terminal box to login to your tenant dashboard space."
        else:
            st.session_state["show_login_prompt"] = False
            
            # --- BACKEND DATABASE CONTEXT EXTRACTION ---
            db_context = ""
            try:
                # 1. Fetch live system inventory summary records
                res = requests.get(f"{API_BASE_URL}/inventory/search", headers=API_key_headers(), timeout=2)
                if res.status_code == 200:
                    units_data = res.json().get("data", [])
                    unique_sizes = sorted(list(set(u["size"] for u in units_data)))
                    
                    city_summary = {}
                    prices = []
                    for u in units_data:
                        city = u["facility_name"].split(" - ")[-1] if " - " in u["facility_name"] else u["facility_name"]
                        city_summary[city] = city_summary.get(city, 0) + 1
                        if "price_monthly" in u:
                            prices.append(u["price_monthly"])
                            
                    price_info = "No pricing telemetry recorded"
                    if prices:
                        price_info = f"Starts at ${min(prices):.2f}/mo up to ${max(prices):.2f}/mo"
                    
                    db_context += (
                        f"Live Storage Inventory Context:\n"
                        f"- Total vacant units available: {len(units_data)}\n"
                        f"- Available sizes: {', '.join(unique_sizes)}\n"
                        f"- Pricing Spectrum: {price_info}\n"
                        f"- Facilities by location/city: {', '.join([f'{k} has {v} units' for k, v in city_summary.items()])}\n\n"
                    )
                else:
                    raise Exception()
                
                # 2. Fetch authenticated tenant session logs
                if st.session_state["access_token"]:
                    bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers(), timeout=2)
                    if bk_res.status_code == 200:
                        user_bookings = bk_res.json().get("data", [])
                        db_context += "Authenticated User's Active Leases & Bookings:\n"
                        if user_bookings:
                            for b in user_bookings:
                                b_id = b.get('booking_id', b.get('id'))
                                db_context += f"- Booking ID #{b_id}: Unit #{b['unit_id']}, Sizing Tier: {b['size']}, Rate: ${b['price_monthly']}/mo, Status: {b['status']}, Start Date: {b['start_date']}, End Date: {b.get('end_date')}\n"
                        else:
                            db_context += "- No active or past bookings found on record.\n"
                    
                    pay_res = requests.get(f"{API_BASE_URL}/payments/me", headers=HTTP_headers(), timeout=2)
                    if pay_res.status_code == 200:
                        user_payments = pay_res.json().get("data", [])
                        db_context += "\nAuthenticated User's Invoice Statements & Payments Ledger:\n"
                        if user_payments:
                            for p in user_payments:
                                p_id = p.get('payment_id', p.get('id'))
                                p_date = p.get('payment_date', p.get('created_at'))
                                p_bk_id = p.get('booking_id', p.get('id'))
                                db_context += f"- Payment ID #{p_id} tied to Booking #{p_bk_id}: Amount ${p['amount']}, Status: {p['status']}, Logged Timestamp: {p_date}\n"
                        else:
                            db_context += "- No payment invoices or transaction statements recorded.\n"
                            
            except Exception:
                # Live Cloud Preview Mode Mock Data Injection
                db_context += (
                    f"Live Storage Inventory Context (Cloud Demo Mode):\n"
                    f"- Total vacant units available: 12\n"
                    f"- Available sizes: 5x5, 5x10, 10x10, 10x20\n"
                    f"- Pricing Spectrum: Starts at $45.00/mo up to $185.00/mo\n"
                    f"- Facilities by location/city: Irvine has 5 units, San Diego has 7 units\n\n"
                )
                if st.session_state["access_token"]:
                    db_context += (
                        f"Authenticated User's Active Leases & Bookings:\n"
                        f"- Booking ID #1042: Unit #B102, Sizing Tier: 10x10, Rate: $120.00/mo, Status: active, Start Date: 2026-01-01, End Date: None\n"
                        f"- Booking ID #1089: Unit #A005, Sizing Tier: 5x5, Rate: $45.00/mo, Status: active, Start Date: 2026-05-15, End Date: None\n\n"
                        f"Authenticated User's Invoice Statements & Payments Ledger:\n"
                        f"- Payment ID #9412 tied to Booking #1042: Amount $120.00, Status: Paid, Logged Timestamp: 2026-07-01\n"
                        f"- Payment ID #9550 tied to Booking #1089: Amount $45.00, Status: Pending, Logged Timestamp: 2026-07-15\n"
                    )

            # --- GEMINI AI GENERATION ENGINE ---
            try:
                if "GEMINI_API_KEY" in st.secrets:
                    api_key_str = st.secrets["GEMINI_API_KEY"]
                elif "GOOGLE_API_KEY" in st.secrets:
                    api_key_str = st.secrets["GOOGLE_API_KEY"]
                else:
                    api_key_str = os.getenv("GEMINI_API_KEY", "")

                client = genai.Client(api_key=api_key_str)
                
                system_instruction = (
                    "You are Antone, an AI-powered real-time chat assistant for a self-storage operator company named Tenant Inc. "
                    "Be professional, clear, and helpful. Use the provided live inventory data and user profile metadata to accurately answer inquiries. "
                    "If the user asks about their active bookings, leases, or pending payment statements, use the context to explain their unit IDs, sizes, "
                    "monthly rates, and payment status. Remind them that they can execute payment directly in the Transaction Ledgers tab."
                )

                formatted_history = []
                for msg in st.session_state["messages"][1:-1]:
                    formatted_history.append(
                        genai.types.Content(
                            role="user" if msg["role"] == "user" else "model",
                            parts=[genai.types.Part.from_text(text=msg["content"])]
                        )
                    )

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                    history=formatted_history
                )
                
                full_ai_prompt = f"{db_context}\nUser Current Name Context: {st.session_state['customer_name']}\nUser Question: {prompt}"
                response = chat.send_message(full_ai_prompt)
                ai_response = response.text
                
            except Exception as e:
                ai_response = f"I encountered an issue analyzing your request with Gemini: `{str(e)}`."
                
        st.session_state["messages"].append({"role": "assistant", "content": ai_response})
        st.rerun()

# RIGHT SIDE: LIVE MANAGEMENT LEDGER WIDGETS
if st.session_state["access_token"] and col_dash:
    with col_dash:
        st.markdown("### 📊 Live Operations Control Center")
        st.write("")
        
        tab_inv, tab_books, tab_pays = st.tabs([
            "🔍 Available Catalog", 
            "📋 Booking Logs", 
            "💳 Transaction Ledgers"
        ])
        
        with tab_inv:
            st.write("")
            available_cities = get_available_cities()
            selected_city_label = st.selectbox("📍 Select Facility City", available_cities, index=0)
            st.write("---")
            
            if " (" in selected_city_label:
                selected_city = selected_city_label.split(" (")[0]
            else:
                selected_city = selected_city_label
            
            if "catalog_page" not in st.session_state:
                st.session_state["catalog_page"] = 0
                
            if "last_selected_city" not in st.session_state:
                st.session_state["last_selected_city"] = selected_city
            elif st.session_state["last_selected_city"] != selected_city:
                st.session_state["catalog_page"] = 0
                st.session_state["last_selected_city"] = selected_city
            
            try:
                query_params = {}
                if selected_city != "All Cities":
                    query_params["facility"] = selected_city
                    
                inv_res = requests.get(f"{API_BASE_URL}/inventory/search", params=query_params, headers=API_key_headers(), timeout=2)
                if inv_res.status_code == 200:
                    units_data = inv_res.json().get("data", [])
                else:
                    raise Exception()
            except Exception:
                # Cloud Demo Mock Inventory Slicing
                all_mock_units = [
                    {"facility_name": "Tenant Inc - Irvine", "unit_id": "I-101", "size": "5x5", "price_monthly": 45.00},
                    {"facility_name": "Tenant Inc - Irvine", "unit_id": "I-102", "size": "5x10", "price_monthly": 75.00},
                    {"facility_name": "Tenant Inc - Irvine", "unit_id": "I-103", "size": "10x10", "price_monthly": 120.00},
                    {"facility_name": "Tenant Inc - Irvine", "unit_id": "I-104", "size": "10x15", "price_monthly": 150.00},
                    {"facility_name": "Tenant Inc - Irvine", "unit_id": "I-105", "size": "10x20", "price_monthly": 185.00},
                    {"facility_name": "Tenant Inc - San Diego", "unit_id": "SD-201", "size": "5x5", "price_monthly": 49.00},
                    {"facility_name": "Tenant Inc - San Diego", "unit_id": "SD-202", "size": "5x10", "price_monthly": 79.00},
                    {"facility_name": "Tenant Inc - San Diego", "unit_id": "SD-203", "size": "10x10", "price_monthly": 129.00},
                ]
                if selected_city == "All Cities":
                    units_data = all_mock_units
                else:
                    units_data = [u for u in all_mock_units if selected_city in u["facility_name"]]

            if not units_data:
                st.info(f"No vacant units found in '{selected_city}' matching criteria.")
            else:
                ITEMS_PER_PAGE = 10
                total_units = len(units_data)
                max_page_idx = max(0, (total_units - 1) // ITEMS_PER_PAGE)
                
                if st.session_state["catalog_page"] > max_page_idx:
                    st.session_state["catalog_page"] = max_page_idx
                    
                current_page = st.session_state["catalog_page"]
                start_idx = current_page * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                sliced_units = units_data[start_idx:end_idx]
                
                for u in sliced_units:
                    with st.container(border=True):
                        c_info, c_action = st.columns([2.5, 1])
                        with c_info:
                            st.markdown(f"**{u['facility_name']}** — `Unit #{u['unit_id']}`")
                            st.caption(f"📐 Size Tier: **{u['size']}** | 💵 Rate: **${u['price_monthly']:.2f}/mo**")
                        with c_action:
                            st.write("")
                            if st.button("Rent ⚡", key=f"rent_{u['unit_id']}", width="stretch"):
                                payload = {"unit_id": u['unit_id'], "days_duration": 30}
                                try:
                                    rent_res = requests.post(f"{API_BASE_URL}/bookings", json=payload, headers=HTTP_headers(), timeout=2)
                                    if rent_res.status_code == 201:
                                        st.toast(f"Unit #{u['unit_id']} successfully reserved!", icon="✅")
                                        st.rerun()
                                    else:
                                        st.error("Booking error occurred.")
                                except Exception:
                                    st.toast(f"[Demo Mode] Successfully reserved Unit #{u['unit_id']}!", icon="✅")
                                    st.rerun()
                                    
                st.write("---")
                col_prev, col_page, col_next = st.columns([1, 2, 1])
                
                with col_prev:
                    if st.button("◀ Previous", width="stretch", disabled=(current_page == 0)):
                        st.session_state["catalog_page"] -= 1
                        st.rerun()
                with col_page:
                    st.markdown(f"<p style='text-align: center; color: gray; margin-top: 6px;'>Page {current_page + 1} of {max_page_idx + 1}<br><small>({total_units} units total)</small></p>", unsafe_allow_html=True)
                with col_next:
                    if st.button("Next ▶", width="stretch", disabled=(current_page == max_page_idx)):
                        st.session_state["catalog_page"] += 1
                        st.rerun()
                
        with tab_books:
            st.write("")
            st.caption("Real-time telemetry of your active and historical lease logs.")
            try:
                bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers(), timeout=2)
                if bk_res.status_code == 200:
                    st.dataframe(bk_res.json().get("data", []), width="stretch", hide_index=True)
                else:
                    raise Exception()
            except Exception:
                mock_bookings = [
                    {"booking_id": 1042, "unit_id": "B102", "size": "10x10", "price_monthly": 120.0, "status": "active", "start_date": "2026-01-01"},
                    {"booking_id": 1089, "unit_id": "A005", "size": "5x5", "price_monthly": 45.0, "status": "active", "start_date": "2026-05-15"}
                ]
                st.dataframe(mock_bookings, width="stretch", hide_index=True)
                
        with tab_pays:
            st.write("")
            st.caption("Automated PCI-compliant invoice payment portal.")
            
            try:
                pay_res = requests.get(f"{API_BASE_URL}/payments/me", headers=HTTP_headers(), timeout=2)
                if pay_res.status_code == 200:
                    payments_list = pay_res.json().get("data", [])
                else:
                    raise Exception()
            except Exception:
                payments_list = [
                    {"payment_id": 9412, "booking_id": 1042, "amount": 120.0, "status": "Paid", "payment_date": "2026-07-01"},
                    {"payment_id": 9550, "booking_id": 1089, "amount": 45.0, "status": "Pending", "payment_date": "2026-07-15"}
                ]
            
            for p in payments_list:
                # Dynamically resolve Payment and Booking IDs matching DB query response structures
                payment_id = p.get('payment_id', p.get('id', 'N/A'))
                booking_id = p.get('booking_id', p.get('id', 'N/A'))
                payment_date = p.get('payment_date', p.get('created_at', 'N/A'))
                amount_val = p.get('amount', 0.0)
                
                with st.container(border=True):
                    p_col1, p_col2 = st.columns([2.5, 1])
                    with p_col1:
                        st.markdown(f"**Invoice #{payment_id}** (Booking `#{booking_id}`)")
                        st.caption(f"💵 Amount: **${float(amount_val):.2f}** | Date: {payment_date}")
                    with p_col2:
                        if p.get('status') == "Paid":
                            st.success("Status: Paid ✅")
                        else:
                            st.warning("Status: Pending ⏳")
                            
                            # Interactive Popover Modal for Card Entry
                            with st.popover("Pay Now 💳", width="stretch"):
                                st.subheader("Credit Card Details")
                                card_number = st.text_input("Card Number", placeholder="4242 •••• •••• 4242", key=f"num_{payment_id}")
                                c_col1, c_col2 = st.columns(2)
                                with c_col1:
                                    exp_date = st.text_input("MM/YY", placeholder="12/28", key=f"exp_{payment_id}")
                                with c_col2:
                                    cvc = st.text_input("CVC", type="password", placeholder="123", key=f"cvc_{payment_id}")
                                
                                st.write("")
                                if st.button("Confirm Payment ⚡", key=f"btn_pay_{payment_id}", width="stretch", type="primary"):
                                    last4 = card_number[-4:] if len(card_number) >= 4 else "4242"
                                    payload = {
                                        "booking_id": booking_id,
                                        "payment_method_token": "pm_card_visa",
                                        "card_brand": "Visa",
                                        "card_last4": last4
                                    }
                                    try:
                                        pay_exec = requests.post(f"{API_BASE_URL}/payments/checkout", json=payload, headers=HTTP_headers(), timeout=2)
                                        if pay_exec.status_code == 200:
                                            st.toast(f"Invoice #{payment_id} paid with Visa *{last4}!", icon="💳")
                                            st.rerun()
                                        else:
                                            st.error(pay_exec.json().get("detail", "Checkout failed."))
                                    except Exception:
                                        st.toast(f"[Demo Mode] Invoice #{payment_id} paid!", icon="💳")
                                        st.rerun()