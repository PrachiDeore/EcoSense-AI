# app.py - EcoSense AI (original features preserved) + Stylish UI (Light/Dark toggle, glassmorphism, animated gradient)
# Features (unchanged):
# - Renewable-aware EV charging recommendation (Open-Meteo)
# - Advanced "What-if" lifestyle simulator (many scenarios)
# - Awareness-based rewards saved in data/users.csv
# - Monthly PDF report generation
# - Quick TTS voice tip (gTTS)
# - Defensive checks and helpful debug panel
#
# Folder:
# Ecosense_AI/
#   app.py
#   assets/logo.png    (optional)
#   data/users.csv     (auto-created)
#
# Run:
# pip install -r requirements.txt
# streamlit run app.py

import re
import math
import io
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, List

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
from gtts import gTTS
from reportlab.pdfgen import canvas
# ---- Persisted UI prefs (theme & accent) ----
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Light ☀️"
if "accent" not in st.session_state:
    st.session_state.accent = "#22c55e"

# ---------------- Page config ----------------
st.set_page_config(page_title="EcoSense AI", page_icon="🌿", layout="wide")

# ---------------- Theming ----------------
# ---------------- Theming ----------------
with st.sidebar:
    st.markdown("### 🎨 Appearance")
    theme_choice = st.radio("Theme", ["Light ☀️", "Dark 🌑"], index=0, horizontal=True)
    accent = st.color_picker("Accent color", "#13A047")  # default green
is_dark = theme_choice == "Dark 🌑"
sidebar_text_color = "#f4fcfc" if is_dark else "#B0CC75"

# CSS: animated gradient background + glassmorphism cards + better typography
bg_grad_start = "#0e1117" if is_dark else "#f9fafb"     # lighter background in light mode
bg_grad_end   = "#111827" if is_dark else "#ffffff"
text_color    = "#f4fcfc" if is_dark else "#3FDC5C"     # 🔥 true black for light mode
muted_color   = "#e8ecf2" if is_dark else "#374151"     # darker muted for light mode
card_rgba = "rgba(255,255,255,0.15)" if is_dark else "rgba(255,255,255,0.88)" # less transparent in light mode
shadow_rgba   = "rgba(0,0,0,0.35)" if is_dark else "rgba(0,0,0,0.08)"
border_rgba   = "rgba(255,255,255,0.18)" if is_dark else "rgba(17,24,39,0.10)"
# High-contrast result text color
result_text_color = "#0f5132" if not is_dark else "#d1fae5" 
 
st.markdown(
    f"""
    <style>
        /* Force readable text in alert boxes */
        div.stAlert > div {{
            color: {"#0f5132" if not is_dark else "#d1fae5"} !important;
            font-weight: 600 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    f"""
    <style>
        /* Global variable for result text */
        :root {{
            --result-text: {result_text_color};
        }}

        /* Fix for Streamlit alerts (st.success, st.info, etc.) */
        .stAlert {{
            color: var(--result-text) !important;
            font-weight: 500;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
<style>
/* Background: animated gradient */
.stApp {{
  background: linear-gradient(-45deg, {bg_grad_start}, {bg_grad_end}, {bg_grad_start});
  background-size: 400% 400%;
  animation: gradientMove 22s ease infinite;
  color: {text_color};
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif;
}}

@keyframes gradientMove {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}

h1, h2, h3, h4, h5, h6 {{
  color: {text_color};
}}

.small-muted {{ color:{muted_color}; font-size:0.9rem; }}

/* ---------------- Sidebar text fix ---------------- */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {{
    color: {text_color} !important;
}}

section[data-testid="stSidebar"] input {{
    color: {text_color} !important;
}}

.eco-hero {{
  text-align:center;
  padding: 0.4rem 0 0.6rem 0;
}}
.eco-title {{
  font-size: 2.25rem;
  line-height: 1.06;
  margin: 0;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, {accent} 0%, #42d392 30%, #2dd4bf 60%, {accent} 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 6px 18px {shadow_rgba});
}}
.eco-sub {{
  margin-top: .25rem;
  color: {muted_color};
}}

.card {{
  background: {card_rgba};
  border: 1px solid {border_rgba};
  box-shadow: 0 12px 40px {shadow_rgba};
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 18px;
  padding: 20px 20px 14px 20px;
  margin-bottom: 16px;
}}

.block-sep {{ margin: 10px 0 6px 0; }}

hr {{ border: none; height: 1px; background: {border_rgba}; margin: 16px 0; }}

/* Buttons */
.stButton>button {{
  background: {accent};
  color: white;
  border: 0;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 600;
  transition: transform .05s ease-in-out, filter .2s ease;
  box-shadow: 0 6px 18px {shadow_rgba};
}}
.stButton>button:hover {{ filter: brightness(1.02); transform: translateY(-1px); }}
.stButton>button:active {{ transform: translateY(0); }}

/* Inputs */
.stTextInput>div>div>input,
.stNumberInput input,
.stSelectbox>div>div>div>input {{
  border-radius: 12px;
  color: {text_color} !important;
}}

/* Tables */
.dataframe tbody tr:hover {{
  background: {border_rgba};
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Paths & data init ----------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = DATA_DIR / "users.csv"

# Initialize or load users_df robustly
if DATA_PATH.exists():
    users_df = pd.read_csv(DATA_PATH, dtype={"actions": str})
    if "actions" not in users_df.columns:
        users_df["actions"] = ""
    users_df["actions"] = users_df["actions"].fillna("").astype(str)
    if "points" not in users_df.columns:
        users_df["points"] = 0
    users_df["points"] = pd.to_numeric(users_df["points"], errors="coerce").fillna(0).astype(int)
    if "vehicle_type" not in users_df.columns:
        users_df["vehicle_type"] = "Non-EV"
    if "username" not in users_df.columns:
        users_df["username"] = ""
else:
    # create with expected columns
    users_df = pd.DataFrame(columns=["username", "vehicle_type", "points", "actions"])
    users_df.to_csv(DATA_PATH, index=False)

# ---------------- UI: Sidebar - Configuration ----------------
with st.sidebar:
    # Brand / logo
    try:
        st.image("assets/logo.png", use_container_width=True)
    except Exception:
        st.markdown("## 🌿 EcoSense AI")
        st.markdown("<span class='small-muted'>Drive the EcoJourney</span>", unsafe_allow_html=True)

    st.markdown("<hr class='block-sep'/>", unsafe_allow_html=True)
    st.header("Settings")

    # Mode and user
    mode = st.radio("Mode", ["🚗 EV User", "🚙 Non-EV User"], horizontal=True)
    username = st.text_input("Your name (nickname)").strip()

    st.markdown("**Location (lat, lon) for renewable forecast**")
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.text_input("Latitude", value="19.07")
    with col_lon:
        lon = st.text_input("Longitude", value="72.87")

    # EV parameters
    if mode.startswith("🚗"):
        st.markdown("**EV parameters**")
        col_a, col_b = st.columns(2)
        with col_a:
            charger_power = st.number_input("Charger power (kW)", min_value=0.1, value=7.0, step=0.1)
            current_soc = st.number_input("Current SoC (%)", min_value=0, max_value=100, value=40, step=1)
        with col_b:
            battery_capacity = st.number_input("Battery capacity (kWh)", min_value=5.0, value=60.0, step=1.0)
            target_soc = st.number_input("Target SoC (%)", min_value=0, max_value=100, value=80, step=1)
    else:
        # defaults to keep code later safe
        charger_power = 7.0
        battery_capacity = 60.0
        current_soc = 40
        target_soc = 80

    st.markdown("**Departure (local)**")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dep_date = st.date_input("Departure date", value=(datetime.now() + timedelta(hours=12)).date())
    with col_d2:
        dep_time = st.time_input("Departure time", value=(datetime.now() + timedelta(hours=12)).time())
    # for simplicity treat entered departure as UTC (Open-Meteo returns UTC). In production you'd convert local->UTC properly.
    departure_time = datetime.combine(dep_date, dep_time).replace(tzinfo=timezone.utc)

    st.markdown("<hr class='block-sep'/>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn1:
        get_plan = st.button("📈 Charging Plan")
    with col_btn2:
        gen_report_btn = st.button("📄 Monthly Report")
    with col_btn3:
        tts_button = st.button("🔊 Quick Voice Tip")

    # Debug toggle
    show_debug = st.checkbox("Show debug panel", value=False)

# ---------------- Session State ----------------
if "points" not in st.session_state:
    st.session_state.points = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "user_loaded" not in st.session_state:
    st.session_state.user_loaded = None

# ---------------- Register or update user in CSV ----------------
def register_or_update_user(name: str, mode_str: str):
    global users_df
    if not name:
        return
    if name not in users_df["username"].values:
        new_row = {
            "username": name,
            "vehicle_type": ("EV" if mode_str.startswith("🚗") else "Non-EV"),
            "points": 0,
            "actions": ""
        }
        users_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
        users_df.to_csv(DATA_PATH, index=False)
    else:
        users_df.loc[users_df["username"] == name, "vehicle_type"] = ("EV" if mode_str.startswith("🚗") else "Non-EV")
        users_df.to_csv(DATA_PATH, index=False)

if username:
    register_or_update_user(username, mode)
    # load points into session
    if st.session_state.get("user_loaded") != username:
        pts_series = users_df.loc[users_df["username"] == username, "points"].values
        st.session_state.points = int(pts_series[0]) if len(pts_series) > 0 else 0
        st.session_state.history = [(datetime.now(), st.session_state.points)]
        st.session_state.user_loaded = username

# ---------------- Header ----------------
st.markdown(
    """
    <div class="eco-hero">
      <h1 class="eco-title">EcoSense AI</h1>
      <div class="eco-sub">Drive the EcoJourney — renewable-aware EV charging & eco coaching</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div class='block-sep'></div>", unsafe_allow_html=True)

# ---------------- Utilities: Open-Meteo fetch & scoring ----------------
@st.cache_data(show_spinner=False, ttl=60 * 15)
def fetch_open_meteo(lat_f: str, lon_f: str, hours: int = 72) -> pd.DataFrame:
    """
    Fetch hourly solar proxy and wind from Open-Meteo, return DataFrame indexed by UTC time.
    Uses 'shortwave_radiation' when available, falls back to 'solar_radiation'.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(lat_f),
        "longitude": float(lon_f),
        "hourly": "shortwave_radiation,wind_speed_10m,cloudcover",
        "forecast_days": 3,
        "timezone": "UTC"
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
        "cloud": hourly.get("cloudcover", [0] * len(times))
    }).set_index("time")
    return df.iloc[:hours].copy()

def compute_green_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Weighted green score using normalized solar (70%) and wind (30%), scaled by cloud factor.
    Returns same DataFrame with 'green_score' column (0..1).
    """
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
    """
    Brute-force sliding window to find contiguous hours_needed block with max average green_score.
    """
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

def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")

# ---------------- Main layout: left (core) & right (profile) ----------------
col_main, col_side = st.columns([2.2, 1])

with col_main:
    # ---------- EV optimizer ----------
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if mode.startswith("🚗"):
            st.subheader("⚡ Renewable-aware EV Charging Optimizer")
            st.caption("We compute a green score (solar + wind) and recommend the best charging window before your departure.")

            if get_plan:
                try:
                    df = fetch_open_meteo(lat, lon, hours=72)
                    df = compute_green_score(df)
                    st.success("Renewable forecast fetched.")

                    # Use Matplotlib (already in your requirements) with nicer style
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

                    needed_kwh = battery_capacity * max(0.0, (target_soc - current_soc) / 100.0)
                    hours_needed = max(1, math.ceil(needed_kwh / max(0.1, charger_power)))

                    df_before = df[df.index <= departure_time]
                    if df_before.empty:
                        st.warning("No forecast hours available before departure time.")
                    else:
                        best_start, best_avg = find_best_charging_window(df_before, hours_needed)
                        if best_start is not None:
                            best_end = best_start + timedelta(hours=hours_needed)
                            st.success(
                                f"Recommended charging window (UTC): "
                                f"**{fmt_dt(best_start)} → {fmt_dt(best_end)}** "
                                f"(avg green score {best_avg:.2f})"
                            )

                            # plot with highlight
                            plot_df = df_before.copy()
                            plot_df["recommended"] = 0
                            start_idx = plot_df.index.get_loc(best_start)
                            plot_df.iloc[start_idx:start_idx + hours_needed, plot_df.columns.get_loc("recommended")] = 1

                            fig, ax = plt.subplots(figsize=(9.5, 3.2))
                            ax.grid(True, linestyle="--", linewidth=0.6)
                            (line,) = ax.plot(plot_df.index, plot_df["green_score"], marker="o", linewidth=2.2, label="Green score")

                            # Highlight window
                            rec = plot_df[plot_df["recommended"] == 1]
                            ax.scatter(rec.index, rec["green_score"], s=90, label="Recommended")

                            ax.set_ylabel("Green Score (0-1)")
                            ax.set_xlabel("UTC time")
                            ax.set_title("Renewable Availability (solar + wind)")
                            ax.legend()
                            plt.xticks(rotation=25)
                            st.pyplot(fig, use_container_width=True)

                            # Nicer preview table
                            preview = plot_df.reset_index().rename(columns={"index": "time"})
                            cols_show = [c for c in ["time", "solar", "wind", "cloud", "green_score", "recommended"] if c in preview.columns]
                            st.dataframe(
                                preview[cols_show].head(24),
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.warning("Couldn't find a contiguous block matching the required charging duration.")
                except Exception as e:
                    st.error("Failed to fetch or process forecast: " + str(e))

            st.markdown(
                f"<span class='small-muted'>💡 Tip: If you have rooftop solar, daytime charging (11:00–15:00 local) is usually best. Wind peaks depend on location.</span>",
                unsafe_allow_html=True,
            )
        else:
            # ---------- Non-EV coach ----------
            st.subheader("🌱 Eco Driving Coach (Non-EV)")
            tips = [
                "Maintain steady speeds and avoid sharp acceleration.",
                "Check tyre pressure monthly to improve economy.",
                "Plan combined trips to reduce distance.",
                "Use public transport or carpool for the commute.",
                "Lighten your vehicle — remove unnecessary weight.",
            ]
            st.info(f"Tip: {tips[datetime.now().minute % len(tips)]}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Advanced "What-if" Simulator ----------
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔮 Lifestyle Simulator — 'What if I...' (Advanced)")
        st.caption("Try: 'bike 6 km 5 days/week', 'skip 1 flight 1200 km', 'install 3 kW solar', 'replace 8 bulbs with LED', 'wfh 2 days/week', 'raise AC by 2C'")

        # Scenario helpers and constants
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

            return "ℹ️ Couldn't parse precisely. Try examples: 'bike 6 km 5 days/week', 'skip 1 flight 1200 km', 'install 3 kW solar'."

        # Input & run simulator
        scenario_input = st.text_input("Describe your scenario", value="")
        if st.button("Simulate impact"):
            if scenario_input.strip():
                out = estimate_impact(scenario_input)
                st.success(out)
            else:
                st.info("Type something like: 'bike 6 km to work 5 days a week'.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Actions & Rewards ----------
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🌟 Eco Actions & Rewards (awareness-based)")

        actions_list = [
            ("Plan trips to reduce driving", 5),
            ("Use public transport / carpool", 10),
            ("Charge during green hours", 8),
            ("Drive smoothly (avoid harsh braking)", 5),
            ("Service vehicle for better efficiency", 6)
        ]

        act_cols = st.columns(3)
        for idx, (label, pts) in enumerate(actions_list):
            with act_cols[idx % 3]:
                if st.button(label):
                    if not username:
                        st.warning("Enter your name in the sidebar to record actions.")
                    else:
                        prev = str(users_df.loc[users_df["username"] == username, "actions"].values[0] or "")
                        new_actions = prev + f"\n- [{datetime.now().strftime('%Y-%m-%d')}] {label}"
                        users_df.loc[users_df["username"] == username, "actions"] = new_actions
                        users_df.loc[users_df["username"] == username, "points"] = int(
                            users_df.loc[users_df["username"] == username, "points"].values[0]
                        ) + pts
                        users_df.to_csv(DATA_PATH, index=False)
                        st.success(f"+{pts} Eco Points — {label}")
                        st.session_state.points = int(users_df.loc[users_df["username"] == username, "points"].values[0])
                        st.session_state.history.append((datetime.now(), st.session_state.points))
                        if st.session_state.points >= 100:
                            st.balloons()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Right column: profile, leaderboard, history, reports, TTS ----------------
with col_side:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🏆 Profile & Leaderboard")
        if username:
            st.markdown(f"**{username}** — {('EV' if mode.startswith('🚗') else 'Non-EV')}")
            st.metric("Eco Points", st.session_state.points)
        else:
            st.info("Enter your name to create profile & earn points.")

        lb = users_df.sort_values(by="points", ascending=False).reset_index(drop=True).head(8)
        if not lb.empty:
            st.dataframe(lb[["username", "vehicle_type", "points"]], use_container_width=True, hide_index=True)
        else:
            st.info("No users yet — be the first!")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Your Points History")
        if st.session_state.history:
            hist_df = pd.DataFrame(st.session_state.history, columns=["time", "points"]).set_index("time")
            st.line_chart(hist_df["points"])
        else:
            st.info("Perform actions to see history here.")
        st.markdown("</div>", unsafe_allow_html=True)

    # PDF report generation
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📄 Monthly PDF Report")
        if gen_report_btn:
            if not username:
                st.warning("Enter your name to generate report.")
            else:
                try:
                    buf = io.BytesIO()
                    c = canvas.Canvas(buf, pagesize=(595, 842))
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(40, 800, "EcoSense AI — Monthly Report")
                    c.setFont("Helvetica", 12)
                    c.drawString(40, 780, f"User: {username}")
                    row = users_df.loc[users_df["username"] == username].iloc[0]
                    c.drawString(40, 760, f"Vehicle: {row['vehicle_type']}")
                    c.drawString(40, 740, f"Eco Points: {int(row['points'])}")
                    c.drawString(40, 720, "Actions:")
                    y = 700
                    for line in str(row["actions"]).split("\n"):
                        if line.strip():
                            c.drawString(60, y, line.strip())
                            y -= 16
                            if y < 80:
                                c.showPage()
                                y = 800
                    c.showPage()
                    c.save()
                    buf.seek(0)
                    st.download_button(
                        "📥 Download Monthly Report (PDF)",
                        buf,
                        file_name=f"{username}_ecosense_report.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error("Failed to generate PDF: " + str(e))
        else:
            st.caption("Click the button in the sidebar to generate the report.")
        st.markdown("</div>", unsafe_allow_html=True)

    # gTTS quick voice tip
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔊 Quick Voice Tip")
        if tts_button:
            tip_text = "Charge your EV during the recommended window to maximize use of renewable energy and reduce carbon emissions."
            try:
                tts = gTTS(tip_text)
                tts.save("eco_tip.mp3")
                audio_bytes = open("eco_tip.mp3", "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error("TTS failed: " + str(e))
        else:
            st.caption("Use the sidebar button to play a short tip.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Footer / notes ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(
    "**Notes:** Green score is a simple normalized mix of solar radiation and wind speed from Open-Meteo (free). "
    "For higher accuracy integrate inverter or grid carbon intensity APIs (WattTime / ElectricityMap)."
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Extra: defensive sanity checks & debug panel ----------------
def _sanity_checks() -> List[str]:
    problems: List[str] = []
    try:
        if not users_df.empty and users_df["username"].duplicated().any():
            problems.append("Duplicate usernames in users.csv.")
        if "points" in users_df.columns:
            if not pd.api.types.is_integer_dtype(users_df["points"].dtype):
                # try to coerce
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
    # also dump a small debug summary
    st.sidebar.write("### Debug snapshot")
    st.sidebar.write(f"Loaded users: {len(users_df)}")
    st.sidebar.write(f"Session points: {st.session_state.points}")
    st.sidebar.write(f"Mode: {mode}")
    st.sidebar.write(f"Departure UTC: {departure_time.isoformat()}")

# End of file
