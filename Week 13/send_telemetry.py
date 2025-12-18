import requests
import json
import random
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

THINGSBOARD_BASE_URL = "http://demo.thingsboard.io/api/v1"

MSSV = "20225164"

def load_access_token():
    try:
        with open("access_token.txt", "r") as f:
            token = f.read().strip()
            if token:
                return token
            else:
                print("Error: access_token.txt is empty")
                return None
    except FileNotFoundError:
        return None

def generate_sensor_data():
    temperature = round(random.uniform(20.0, 35.0), 2)  # Temperature: 20-35°C
    humidity = round(random.uniform(40.0, 80.0), 2)     # Humidity: 40-80%
    return temperature, humidity

def send_telemetry(access_token, temperature, humidity, mssv): 
    # Construct the telemetry endpoint URL
    telemetry_url = f"{THINGSBOARD_BASE_URL}/{access_token}/telemetry"
    
    # Prepare telemetry data payload
    payload = {
        "temperature": temperature,
        "humidity": humidity,
        "mssv": mssv
    }
    
    print("Sending Telemetry Data to ThingsBoard")
    print(f"Endpoint: {telemetry_url}")
    print(f"\nTelemetry Data:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            telemetry_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Check response status
        if response.status_code == 200:
            print("SUCCESS - Data sent successfully!")
            return True
            
        elif response.status_code == 401:
            print("AUTHENTICATION ERROR (HTTP 401)")
            print("The ACCESS_TOKEN is invalid or expired.")
            return False
            
        else:
            print(f"ERROR - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\nError: Request timeout. Please check your internet connection.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nError: Request failed - {e}")
        return False

def send_multiple_telemetry(access_token, count=5, interval=2):
    success_count = 0
    for i in range(count):
        
        # Generate random sensor data
        temperature, humidity = generate_sensor_data()
        
        # Send telemetry
        if send_telemetry(access_token, temperature, humidity, MSSV):
            success_count += 1
        
        # Wait before sending next data point (except for the last one)
        if i < count - 1:
            time.sleep(interval)

def main():
    # Load access token
    access_token = load_access_token()
    if not access_token:
        return
    
    send_multiple_telemetry(access_token, count=5, interval=2)

if __name__ == "__main__":
    main()
