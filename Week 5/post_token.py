import requests
import json
import os


LOGIN_URL = "https://iot-api.deno.dev/login"

email = "hunganh1310.work@gmail.com"
mssv = "202325164"

# Dữ liệu đăng nhập dưới dạng dictionary
login_data = {
    "email": email,
    "mssv": mssv
}

# Tên tệp tin để lưu token
TOKEN_FILE = "token.txt"

def get_and_save_token():
    """
    Gửi yêu cầu POST để lấy token và lưu vào tệp tin.
    """
    print("Đang đăng nhập để lấy token...")
    try:
        # Gửi yêu cầu POST với body là JSON
        response = requests.post(LOGIN_URL, json=login_data)
        
        # Kiểm tra trạng thái phản hồi
        if response.status_code == 200:
            # Phân tích cú pháp JSON để lấy token
            response_data = response.json()
            token = response_data.get("token")
            
            if token:
                # Lưu token vào tệp tin
                with open(TOKEN_FILE, "w") as f:
                    f.write(token)
                print(f"✅ Đăng nhập thành công! Token đã được lưu vào tệp tin: {TOKEN_FILE}")
                print(f"Token: {token}")
            else:
                print("❌ Lỗi: Không tìm thấy 'token' trong phản hồi JSON.")
                print(f"Phản hồi server: {response.text}")
        else:
            print(f"❌ Đăng nhập thất bại. Mã lỗi: {response.status_code}")
            print(f"Chi tiết lỗi: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Có lỗi xảy ra khi kết nối: {e}")

# Chạy hàm
get_and_save_token()