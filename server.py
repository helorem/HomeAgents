#!/usr/bin/python

import socket
import threading
import time
import Queue
import struct
import Image

import Tools
import CtrlButton

BUFFER_SIZE = 512
HEARTBEAT = 0

class Client(threading.Thread):
    def __init__(self, sock, id, server):
        threading.Thread.__init__(self)
        self.server = server
        self.id = id
        self.sock = sock
        self.is_running = False
        self.last_heartbeat = time.time()
        self.write_queue = Queue.Queue()
        self.commands = {}

        self.sock.settimeout(0.00001)
        #self.sock.setblocking(0)

    def run(self):
        try:
            self.is_running = True
            while self.is_running:
                data = []
                try:
                    recv_data = self.sock.recv(BUFFER_SIZE)
                    if not recv_data:
                        self.on_disconnected()
                        break
                    data.append(recv_data)
                    while len(recv_data) >= BUFFER_SIZE:
                        recv_data = self.sock.recv(BUFFER_SIZE)
                        data.append(recv_data)
                except socket.timeout:
                    pass
                except socket.error:
                    self.on_disconnected()
                    break
                if data:
                    self.on_receive("".join(data))
                if not self.write_queue.empty():
                    data = self.write_queue.get()

                    print Tools.str_to_hex2(data)

                    self.sock.sendall(data)
                else:
                    self.check_alive()
        finally:
            self.sock.close()

    def __get_command_by_num(self, val):
        return Tools.COMMANDS.keys()[Tools.COMMANDS.values().index(val)]

    def stop(self):
        self.is_running = False

    def write(self, data):
        self.write_queue.put(data)

    def on_receive(self, data):
        cmd, cmd_id = struct.unpack("BB", data[0:2])
        cmd = self.__get_command_by_num(cmd)
        data = data[2:]

        self.last_heartbeat = time.time()

        self.server.call_command_listeners(self, cmd, data)

        if cmd_id in self.commands:
            callback, callback_params = self.commands[cmd_id]
            if callback:
                if callback_params:
                    callback((cmd, data), callback_params)
                else:
                    callback((cmd, data))
            del self.commands[cmd_id]

    def on_disconnected(self):
        self.server.remove_client(self.id)

    def check_alive(self):
        if HEARTBEAT > 0:
            now = time.time()
            if now - self.last_heartbeat >= HEARTBEAT * 2:
                self.on_disconnected()
            elif now - self.last_heartbeat >= HEARTBEAT:
                self.send_command("ping")

    def __get_cmd_id(self):
        res = 0
        for i in range(1, 0xFF):
            if i not in self.commands:
                res = i
                break
        return res

    def send_command(self, command, args=None, callback=None, param=None):
        if command not in Tools.COMMANDS:
            #TODO error
            print "Command '%s' is invalid" % command
            return
        cmd_id = self.__get_cmd_id()
        if cmd_id <= 0:
            #TODO improve
            print "Command list is full, waiting..."
            while cmd_id <= 0:
                time.sleep(1)
                cmd_id = self.__get_cmd_id()

        print "<< %s" % command

        self.commands[cmd_id] = (callback, param)
        if args:
            if args:
                to_write = struct.pack("BB", Tools.COMMANDS[command], cmd_id)
                to_write = "%s%s" % (to_write, args)
                self.write(to_write)
        else:
            to_write = struct.pack("BB", Tools.COMMANDS[command], cmd_id)
            self.write(to_write)


class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = False
        self.clients = {}
        self.listeners = {
            "connect" : [],
            "disconnect" : []
        }
        self.command_listeners = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)

    def add_listener(self, event, callback, params=None):
        if event in self.listeners:
            self.listeners[event].append((callback, params))

    def call_listeners(self, event, data):
        if event in self.listeners:
            for callback, params in self.listeners[event]:
                if params:
                    callback(data, params)
                else:
                    callback(data)

    def add_command_listener(self, command, callback, params=None):
        if not command in self.listeners:
            self.command_listeners[command] = []
        self.command_listeners[command].append((callback, params))

    def call_command_listeners(self, client, command, data):
        if command in self.command_listeners:
            for callback, params in self.command_listeners[command]:
                if params:
                    callback(client, data, params)
                else:
                    callback(client, data)

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(10)

        print "Listen %s:%d" % (self.host, self.port)
        self.is_running = True
        try:
            while self.is_running:
                try:
                    (clientsock, (ip, port)) = self.sock.accept()
                    id = "%s:%d" % (ip, port)
                    client = Client(clientsock, id, self)
                    self.clients[id] = client
                    client.start()
                    self.call_listeners("connect", client)
                except socket.timeout:
                    pass
        finally:
            for ip, client in self.clients.iteritems():
                client.stop()
            for ip, client in self.clients.iteritems():
                client.join()

    def remove_client(self, id):
        if id in self.clients:
            client = self.clients[id]
            self.call_listeners("disconnect", client)
            client.stop()
            del self.clients[id]

    def stop(self):
        self.is_running = False


#TEST FCT
def on_connect(client):
    print "Client %s is connected" % client.id
    time.sleep(1)
    client.send_command("who_are_you", callback=on_description, param=client)

#TEST FCT
def on_disconnect(client):
    print "Client %s is disconnected" % client.id
    global actual_img
    actual_img = None

CtrlButton.init(Image.open("button_off.png").convert("RGB"), Image.open("button_on.png").convert("RGB"), Image.open("button_mask.png").convert("RGB"))
g_ctrls = []

def print_cb(data):
    cmd, args = data
    print ">> %s" % (cmd)
    if len(args) > 0:
        print Tools.str_to_hex2(args)

def on_touch_up(client, data):
    global g_ctrls

    x, y = struct.unpack("HH", data[0:4])
    print ">> click %d:%d" % (x, y)
    for ctrl in g_ctrls:
        if ctrl.onTouchUp(x, y):
            break

def on_description(data, client):
    print ">> description %s" % (data,)
    args = struct.pack("HHHHH", 0, 0, 240, 320, Tools.encode_color565(16, 28, 40))
    client.send_command("fill_color", args=args, callback=on_filled, param=client)

def on_filled(data, client):
    global g_ctrls
    button = CtrlButton.CtrlButton(client, 30, 30)
    g_ctrls.append(button)
    button.show()

host = "0.0.0.0"
port = 7654

server = Server(host, port)
server.add_command_listener("touch_up", on_touch_up)
server.add_listener("connect", on_connect)
server.add_listener("disconnect", on_disconnect)
server.start()


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "\nOVER"
finally:
    server.stop()
    server.join()

