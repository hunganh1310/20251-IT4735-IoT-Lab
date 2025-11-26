#!/usr/bin/env python3
import json
import time
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"
if not CLOUDAMQP_URL:
    raise RuntimeError("Invalid Broker URL")

EXCHANGE = "sensors_topic"

# lưu tổng và số lượng theo location để tính trung bình
sums = {}
counts = {}

def print_averages():
    if not counts:
        print("Chưa có dữ liệu temperature nào.")
        return
    print("=== Current temperature averages ===")
    for loc, cnt in counts.items():
        avg = sums[loc] / cnt if cnt else 0.0
        print(f" - {loc}: avg = {avg:.2f} (n={cnt})")

def main():
    params = pika.URLParameters(CLOUDAMQP_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    q = ch.queue_declare(queue='', exclusive=True)
    queue_name = q.method.queue

    # bind tất cả temperature messages từ mọi địa điểm
    ch.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="*.temperature")


    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode())
            loc = data.get("location")
            temp = data.get("temperature")
            ts = data.get("timestamp", "")
            if loc is None or temp is None:
                print("Bỏ message thiếu trường location/temperature:", data)
                return
            sums.setdefault(loc, 0.0)
            counts.setdefault(loc, 0)
            sums[loc] += float(temp)
            counts[loc] += 1
            print(f"Received temperature from {loc} @ {ts}: {temp}")
            print_averages()
        except Exception as e:
            print("Error processing message:", e)

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        print("\nConsumer2 stopped.")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
