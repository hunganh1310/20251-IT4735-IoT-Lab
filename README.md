# IoT and Application Lab - IT4735

This repository contains laboratory exercises and assignments for the course **20251-IT-4735-IoT and Application** at Hanoi University of Science and Technology (HUST).

## Course Information

- **Course Code:** IT4735
- **Course Name:** IoT and Application
- **Semester:** 20251
- **Institution:** Hanoi University of Science and Technology (HUST)

## Repository Structure

```
IOT LAB/
├── Week 5/          # MQTT Protocol Labs
│   ├── get_token.py
│   ├── get.py
│   ├── post_token.py
│   ├── post.py
│   └── BTVN/        # Homework assignments
│       ├── mqtt_chat.py
│       ├── mqtt_logger.py
│       └── mqtt_publisher.py
│
├── Week 7/          # Message Queue & Data Processing
│   ├── chat_client.py
│   ├── producer.py
│   ├── producer_topic.py
│   ├── consumer_*.py
│   └── *.csv
│
└── Week 10/         # Embedded Systems with PlatformIO
    ├── src/
    │   └── main.cpp
    ├── platformio.ini
    ├── diagram.json
    └── wokwi.toml
```

## Prerequisites

### Software Requirements

- **Python 3.8+** - For MQTT and message queue labs
- **PlatformIO** - For embedded systems development
- **VS Code** - Recommended IDE with PlatformIO extension
- **Wokwi Simulator** - For ESP32/Arduino simulation

### Python Dependencies

```bash
pip install paho-mqtt requests kafka-python
```

## Labs Overview

### Week 5 - MQTT Protocol
- REST API with token authentication
- MQTT publish/subscribe patterns
- MQTT chat application
- Data logging with MQTT

### Week 7 - Message Queues
- Apache Kafka producers and consumers
- Topic-based messaging
- Data processing and CSV logging
- Temperature averaging consumer

### Week 10 - Embedded Systems
- ESP32/Arduino programming
- PlatformIO project structure
- Wokwi simulation

## Getting Started

1. Clone this repository
2. Install required dependencies
3. Navigate to the specific week's folder
4. Follow the instructions in each lab

## Usage

### Running Python Scripts
```bash
cd "Week 5"
python mqtt_chat.py
```

### Building PlatformIO Projects
```bash
cd "Week 10"
pio run
```

### Simulating with Wokwi
Open the project in VS Code with Wokwi extension and run the simulation.

## Author

Student at Hanoi University of Science and Technology (HUST)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Course Instructor and Teaching Assistants
- Hanoi University of Science and Technology (HUST)
- School of Information and Communication Technology
