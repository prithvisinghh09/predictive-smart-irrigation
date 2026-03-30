import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import time
import datetime

# --- CONFIGURATION ---
FIREBASE_URL = "https://irrigation-71320-default-rtdb.firebaseio.com/sensor_logs.json"
PREDICT_URL = "https://irrigation-71320-default-rtdb.firebaseio.com/latest_prediction.json"

def run_prediction_cycle():
    print(f"\n--- Starting AI Cycle: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 1. EXTRACT: Fetch the latest data directly from the cloud
    response = requests.get(FIREBASE_URL)
    if response.status_code != 200 or not response.json():
        print("Failed to fetch data or database is empty.")
        return

    data = response.json()
    records = []
    for unique_id, entry in data.items():
        try:
            records.append({
                "temperature_c": entry["weather_data"]["temperature_celsius"],
                "humidity_percent": entry["weather_data"]["humidity_percentage"],
                "current_moisture": entry["soil_data"]["moisture_percentage"]
            })
        except KeyError:
            pass # Skip malformed rows

    df = pd.DataFrame(records)
    
    if len(df) < 15:
        print(f"Not enough data yet. Need 15 rows, currently have {len(df)}.")
        return

    # 2. TRAIN: Shift data and build the Random Forest
    STEPS_AHEAD = 4 # 1 Hour ahead
    df["future_moisture"] = df["current_moisture"].shift(-STEPS_AHEAD)
    df = df.dropna()

    X = df[["temperature_c", "humidity_percent", "current_moisture"]]
    y = df["future_moisture"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 3. PREDICT: Guess the future based on the most recent row
    latest_temp = df.iloc[-1]["temperature_c"]
    latest_hum = df.iloc[-1]["humidity_percent"]
    latest_moist = df.iloc[-1]["current_moisture"]

    prediction_input = pd.DataFrame([[latest_temp, latest_hum, latest_moist]], columns=["temperature_c", "humidity_percent", "current_moisture"])
    predicted_future = model.predict(prediction_input)
    final_prediction = round(predicted_future[0], 1)

    # 4. PUSH: Send the verdict back to the dashboard
    action_text = "Yes - Water Soon" if final_prediction < 50.0 else "No - Stable"
    payload = {"predicted_moisture": final_prediction, "action_required": action_text}

    put_response = requests.put(PREDICT_URL, json=payload)
    if put_response.status_code == 200:
        print(f"[SUCCESS] Predicted {final_prediction}%. Uploaded to Dashboard.")
    else:
        print(f"[FAILED] Could not upload. HTTP Code: {put_response.status_code}")

# --- THE CONTINUOUS LOOP ---
# This keeps the cloud server running 24/7
while True:
    try:
        run_prediction_cycle()
    except Exception as e:
        print(f"[ERROR] Cycle failed: {e}")
    
    print("Sleeping for 60 minutes...")
    time.sleep(3600) # Pauses the script for 3600 seconds (1 hour)