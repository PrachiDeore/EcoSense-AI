# EcoSense-AI
🌿 EcoSense AI

EcoSense AI is an interactive Streamlit app designed to guide users toward eco-friendly behavior through renewable-aware EV charging, lifestyle impact simulations, and reward-based sustainability coaching.

🚀 Features

⚡ EV Charging Optimizer
Recommends the best time to charge based on solar and wind forecasts from Open-Meteo.

🔮 Lifestyle Impact Simulator
Natural-language inputs like “bike 6 km 5 days/week” estimate CO₂ savings instantly.

📊 Awareness-Based Rewards
Users earn eco-points for sustainable actions, stored in a local CSV.

📄 Monthly Report Generator
Generates downloadable PDF reports summarizing a user's progress.

🔊 TTS Voice Tips
Uses Google Text-to-Speech for fast eco-coaching reminders.

📁 Folder Structure
Ecosense_AI/
│
├── app.py                  # Main Streamlit application
├── assets/
│   └── logo.png            # Optional logo for sidebar branding
├── data/
│   └── users.csv           # Auto-generated user data (points, actions)
├── requirements.txt        # Required Python dependencies

🛠️ Installation

Make sure Python ≥ 3.8 is installed. Then:

git clone <repo-url>
cd Ecosense_AI
pip install -r requirements.txt
streamlit run app.py

✅ Requirements

The app depends on:

streamlit

pandas

matplotlib

requests

gtts

reportlab

These are included in the requirements.txt.

🔧 How It Works

Charging Optimizer:
Uses Open-Meteo API to fetch 3-day hourly forecasts for solar radiation, wind speed, and cloud cover. A weighted green score helps identify the cleanest hours to charge your EV before departure.

What-If Simulator:
Parses natural language for transport, diet, electricity, and habits to estimate CO₂ reduction using approximations and emission factors.

Rewards & Points:
Points are awarded for eco-friendly behaviors logged by the user. Actions are stored in data/users.csv.

PDF Reports:
Monthly summaries are created using reportlab with user name, EV type, points, and action history.

📌 Notes

Solar + wind forecast data is normalized and approximate. For more precision, consider integrating APIs like:

WattTime API

ElectricityMap API

All times are treated as UTC (due to Open-Meteo's API); convert to local time as needed in production.

👨‍💻 Future Work

Integration with live grid carbon intensity APIs

Advanced user authentication and cloud-based storage

Enhanced gamification (badges, levels)

Mobile app version or PWA wrapper

Localization and multi-language support

Leaderboard with global rankings
