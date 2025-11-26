#!/usr/bin/env python3
import os
import json
import time
import random
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"
if not CLOUDAMQP_URL:
    raise RuntimeError("Invalid Broker URL")

EXCHANGE = "sensors_topic"  # topic exchange

LOCATIONS = ["home", "office"]
TYPES = ["temperature", "humidity"]

def make_message(location, mtype):
    ts = int(time.time())
    if mtype == "temperature":
        value = round(random.uniform(18.0, 35.0), 1)
        payload = {"timestamp": ts, "location": location, "temperature": value}
    else:
        value = round(random.uniform(30.0, 90.0), 1)
        payload = {"timestamp": ts, "location": location, "humidity": value}
    return payload

def main(interval=1.0):
    params = pika.URLParameters(CLOUDAMQP_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    try:
        while True:
            location = random.choice(LOCATIONS)
            mtype = random.choice(TYPES)
            routing_key = f"{location}.{mtype}"
            msg = make_message(location, mtype)
            body = json.dumps(msg)
            ch.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(content_type='application/json', delivery_mode=1)
            )
            print(f"Published ({routing_key}): {body}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nProducer stopped.")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
