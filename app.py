# app.py — EcoSense AI (SaaS Dashboard Edition)
# ------------------------------------------------------------------------------------
# ✅ What you get in this one file
# - SaaS-style layout (sidebar navigation with icons, KPI cards, clean grid)
# - Optional authentication (streamlit-authenticator) with demo users
# - Theme + accent persistence, glassmorphism, animated gradient, alert text fixes
# - User profiles & leaderboard persisted to data/users.csv (auto-created)
# - EV charging optimizer (Open-Meteo renewable-aware window suggestion)
# - Advanced "What-if" lifestyle simulator (CO2/energy impact for many scenarios)
# - Rewards (awareness-based), points history sparkline, monthly PDF report
# - Quick TTS tip (gTTS), Debug / sanity panel
# - Strong defaults, graceful fallbacks, defensive checks
#
# 📦 Suggested requirements.txt
# streamlit==1.37.1
# streamlit-option-menu==0.3.12
# streamlit-authenticator==0.3.2
# pandas==2.2.2
# requests==2.32.3
# matplotlib==3.9.0
# reportlab==4.2.0
# gTTS==2.5.3
# pyyaml==6.0.2
#
# 🏃 Run it
#   pip install -r requirements.txt
#   streamlit run app.py
# ------------------------------------------------------------------------------------

import io
import os
import re
import math
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import streamlit as st

import streamlit as st
import json
from pathlib import Path
from auth import authenticate_user, create_user, add_action_points, load_users, save_users


# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="EcoSense AI Login/Signup", page_icon="🌿", layout="centered")

# ----------------- SESSION STATE -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "signup_error" not in st.session_state:
    st.session_state.signup_error = ""

# ----------------- USERS DATA FILE -----------------
USER_FILE = "users.json"

# Load users
def load_users():
    if Path(USER_FILE).exists():
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

# Save users
def save_users(users):
    if isinstance(users, pd.DataFrame):
        users = users.to_dict(orient='records')
    elif not isinstance(users, (dict, list)):
        raise ValueError("users should be a dict, list of dicts, or a DataFrame")
    # continue with saving users

 

# ----------------- THEME TOGGLE -----------------
theme_choice = st.radio("Theme", ["Light", "Dark"], 
                        index=0 if st.session_state.theme=="Light" else 1, 
                        horizontal=True)
st.session_state.theme = theme_choice
is_dark = theme_choice == "Dark"

# ----------------- STYLING -----------------
bg_gradient = "linear-gradient(270deg, #22c55e, #06b6d4, #3b82f6, #8b5cf6)" if not is_dark else "linear-gradient(270deg, #111827, #1f2937, #374151, #1f2937)"
text_color = "black" if not is_dark else "white"
card_bg = "rgba(255,255,255,0.7)" if not is_dark else "rgba(255,255,255,0.1)"
card_shadow = "rgba(0,0,0,0.3)" if not is_dark else "rgba(0,0,0,0.7)"

st.markdown(f"""
<style>
body, .main {{
    background: {bg_gradient};
    background-size: 800% 800%;
    animation: gradientBG 15s ease infinite;
    color: {text_color};
}}
@keyframes gradientBG {{
    0% {{background-position:0% 50%;}}
    50% {{background-position:100% 50%;}}
    100% {{background-position:0% 50%;}}
}}
.login-card {{
    max-width: 400px;
    margin: 3rem auto;
    padding: 2rem;
    background: {card_bg};
    border-radius: 20px;
    box-shadow: 0 8px 20px {card_shadow};
    text-align: center;
}}
.login-card input {{
    width: 100% !important;
    padding: 0.7rem;
    margin: 0.5rem 0;
    border-radius: 10px;
    border: none;
}}
.login-card button {{
    width: 100% !important;
    padding: 0.7rem;
    margin-top: 1rem;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}}
.login-card button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}}
</style>
""", unsafe_allow_html=True)

# ----------------- LOGO -----------------
logo_path = Path("assets/logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=120)
else:
    st.markdown("## 🌿 EcoSense AI")

# ----------------- LOGOUT FUNCTION -----------------
def logout():
    st.session_state.logged_in = False
    st.session_state.login_error = ""

# ----------------- LOGIN HANDLER -----------------
def handle_login():
    users = load_users()
    username = st.session_state.username
    password = st.session_state.password
    if username in users and users[username] == password:
        st.session_state.logged_in = True
        st.session_state.login_error = ""
    else:
        st.session_state.logged_in = False
        st.session_state.login_error = "❌ Invalid username or password"

# ----------------- SIGNUP HANDLER -----------------
def handle_signup():
    users = load_users()
    username = st.session_state.new_username
    password = st.session_state.new_password
    if username in users:
        st.session_state.signup_error = "❌ Username already exists!"
    elif len(username) < 12 or len(password) < 12:
        st.session_state.signup_error = "❌ Username and password must be at least 3 characters"
    else:
        users[username] = password
        save_users(users)
        st.success("✅ Signup successful! You can now login.")
        st.session_state.signup_error = ""

# ----------------- LOGIN/SIGNUP PAGE -----------------
if not st.session_state.logged_in:
    tab = st.radio("Go to", ["Login", "Sign Up"], horizontal=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    if tab == "Login":
        st.markdown("### 🔑 Login to EcoSense AI")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=handle_login)
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
    
    else:  # Sign Up
        st.markdown("### 📝 Sign Up for EcoSense AI")
        st.text_input("New Username", key="new_username")
        st.text_input("New Password", type="password", key="new_password")
        st.button("Sign Up", on_click=handle_signup)
        if st.session_state.signup_error:
            st.error(st.session_state.signup_error)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- AFTER LOGIN -----------------
if st.session_state.logged_in:
    st.sidebar.markdown("### 👤 Account")
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.success("✅ Logged in successfully!")
    st.markdown("## Welcome to EcoSense AI Dashboard!")


# Optional extras (auth / option menu / PDF / TTS)
try:
    from streamlit_option_menu import option_menu  # type: ignore
except Exception:  # graceful fallback
    option_menu = None

try:
    import streamlit_authenticator as stauth  # type: ignore
except Exception:
    stauth = None

try:
    from gtts import gTTS  # type: ignore
except Exception:
    gTTS = None

try:
    from reportlab.pdfgen import canvas  # type: ignore
except Exception:
    canvas = None

# -------------------------------- Page Config ---------------------------------
st.set_page_config(page_title="EcoSense AI", page_icon="🌿", layout="wide")

# ------------------------------- Session Defaults -----------------------------
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Light ☀️"
if "accent" not in st.session_state:
    st.session_state.accent = "#22c55e"
if "authed_user" not in st.session_state:
    st.session_state.authed_user = None
if "points" not in st.session_state:
    st.session_state.points = 0
if "history" not in st.session_state:
    st.session_state.history = []  # (datetime, points)
if "latlon" not in st.session_state:
    st.session_state.latlon = ("19.07", "72.87")  # Mumbai default
if "ev_profile" not in st.session_state:
    st.session_state.ev_profile = {
        "charger_power": 7.0,
        "battery_capacity": 60.0,
        "current_soc": 40,
        "target_soc": 80,
    }
if "departure" not in st.session_state:
    dep_dt = datetime.now(timezone.utc) + timedelta(hours=12)
    st.session_state.departure = dep_dt

# --------------------------------- Paths & Data --------------------------------
DATA_DIR = Path("data"); DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = DATA_DIR / "users.csv"

# initialize CSV if needed
if not DATA_PATH.exists():
    pd.DataFrame(
        columns=["username", "email", "vehicle_type", "points", "actions", "created_at"]
    ).to_csv(DATA_PATH, index=False)

# load users
users_df = pd.read_csv(DATA_PATH, dtype={"actions": str}) if DATA_PATH.exists() else pd.DataFrame()
if users_df.empty:
    users_df = pd.DataFrame(columns=["username", "email", "vehicle_type", "points", "actions", "created_at"])  
# clean types
if "points" in users_df.columns:
    users_df["points"] = pd.to_numeric(users_df["points"], errors="coerce").fillna(0).astype(int)
else:
    users_df["points"] = 0
if "actions" in users_df.columns:
    users_df["actions"] = users_df["actions"].fillna("")
else:
    users_df["actions"] = ""
for col in ["username", "email", "vehicle_type", "created_at"]:
    if col not in users_df.columns:
        users_df[col] = ""

# --------------------------------- Theming ------------------------------------
# Sidebar quick switcher
with st.sidebar:
    st.markdown("### 🎨 Appearance")
    theme_choice = st.radio("Theme", ["Light ☀️", "Dark 🌑"], index=0, horizontal=True)
    accent = st.color_picker("Accent", st.session_state.accent)
    st.session_state.theme_choice = theme_choice
    st.session_state.accent = accent

is_dark = theme_choice == "Dark 🌑"

bg_grad_start = "#03D1D8" if is_dark else "#f9fafb"
bg_grad_end   = "#B5F34A" if is_dark else "#ffffff"
text_color    = "#f5fcf4" if is_dark else "#C0F352"
muted_color   = "#c7d2fe" if is_dark else "#4b5563"
card_rgba     = "rgba(255,255,255,0.12)" if is_dark else "rgba(255,255,255,0.88)"
shadow_rgba   = "rgba(0,0,0,0.35)" if is_dark else "rgba(0,0,0,0.08)"
border_rgba   = "rgba(255,255,255,0.18)" if is_dark else "rgba(17,24,39,0.10)"
result_text_color = "#d1fae5" if is_dark else "#272611"  # readable inside alerts


# Global CSS (animated gradient, glass cards, alert text fix)
st.markdown(
"""
<style>
/* Improve alert / result text readability */
.stAlert, .stAlert p {
  color: #0b0b0b !important;   /* dark text for light mode */
  font-weight: 600 !important;
}

/* If you want to force white text for specific alerts instead:
:root[data-theme='light'] .stAlert, :root[data-theme='light'] .stAlert p {
  color: #ffffff !important;
}
*/

/* Sidebar: make text darker and more visible in light mode */
[data-testid="stSidebar"] * {
  color: #f9fafb !important;
}

/* Header / cards: fallback */
.css-1v3fvcr, .css-1d391kg {
  color: #0b0b0b !important;
}

/* Prevent small muted text from being too light */
span[style*="opacity: 0.6"], .css-1v3fvcr * {
  color: inherit !important;
}
</style>
""",
unsafe_allow_html=True
)
# Main app styling
st.markdown(
    f"""
<style>
.stApp {{
  background: linear-gradient(-45deg, {bg_grad_start}, {bg_grad_end}, {bg_grad_start});
  background-size: 400% 400%;
  animation: gradMove 22s ease infinite;
  color: {text_color};
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif;
}}
@keyframes gradMove {{ 0% {{background-position:0% 50%}} 50% {{background-position:100% 50%}} 100% {{background-position:0% 50%}} }}

h1,h2,h3,h4,h5,h6 {{ color: {text_color}; }}
.small-muted {{ color:{muted_color}; font-size:0.9rem; }}

/* Cards */
.card {{
  background: {card_rgba};
  border: 1px solid {border_rgba};
  box-shadow: 0 16px 40px {shadow_rgba};
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-radius: 18px; padding: 20px 20px 14px 20px; margin-bottom: 16px;
}}

/* Inputs & buttons */
.stButton>button {{ background: {accent}; color: white; border: 0; border-radius: 12px; padding: 10px 16px; font-weight: 600; box-shadow: 0 6px 18px {shadow_rgba}; }}
.stButton>button:hover {{ filter: brightness(1.02); transform: translateY(-1px); }}
.stButton>button:active {{ transform: translateY(0); }}

/* Sidebar text */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {{ color: {text_color} !important; }}

/* Tables hover */
.dataframe tbody tr:hover {{ background: {border_rgba}; }}

/* Fix Streamlit alerts text color */
div.stAlert, div.stAlert p, div.stAlert span, div.stAlert div {{
  color: {result_text_color} !important; font-weight: 600 !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------- Utilities & Helpers -------------------------
@dataclass
class EVProfile:
    charger_power: float
    battery_capacity: float
    current_soc: int
    target_soc: int


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


@st.cache_data(show_spinner=False, ttl=60 * 15)
def fetch_open_meteo(lat_f: str, lon_f: str, hours: int = 72) -> pd.DataFrame:
    """Fetch hourly solar proxy & wind (UTC) from Open-Meteo. Returns 0..hours DataFrame.
    Uses 'shortwave_radiation' when available; falls back to 'solar_radiation'."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(lat_f),
        "longitude": float(lon_f),
        "hourly": "shortwave_radiation,wind_speed_10m,cloudcover",
        "forecast_days": 3,
        "timezone": "UTC",
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 400:
        params["hourly"] = "solar_radiation,wind_speed_10m,cloudcover"
        r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    hourly = data.get("hourly", {})
    times = pd.to_datetime(hourly.get("time", []), utc=True)
    solar_series = hourly.get("shortwave_radiation") or hourly.get("solar_radiation") or [0] * len(times)
    df = pd.DataFrame({
        "time": times,
        "solar": solar_series,
        "wind": hourly.get("wind_speed_10m", [0] * len(times)),
        "cloud": hourly.get("cloudcover", [0] * len(times)),
    }).set_index("time")
    return df.iloc[:hours].copy()


def compute_green_score(df: pd.DataFrame) -> pd.DataFrame:
    """Weighted green score using normalized solar (70%) and wind (30%), scaled by cloud factor."""
    if df.empty:
        return df
    solar_max = max(df["solar"].max(), 1.0)
    wind_max = max(df["wind"].max(), 1.0)
    solar_norm = df["solar"] / solar_max
    wind_norm = df["wind"] / wind_max
    green = 0.7 * solar_norm + 0.3 * wind_norm
    if "cloud" in df.columns:
        cloud_factor = (100 - df["cloud"]) / 100.0
        green = green * cloud_factor
    df["green_score"] = green.clip(lower=0.0, upper=1.0)
    return df


def find_best_charging_window(df_before: pd.DataFrame, hours_needed: int) -> Tuple[Optional[datetime], Optional[float]]:
    """Brute-force sliding window to find contiguous hours_needed block with max average green_score."""
    if df_before.empty or hours_needed <= 0:
        return None, None
    arr = df_before["green_score"].values
    if len(arr) < hours_needed:
        return None, None
    best_avg = -1.0
    best_start = None
    for i in range(0, len(arr) - hours_needed + 1):
        avg = float(arr[i:i + hours_needed].mean())
        if avg > best_avg:
            best_avg = avg
            best_start = df_before.index[i]
    return best_start, best_avg


# --------------- User Persistence & Leaderboard Utilities ---------------------
def save_users(df: pd.DataFrame) -> None:
    df.to_csv(DATA_PATH, index=False)
def save_users(users):
    """
    Save users dictionary to CSV file.
    `users` can be:
    1. dict of dicts: {username: {"password": "1234", ...}}
    2. list of dicts: [{"username": "prachi", "password": "1234"}, ...]
    """
    # If users is a dict of dicts
    if isinstance(users, dict):
        df = pd.DataFrame.from_dict(users, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'username'}, inplace=True)
    # If users is already a list of dicts
    elif isinstance(users, list):
        df = pd.DataFrame(users)
    else:
        raise ValueError("users should be a dict or list of dicts")

    df.to_csv(DATA_PATH, index=False)

def ensure_user(username: str, email: str = "", vehicle: str = "Non-EV") -> None:
    global users_df
    if not username:
        return
    if username not in users_df["username"].astype(str).tolist():
        new_row = {
            "username": username,
            "email": email,
            "vehicle_type": vehicle,
            "points": 0,
            "actions": "",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        users_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
        save_users(users_df.to_dict(orient='records'))




def add_action_points(username: str, label: str, pts: int) -> None:
    global users_df
    if not username:
        return
    if username not in users_df["username"].values:
        ensure_user(username)
    prev_actions = str(users_df.loc[users_df["username"] == username, "actions"].values[0] or "")
    new_actions = prev_actions + f"\n- [{datetime.now().strftime('%Y-%m-%d')}] {label}"
    users_df.loc[users_df["username"] == username, "actions"] = new_actions
    users_df.loc[users_df["username"] == username, "points"] = (
        int(users_df.loc[users_df["username"] == username, "points"].values[0]) + int(pts)
    )
if isinstance(users_df, pd.DataFrame):
    save_users(users_df.to_dict(orient='records'))
else:
    raise TypeError("users_df must be a DataFrame")



# --------------------------------- Auth Layer ---------------------------------
# Demo credentials (replace with your own; or move to st.secrets)
DEFAULT_AUTH_YAML = {
    "credentials": {
        "usernames": {
            "demo": {"email": "demo@ecosense.ai", "name": "Demo User", "password": "pbkdf2:sha256:260000$demo$0b5c1f3c1f0c3f8f4df0b2f1f2d2d9e9f7a1bd6a9b3c4e5f6a7b8c9d0e1f2a3b"},
            # password for demo is: demo123 (pre-hashed)
        }
    },
    "cookie": {"name": "ecosense_cookie", "key": "random_signature_key", "expiry_days": 7},
    "preauthorized": {"emails": ["demo@ecosense.ai"]},
}


def get_authenticator():
    if stauth is None:
        return None, None
    # Prefer secrets if provided
    auth_yaml = st.secrets.get("auth", None)
    config = auth_yaml if auth_yaml else DEFAULT_AUTH_YAML
    try:
        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )
        return authenticator, config
    except Exception:
        return None, None


authenticator, auth_config = get_authenticator()

# ------------------------------- Header / Branding ----------------------------
st.markdown(
    f"""
<div class="card" style="padding: 12px 18px; display:flex; align-items:center; gap:16px;">
  <div style="font-size: 28px; font-weight: 800; letter-spacing:-.02em;">
    <span style="background: linear-gradient(90deg, {st.session_state.accent}, #42d392 30%, #2dd4bf 60%, {st.session_state.accent} 100%); -webkit-background-clip: text; background-clip: text; color: transparent;">EcoSense AI</span>
  </div>
  <div class="small-muted">Drive the EcoJourney — renewable-aware EV charging & eco coaching</div>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------------- Sidebar (Auth + Nav) ------------------------
with st.sidebar:
    if Path("assets/logo.png").exists():
        st.image("assets/logo.png")
    else:
        st.markdown("## 🌿 EcoSense AI")
 

    # ---------------- Auth block -----------------
    user_info: Dict[str, str] = {"name": "", "email": ""}
    if authenticator:
        try:
            name, auth_status, username = authenticator.login("Login", "sidebar")
        except Exception:
            name, auth_status, username = None, None, None

        if auth_status:
            st.success(f"Signed in as **{name}**")
            st.session_state.authed_user = username or name or ""
            user_info["name"] = name or ""
            user_info["email"] = auth_config.get("credentials", {}).get("usernames", {}).get(username, {}).get("email", "")
            ensure_user(st.session_state.authed_user, user_info["email"], "Non-EV")
        elif auth_status is False:
            st.error("Invalid username/password")
        else:
            st.info("Please log in (or continue as guest below)")
            st.markdown("<hr>", unsafe_allow_html=True)
    else:
        st.info("Auth optional: install `streamlit-authenticator` to enable login")

    # Guest/override name
    username_input = st.text_input("Name (for profile/leaderboard)", value=st.session_state.authed_user or "")
    email_input = st.text_input("Email (optional)", value=user_info.get("email", ""))
    vehicle_type = st.selectbox("Vehicle Type", ["EV", "Non-EV"], index=1)

    if username_input:
        ensure_user(username_input, email_input, vehicle_type)
        st.session_state.authed_user = username_input
        # sync session points
        try:
            pts_val = int(users_df.loc[users_df["username"] == username_input, "points"].values[0])
        except Exception:
            pts_val = 0
        st.session_state.points = pts_val
        if not st.session_state.history:
            st.session_state.history = [(datetime.now(), st.session_state.points)]

    st.markdown("<hr>", unsafe_allow_html=True)

    # Location + EV settings
    st.markdown("**Location (lat, lon)** for forecast")
    cl, cr = st.columns(2)
    with cl:
        lat = st.text_input("Lat", value=st.session_state.latlon[0])
    with cr:
        lon = st.text_input("Lon", value=st.session_state.latlon[1])
    st.session_state.latlon = (lat, lon)

    st.markdown("**EV parameters**")
    c1, c2 = st.columns(2)
    with c1:
        charger_power = st.number_input("Charger kW", 0.1, 200.0, st.session_state.ev_profile["charger_power"], 0.1)
        current_soc = st.number_input("Current SoC %", 0, 100, st.session_state.ev_profile["current_soc"], 1)
    with c2:
        battery_capacity = st.number_input("Battery kWh", 5.0, 200.0, st.session_state.ev_profile["battery_capacity"], 1.0)
        target_soc = st.number_input("Target SoC %", 0, 100, st.session_state.ev_profile["target_soc"], 1)

    st.session_state.ev_profile = {
        "charger_power": charger_power,
        "battery_capacity": battery_capacity,
        "current_soc": current_soc,
        "target_soc": target_soc,
    }

    d1, d2 = st.columns(2)
    with d1:
        dep_date = st.date_input("Departure date", value=st.session_state.departure.date())
    with d2:
        dep_time = st.time_input("Departure time", value=st.session_state.departure.time())
    st.session_state.departure = datetime.combine(dep_date, dep_time).replace(tzinfo=timezone.utc)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Sidebar nav
    nav_options = ["🏠 Dashboard", "⚡ Charging", "🧮 Simulator", "🎁 Rewards", "📄 Reports", "⚙️ Settings"]
    if option_menu:
        selected = option_menu(
            "Navigation",
            nav_options,
            icons=["house", "lightning-charge", "calculator", "gift", "file-earmark-text", "gear"],
            menu_icon="menu-button-wide",
            default_index=0,
            styles={
                "container": {"padding": "6px", "background-color": "transparent"},
                "icon": {"color": text_color, "font-size": "18px"},
                "nav-link": {"color": text_color, "font-size": "16px", "text-align": "left", "margin":"0px"},
                "nav-link-selected": {"background-color": st.session_state.accent, "color": "white"},
            },
        )
    else:
        selected = st.radio("Navigate", nav_options, index=0)

    # Debug toggle
    show_debug = st.checkbox("Show debug panel", value=False)

    # Logout if auth
    if authenticator and st.session_state.authed_user:
        if st.button("🔒 Logout"):
            try:
                authenticator.logout("Logout", "sidebar")
            except Exception:
                pass
            st.session_state.authed_user = None

# -------------------------- Reusable UI Components ----------------------------
def saas_card(title: str, inner_html: str, icon: str = "📊") -> None:
    st.markdown(
        f"""
        <div class='card'>
          <div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>
            <div style='font-size:22px'>{icon}</div>
            <div style='font-weight:700; font-size:18px'>{title}</div>
          </div>
          <div style='font-size:15px; color:{text_color};'>{inner_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(title: str, value: str, help_text: str = ""):
    st.markdown(
        f"""
        <div class='card' style='padding:16px'>
           <div style='font-size:14px; color:{muted_color}; margin-bottom:6px'>{title}</div>
           <div style='font-size:28px; font-weight:800;'>{value}</div>
           <div class='small-muted'>{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------ Pages -----------------------------------
# 1) Dashboard
if selected.startswith("🏠"):
    st.markdown("### 📊 Dashboard")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Eco Points", str(st.session_state.points), "Earn more by completing eco actions")
    with c2:
        # pretend KPI from last charging plan (if any)
        kpi("Green Charging %", "—", "Run a charging plan to update")
    with c3:
        # sim CO2 saved estimate placeholder
        kpi("Estimated CO₂ Saved", "—", "Use Simulator to see potential savings")

    # Points history chart
    st.markdown("#### 📈 Points History")
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history, columns=["time", "points"]).set_index("time")
        st.line_chart(hist_df["points"])
    else:
        st.info("Perform actions to build up your history chart.")

    # Leaderboard snapshot
    st.markdown("#### 🏆 Leaderboard (Top 8)")
    if not users_df.empty:
        lb = users_df.sort_values(by="points", ascending=False).reset_index(drop=True).head(8)
        st.dataframe(lb[["username", "vehicle_type", "points"]], use_container_width=True, hide_index=True)
    else:
        st.info("No users yet — be the first!")

# 2) Charging Optimizer
elif selected.startswith("⚡"):
    st.markdown("### ⚡ Renewable-aware EV Charging Optimizer")
    st.caption("We compute a green score (solar + wind) and recommend the best charging window before your departure.")

    lat, lon = st.session_state.latlon
    ep = st.session_state.ev_profile
    departure_time = st.session_state.departure

    # Buttons
    colb = st.columns(3)
    get_plan = colb[0].button("📈 Get Charging Plan")
    export_btn = colb[1].button("⬇️ Export 24h CSV")

    if get_plan:
        try:
            df = fetch_open_meteo(lat, lon, hours=72)
            df = compute_green_score(df)
            st.success("Renewable forecast fetched.")

            plt.rcParams.update({
                "axes.edgecolor": "#9aa0a6",
                "axes.facecolor": "none",
                "figure.facecolor": "none",
                "grid.color": "#9aa0a633",
                "text.color": text_color,
                "axes.labelcolor": text_color,
                "xtick.color": text_color,
                "ytick.color": text_color,
            })

            needed_kwh = ep["battery_capacity"] * max(0.0, (ep["target_soc"] - ep["current_soc"]) / 100.0)
            hours_needed = max(1, math.ceil(needed_kwh / max(0.1, ep["charger_power"])))

            df_before = df[df.index <= departure_time]
            if df_before.empty:
                st.warning("No forecast hours available before departure time.")
            else:
                best_start, best_avg = find_best_charging_window(df_before, hours_needed)
                if best_start is not None:
                    best_end = best_start + timedelta(hours=hours_needed)
                    st.success(
                        f"Recommended (UTC): **{fmt_dt(best_start)} → {fmt_dt(best_end)}** (avg green score {best_avg:.2f})"
                    )

                    plot_df = df_before.copy()
                    plot_df["recommended"] = 0
                    start_idx = plot_df.index.get_loc(best_start)
                    plot_df.iloc[start_idx:start_idx + hours_needed, plot_df.columns.get_loc("recommended")] = 1

                    fig, ax = plt.subplots(figsize=(9.5, 3.2))
                    ax.grid(True, linestyle="--", linewidth=0.6)
                    ax.plot(plot_df.index, plot_df["green_score"], marker="o", linewidth=2.2, label="Green score")
                    rec = plot_df[plot_df["recommended"] == 1]
                    ax.scatter(rec.index, rec["green_score"], s=90, label="Recommended")
                    ax.set_ylabel("Green Score (0-1)"); ax.set_xlabel("UTC time"); ax.set_title("Renewable Availability")
                    ax.legend(); plt.xticks(rotation=25)
                    st.pyplot(fig, use_container_width=True)

                    # Preview table
                    preview = plot_df.reset_index().rename(columns={"index": "time"})
                    cols_show = [c for c in ["time", "solar", "wind", "cloud", "green_score", "recommended"] if c in preview.columns]
                    st.dataframe(preview[cols_show].head(24), use_container_width=True, hide_index=True)
                else:
                    st.warning("Couldn't find a contiguous block matching the required charging duration.")
        except Exception as e:
            st.error("Failed to fetch/process forecast: " + str(e))

    if export_btn:
        try:
            df = fetch_open_meteo(lat, lon, hours=24)
            df = compute_green_score(df).reset_index()
            csv_bytes = df.to_csv(index=False).encode()
            st.download_button("Download next 24h (CSV)", csv_bytes, file_name="renewables_24h.csv", mime="text/csv")
        except Exception as e:
            st.error("Export failed: " + str(e))

    st.markdown(
        f"<span class='small-muted'>💡 Tip: Rooftop solar? Prefer daytime charging (11:00–15:00 local). Wind peaks vary by region.</span>",
        unsafe_allow_html=True,
    )

# 3) Simulator
elif selected.startswith("🧮"):
    st.markdown("### 🔮 Lifestyle Impact Simulator — 'What if I...' (Advanced)")
    st.caption("Examples: 'bike 6 km 5 days/week', 'skip 1 flight 1200 km', 'install 3 kW solar', 'replace 8 bulbs with LED', 'wfh 2 days/week', 'raise AC by 2C'")

    # Constants
    EF_CAR_KG_PER_KM = 0.18
    EF_ELECTRIC_GRID = 0.7
    FLIGHT_KG_PER_KM = 0.20
    LED_KWH_SAVING_PER_BULB_YR = 44
    SOLAR_KWH_PER_KW_DAY = 4.5
    AC_KWH_PER_DEG_PER_DAY = 0.4
    IDLING_L_PER_HR = 0.8
    EF_KG_PER_L_FUEL = 2.31
    SPEED_SAVING_FACTOR = 0.15

    def _get_number(text: str, default: float) -> float:
        m = re.search(r"(\d+(\.\d+)?)", text)
        return float(m.group(1)) if m else float(default)

    def _km_in_text(text: str, default: float) -> float:
        m = re.search(r"(\d+(\.\d+)?)\s*(km|kilometer|kilometre)s?", text)
        if m:
            return float(m.group(1))
        m = re.search(r"(\d+(\.\d+)?)\s*(mile|miles)", text)
        if m:
            return float(m.group(1)) * 1.609
        return float(default)

    def _days_per_week(text: str, default: float = 5) -> float:
        m = re.search(r"(\d+)\s*(day|days)\s*(a|per)?\s*week", text)
        if m:
            return float(m.group(1))
        m = re.search(r"(\d+)\s*x\s*/?\s*week", text)
        if m:
            return float(m.group(1))
        return default

    def _percent_in_text(text: str, default: float) -> float:
        m = re.search(r"(\d+(\.\d+)?)\s*%", text)
        return float(m.group(1)) if m else float(default)

    def estimate_impact(sentence: str) -> str:
        s = sentence.lower().strip()

        # Bike / walk
        if any(k in s for k in ["bike", "cycle", "bicycle", "walk"]):
            km = _km_in_text(s, 5)
            days = _days_per_week(s, 5)
            yearly_km = km * days * 52
            saved = yearly_km * EF_CAR_KG_PER_KM
            return f"🚲 Switching {km:.1f} km/day, {days:.0f} days/week from car saves ~{saved/1000:.2f} t CO₂/year."

        # Vegetarian / vegan
        if "vegan" in s:
            return "🥗 Going vegan can save ~1.0–1.5 t CO₂/year (diet-dependent)."
        if "vegetarian" in s or "go veg" in s:
            return "🥗 Going vegetarian can save ~0.5–1.0 t CO₂/year (diet-dependent)."

        # Public transport / carpool
        if any(k in s for k in ["public transport", "bus", "train", "metro", "carpool"]):
            km = _km_in_text(s, 20)
            days = _days_per_week(s, 5)
            saved = km * days * 52 * EF_CAR_KG_PER_KM * 0.5
            return f"🚌 Switching {km:.0f} km/day, {days:.0f} days/week to public transport saves ~{saved/1000:.2f} t CO₂/year."

        # WFH
        if "work from home" in s or "wfh" in s:
            km = _km_in_text(s, 20)
            days = _days_per_week(s, 2)
            saved = km * days * 52 * EF_CAR_KG_PER_KM
            return f"💻 WFH {days:.0f} day(s)/week (commute {km:.0f} km/day) saves ~{saved/1000:.2f} t CO₂/year."

        # Flights
        if "flight" in s or "fly" in s:
            km = _km_in_text(s, 1200)
            trips = _get_number(s, 1)
            saved = km * 2 * trips * FLIGHT_KG_PER_KM
            return f"✈️ Skipping {int(trips)} flight(s) of {km:.0f} km (each way) saves ~{saved/1000:.2f} t CO₂."

        # LEDs
        if "led" in s and ("bulb" in s or "light" in s):
            bulbs = _get_number(s, 6)
            saved_kwh = bulbs * LED_KWH_SAVING_PER_BULB_YR
            saved = saved_kwh * EF_ELECTRIC_GRID
            return f"💡 Replacing {int(bulbs)} bulbs with LED saves ~{saved_kwh:.0f} kWh/year (~{saved/1000:.2f} t CO₂)."

        # Solar
        if "solar" in s:
            kw = _get_number(s, 3)
            yearly_kwh = kw * SOLAR_KWH_PER_KW_DAY * 365
            saved = yearly_kwh * EF_ELECTRIC_GRID
            return f"🔆 {kw:.1f} kW solar → ~{yearly_kwh:.0f} kWh/year → offsets ~{saved/1000:.2f} t CO₂/year."

        # AC setpoint up
        if "ac" in s and any(k in s for k in ["raise", "increase", "+"]):
            deg = _get_number(s, 2)
            days = 180
            saved_kwh = deg * AC_KWH_PER_DEG_PER_DAY * days
            saved = saved_kwh * EF_ELECTRIC_GRID
            return f"❄️ Raising AC by {deg:.0f}°C saves ~{saved_kwh:.0f} kWh/season (~{saved/1000:.2f} t CO₂)."

        # Drive slower
        if any(k in s for k in ["limit speed", "drive slower", "90 km/h"]):
            km = _km_in_text(s, 10000)
            saved = km * EF_CAR_KG_PER_KM * SPEED_SAVING_FACTOR
            return f"🚘 Limiting speed saves ~{saved/1000:.2f} t CO₂/year over {km:.0f} km."

        # Switch % of trips
        if "%" in s and any(k in s for k in ["bus", "train", "metro", "public"]):
            percent = _percent_in_text(s, 30) / 100.0
            km = _km_in_text(s, 12000)
            saved = km * percent * EF_CAR_KG_PER_KM * 0.5
            return f"🚍 Shifting {percent*100:.0f}% of {km:.0f} km/year to public transit saves ~{saved/1000:.2f} t CO₂/year."

        # Idling
        if "idle" in s or "idling" in s:
            hours = _get_number(s, 50)
            liters = hours * IDLING_L_PER_HR
            saved = liters * EF_KG_PER_L_FUEL
            return f"🕒 Avoiding {hours:.0f} h idling saves ~{saved/1000:.2f} t CO₂."

        # Switch to EV
        if "switch to ev" in s or ("switch" in s and "ev" in s):
            km = _km_in_text(s, 12000)
            ice = km * EF_CAR_KG_PER_KM
            ev = (km * 0.15) * EF_ELECTRIC_GRID
            saved = max(ice - ev, 0)
            return f"⚡ Switching to EV for {km:.0f} km/year saves ~{saved/1000:.2f} t CO₂/year."

        return "ℹ️ Try: 'bike 6 km 5 days/week', 'skip 1 flight 1200 km', 'install 3 kW solar'"

    scenario = st.text_input("Describe your scenario", value="")
    if st.button("Simulate impact"):
        if scenario.strip():
            out = estimate_impact(scenario)
            st.success(out)
        else:
            st.info("Type something like: 'bike 6 km to work 5 days a week'.")

# 4) Rewards
elif selected.startswith("🎁"):
    st.markdown("### 🌟 Eco Actions & Rewards")

    actions_list = [
        ("Plan trips to reduce driving", 5),
        ("Use public transport / carpool", 10),
        ("Charge during green hours", 8),
        ("Drive smoothly (avoid harsh braking)", 5),
        ("Service vehicle for better efficiency", 6),
    ]

    cols = st.columns(3)
    for idx, (label, pts) in enumerate(actions_list):
        with cols[idx % 3]:
            if st.button(label):
                if not st.session_state.authed_user:
                    st.warning("Enter your name in the sidebar to record actions.")
                else:
                    add_action_points(st.session_state.authed_user, label, pts)
                    st.success(f"+{pts} points — {label}")
                    st.session_state.points = int(users_df.loc[users_df["username"] == st.session_state.authed_user, "points"].values[0])
                    st.session_state.history.append((datetime.now(), st.session_state.points))
                    if st.session_state.points >= 100:
                        st.balloons()

    # Show profile & leaderboard here as well
    st.markdown("#### 🏆 Profile & Leaderboard")
    if st.session_state.authed_user:
        st.metric("Your Eco Points", st.session_state.points)
    if not users_df.empty:
        lb = users_df.sort_values(by="points", ascending=False).reset_index(drop=True).head(10)
        st.dataframe(lb[["username", "vehicle_type", "points"]], use_container_width=True, hide_index=True)
    else:
        st.info("No users yet — be the first!")

# 5) Reports
elif selected.startswith("📄"):
    st.markdown("### 📄 Monthly PDF Report")
    if not st.session_state.authed_user:
        st.warning("Enter your name in the sidebar to generate your report.")
    else:
        if canvas is None:
            st.error("Install reportlab to enable PDF generation: pip install reportlab")
        else:
            if st.button("Generate & Download PDF"):
                try:
                    username = st.session_state.authed_user
                    row = users_df.loc[users_df["username"] == username]
                    if row.empty:
                        st.warning("User not found in database; saving now…")
                        ensure_user(username, "", "Non-EV")
                        row = users_df.loc[users_df["username"] == username]
                    row = row.iloc[0]

                    buf = io.BytesIO()
                    c = canvas.Canvas(buf, pagesize=(595, 842))
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(40, 800, "EcoSense AI — Monthly Report")
                    c.setFont("Helvetica", 12)
                    c.drawString(40, 780, f"User: {username}")
                    c.drawString(40, 764, f"Email: {row['email']}")
                    c.drawString(40, 748, f"Vehicle: {row['vehicle_type']}")
                    c.drawString(40, 732, f"Eco Points: {int(row['points'])}")
                    c.drawString(40, 712, "Actions:")
                    y = 692
                    for line in str(row["actions"]).split("\n"):
                        if line.strip():
                            c.drawString(60, y, line.strip()); y -= 16
                            if y < 80:
                                c.showPage(); y = 800
                    c.showPage(); c.save(); buf.seek(0)
                    st.download_button("📥 Download Report (PDF)", buf, file_name=f"{username}_ecosense_report.pdf", mime="application/pdf")
                except Exception as e:
                    st.error("Failed to generate PDF: " + str(e))

    st.markdown("#### 🔊 Quick Voice Tip")
    if gTTS is None:
        st.info("Install gTTS to enable text-to-speech: pip install gTTS")
    else:
        if st.button("Play Tip"):
            try:
                tip_text = "Charge during the recommended window to maximize renewable energy and cut carbon emissions."
                tts = gTTS(tip_text); tts.save("eco_tip.mp3")
                audio_bytes = open("eco_tip.mp3", "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error("TTS failed: " + str(e))

# 6) Settings
elif selected.startswith("⚙️"):
    st.markdown("### ⚙️ Settings & Preferences")

    # Theme & accent (already in sidebar), expose additional toggles here
    st.markdown("#### Appearance")
    st.write("Use the sidebar to change theme and accent.")

    st.markdown("#### Account")
    uname = st.text_input("Display Name", value=st.session_state.authed_user or "")
    email = st.text_input("Email", value="")
    veh = st.selectbox("Vehicle", ["EV", "Non-EV"], index=1)

    if st.button("Save Profile"):
        if uname:
            ensure_user(uname, email, veh)
            st.session_state.authed_user = uname
            st.success("Profile saved.")
        else:
            st.warning("Enter a name.")

    st.markdown("#### Data Export")
    if not users_df.empty:
        st.download_button("⬇️ Download users.csv", users_df.to_csv(index=False).encode(), file_name="users.csv", mime="text/csv")

# --------------------------------- Footer & Notes -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(
    "**Notes:** Green score is a simple normalized mix of solar radiation and wind speed from Open-Meteo (free). "
    "For higher accuracy integrate inverter or grid carbon intensity APIs (WattTime / ElectricityMap)."
)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------ Debug / Sanity Panel --------------------------
def _sanity_checks() -> List[str]:
    problems: List[str] = []
    try:
        if not users_df.empty and users_df["username"].duplicated().any():
            problems.append("Duplicate usernames in users.csv.")
        if "points" in users_df.columns:
            if not pd.api.types.is_integer_dtype(users_df["points"].dtype):
                coerced = pd.to_numeric(users_df["points"], errors="coerce")
                if coerced.isna().any():
                    problems.append("Points column contains non-numeric values.")
                else:
                    problems.append("Points column not integer dtype; consider converting to int.")
        else:
            problems.append("Points column missing in users.csv.")
        if "actions" in users_df.columns:
            if not (pd.api.types.is_object_dtype(users_df["actions"].dtype) or pd.api.types.is_string_dtype(users_df["actions"].dtype)):
                problems.append("Actions column exists but is not string/object dtype.")
        else:
            problems.append("Actions column missing in users.csv.")
        if "vehicle_type" in users_df.columns:
            bad = users_df[~users_df["vehicle_type"].isin(["EV", "Non-EV"])]
            if not bad.empty:
                problems.append("Some vehicle_type values are unexpected (expected 'EV' or 'Non-EV').")
        else:
            problems.append("vehicle_type column missing in users.csv.")
        if "username" in users_df.columns:
            if users_df["username"].isnull().any() or (users_df["username"].astype(str).str.strip() == "").any():
                problems.append("Some username entries are empty or null.")
        else:
            problems.append("username column missing in users.csv.")
    except Exception as e:
        problems.append(f"Sanity-check runner error: {e}")
    return problems

if show_debug:
    issues = _sanity_checks()
    st.sidebar.write("## Debug / Sanity checks")
    if not issues:
        st.sidebar.success("Sanity checks passed.")
    else:
        st.sidebar.error("Sanity checks found issues:")
        for it in issues:
            st.sidebar.write("- " + it)
    st.sidebar.write("### Debug snapshot")
    st.sidebar.write(f"Loaded users: {len(users_df)}")
    st.sidebar.write(f"Session points: {st.session_state.points}")
    st.sidebar.write(f"User: {st.session_state.authed_user}")
    st.sidebar.write(f"Location: {st.session_state.latlon}")
    st.sidebar.write(f"Departure UTC: {st.session_state.departure.isoformat()}")

# --------------------------------- Developer Tips -----------------------------
# 1) To enable real authentication, add to .streamlit/secrets.toml:
# [auth]
#   [[auth.credentials.usernames.user1]]
#   email = "user1@example.com"
#   name = "User One"
#   # use stauth.Hasher(["yourpassword"]).generate() to create hash, then paste:
#   password = "pbkdf2:sha256:260000$..."
#
#   [auth.cookie]
#   name = "ecosense_cookie"
#   key = "a_long_random_secret"
#   expiry_days = 14
#
# 2) Replace demo KPIs with real metrics from your domain logic.
# 3) Move constants to a config module if needed.
# 4) Add billing (Stripe / Razorpay) by linking a hosted checkout page and storing subscription status per user.
# 5) Consider a real DB (Supabase / Firebase / Postgres) for multi-user scale.
