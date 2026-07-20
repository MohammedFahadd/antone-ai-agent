# app.py
import streamlit as st
import requests
from google import genai

# Base URL pointing to your running FastAPI backend
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_API_KEY = "NectarPlatformSecretToken2026"

st.set_page_config(
    page_title="Antone AI - Tenant Inc",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection to visually polish the chat input container positioning
st.markdown(
    """
    <style>
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
    """, 
    unsafe_allow_html=True
)

# Initialize persistent session states for auth tokens and messages
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
    """Queries the catalog to extract unique facility locations and count available units dynamically."""
    try:
        res = requests.get(f"{API_BASE_URL}/inventory/search", headers=API_key_headers())
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
    return ["All Cities", "Irvine", "San Diego"]


# =========================================================================
# SIDEBAR: NAVIGATION PANEL & SESSION METRICS
# =========================================================================
with st.sidebar:
    st.title("🔑 Tenant Space Control")
    st.write("---")
    
    if not st.session_state["access_token"]:
        page_route = st.selectbox("Navigate Portal Pages", ["🔑 Login to Account", "✨ Register Profile"])
        st.write("---")
        
        if page_route == "🔑 Login to Account":
            st.subheader("Login Portal")
            login_email = st.text_input("Email Address", placeholder="name@example.com", key="login_email")
            login_password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            st.write("")
            
            if st.button("Secure Login 🔓", use_container_width=True, type="primary"):
                payload = {"email": login_email, "password": login_password}
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
                    if res.status_code == 200:
                        st.session_state["access_token"] = res.json()["access_token"]
                        profile_res = requests.get(f"{API_BASE_URL}/customers/me", headers=HTTP_headers())
                        if profile_res.status_code == 200:
                            st.session_state["customer_name"] = profile_res.json()["data"]["first_name"]
                        st.session_state["show_login_prompt"] = False
                        st.toast("Welcome back! Control center unlocked.", icon="🔓")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Invalid email or password."))
                except Exception as e:
                    st.error(f"Backend Link Offline: {str(e)}")
                    
        elif page_route == "✨ Register Profile":
            st.subheader("Registration Portal")
            reg_first_name = st.text_input("First Name", placeholder="John")
            reg_last_name = st.text_input("Last Name", placeholder="Doe")
            reg_email = st.text_input("Email Address", placeholder="name@example.com")
            reg_password = st.text_input("Password", type="password", placeholder="••••••••")
            st.write("")
            
            if st.button("Create Account 📝", use_container_width=True, type="primary"):
                payload = {"first_name": reg_first_name, "last_name": reg_last_name, "email": reg_email, "password": reg_password}
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
                    if res.status_code == 200:
                        st.success("Account created successfully! Select 'Login to Account' from the navigation dropdown above to access your portal.")
                    else:
                        st.error(res.json().get("detail", "Registration rejected."))
                except Exception as e:
                    st.error(f"Backend Link Offline: {str(e)}")

    else:
        st.subheader(f"Welcome back, {st.session_state['customer_name']}! 👋")
        st.caption("Session Status: Authenticated via Secure JWT Token")
        st.write("---")
        
        try:
            bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers())
            if bk_res.status_code == 200:
                active_count = bk_res.json().get("count", 0)
                st.metric(label="Your Subleased Units", value=active_count)
        except Exception:
            pass
            
        st.write("---")
        if st.button("Log Out Session 🚪", use_container_width=True):
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
        
        profile_flagged_keywords = ["my unit", "my booking", "my statement", "my bill", "my payment", "balance", "sublease", "invoice", "rent unit", "ledger", "details"]
        requires_profile_context = any(word in prompt.lower() for word in profile_flagged_keywords)
        
        if requires_profile_context and not st.session_state["access_token"]:
            st.session_state["show_login_prompt"] = True
            ai_response = "I can definitely help locate that layout detail for you, but those metrics contain personal profile information! Please use the sidebar terminal box to login to your tenant dashboard space."
        else:
            st.session_state["show_login_prompt"] = False
            greeting = f"Sure thing, {st.session_state['customer_name']}! " if st.session_state["access_token"] else ""
            
            # --- BACKEND DATABASE CONTEXT EXTRACTION ---
            db_context = ""
            try:
                # 1. Fetch live system inventory summary records
                res = requests.get(f"{API_BASE_URL}/inventory/search", headers=API_key_headers())
                if res.status_code == 200:
                    units_data = res.json().get("data", [])
                    unique_sizes = sorted(list(set(u["size"] for u in units_data)))
                    
                    # Track cities and gather pricing arrays
                    city_summary = {}
                    prices = []
                    
                    for u in units_data:
                        city = u["facility_name"].split(" - ")[-1] if " - " in u["facility_name"] else u["facility_name"]
                        city_summary[city] = city_summary.get(city, 0) + 1
                        if "price_monthly" in u:
                            prices.append(u["price_monthly"])
                            
                    # Calculate active price boundaries for context injection
                    price_info = "No pricing telemetry recorded"
                    if prices:
                        price_info = f"Starts at ${min(prices):.2f}/mo (Cheapest unit available) up to ${max(prices):.2f}/mo"
                    
                    db_context += (
                        f"Live Storage Inventory Context:\n"
                        f"- Total vacant units available: {len(units_data)}\n"
                        f"- Available sizes: {', '.join(unique_sizes)}\n"
                        f"- Pricing Spectrum: {price_info}\n"
                        f"- Facilities by location/city: {', '.join([f'{k} has {v} units' for k, v in city_summary.items()])}\n\n"
                    )
                else:
                    db_context += f"\n[Backend API Error: Returned status code {res.status_code}]\n"
                
                # 2. Fetch authenticated tenant session logs (If active token is verified)
                if st.session_state["access_token"]:
                    bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers())
                    if bk_res.status_code == 200:
                        user_bookings = bk_res.json().get("data", [])
                        db_context += "Authenticated User's Active Leases & Bookings:\n"
                        if user_bookings:
                            for b in user_bookings:
                                db_context += f"- Booking ID #{b['booking_id']}: Unit #{b['unit_id']}, Sizing Tier: {b['size']}, Rate: ${b['price_monthly']}/mo, Status: {b['status']}, Start Date: {b['start_date']}, End Date: {b['end_date']}\n"
                        else:
                            db_context += "- No active or past bookings found on record.\n"
                    
                    pay_res = requests.get(f"{API_BASE_URL}/payments/me", headers=HTTP_headers())
                    if pay_res.status_code == 200:
                        user_payments = pay_res.json().get("data", [])
                        db_context += "\nAuthenticated User's Invoice Statements & Payments Ledger:\n"
                        if user_payments:
                            for p in user_payments:
                                db_context += f"- Payment ID #{p['payment_id']} tied to Booking #{p['booking_id']}: Amount ${p['amount']}, Status: {p['status']}, Logged Timestamp: {p['payment_date']}\n"
                        else:
                            db_context += "- No payment invoices or transaction statements recorded.\n"
                            
            except Exception as e:
                db_context += f"\n[System Exception connecting to backend: {str(e)}]\n"

            # --- GEMINI AI GENERATION ENGINE WITH PERSISTENT MEMORY ---
            try:
                # Dynamic API key secret fallbacks initialization mapping
                if "GEMINI_API_KEY" in st.secrets:
                    api_key_str = st.secrets["GEMINI_API_KEY"]
                elif "GOOGLE_API_KEY" in st.secrets:
                    api_key_str = st.secrets["GOOGLE_API_KEY"]
                else:
                    # Cleaned hardcoded key to placeholder to pass Git secret validation rules safely
                    api_key_str = "YOUR_GEMINI_API_KEY_HERE"

                # Initialize the modern client
                client = genai.Client(api_key=api_key_str)
                
                system_instruction = (
                    "You are Antone, an AI-powered real-time chat assistant for a self-storage operator company named Tenant Inc. "
                    "Be professional, clear, and helpful. Use the provided live inventory data and user profile metadata to accurately answer inquiries. "
                    "If the user asks about their active bookings or leases, use the authenticated user bookings context to describe their unit IDs, sizes, "
                    "monthly rates, and status. If asked general storage questions, answer them knowledgeably using your training data."
                )

                # Format the conversation history array for the Gemini SDK session
                # Skipping index 0 to exclude the static initial welcome greeting
                formatted_history = []
                for msg in st.session_state["messages"][1:-1]:
                    formatted_history.append(
                        genai.types.Content(
                            role="user" if msg["role"] == "user" else "model",
                            parts=[genai.types.Part.from_text(text=msg["content"])]
                        )
                    )

                # Spin up an interactive multi-turn chat instance matching the system instructions
                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                    history=formatted_history
                )
                
                # Prepend fresh runtime environment data structures straight into the newest turn context
                full_ai_prompt = f"{db_context}\nUser Current Name Context: {st.session_state['customer_name']}\nUser Question: {prompt}"
                
                # Send the multi-layered question along the history timeline context chain
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
                    
                inv_res = requests.get(f"{API_BASE_URL}/inventory/search", params=query_params, headers=API_key_headers())
                if inv_res.status_code == 200:
                    units_data = inv_res.json().get("data", [])
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
                                Glen = len(sliced_units)
                                with c_info:
                                    st.markdown(f"**{u['facility_name']}** — `Unit #{u['unit_id']}`")
                                    st.caption(f"📐 Size Tier: **{u['size']}** | 💵 Rate: **${u['price_monthly']:.2f}/mo**")
                                with c_action:
                                    st.write("")
                                    if st.button("Rent ⚡", key=f"rent_{u['unit_id']}", use_container_width=True):
                                        payload = {"unit_id": u['unit_id'], "days_duration": 30}
                                        rent_res = requests.post(f"{API_BASE_URL}/bookings", json=payload, headers=HTTP_headers())
                                        if rent_res.status_code == 201:
                                            st.toast(f"Unit #{u['unit_id']} successfully reserved!", icon="✅")
                                            st.rerun()
                                        else:
                                            st.error("Booking error occurred.")
                                            
                        st.write("---")
                        col_prev, col_page, col_next = st.columns([1, 2, 1])
                        
                        with col_prev:
                            if st.button("◀ Previous", use_container_width=True, disabled=(current_page == 0)):
                                st.session_state["catalog_page"] -= 1
                                st.rerun()
                        with col_page:
                            st.markdown(f"<p style='text-align: center; color: gray; margin-top: 6px;'>Page {current_page + 1} of {max_page_idx + 1}<br><small>({total_units} units total)</small></p>", unsafe_allow_html=True)
                        with col_next:
                            if st.button("Next ▶", use_container_width=True, disabled=(current_page == max_page_idx)):
                                st.session_state["catalog_page"] += 1
                                st.rerun()
                                
            except Exception as e:
                st.error(f"Error accessing available inventory: {str(e)}")
                
        with tab_books:
            st.write("")
            st.caption("Real-time telemetry of your active and historical lease logs.")
            try:
                bk_res = requests.get(f"{API_BASE_URL}/bookings/me", headers=HTTP_headers())
                if bk_res.status_code == 200:
                    bk_data = bk_res.json().get("data", [])
                    if not bk_data:
                        st.info("No lease agreements found on record.")
                    else:
                        st.dataframe(bk_data, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error syncing booking history: {str(e)}")
                
        with tab_pays:
            st.write("")
            st.caption("Automated system statements invoice billing balances ledger tracker.")
            try:
                pay_res = requests.get(f"{API_BASE_URL}/payments/me", headers=HTTP_headers())
                if pay_res.status_code == 200:
                    pay_data = pay_res.json().get("data", [])
                    if not pay_data:
                        st.info("No statement invoices found.")
                    else:
                        st.dataframe(pay_data, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error syncing payment ledger: {str(e)}")