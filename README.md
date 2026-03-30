# Predictive Smart irrigation IoT Node 🌱

An end-to-end Internet of Things (IoT) and Machine Learning pipeline designed to monitor soil conditions and predict future watering needs using environmental data. 

## System Architecture
This project implements a full edge-to-cloud data pipeline:
* **Edge Device:** An ESP8266 microcontroller collects live soil moisture, temperature, and humidity data.
* **Cloud Database:** Firebase Realtime Database acts as the central hub, logging sensor telemetry every 15 minutes.
* **Machine Learning Engine:** A Python backend running on a cloud server continuously fetches historical data and trains a `RandomForestRegressor` model to predict the soil moisture 6 hours into the future.
* **Frontend Dashboard:** A responsive HTML/JS dashboard visualizes the live data using Chart.js and displays the AI's predictive forecast and recommended actions.

## Tech Stack
* **Hardware:** ESP8266 NodeMCU, Capacitive Soil Moisture Sensor
* **Backend & ML:** Python, Pandas, Scikit-Learn (Random Forest)
* **Cloud Infrastructure:** Firebase Realtime Database, PythonAnywhere
* **Frontend:** HTML5, CSS3, JavaScript, Chart.js

## How it Works
1. The ESP8266 pushes telemetry to Firebase.
2. The `cloud_ai.py` script wakes up hourly, extracts the dataset, and aligns current weather variables with future moisture states (shifted by 24 intervals).
3. The model outputs a 1-hour forecast and pushes the prediction back to a dedicated Firebase node.
4. The web dashboard listens for state changes and updates the UI in real-time.
