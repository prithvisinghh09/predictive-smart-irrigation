import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import os

print("--- Initializing Predictive Model ---")

# 1. Check if the file exists
if not os.path.exists("sensor_data.csv"):
    print("Error: Could not find sensor_data.csv. Did you run the extraction script?")
    exit()

# 2. Load the data
df = pd.read_csv("sensor_data.csv")
df = df.sort_values(by="timestamp").reset_index(drop=True)

total_rows = len(df)
print(f"Dataset loaded. Total readings found: {total_rows}")

# 3. Define our prediction window (4 steps of 15 mins = 1 hour ahead)
STEPS_AHEAD = 4 

# 4. The Safety Check!
# We need enough rows to shift the data, PLUS enough rows to split into training/testing.
# Let's require an absolute minimum of 15 readings (about 4 hours of data) to do a basic test.
MINIMUM_REQUIRED_ROWS = 15

if total_rows < MINIMUM_REQUIRED_ROWS:
    print("\n⚠️ MODEL TRAINING PAUSED ⚠️")
    print(f"You only have {total_rows} readings. Machine learning needs more historical data to find patterns.")
    print(f"Let your ESP8266 run for at least {MINIMUM_REQUIRED_ROWS - total_rows} more cycles (about {(MINIMUM_REQUIRED_ROWS - total_rows) * 15} minutes).")
    print("Go grab a coffee, let the sensor gather some history, and run this script again later!")
    exit()

print("\nEnough data found! Proceeding with training...")

# 5. Data Shifting (Creating the "Future" Target)
df["future_moisture"] = df["current_moisture"].shift(-STEPS_AHEAD)

# Drop the last few rows because they don't have a "future" yet
df = df.dropna()

# 6. Define Features (X) and Target (y)
X = df[["temperature_c", "humidity_percent", "current_moisture"]]
y = df["future_moisture"]

# 7. Split data: 80% for training, 20% for testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Random Forest...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 8. Test the accuracy
predictions = model.predict(X_test)
error = mean_absolute_error(y_test, predictions)

print("\n--- Training Complete ---")
print(f"Model Accuracy Error: +/- {error:.2f}% moisture")

# --- SIMULATE A LIVE PREDICTION ---
print("\n--- Live Prediction Simulation ---")
# Using the most recent row in your database as the "live" data
latest_temp = df.iloc[-1]["temperature_c"]
latest_hum = df.iloc[-1]["humidity_percent"]
latest_moist = df.iloc[-1]["current_moisture"]

predicted_future = model.predict([[latest_temp, latest_hum, latest_moist]])
print(f"Right now: {latest_temp}°C, {latest_hum}% Hum, {latest_moist}% Moisture")
print(f"PREDICTED moisture in 1 hour: {predicted_future[0]:.1f}%")

if predicted_future[0] < 50.0:
    print("ACTION: Future state is critical. The plants will need water soon.")
else:
    print("ACTION: Soil will remain stable. No watering needed.")
    print("\n--- Pushing Prediction to Firebase ---")
# We create a specific 'folder' just for the AI prediction
firebase_predict_url = "https://irrigation-71320-default-rtdb.firebaseio.com/latest_prediction.json"

# Package the AI's thought process into a neat payload
payload = {
    "predicted_moisture": round(predicted_future[0], 1),
    "action_required": "Yes - Water Soon" if predicted_future[0] < 50.0 else "No - Stable"
}

# We use requests.put() to overwrite the old prediction with this brand new one
try:
    response = requests.put(firebase_predict_url, json=payload)
    if response.status_code == 200:
        print("[SUCCESS] The AI prediction is now live on the database.")
    else:
        print(f"[FAILED] to upload to Firebase. HTTP Code: {response.status_code}")
        print("Response:", response.text)
except Exception as e:
    print(f"[NETWORK ERROR]: {e}")