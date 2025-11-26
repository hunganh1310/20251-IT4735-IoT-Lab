#!/usr/bin/env python3
import os
import json
import pika
import csv

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"


EXCHANGE_NAME = "logs"
OUTPUT_FILE = "logs.csv"

def ensure_header(file_path):
    # Nếu file chưa tồn tại hoặc rỗng, ghi header
    try:
        need_header = True
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            need_header = False
    except Exception:
        need_header = True

    if need_header:
        with open(file_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "temperature", "humidity"])

def main():
    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    ensure_header(OUTPUT_FILE)

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode())
            ts = data.get("timestamp")
            temp = data.get("temperature")
            hum = data.get("humidity")
            with open(OUTPUT_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([ts, temp, hum])
            print(f"Ghi vào file: {ts}, {temp}, {hum}")
        except Exception as e:
            print("Lỗi khi xử lý/ghi file:", e)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\nConsumer2 thoát.")
    finally:
        try:
            connection.close()
        except Exception:
            pass

if __name__ == "__main__":
    import os
    main()
