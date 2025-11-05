import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib

# ------------------ Paths ------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = DATA_DIR / "users.csv"

# ------------------ Utilities ------------------
def hash_password(password: str) -> str:
    """Return SHA256 hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> pd.DataFrame:
    """Load users CSV or return empty DataFrame."""
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, dtype={"actions": str})
    else:
        df = pd.DataFrame(columns=[
            "username", "password", "email", "vehicle_type",
            "points", "actions", "created_at"
        ])
    # Type cleaning
    df["points"] = pd.to_numeric(df.get("points", 0), errors="coerce").fillna(0).astype(int)
    df["actions"] = df.get("actions", "").fillna("")
    for col in ["username", "password", "email", "vehicle_type", "created_at"]:
        if col not in df.columns:
            df[col] = ""
    return df

def save_users(df: pd.DataFrame) -> None:
    """Save users DataFrame back to CSV."""
    df.to_csv(DATA_PATH, index=False)

# ------------------ Auth ------------------
def authenticate_user(username: str, password: str) -> bool:
    """Check username & password against CSV."""
    df = load_users()
    row = df[df["username"] == username]
    if row.empty:
        return False
    return row.iloc[0]["password"] == hash_password(password)

def create_user(username: str, password: str, email: str = "", vehicle_type: str = "") -> str:
    """Add a new user if not exists."""
    df = load_users()
    if username in df["username"].values:
        return "❌ Username already exists!"
    if len(username) < 3 or len(password) < 3:
        return "❌ Username & password must be at least 3 characters"

    new_user = {
        "username": username,
        "password": hash_password(password),
        "email": email,
        "vehicle_type": vehicle_type,
        "points": 0,
        "actions": "",
        "created_at": datetime.utcnow().isoformat()
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    save_users(df)
    return "✅ Signup successful! You can now login."

# ------------------ Points / Rewards ------------------
def add_action_points(username: str, action: str, pts: int) -> None:
    """Add eco-action with points to user history."""
    df = load_users()
    idx = df.index[df["username"] == username]
    if len(idx) == 0:
        return
    i = idx[0]
    df.at[i, "points"] = int(df.at[i, "points"]) + pts
    actions = str(df.at[i, "actions"])
    new_entry = f"{datetime.utcnow().isoformat()}::{action}::{pts}"
    df.at[i, "actions"] = actions + "|" + new_entry if actions else new_entry
    save_users(df)
