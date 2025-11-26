#!/usr/bin/env python3
"""
mqtt_logger.py

Subscriber that:
- Subscribes to sensors/+/status and sensors/+/data (QoS 2).
- Khi nhận status "online" -> mở file log log_<client_id>.csv
- Khi nhận data -> ghi 1 dòng: receive_time_iso, send_timestamp, temperature, humidity
- Khi nhận status "offline" (hoặc LWT offline) -> đóng file log
"""
import os
import json
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_STATUS = "sensors/+/status"
TOPIC_DATA = "sensors/+/data"

# Map client_id -> open file handle (and file path)
open_files = {}

def open_log_for_client(client_id):
    if client_id in open_files:
        return open_files[client_id]["file"]
    fname = f"log_{client_id}.csv"
    is_new = not os.path.exists(fname)
    f = open(fname, "a", buffering=1, encoding="utf-8")  # line-buffered
    if is_new:
        f.write("receive_time_iso,send_timestamp,temperature,humidity\n")
    open_files[client_id] = {"file": f, "path": fname}
    print(f"[logger] Opened log file {fname} for client {client_id}")
    return f

def close_log_for_client(client_id):
    info = open_files.pop(client_id, None)
    if info:
        try:
            info["file"].close()
            print(f"[logger] Closed log file {info['path']} for client {client_id}")
        except Exception as e:
            print(f"[logger] Error closing file for {client_id}: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[logger] Connected to broker {BROKER}:{PORT}")
        # Subscribe to status and data for all clients
        client.subscribe([(TOPIC_STATUS, 2), (TOPIC_DATA, 2)])
    else:
        print(f"[logger] Failed to connect, rc={rc}")

def parse_client_id_from_topic(topic):
    # topic pattern: sensors/<client_id>/status  OR sensors/<client_id>/data
    parts = topic.split('/')
    if len(parts) >= 3:
        return parts[1]
    return None

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8', errors='ignore')
    client_id = parse_client_id_from_topic(topic)
    if not client_id:
        print(f"[logger] Could not parse client_id from topic {topic}")
        return

    if topic.endswith("/status"):
        # status message expected to be JSON {"client_id": "...", "status": "online"|"offline", ...}
        try:
            data = json.loads(payload)
            status = data.get("status", "").lower()
        except Exception:
            # If not JSON, fallback to raw string
            status = payload.strip().lower()
        print(f"[logger] Status from {client_id}: {status} (raw: {payload})")

        if status == "online":
            open_log_for_client(client_id)
        elif status == "offline" or status == "unexpected_disconnect":
            # offline or LWT offline
            close_log_for_client(client_id)
        else:
            # other statuses ignored for now
            pass

    elif topic.endswith("/data"):
        # data payload expected JSON: {"client_id":"...", "timestamp": <int>, "temperature":.., "humidity":..}
        try:
            data = json.loads(payload)
            send_ts = data.get("timestamp", "")
            temp = data.get("temperature", "")
            hum = data.get("humidity", "")
        except Exception as e:
            print(f"[logger] Failed to parse data JSON from {client_id}: {e} -- payload: {payload}")
            return

        # Ensure log file open
        if client_id not in open_files:
            # The requirement: open file on receiving online. But to be robust, open even if missed online msg.
            print(f"[logger] Warning: no open file for {client_id} when data arrived; opening file automatically.")
            f = open_log_for_client(client_id)
        else:
            f = open_files[client_id]["file"]

        receive_time = datetime.utcnow().isoformat() + "Z"
        line = f'{receive_time},{send_ts},{temp},{hum}\n'
        try:
            f.write(line)
            # May flush depending on buffering mode; using line-buffered.
            print(f"[logger] Wrote data for {client_id}: {line.strip()}")
        except Exception as e:
            print(f"[logger] Error writing to file for {client_id}: {e}")

def on_disconnect(client, userdata, rc):
    print(f"[logger] Disconnected from broker (rc={rc}). Closing all open files.")
    # Close all files gracefully
    for cid in list(open_files.keys()):
        close_log_for_client(cid)

def main():
    client = mqtt_client.Client(client_id="logger_" + str(int(time.time())), clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
