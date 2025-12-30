from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="IoT Management API", version="1.0.0")

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db = []
devices_db = []
sensor_data_db = []


def get_next_id(db_list):
    if not db_list:
        return 1
    return db_list[-1].id + 1


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str = "user"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None


class User(UserBase):
    id: int
    password: str
    role: str
    created_at: datetime


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class DeviceLoginRequest(BaseModel):
    device_id: int
    device_key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceBase(BaseModel):
    user_id: int
    name: str
    device_key: str
    is_online: bool = False


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    user_id: Optional[int] = None
    name: Optional[str] = None
    device_key: Optional[str] = None
    is_online: Optional[bool] = None


class Device(DeviceBase):
    id: int
    created_at: datetime


class DeviceDetailResponse(Device):
    creator_username: Optional[str] = None


class SensorDataBase(BaseModel):
    device_id: int
    type: str
    value: float


class SensorDataCreate(SensorDataBase):
    pass


class SensorDataUpdate(BaseModel):
    device_id: Optional[int] = None
    type: Optional[str] = None
    value: Optional[float] = None


class SensorData(SensorDataBase):
    id: int
    received_at: datetime


class SensorDataDetailResponse(SensorData):
    device_name: Optional[str] = None


@app.on_event("startup")
def startup_event():
    admin_exists = any(u.username == "admin" for u in users_db)
    if not admin_exists:
        admin_user = User(
            id=1,
            username="admin",
            email="admin@iot.com",
            password=get_password_hash("admin123"),
            role="admin",
            created_at=datetime.now(),
        )
        users_db.append(admin_user)
        print("Default admin created: admin/admin123")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id_str is None or role is None:
            raise credentials_exception
        user_id = int(user_id_str)
        return {"id": user_id, "role": role}
    except (InvalidTokenError, ValueError):
        raise credentials_exception


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User access required")
    return current_user


async def require_device(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "device":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device access required")
    return current_user


@app.post("/auth/login", response_model=TokenResponse)
def login_user(request: LoginRequest):
    user = next((u for u in users_db if u.username == request.username), None)
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role, "username": user.username})
    return TokenResponse(access_token=access_token)


@app.post("/auth/device-login", response_model=TokenResponse)
def login_device(request: DeviceLoginRequest):
    device = next((d for d in devices_db if d.id == request.device_id), None)
    if not device or device.device_key != request.device_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")
    access_token = create_access_token(data={"sub": str(device.id), "role": "device", "device_id": device.id})
    return TokenResponse(access_token=access_token)


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    if any(u.username == user.username for u in users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = get_password_hash(user.password)
    new_user = User(id=get_next_id(users_db), username=user.username, email=user.email, password=hashed_password, role=user.role, created_at=datetime.now())
    users_db.append(new_user)
    return UserResponse(id=new_user.id, username=new_user.username, email=new_user.email, role=new_user.role, created_at=new_user.created_at)


@app.get("/users", response_model=List[UserResponse])
def get_users(current_user: dict = Depends(require_admin)):
    return [UserResponse(id=u.id, username=u.username, email=u.email, role=u.role, created_at=u.created_at) for u in users_db]


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: dict = Depends(require_user)):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user.id, username=user.username, email=user.email, role=user.role, created_at=user.created_at)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(require_user)):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    for i, u in enumerate(users_db):
        if u.id == user_id:
            updated_data = user_update.dict(exclude_unset=True)
            if "password" in updated_data and updated_data["password"]:
                updated_data["password"] = get_password_hash(updated_data["password"])
            updated_user = u.copy(update=updated_data)
            users_db[i] = updated_user
            return UserResponse(id=updated_user.id, username=updated_user.username, email=updated_user.email, role=updated_user.role, created_at=updated_user.created_at)
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    for i, u in enumerate(users_db):
        if u.id == user_id:
            del users_db[i]
            return {"detail": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/devices", response_model=Device)
def create_device(device: DeviceCreate, current_user: dict = Depends(require_user)):
    if not any(u.id == device.user_id for u in users_db):
        raise HTTPException(status_code=400, detail="User ID does not exist")
    if current_user["role"] != "admin" and current_user["id"] != device.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create devices for yourself")
    new_device = Device(id=get_next_id(devices_db), **device.dict(), created_at=datetime.now())
    devices_db.append(new_device)
    return new_device


@app.get("/devices", response_model=List[DeviceDetailResponse])
def get_devices(creator_username: Optional[str] = None, offline_only: bool = Query(False), current_user: dict = Depends(require_user)):
    filtered_devices = devices_db
    if current_user["role"] != "admin":
        filtered_devices = [d for d in filtered_devices if d.user_id == current_user["id"]]
    if offline_only:
        filtered_devices = [d for d in filtered_devices if not d.is_online]
    if creator_username:
        target_user = next((u for u in users_db if u.username == creator_username), None)
        if target_user is None:
            filtered_devices = []
        else:
            filtered_devices = [d for d in filtered_devices if d.user_id == target_user.id]
    response_list = []
    for d in filtered_devices:
        creator_name = next((u.username for u in users_db if u.id == d.user_id), "Unknown")
        response_list.append(DeviceDetailResponse(**d.dict(), creator_username=creator_name))
    return response_list


@app.get("/devices/{device_id}", response_model=Device)
def get_device(device_id: int, current_user: dict = Depends(require_user)):
    d = next((x for x in devices_db if x.id == device_id), None)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    if current_user["role"] != "admin" and d.user_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return d


@app.put("/devices/{device_id}", response_model=Device)
def update_device(device_id: int, device_update: DeviceUpdate, current_user: dict = Depends(require_user)):
    for i, d in enumerate(devices_db):
        if d.id == device_id:
            if current_user["role"] != "admin" and d.user_id != current_user["id"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
            updated_data = device_update.dict(exclude_unset=True)
            updated_device = d.copy(update=updated_data)
            devices_db[i] = updated_device
            return updated_device
    raise HTTPException(status_code=404, detail="Device not found")


@app.delete("/devices/{device_id}")
def delete_device(device_id: int, current_user: dict = Depends(require_user)):
    for i, d in enumerate(devices_db):
        if d.id == device_id:
            if current_user["role"] != "admin" and d.user_id != current_user["id"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
            del devices_db[i]
            return {"detail": "Device deleted"}
    raise HTTPException(status_code=404, detail="Device not found")


@app.post("/sensor_data", response_model=SensorData)
def create_sensor_data(data: SensorDataCreate, current_user: dict = Depends(get_current_user)):
    if not any(d.id == data.device_id for d in devices_db):
        raise HTTPException(status_code=400, detail="Device ID does not exist")
    if current_user["role"] == "device":
        if current_user["id"] != data.device_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device can only create data for itself")
    elif current_user["role"] in ["user", "admin"]:
        device = next((d for d in devices_db if d.id == data.device_id), None)
        if device and current_user["role"] != "admin" and device.user_id != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create data for your own devices")
    new_data = SensorData(id=get_next_id(sensor_data_db), **data.dict(), received_at=datetime.now())
    sensor_data_db.append(new_data)
    return new_data


@app.get("/sensor_data", response_model=List[SensorDataDetailResponse])
def get_sensor_data(device_name: Optional[str] = None, last_n_seconds: Optional[int] = Query(None), current_user: dict = Depends(require_user)):
    filtered_data = sensor_data_db
    if current_user["role"] != "admin":
        user_device_ids = [d.id for d in devices_db if d.user_id == current_user["id"]]
        filtered_data = [sd for sd in filtered_data if sd.device_id in user_device_ids]
    if device_name:
        target_device = next((d for d in devices_db if d.name == device_name), None)
        if target_device is None:
            filtered_data = []
        else:
            filtered_data = [sd for sd in filtered_data if sd.device_id == target_device.id]
    if last_n_seconds is not None:
        cutoff_time = datetime.now() - timedelta(seconds=last_n_seconds)
        filtered_data = [sd for sd in filtered_data if sd.received_at >= cutoff_time]
    response_list = []
    for sd in filtered_data:
        d_name = next((d.name for d in devices_db if d.id == sd.device_id), "Unknown")
        response_list.append(SensorDataDetailResponse(**sd.dict(), device_name=d_name))
    return response_list


@app.get("/sensor_data/{data_id}", response_model=SensorData)
def get_sensor_data_detail(data_id: int, current_user: dict = Depends(require_user)):
    sd = next((x for x in sensor_data_db if x.id == data_id), None)
    if not sd:
        raise HTTPException(status_code=404, detail="Sensor Data not found")
    if current_user["role"] != "admin":
        device = next((d for d in devices_db if d.id == sd.device_id), None)
        if not device or device.user_id != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return sd


@app.put("/sensor_data/{data_id}", response_model=SensorData)
def update_sensor_data(data_id: int, data_update: SensorDataUpdate, current_user: dict = Depends(require_user)):
    for i, sd in enumerate(sensor_data_db):
        if sd.id == data_id:
            if current_user["role"] != "admin":
                device = next((d for d in devices_db if d.id == sd.device_id), None)
                if not device or device.user_id != current_user["id"]:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
            updated_data = data_update.dict(exclude_unset=True)
            updated_obj = sd.copy(update=updated_data)
            sensor_data_db[i] = updated_obj
            return updated_obj
    raise HTTPException(status_code=404, detail="Sensor Data not found")


@app.delete("/sensor_data/{data_id}")
def delete_sensor_data(data_id: int, current_user: dict = Depends(require_user)):
    for i, sd in enumerate(sensor_data_db):
        if sd.id == data_id:
            if current_user["role"] != "admin":
                device = next((d for d in devices_db if d.id == sd.device_id), None)
                if not device or device.user_id != current_user["id"]:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
            del sensor_data_db[i]
            return {"detail": "Sensor Data deleted"}
    raise HTTPException(status_code=404, detail="Sensor Data not found")
