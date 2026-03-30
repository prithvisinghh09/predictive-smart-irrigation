import requests
import pandas as pd

# 1. Your Firebase Database URL (adding .json to get the raw data)
FIREBASE_URL = "https://irrigation-71320-default-rtdb.firebaseio.com/sensor_logs.json"

print("Fetching data from Firebase...")
response = requests.get(FIREBASE_URL)

if response.status_code == 200:
    data = response.json()
    
    if data:
        records = []
        # 2. Loop through the unique Firebase IDs and flatten the data
        for unique_id, entry in data.items():
            try:
                records.append({
                    "timestamp": entry["timestamp_ist"],
                    "temperature_c": entry["weather_data"]["temperature_celsius"],
                    "humidity_percent": entry["weather_data"]["humidity_percentage"],
                    "current_moisture": entry["soil_data"]["moisture_percentage"]
                })
            except KeyError as e:
                # Skips any incomplete rows if a sensor misfired
                print(f"Skipping incomplete entry {unique_id}")
        
        # 3. Convert to a Pandas DataFrame and save as CSV
        df = pd.DataFrame(records)
        df.to_csv("sensor_data.csv", index=False)
        print(f"Success! Saved {len(df)} records to sensor_data.csv")
    else:
        print("Database is empty. Wait for the ESP8266 to upload data!")
else:
    print(f"Failed to connect. HTTP Code: {response.status_code}")