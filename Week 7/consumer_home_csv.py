#!/usr/bin/env python3
import os
import json
import csv
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"
if not CLOUDAMQP_URL:
    raise RuntimeError("Invalid Broker URL")

EXCHANGE = "sensors_topic"
OUTPUT_FILE = "home_logs.csv"

def ensure_header(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "location", "temperature", "humidity"])

def main():
    params = pika.URLParameters(CLOUDAMQP_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    # khai báo queue tạm (exclusive) để chỉ consumer này nhận; có thể đổi thành queue named để tồn tại lâu dài
    q = ch.queue_declare(queue='', exclusive=True)
    queue_name = q.method.queue

    # Bind để nhận tất cả routing key bắt đầu bằng 'home.'
    ch.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="home.*")

    ensure_header(OUTPUT_FILE)

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode())
            ts = data.get("timestamp", "")
            loc = data.get("location", "")
            temp = data.get("temperature", "")
            hum = data.get("humidity", "")
            with open(OUTPUT_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([ts, loc, temp, hum])
            print(f"Wrote to CSV: {ts},{loc},{temp},{hum}")
        except Exception as e:
            print("Error processing message:", e)

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        print("\nConsumer1 stopped.")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
