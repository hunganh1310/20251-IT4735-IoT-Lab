import requests
import json
import os
from datetime import datetime

# URL của API để lấy dữ liệu
DATA_URL = "https://iot-api.deno.dev/api/get_data"

# Tên tệp tin chứa token
TOKEN_FILE = "token.txt"

def get_data_with_token():
    """
    Đọc token từ tệp, gửi yêu cầu GET và hiển thị dữ liệu.
    """
    # 1. Kiểm tra và đọc token từ tệp
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Lỗi: Không tìm thấy tệp '{TOKEN_FILE}'. Vui lòng chạy lại câu c để lấy token.")
        return

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()
    
    if not token:
        print("❌ Lỗi: Tệp token.txt trống. Vui lòng chạy lại câu c để lấy token.")
        return

    # 2. Định nghĩa headers với token xác thực
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("Đang lấy dữ liệu từ API...")
    try:
        # 3. Gửi yêu cầu GET với headers
        response = requests.get(DATA_URL, headers=headers)
        
        # 4. Kiểm tra phản hồi
        if response.status_code == 200:
            data = response.json()
            
            # 5. Phân tích và hiển thị dữ liệu
            print("✅ Lấy dữ liệu thành công!")
            print("---------------------------------")
            print(f"Nhiệt độ: {data.get('temp')} °C")
            print(f"Độ ẩm: {data.get('humid')} %")
            
            # Chuyển đổi timestamp sang định dạng YYYY/MM/DD HH:MM:SS
            timestamp = data.get("timestamp")
            if timestamp:
                dt_object = datetime.fromtimestamp(timestamp / 1000)
                formatted_time = dt_object.strftime("%Y/%m/%d %H:%M:%S")
                print(f"Thời gian: {formatted_time}")
            else:
                print("Thời gian: Không có dữ liệu timestamp.")
        else:
            print(f"❌ Lỗi khi lấy dữ liệu. Mã lỗi: {response.status_code}")
            print(f"Chi tiết lỗi: {response.text}")
            # Lỗi 401 thường do token hết hạn
            if response.status_code == 401:
                print("Lưu ý: Token có thể đã hết hạn. Vui lòng chạy lại câu c để lấy token mới.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Có lỗi xảy ra khi kết nối: {e}")

# Chạy hàm
get_data_with_token()