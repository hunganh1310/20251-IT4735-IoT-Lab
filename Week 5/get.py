import requests
import json
import numpy as np

URL = "https://api.thingspeak.com/channels/3100276/feeds.json?results=10"

try:
    response = requests.get(URL)
    
    if response.status_code == 200:
        data = response.json()
        
        feeds = data.get("feeds", [])
    
        field1_values = []
        field2_values = []
        
        for entry in feeds:
            try:
                if entry.get("field1") is not None:
                    field1_values.append(float(entry["field1"]))
                if entry.get("field2") is not None:
                    field2_values.append(float(entry["field2"]))
            except (ValueError, TypeError):
                continue
                
        if field1_values and field2_values:
            # Tính toán giá trị trung bình
            avg_field1 = np.mean(field1_values)
            avg_field2 = np.mean(field2_values)
            
            # Tính toán độ lệch chuẩn
            std_field1 = np.std(field1_values)
            std_field2 = np.std(field2_values)
            
            # Hiển thị kết quả
            print("Phân tích dữ liệu từ ThingSpeak:")
            print("---------------------------------")
            print(f"Tổng số bản ghi: {len(feeds)}")
            
            print("\nKết quả cho trường field1 (Nhiệt độ):")
            print(f"   Giá trị trung bình: {avg_field1:.2f}")
            print(f"   Độ lệch chuẩn: {std_field1:.2f}")
            
            print("\nKết quả cho trường field2 (Độ ẩm):")
            print(f"   Giá trị trung bình: {avg_field2:.2f}")
            print(f"   Độ lệch chuẩn: {std_field2:.2f}")
        else:
            print("Không có dữ liệu hợp lệ để phân tích từ ThingSpeak.")
            
    else:
        print(f"Gửi yêu cầu thất bại. Mã lỗi: {response.status_code}")
        print(f"Chi tiết lỗi: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Có lỗi xảy ra khi kết nối: {e}")