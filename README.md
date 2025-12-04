# 🌐 IoT and Application Lab - IT4735

This repository contains laboratory exercises and assignments for the course **20251-IT-4735-IoT and Application** at Hanoi University of Science and Technology (HUST).

## 📚 Course Information

| Field | Value |
|-------|-------|
| **Course Code** | IT4735 |
| **Course Name** | IoT and Application |
| **Semester** | 20251 |
| **Institution** | Hanoi University of Science and Technology (HUST) |

## 📁 Repository Structure

```
IOT LAB/
├── Week 5/              # REST API & MQTT Protocol
│   ├── get.py           # HTTP GET request
│   ├── post.py          # HTTP POST request
│   ├── get_token.py     # GET with token auth
│   ├── post_token.py    # POST with token auth
│   └── BTVN/            # Homework
│       ├── mqtt_chat.py
│       ├── mqtt_logger.py
│       └── mqtt_publisher.py
│
├── Week 7/              # Apache Kafka & Message Queues
│   ├── producer.py
│   ├── producer_topic.py
│   ├── consumer_print.py
│   ├── consumer_file.py
│   ├── consumer_home_csv.py
│   ├── consumer_temperature_avg.py
│   └── chat_client.py
│
├── Week 10/             # ESP32 Sensors & LCD (Wokwi)
│   └── DHT22 + PIR + LCD I2C + LED
│       • Temperature & humidity display on LCD
│       • Motion detection with PIR sensor
│       • Auto backlight control (10s timeout)
│       • LED alert when temp > threshold
│
├── Week 10 HW/          # ESP32 WiFi Configuration
│   └── Double Reset WiFi Config
│       • AP mode for WiFi setup
│       • Web interface configuration
│       • Preferences storage
│
└── Week 11/             # ESP32 MQTT IoT
    └── MQTT LED Control
        • WiFi connection
        • MQTT publish/subscribe
        • Remote LED control via HiveMQ
        • Button input with debounce
```

## 🛠️ Prerequisites

### Software Requirements

| Tool | Purpose |
|------|---------|
| **Python 3.8+** | MQTT and Kafka labs |
| **VS Code** | IDE with extensions |
| **PlatformIO** | ESP32 development |
| **Wokwi Extension** | Circuit simulation |

### Python Dependencies

```bash
pip install paho-mqtt requests kafka-python
```

### PlatformIO Libraries

```ini
lib_deps = 
    adafruit/DHT sensor library
    marcoschwartz/LiquidCrystal_I2C
    knolleary/PubSubClient
    bblanchon/ArduinoJson
```

## 🔬 Labs Overview

### Week 5 - REST API & MQTT Protocol
- ✅ HTTP GET/POST requests
- ✅ Token-based authentication
- ✅ MQTT publish/subscribe patterns
- ✅ Real-time chat application
- ✅ Sensor data logging

### Week 7 - Apache Kafka
- ✅ Kafka producers and consumers
- ✅ Topic-based messaging
- ✅ Data processing pipelines
- ✅ CSV logging
- ✅ Temperature averaging

### Week 10 - Embedded Sensors (Wokwi)
- ✅ ESP32 + DHT22 temperature/humidity
- ✅ PIR motion sensor
- ✅ LCD 16x2 I2C display
- ✅ Auto backlight timeout
- ✅ Temperature threshold LED alert

### Week 10 HW - WiFi Configuration
- ✅ Double reset detection
- ✅ AP mode web server
- ✅ WiFi credential storage
- ✅ Web-based configuration UI

### Week 11 - MQTT IoT Control
- ✅ ESP32 WiFi connection
- ✅ MQTT broker integration (HiveMQ)
- ✅ Remote LED control
- ✅ JSON message parsing
- ✅ Button state publishing

## 🚀 Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/hunganh1310/20251-IoT-Lab.git
cd "IOT LAB"
```

### 2. Run Python Scripts
```bash
cd "Week 5"
python mqtt_chat.py
```

### 3. Build PlatformIO Projects
```bash
cd "Week 10"
pio run
```

### 4. Run Wokwi Simulation
1. Open project in VS Code
2. Press `F1` → `Wokwi: Start Simulator`
3. Interact with the circuit

## 📊 Wokwi Simulation

The embedded projects use Wokwi for simulation. Each project contains:
- `diagram.json` - Circuit schematic
- `wokwi.toml` - Simulation config
- `src/main.cpp` - Arduino code

**Tip:** Click on sensors in Wokwi to change their values!

## 👨‍💻 Author

**Hung Anh** - Student at Hanoi University of Science and Technology (HUST)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Course Instructor and Teaching Assistants
- Hanoi University of Science and Technology (HUST)
- School of Information and Communication Technology
