# 🧪 POSTMAN TEST FLOW - IoT Management API

## 📋 Mục tiêu Test
Test tất cả các positive scenarios với đầy đủ xác thực (authentication) và phân quyền (authorization).

---

## 🔐 Phân quyền (Authorization Rules)

### User APIs
- ✅ **Admin**: Tạo, xem tất cả, xóa user
- ✅ **User**: Chỉ cập nhật thông tin của chính mình

### Device APIs
- ✅ **Admin**: Toàn quyền CRUD tất cả devices
- ✅ **User**: Chỉ CRUD devices do chính mình tạo

### SensorData APIs
- ✅ **Admin**: Toàn quyền CRUD tất cả data
- ✅ **User**: Đọc/Sửa/Xóa data từ devices của mình
- ✅ **Device**: CHỈ được tạo (POST) data, không được đọc/sửa/xóa

---

## 🚀 LUỒNG TEST CHÍNH

### SETUP: Chuẩn bị Postman Environment

1. Mở Postman
2. Click vào **Environments** (bên trái)
3. Click **"+"** để tạo environment mới
4. Đặt tên: **"IoT API Testing"**
5. Thêm 3 variables:
   - `admin_token` = (để trống)
   - `user_token` = (để trống)
   - `device_token` = (để trống)
6. Click **Save**
7. Chọn environment **"IoT API Testing"** ở dropdown phía trên

---

## ✅ PHASE 1: ADMIN AUTHENTICATION & USER MANAGEMENT

### Test 1.1: Admin Login ⭐

**Mục đích:** Xác thực tài khoản admin và lấy admin token

```
POST http://localhost:8000/auth/login
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Expected Response:** `200 OK`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Action:** 
1. Copy `access_token` từ response
2. Vào **Environments** → **IoT API Testing**
3. Paste vào giá trị của `admin_token`
4. **Save environment**

---

### Test 1.2: Admin tạo User thường ⭐

**Mục đích:** Chứng minh chỉ admin mới có quyền tạo user

```
POST http://localhost:8000/users
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "username": "user_alice",
  "password": "alice123",
  "email": "alice@example.com",
  "role": "user"
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 2,
  "username": "user_alice",
  "email": "alice@example.com",
  "role": "user",
  "created_at": "2025-12-30T..."
}
```

**Note:** User ID = 2 (admin có ID = 1)

---

### Test 1.3: Admin xem danh sách tất cả Users ⭐

**Mục đích:** Chứng minh admin có quyền xem tất cả users

```
GET http://localhost:8000/users
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@iot.com",
    "role": "admin",
    "created_at": "..."
  },
  {
    "id": 2,
    "username": "user_alice",
    "email": "alice@example.com",
    "role": "user",
    "created_at": "..."
  }
]
```

---

### Test 1.4: Admin xem thông tin User cụ thể ⭐

**Mục đích:** Admin có thể xem thông tin bất kỳ user nào

```
GET http://localhost:8000/users/2
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK`
```json
{
  "id": 2,
  "username": "user_alice",
  "email": "alice@example.com",
  "role": "user",
  "created_at": "..."
}
```

---

## ✅ PHASE 2: USER AUTHENTICATION & DEVICE MANAGEMENT

### Test 2.1: User Login ⭐

**Mục đích:** User thường xác thực và lấy user token

```
POST http://localhost:8000/auth/login
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "username": "user_alice",
  "password": "alice123"
}
```

**Expected Response:** `200 OK`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Action:**
1. Copy `access_token`
2. Paste vào `user_token` trong Environment
3. **Save**

---

### Test 2.2: User tạo Device của mình ⭐

**Mục đích:** User tạo device với user_id = 2 (chính mình)

```
POST http://localhost:8000/devices
```

**Headers:**
```
Authorization: Bearer {{user_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "user_id": 2,
  "name": "Temperature Sensor 01",
  "device_key": "temp-sensor-secret-123",
  "is_online": true
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 2,
  "name": "Temperature Sensor 01",
  "device_key": "temp-sensor-secret-123",
  "is_online": true,
  "created_at": "..."
}
```

**Note:** Device ID = 1

---

### Test 2.3: User xem danh sách Devices của mình ⭐

**Mục đích:** User chỉ thấy devices do mình tạo

```
GET http://localhost:8000/devices
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 2,
    "name": "Temperature Sensor 01",
    "device_key": "temp-sensor-secret-123",
    "is_online": true,
    "created_at": "...",
    "creator_username": "user_alice"
  }
]
```

---

### Test 2.4: User xem chi tiết Device của mình ⭐

**Mục đích:** User có quyền xem chi tiết device của mình

```
GET http://localhost:8000/devices/1
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 2,
  "name": "Temperature Sensor 01",
  "device_key": "temp-sensor-secret-123",
  "is_online": true,
  "created_at": "..."
}
```

---

### Test 2.5: User cập nhật Device của mình ⭐

**Mục đích:** User có quyền cập nhật device của mình

```
PUT http://localhost:8000/devices/1
```

**Headers:**
```
Authorization: Bearer {{user_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "is_online": false
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 2,
  "name": "Temperature Sensor 01",
  "device_key": "temp-sensor-secret-123",
  "is_online": false,
  "created_at": "..."
}
```

---

### Test 2.6: User cập nhật thông tin của chính mình ⭐

**Mục đích:** User có quyền cập nhật profile của chính mình

```
PUT http://localhost:8000/users/2
```

**Headers:**
```
Authorization: Bearer {{user_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "email": "alice.new@example.com"
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 2,
  "username": "user_alice",
  "email": "alice.new@example.com",
  "role": "user",
  "created_at": "..."
}
```

---

## ✅ PHASE 3: DEVICE AUTHENTICATION & SENSOR DATA

### Test 3.1: Device Login ⭐

**Mục đích:** Device xác thực và lấy device token

```
POST http://localhost:8000/auth/device-login
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "device_id": 1,
  "device_key": "temp-sensor-secret-123"
}
```

**Expected Response:** `200 OK`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Action:**
1. Copy `access_token`
2. Paste vào `device_token` trong Environment
3. **Save**

---

### Test 3.2: Device gửi Sensor Data (Temperature) ⭐

**Mục đích:** Device chỉ có quyền tạo (POST) sensor data

```
POST http://localhost:8000/sensor_data
```

**Headers:**
```
Authorization: Bearer {{device_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "device_id": 1,
  "type": "temperature",
  "value": 25.5
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "device_id": 1,
  "type": "temperature",
  "value": 25.5,
  "received_at": "2025-12-30T..."
}
```

---

### Test 3.3: Device gửi Sensor Data (Humidity) ⭐

**Mục đích:** Device có thể gửi nhiều loại data

```
POST http://localhost:8000/sensor_data
```

**Headers:**
```
Authorization: Bearer {{device_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "device_id": 1,
  "type": "humidity",
  "value": 65.0
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 2,
  "device_id": 1,
  "type": "humidity",
  "value": 65.0,
  "received_at": "2025-12-30T..."
}
```

---

## ✅ PHASE 4: USER READS & MANAGES SENSOR DATA

### Test 4.1: User xem tất cả Sensor Data từ devices của mình ⭐

**Mục đích:** User có quyền đọc data từ devices của mình

```
GET http://localhost:8000/sensor_data
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK`
```json
[
  {
    "id": 1,
    "device_id": 1,
    "type": "temperature",
    "value": 25.5,
    "received_at": "...",
    "device_name": "Temperature Sensor 01"
  },
  {
    "id": 2,
    "device_id": 1,
    "type": "humidity",
    "value": 65.0,
    "received_at": "...",
    "device_name": "Temperature Sensor 01"
  }
]
```

---

### Test 4.2: User xem Sensor Data theo tên Device ⭐

**Mục đích:** User có thể filter data theo device name

```
GET http://localhost:8000/sensor_data?device_name=Temperature Sensor 01
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK` - Array chứa data từ device đó

---

### Test 4.3: User xem Sensor Data trong khoảng thời gian ⭐

**Mục đích:** User có thể filter data theo thời gian

```
GET http://localhost:8000/sensor_data?last_n_seconds=3600
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK` - Data từ 1 giờ trước đến giờ

---

### Test 4.4: User xem chi tiết một Sensor Data ⭐

**Mục đích:** User có quyền xem chi tiết data từ device của mình

```
GET http://localhost:8000/sensor_data/1
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "device_id": 1,
  "type": "temperature",
  "value": 25.5,
  "received_at": "..."
}
```

---

### Test 4.5: User cập nhật Sensor Data ⭐

**Mục đích:** User có quyền sửa data từ device của mình

```
PUT http://localhost:8000/sensor_data/1
```

**Headers:**
```
Authorization: Bearer {{user_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "value": 26.0
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 1,
  "device_id": 1,
  "type": "temperature",
  "value": 26.0,
  "received_at": "..."
}
```

---

### Test 4.6: User xóa Sensor Data ⭐

**Mục đích:** User có quyền xóa data từ device của mình

```
DELETE http://localhost:8000/sensor_data/2
```

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response:** `200 OK`
```json
{
  "detail": "Sensor Data deleted"
}
```

---

## ✅ PHASE 5: ADMIN FULL ACCESS

### Test 5.1: Admin tạo Device cho User ⭐

**Mục đích:** Admin có quyền tạo device cho bất kỳ user nào

```
POST http://localhost:8000/devices
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "user_id": 2,
  "name": "Humidity Sensor 02",
  "device_key": "humidity-sensor-secret-456",
  "is_online": true
}
```

**Expected Response:** `200 OK`
```json
{
  "id": 2,
  "user_id": 2,
  "name": "Humidity Sensor 02",
  "device_key": "humidity-sensor-secret-456",
  "is_online": true,
  "created_at": "..."
}
```

---

### Test 5.2: Admin xem tất cả Devices ⭐

**Mục đích:** Admin có quyền xem tất cả devices

```
GET http://localhost:8000/devices
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK` - Array chứa tất cả devices

---

### Test 5.3: Admin xem tất cả Sensor Data ⭐

**Mục đích:** Admin có quyền xem tất cả sensor data

```
GET http://localhost:8000/sensor_data
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK` - Array chứa tất cả data

---

### Test 5.4: Admin tạo Sensor Data ⭐

**Mục đích:** Admin có thể tạo sensor data cho bất kỳ device nào

```
POST http://localhost:8000/sensor_data
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "device_id": 1,
  "type": "pressure",
  "value": 1013.25
}
```

**Expected Response:** `200 OK`

---

### Test 5.5: Admin cập nhật Sensor Data ⭐

**Mục đích:** Admin có quyền sửa bất kỳ sensor data nào

```
PUT http://localhost:8000/sensor_data/1
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "value": 27.0
}
```

**Expected Response:** `200 OK`

---

### Test 5.6: Admin xóa Device ⭐

**Mục đích:** Admin có quyền xóa bất kỳ device nào

```
DELETE http://localhost:8000/devices/2
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK`
```json
{
  "detail": "Device deleted"
}
```

---

### Test 5.7: Admin xóa User ⭐

**Mục đích:** Admin có quyền xóa user (thường test cuối cùng)

```
DELETE http://localhost:8000/users/2
```

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response:** `200 OK`
```json
{
  "detail": "User deleted"
}
```

---

## 📊 SUMMARY - TỔNG KẾT

### Tổng số test cases: 27 positive scenarios

| Phase | Tests | Mô tả |
|-------|-------|-------|
| Phase 1 | 4 | Admin authentication & user management |
| Phase 2 | 6 | User authentication & device management |
| Phase 3 | 3 | Device authentication & sensor data creation |
| Phase 4 | 6 | User reads & manages sensor data |
| Phase 5 | 7 | Admin full access demonstration |

---

## ✅ CHECKLIST TEST

- [ ] Phase 1: Admin login và quản lý users
- [ ] Phase 2: User login và quản lý devices
- [ ] Phase 3: Device login và gửi sensor data
- [ ] Phase 4: User đọc và quản lý sensor data
- [ ] Phase 5: Admin có toàn quyền

---

## 🎯 Kết quả mong đợi

Sau khi test xong tất cả 27 scenarios:

✅ **Authentication**: 3 loại login (admin, user, device) hoạt động
✅ **User Management**: Admin quản lý users, user tự update
✅ **Device Management**: Admin & user quản lý devices (user chỉ devices của mình)
✅ **Sensor Data**: Device tạo, User đọc/sửa/xóa, Admin toàn quyền
✅ **Authorization**: Phân quyền chặt chẽ theo role

---

**🎉 Test thành công = Hệ thống hoạt động đúng yêu cầu!**
