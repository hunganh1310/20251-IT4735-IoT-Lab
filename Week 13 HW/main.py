from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI()

#In-Memory Databases
users_db = []
devices_db = []
sensor_data_db = []

# Helpers
def get_next_id(db_list):
    if not db_list:
        return 1
    return db_list[-1].id + 1

# Models
# User Models
class UserBase(BaseModel):
    username: str
    password: str
    email: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime

# Device Models
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

# SensorData Models
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


#User APIs

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    new_user = User(
        id=get_next_id(users_db),
        **user.dict(),
        created_at=datetime.now()
    )
    users_db.append(new_user)
    return new_user

@app.get("/users", response_model=List[User])
def get_users():
    return users_db

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    for u in users_db:
        if u.id == user_id:
            return u
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user_update: UserUpdate):
    for i, u in enumerate(users_db):
        if u.id == user_id:
            updated_data = user_update.dict(exclude_unset=True)
            updated_user = u.copy(update=updated_data)
            users_db[i] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, u in enumerate(users_db):
        if u.id == user_id:
            del users_db[i]
            return {"detail": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")


#Device APIs

@app.post("/devices", response_model=Device)
def create_device(device: DeviceCreate):
    # Verify user exists
    user_exists = any(u.id == device.user_id for u in users_db)
    if not user_exists:
        raise HTTPException(status_code=400, detail="User ID does not exist")
    
    new_device = Device(
        id=get_next_id(devices_db),
        **device.dict(),
        created_at=datetime.now()
    )
    devices_db.append(new_device)
    return new_device

@app.get("/devices", response_model=List[DeviceDetailResponse])
def get_devices(
    creator_username: Optional[str] = None,
    offline_only: bool = Query(False, description="Filter for offline devices")
):
    filtered_devices = devices_db

    # Filter by offline
    if offline_only:
        filtered_devices = [d for d in filtered_devices if not d.is_online]

    # Filter by creator_username
    if creator_username:
        # Find user id for the username
        target_user_id = None
        for u in users_db:
            if u.username == creator_username:
                target_user_id = u.id
                break
        
        if target_user_id is None:
            # If user not found, technically returns empty list for devices
            filtered_devices = []
        else:
            filtered_devices = [d for d in filtered_devices if d.user_id == target_user_id]

    # Enhance response with creator_username
    response_list = []
    for d in filtered_devices:
        creator_name = "Unknown"
        for u in users_db:
            if u.id == d.user_id:
                creator_name = u.username
                break
        
        # Create a response object
        response_obj = DeviceDetailResponse(
            **d.dict(),
            creator_username=creator_name
        )
        response_list.append(response_obj)
        
    return response_list

@app.get("/devices/{device_id}", response_model=Device)
def get_device(device_id: int):
    for d in devices_db:
        if d.id == device_id:
            return d
    raise HTTPException(status_code=404, detail="Device not found")

@app.put("/devices/{device_id}", response_model=Device)
def update_device(device_id: int, device_update: DeviceUpdate):
    for i, d in enumerate(devices_db):
        if d.id == device_id:
            updated_data = device_update.dict(exclude_unset=True)
            updated_device = d.copy(update=updated_data)
            devices_db[i] = updated_device
            return updated_device
    raise HTTPException(status_code=404, detail="Device not found")

@app.delete("/devices/{device_id}")
def delete_device(device_id: int):
    for i, d in enumerate(devices_db):
        if d.id == device_id:
            del devices_db[i]
            return {"detail": "Device deleted"}
    raise HTTPException(status_code=404, detail="Device not found")


#SensorData APIs

@app.post("/sensor_data", response_model=SensorData)
def create_sensor_data(data: SensorDataCreate):
    # Verify device exists
    device_exists = any(d.id == data.device_id for d in devices_db)
    if not device_exists:
        raise HTTPException(status_code=400, detail="Device ID does not exist")

    new_data = SensorData(
        id=get_next_id(sensor_data_db),
        **data.dict(),
        received_at=datetime.now()
    )
    sensor_data_db.append(new_data)
    return new_data

@app.get("/sensor_data", response_model=List[SensorDataDetailResponse])
def get_sensor_data(
    device_name: Optional[str] = None,
    last_n_seconds: Optional[int] = Query(None, description="Get data from last N seconds")
):
    filtered_data = sensor_data_db

    # Filter by device_name
    if device_name:
        target_device_id = None
        for d in devices_db:
            if d.name == device_name:
                target_device_id = d.id
                break
        
        if target_device_id is None:
            filtered_data = [] # Device name not found, so no data matches
        else:
            filtered_data = [sd for sd in filtered_data if sd.device_id == target_device_id]

    # Filter by time window
    if last_n_seconds is not None:
        cutoff_time = datetime.now() - timedelta(seconds=last_n_seconds)
        filtered_data = [sd for sd in filtered_data if sd.received_at >= cutoff_time]

    # Enhance response with device_name
    response_list = []
    for sd in filtered_data:
        d_name = "Unknown"
        for d in devices_db:
            if d.id == sd.device_id:
                d_name = d.name
                break
        
        response_obj = SensorDataDetailResponse(
            **sd.dict(),
            device_name=d_name
        )
        response_list.append(response_obj)

    return response_list

@app.get("/sensor_data/{data_id}", response_model=SensorData)
def get_sensor_data_detail(data_id: int):
    for sd in sensor_data_db:
        if sd.id == data_id:
            return sd
    raise HTTPException(status_code=404, detail="Sensor Data not found")

@app.put("/sensor_data/{data_id}", response_model=SensorData)
def update_sensor_data(data_id: int, data_update: SensorDataUpdate):
    for i, sd in enumerate(sensor_data_db):
        if sd.id == data_id:
            updated_data = data_update.dict(exclude_unset=True)
            updated_obj = sd.copy(update=updated_data)
            sensor_data_db[i] = updated_obj
            return updated_obj
    raise HTTPException(status_code=404, detail="Sensor Data not found")

@app.delete("/sensor_data/{data_id}")
def delete_sensor_data(data_id: int):
    for i, sd in enumerate(sensor_data_db):
        if sd.id == data_id:
            del sensor_data_db[i]
            return {"detail": "Sensor Data deleted"}
    raise HTTPException(status_code=404, detail="Sensor Data not found")