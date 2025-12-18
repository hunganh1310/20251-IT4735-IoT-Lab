import os
import json
import random
import time
from dotenv import load_dotenv
from paho.mqtt.client import Client, CallbackAPIVersion

# Load environment variables from .env file
load_dotenv()

# ThingsBoard MQTT broker configuration
THINGSBOARD_HOST = "demo.thingsboard.io"
THINGSBOARD_PORT = 1883

# MQTT topic for telemetry
TELEMETRY_TOPIC = "v1/devices/me/telemetry"

# Student ID from environment variables
MSSV = "20225164"

# Result codes for MQTT connection
RESULT_CODES = {
    0: "Connection successful",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorised",
}


def load_access_token():
    try:
        with open("credentials", "r") as f:
            token = f.read().strip()
            if token:
                return token
            else:
                print("Error: credentials file is empty")
                return None
    except FileNotFoundError:
        return None


def generate_sensor_data():
    temperature = round(random.uniform(20.0, 35.0), 2)  # Temperature: 20-35°C
    humidity = round(random.uniform(40.0, 80.0), 2)     # Humidity: 40-80%
    return temperature, humidity


class TelemetryClient:
    
    def __init__(self, host, port, access_token):
        self.host = host
        self.port = port
        self.access_token = access_token
        self.connected = False
        
        # Create MQTT client with callback API version 2
        self.client = Client(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Set username to access token as required by ThingsBoard
        self.client.username_pw_set(access_token)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
        else:
            self.connected = False
            print(f"Connection failed: {RESULT_CODES.get(reason_code, 'Unknown error')}")
    
    def on_publish(self, client, userdata, mid, reason_code, properties):
        pass
    
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.connected = False
        if reason_code != 0:
            print(f"Unexpected disconnection (code: {reason_code})")
    
    def connect(self):
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection to establish
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            return self.connected
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def send_telemetry(self, temperature, humidity, mssv):
        if not self.connected:
            print("Not connected")
            return False
        
        # Prepare telemetry data payload
        payload = {
            "temperature": temperature,
            "humidity": humidity,
            "mssv": mssv
        }
        
        print(f"Sending: temp={temperature}, humidity={humidity}, mssv={mssv}")
        
        # Publish to telemetry topic
        result = self.client.publish(TELEMETRY_TOPIC, json.dumps(payload))
        
        if result.rc == 0:
            return True
        else:
            print(f"Failed (code: {result.rc})")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()


def send_single_telemetry(client):
    temperature, humidity = generate_sensor_data()
    
    if client.send_telemetry(temperature, humidity, MSSV):
        print("✓ Sent successfully")
        return True
    else:
        print("✗ Failed")
        return False


def send_multiple_telemetry(client, count=5, interval=2):
    print(f"Sending {count} data points with {interval}s interval\n")
    
    success_count = 0
    for i in range(count):
        print(f"[{i+1}/{count}] ", end="")
        
        temperature, humidity = generate_sensor_data()
        
        if client.send_telemetry(temperature, humidity, MSSV):
            success_count += 1
        
        # Wait before sending next data point (except for the last one)
        if i < count - 1:
            time.sleep(interval)
    
    # Summary
    print(f"\nSummary: {success_count}/{count} successful")


def main():
    # Load access token
    access_token = load_access_token()
    if not access_token:
        return
    
    print(f"MSSV: {MSSV}\n")
    
    # Create telemetry client
    client = TelemetryClient(THINGSBOARD_HOST, THINGSBOARD_PORT, access_token)
    
    # Connect to broker
    if not client.connect():
        print("Failed to connect")
        return
    
    try:
        send_multiple_telemetry(client, count=5, interval=2)
    
    finally:
        time.sleep(1)
        client.disconnect()


if __name__ == "__main__":
    main()
