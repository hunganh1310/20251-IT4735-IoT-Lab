import requests
import json

# URL API của ThingSpeak
url = "https://api.thingspeak.com/update?api_key=PDK7V4MC6UFSLZIT"

# Dữ liệu cần gửi (body dạng JSON)
payload = {
    "field1": 20,          # Nhiệt độ
    "field2": 33,          # Độ ẩm
    "field3": 20225164     # Mã số sinh viên
}

# Header khai báo kiểu dữ liệu JSON
headers = {
    "Content-Type": "application/json"
}
# Gửi yêu cầu POST
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Kiểm tra phản hồi từ server
if response.status_code == 200:
    print("✅ Gửi dữ liệu thành công!")
    print("ID bản ghi trên server:", response.text)
else:
    print("❌ Lỗi khi gửi dữ liệu:", response.status_code, response.text)
