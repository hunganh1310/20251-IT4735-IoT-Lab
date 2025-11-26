#!/usr/bin/env python3
"""
mqtt_publisher.py

Usage:
    python mqtt_publisher.py --id clientA
    python mqtt_publisher.py --id clientB --broker test.mosquitto.org --port 1883

Behavior:
- Thiết lập LWT (retain, QoS=2) báo offline.
- Sau khi connect, publish "online" (retain, QoS=2).
- Gửi JSON data mỗi 1s (temperature, humidity, timestamp) trong 60s.
- Sau 60s publish "offline" (retain, QoS=2) và disconnect.
"""
import argparse
import json
import time
import random
import sys
from paho.mqtt import client as mqtt_client

def gen_sensor_data(client_id):
    """Return sensor dict: temperature, humidity, timestamp, client_id"""
    temp = round(random.uniform(20.0, 30.0), 2)
    hum = round(random.uniform(30.0, 80.0), 2)
    ts = int(time.time())
    return {"client_id": client_id, "timestamp": ts, "temperature": temp, "humidity": hum}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", "-i", required=True, help="Client ID to use")
    parser.add_argument("--broker", default="test.mosquitto.org", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between sensor publishes")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds to publish sensor data")
    args = parser.parse_args()

    client_id = args.id
    broker = args.broker
    port = args.port
    topic_status = f"sensors/{client_id}/status"
    topic_data = f"sensors/{client_id}/data"

    client = mqtt_client.Client(client_id=client_id, clean_session=True)

    # LWT: offline message, retained, QoS 2
    lwt_payload = json.dumps({"client_id": client_id, "status": "offline", "reason": "unexpected_disconnect"})
    client.will_set(topic_status, payload=lwt_payload, qos=2, retain=True)

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            print(f"[{client_id}] Connected to broker {broker}:{port}")
            # Publish online (retained, QoS 2)
            online_payload = json.dumps({"client_id": client_id, "status": "online"})
            c.publish(topic_status, payload=online_payload, qos=2, retain=True)
        else:
            print(f"[{client_id}] Failed to connect, return code {rc}")
            sys.exit(1)

    client.on_connect = on_connect

    # Start loop
    client.connect(broker, port, keepalive=60)
    client.loop_start()

    start = time.time()
    try:
        elapsed = 0
        while elapsed < args.duration:
            data = gen_sensor_data(client_id)
            payload = json.dumps(data)
            # Publish data with QoS 2, non-retained
            result = client.publish(topic_data, payload=payload, qos=2, retain=False)
            # Optionally check mid/rc
            rc = result.rc
            if rc != 0:
                print(f"[{client_id}] Publish returned rc={rc}")
            print(f"[{client_id}] Sent data: {payload}")
            time.sleep(args.interval)
            elapsed = time.time() - start
    except KeyboardInterrupt:
        print(f"[{client_id}] Interrupted by user.")
    finally:
        # Publish offline retained message QoS 2
        offline_payload = json.dumps({"client_id": client_id, "status": "offline"})
        client.publish(topic_status, payload=offline_payload, qos=2, retain=True)
        time.sleep(0.5)  # give broker time to receive retained message
        client.loop_stop()
        client.disconnect()
        print(f"[{client_id}] Disconnected, offline message sent.")

if __name__ == "__main__":
    main()
