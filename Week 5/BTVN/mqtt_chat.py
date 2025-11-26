import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import json
import time
from paho.mqtt import client as mqtt_client

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_STATUS = "chat/status"
TOPIC_GLOBAL = "chat/global"
TOPIC_PRIVATE = "chat/private/"

class MQTTChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Chat App")
        self.client = None
        self.client_id = None
        self.connected = False
        self.users_online = set()
        self.chat_messages = {"global": []}
        self.current_target = "global"

        self._build_ui()

    def _build_ui(self):
        # khung trái: danh sách user
        self.frame_left = tk.Frame(self.root, width=150, bg="#f0f0f0")
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)

        self.list_users = tk.Listbox(self.frame_left)
        self.list_users.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.list_users.bind("<<ListboxSelect>>", self.on_user_select)

        # khung phải: chat box
        self.frame_right = tk.Frame(self.root)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.text_chat = tk.Text(self.frame_right, state=tk.DISABLED, wrap=tk.WORD)
        self.text_chat.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.entry_message = tk.Entry(self.frame_right)
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.button_send = tk.Button(self.frame_right, text="Send", command=self.send_message)
        self.button_send.pack(side=tk.RIGHT, padx=5, pady=5)

        # yêu cầu nhập ID
        self.client_id = simpledialog.askstring("User ID", "Nhập MSSV (ví dụ: 20225164):", parent=self.root)
        if not self.client_id:
            self.root.destroy()
            return

        self.connect_mqtt()

    def connect_mqtt(self):
        self.client = mqtt_client.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # LWT báo offline nếu ngắt đột ngột
        lwt_payload = json.dumps({"id": self.client_id, "status": "offline"})
        self.client.will_set(TOPIC_STATUS, lwt_payload, qos=1, retain=False)

        self.client.connect(BROKER, PORT, keepalive=60)
        threading.Thread(target=self.client.loop_forever, daemon=True).start()

    # =================== MQTT CALLBACKS ===================
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker.")
            # subscribe topic
            self.client.subscribe(TOPIC_STATUS)
            self.client.subscribe(TOPIC_GLOBAL)
            self.client.subscribe(TOPIC_PRIVATE + self.client_id)

            # Gửi trạng thái online
            payload = json.dumps({"id": self.client_id, "status": "online"})
            self.client.publish(TOPIC_STATUS, payload, qos=1)

            self.add_user("global")  # nhóm chung
        else:
            messagebox.showerror("MQTT", "Không kết nối được broker!")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("Disconnected from broker.")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except:
            return

        if topic == TOPIC_STATUS:
            uid = data.get("id")
            status = data.get("status")
            if uid == self.client_id:
                return

            if status == "online":
                self.add_user(uid)
            elif status == "offline":
                self.remove_user(uid)

        elif topic == TOPIC_GLOBAL:
            sender = data.get("from")
            text = data.get("message")
            self.append_message("global", f"[{sender}] {text}")

        elif topic.startswith(TOPIC_PRIVATE):
            sender = data.get("from")
            text = data.get("message")
            self.append_message(sender, f"[{sender}] {text}")

    # =================== UI LOGIC ===================
    def add_user(self, uid):
        if uid not in self.users_online:
            self.users_online.add(uid)
            self.chat_messages.setdefault(uid, [])
            self.refresh_user_list()

    def remove_user(self, uid):
        if uid in self.users_online:
            self.users_online.remove(uid)
            self.refresh_user_list()

    def refresh_user_list(self):
        self.list_users.delete(0, tk.END)
        for user in ["global"] + sorted(list(self.users_online)):
            self.list_users.insert(tk.END, user)

    def on_user_select(self, event):
        selection = self.list_users.curselection()
        if selection:
            index = selection[0]
            self.current_target = self.list_users.get(index)
            self.update_chat_display()

    def update_chat_display(self):
        self.text_chat.config(state=tk.NORMAL)
        self.text_chat.delete(1.0, tk.END)
        for msg in self.chat_messages.get(self.current_target, []):
            self.text_chat.insert(tk.END, msg + "\n")
        self.text_chat.config(state=tk.DISABLED)

    def append_message(self, target, msg):
        self.chat_messages.setdefault(target, []).append(msg)
        if target == self.current_target:
            self.text_chat.config(state=tk.NORMAL)
            self.text_chat.insert(tk.END, msg + "\n")
            self.text_chat.config(state=tk.DISABLED)

    def send_message(self):
        msg = self.entry_message.get().strip()
        if not msg or not self.connected:
            return
        self.entry_message.delete(0, tk.END)

        data = {"from": self.client_id, "message": msg}

        if self.current_target == "global":
            self.client.publish(TOPIC_GLOBAL, json.dumps(data), qos=1)
            self.append_message("global", f"[Me] {msg}")
        else:
            topic = TOPIC_PRIVATE + self.current_target
            self.client.publish(topic, json.dumps(data), qos=1)
            self.append_message(self.current_target, f"[Me → {self.current_target}] {msg}")

    def on_close(self):
        if self.connected:
            payload = json.dumps({"id": self.client_id, "status": "offline"})
            self.client.publish(TOPIC_STATUS, payload, qos=1)
            time.sleep(0.2)
            self.client.disconnect()
        self.root.destroy()

# ================== MAIN ==================
if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTChatApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
