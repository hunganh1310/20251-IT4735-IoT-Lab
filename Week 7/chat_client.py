#!/usr/bin/env python3
import os
import json
import time
import threading
import queue
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import pika

CLOUDAMQP_URL = "amqps://wkkljzrr:BHe9Y-5-uIo477c_GHygiljXW1t4y7ai@armadillo.rmq.cloudamqp.com/wkkljzrr"
if not CLOUDAMQP_URL:
    raise RuntimeError("Invalid Broker URL")

EXCHANGE_PRESENCE = "presence"
EXCHANGE_CHAT = "chat"

# Thread-safe queue để chuyển message từ AMQP consumer thread đến Tk mainloop
incoming_q = queue.Queue()


def now_ts():
    return int(time.time())


class AMQPClient(threading.Thread):
    """
    Thread chạy pika.BlockingConnection để nhận messages.
    Mỗi message sẽ được parse và đưa vào incoming_q để GUI xử lý.
    """

    def __init__(self, client_id):
        super().__init__(daemon=True)
        self.client_id = client_id
        self._closing = False
        self.connection = None
        self.channel = None
        self.queue_name = None

    def run(self):
        params = pika.URLParameters(CLOUDAMQP_URL)
        # tự reconnect loop đơn giản
        while not self._closing:
            try:
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                # exchanges
                self.channel.exchange_declare(exchange=EXCHANGE_PRESENCE, exchange_type='fanout', durable=False)
                self.channel.exchange_declare(exchange=EXCHANGE_CHAT, exchange_type='topic', durable=False)

                # exclusive queue cho client
                result = self.channel.queue_declare(queue='', exclusive=True)
                self.queue_name = result.method.queue

                # bind để nhận presence (fanout)
                self.channel.queue_bind(exchange=EXCHANGE_PRESENCE, queue=self.queue_name)
                # bind để nhận chat.global và chat.user.<id>
                self.channel.queue_bind(exchange=EXCHANGE_CHAT, queue=self.queue_name, routing_key='chat.global')
                self.channel.queue_bind(exchange=EXCHANGE_CHAT, queue=self.queue_name, routing_key=f'chat.user.{self.client_id}')

                # bắt đầu consume
                for method_frame, properties, body in self.channel.consume(queue=self.queue_name, inactivity_timeout=1):
                    if self._closing:
                        break
                    if method_frame is None:
                        continue
                    try:
                        msg = json.loads(body.decode())
                    except Exception:
                        msg = {"raw": body.decode()}
                    # đẩy vào queue để GUI xử lý
                    incoming_q.put((method_frame.routing_key, msg))
                    # ack (auto-ack style). use basic_ack để tránh mất message nếu cần.
                    self.channel.basic_ack(method_frame.delivery_tag)
                # break loop khi _closing true
            except Exception as e:
                # lỗi kết nối: chờ 2s rồi reconnect
                incoming_q.put(("__system__", {"type": "error", "error": str(e)}))
                time.sleep(2)
            finally:
                try:
                    if self.connection and not self.connection.is_closed:
                        self.connection.close()
                except Exception:
                    pass

    def publish_presence(self, kind):
        """
        kind: 'announce' with status online/offline or 'request'
        announce: {"type":"presence","kind":"announce","user":id,"status":"online"}
        request: {"type":"presence","kind":"request","from":id}
        """
        if not self.channel or self.channel.is_closed:
            return
        if kind == 'announce':
            msg = {"type": "presence", "kind": "announce", "user": self.client_id, "status": "online", "ts": now_ts()}
        elif kind == 'offline':
            msg = {"type": "presence", "kind": "announce", "user": self.client_id, "status": "offline", "ts": now_ts()}
        elif kind == 'request':
            msg = {"type": "presence", "kind": "request", "from": self.client_id, "ts": now_ts()}
        else:
            return
        self.channel.basic_publish(exchange=EXCHANGE_PRESENCE, routing_key='', body=json.dumps(msg))

    def publish_chat(self, to, text):
        """
        to: 'global' or recipient_id
        text: message text
        """
        if not self.channel or self.channel.is_closed:
            return
        payload = {
            "type": "chat",
            "from": self.client_id,
            "to": to,
            "message": text,
            "ts": now_ts()
        }
        if to == "global":
            routing = "chat.global"
        else:
            routing = f"chat.user.{to}"
        self.channel.basic_publish(exchange=EXCHANGE_CHAT, routing_key=routing, body=json.dumps(payload))

    def close(self):
        self._closing = True
        # trước khi đóng, gửi offline announce
        try:
            if self.channel and (not self.channel.is_closed):
                msg = {"type": "presence", "kind": "announce", "user": self.client_id, "status": "offline", "ts": now_ts()}
                self.channel.basic_publish(exchange=EXCHANGE_PRESENCE, routing_key='', body=json.dumps(msg))
        except Exception:
            pass
        # đóng connection
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass


class ChatGUI:
    def __init__(self, root):
        self.root = root
        root.title("Hello!")
        root.geometry("820x520")

        # Top frame: connect area
        top = tk.Frame(root)
        top.pack(fill='x', padx=6, pady=6)
        tk.Label(top, text="ID (MSSV):").pack(side='left')
        self.id_entry = tk.Entry(top)
        self.id_entry.pack(side='left', padx=6)
        self.connect_btn = tk.Button(top, text="Kết nối", command=self.connect)
        self.connect_btn.pack(side='left')

        # main frames
        main = tk.Frame(root)
        main.pack(fill='both', expand=True, padx=6, pady=6)

        # left: user list
        left = tk.Frame(main, width=200)
        left.pack(side='left', fill='y')
        tk.Label(left, text="Users (online)").pack()
        self.user_listbox = tk.Listbox(left, width=25, height=25)
        self.user_listbox.pack(fill='y', expand=True)
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        # right: messages
        right = tk.Frame(main)
        right.pack(side='left', fill='both', expand=True)
        tk.Label(right, text="Messages").pack(anchor='w')
        self.msg_area = scrolledtext.ScrolledText(right, state='disabled', wrap='word')
        self.msg_area.pack(fill='both', expand=True)

        # bottom: entry + send
        bottom = tk.Frame(root)
        bottom.pack(fill='x', padx=6, pady=6)
        self.msg_entry = tk.Entry(bottom)
        self.msg_entry.pack(side='left', fill='x', expand=True, padx=(0,6))
        self.send_btn = tk.Button(bottom, text="Send", width=10, command=self.send_message)
        self.send_btn.pack(side='left')

        # internal state
        self.client_id = None
        self.amqp = None
        # conversations: key 'global' or other_id -> list of (ts, from, text)
        self.conversations = {"global": []}
        # online users set
        self.online_users = set()
        self.online_users.add("global")
        # currently selected target
        self.selected = "global"
        # ensure global in user listbox
        self.refresh_user_listbox()

        # poll incoming queue periodically
        self.root.after(100, self.poll_incoming)

        # handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_user_listbox(self):
        # keep selection stable if possible
        cur = self.selected
        self.user_listbox.delete(0, tk.END)
        for u in sorted(self.online_users, key=lambda x: (x!="global", x)):
            self.user_listbox.insert(tk.END, u)
        # reselect
        try:
            idx = list(sorted(self.online_users, key=lambda x: (x!="global", x))).index(cur)
            self.user_listbox.select_set(idx)
            self.user_listbox.see(idx)
        except Exception:
            # select global by default
            try:
                idx = list(sorted(self.online_users, key=lambda x: (x!="global", x))).index("global")
                self.user_listbox.select_set(idx)
                self.selected = "global"
            except Exception:
                pass

    def on_user_select(self, event=None):
        sel = self.user_listbox.curselection()
        if not sel:
            return
        val = self.user_listbox.get(sel[0])
        self.selected = val
        self.show_conversation(val)

    def show_conversation(self, key):
        self.msg_area.configure(state='normal')
        self.msg_area.delete('1.0', tk.END)
        conv_key = "global" if key == "global" else f"user:{key}"
        msgs = self.conversations.get(conv_key, [])
        for ts, frm, text in msgs:
            tstr = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            self.msg_area.insert(tk.END, f"[{tstr}] {frm}: {text}\n")
        self.msg_area.configure(state='disabled')

    def append_message(self, conv_key, ts, frm, text):
        # conv_key: 'global' or 'user:<id>'
        self.conversations.setdefault(conv_key, [])
        self.conversations[conv_key].append((ts, frm, text))
        # if currently viewing this conv, update display
        viewing_key = "global" if self.selected == "global" else f"user:{self.selected}"
        if viewing_key == conv_key:
            self.msg_area.configure(state='normal')
            tstr = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            self.msg_area.insert(tk.END, f"[{tstr}] {frm}: {text}\n")
            self.msg_area.see(tk.END)
            self.msg_area.configure(state='disabled')

    def connect(self):
        if self.amqp:
            messagebox.showinfo("Info", "Đã kết nối rồi.")
            return
        cid = self.id_entry.get().strip()
        if not cid:
            messagebox.showerror("Error", "Vui lòng nhập ID (MSSV).")
            return
        self.client_id = cid
        # khởi thread amqp
        self.amqp = AMQPClient(self.client_id)
        self.amqp.start()
        # chờ một chút cho thread kết nối, rồi gửi announce và request
        def after_connect():
            try:
                # publish announce and request
                # chờ channel sẵn sàng
                # đơn giản: lặp thử vài lần
                tries = 0
                while tries < 10:
                    if self.amqp.channel and (not self.amqp.channel.is_closed):
                        break
                    time.sleep(0.2)
                    tries += 1
                # publish announce and request
                try:
                    self.amqp.publish_presence('announce')
                    self.amqp.publish_presence('request')
                except Exception as e:
                    incoming_q.put(("__system__", {"type":"error","error":f"Publish presence failed: {e}"}))
            except Exception as e:
                incoming_q.put(("__system__", {"type":"error","error":str(e)}))

        threading.Thread(target=after_connect, daemon=True).start()
        self.connect_btn.config(state='disabled')
        self.id_entry.config(state='disabled')

    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text or not self.amqp:
            return
        target = self.selected
        if target == "global":
            to = "global"
        else:
            to = target
        try:
            self.amqp.publish_chat(to, text)
            # append own message locally
            conv_key = "global" if to == "global" else f"user:{to}"
            self.append_message(conv_key, now_ts(), self.client_id, text)
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Gửi thất bại: {e}")

    def poll_incoming(self):
        while True:
            try:
                routing_key, msg = incoming_q.get_nowait()
            except queue.Empty:
                break
            try:
                self.handle_incoming(routing_key, msg)
            except Exception as e:
                print("Error handling incoming:", e)
        self.root.after(100, self.poll_incoming)

    def handle_incoming(self, routing_key, msg):
        # hệ thống lỗi
        if routing_key == "__system__":
            if msg.get("type") == "error":
                self.msg_area.configure(state='normal')
                self.msg_area.insert(tk.END, f"[SYSTEM ERROR] {msg.get('error')}\n")
                self.msg_area.configure(state='disabled')
            return

        mtype = msg.get("type")
        if mtype == "presence":
            kind = msg.get("kind")
            if kind == "announce":
                user = msg.get("user")
                status = msg.get("status")
                if user == self.client_id:
                    return  # ignore own announce for list (we already know)
                if status == "online":
                    # add user to online list
                    if user not in self.online_users:
                        self.online_users.add(user)
                        # initialize conversation buffer
                        self.conversations.setdefault(f"user:{user}", [])
                        self.refresh_user_listbox()
                    # also log in message area
                    self.append_message("global", msg.get("ts", now_ts()), "system", f"{user} đã online")
                elif status == "offline":
                    if user in self.online_users:
                        try:
                            self.online_users.remove(user)
                            self.refresh_user_listbox()
                        except Exception:
                            pass
                    self.append_message("global", msg.get("ts", now_ts()), "system", f"{user} đã offline")
            elif kind == "request":
                # một client mới yêu cầu ai đang online -> trả lời bằng announce của mình
                fr = msg.get("from")
                # if request comes from others, we should publish announce for ourselves
                # but do not respond to our own request
                if fr != self.client_id and self.amqp:
                    try:
                        self.amqp.publish_presence('announce')
                    except Exception:
                        pass
        elif mtype == "chat":
            frm = msg.get("from")
            to = msg.get("to")
            text = msg.get("message")
            ts = msg.get("ts", now_ts())
            # nhận message global
            if to == "global":
                # store under 'global'
                self.append_message("global", ts, frm, text)
            else:
                # private: if I'm recipient or sender
                # message from someone to me: to == my id
                # message could be sent to someone else; we ignore unless from or to equals me
                if to == self.client_id:
                    # incoming private message to me
                    conv_key = f"user:{frm}"
                    self.append_message(conv_key, ts, frm, text)
                    # ensure sender in online list
                    if frm not in self.online_users:
                        self.online_users.add(frm)
                        self.conversations.setdefault(conv_key, [])
                        self.refresh_user_listbox()
                else:
                    # Could be my own message published earlier — other clients will receive it; ignore here
                    pass
        else:
            # raw unknown
            self.append_message("global", now_ts(), "raw", str(msg))

    def on_close(self):
        # khi đóng cửa sổ: gửi offline và dừng amqp thread
        if self.amqp:
            try:
                self.amqp.close()
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()
