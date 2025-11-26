#!/usr/bin/env python3
import os
import json
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"

EXCHANGE_NAME = "logs"

def main():
    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

    # Tạo queue tạm (exclusive) với tên do server sinh
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # Bind queue tới exchange fanout
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)


    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode())
            ts = data.get("timestamp")
            temp = data.get("temperature")
            hum = data.get("humidity")
            print(f"Received -> timestamp: {ts}, temperature: {temp}, humidity: {hum}")
        except Exception as e:
            print("Lỗi khi xử lý message:", e)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\nConsumer1 thoát.")
    finally:
        try:
            connection.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
