#!/usr/bin/env python3
import os
import json
import time
import random
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"
if not CLOUDAMQP_URL:
    raise RuntimeError("Invalid Broker URL")

EXCHANGE_NAME = "logs"  # fanout exchange

def random_log():
    ts = int(time.time())
    temp = round(random.uniform(18.0, 35.0), 1)
    hum = round(random.uniform(30.0, 90.0), 1)
    return {"timestamp": ts, "temperature": temp, "humidity": hum}

def main(publish_interval=1.0):
    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Tạo exchange fanout
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

    try:
        while True:
            log = random_log()
            body = json.dumps(log)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=body)
            print(f"Published: {body}")
            time.sleep(publish_interval)
    except KeyboardInterrupt:
        print("\nProducer thoát.")
    finally:
        try:
            connection.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
