#!/usr/bin/python

import socket
import threading
import time
import Queue
import struct

import Tools

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

#TEST
img_buffer = {}

#TEST FCT
actual_img = None
def send_img(client, filename):
    global actual_img
    global img_buffer

    print "send_img", filename

    found = False
    if actual_img:
        name = "%s_%s" % (actual_img, filename)
        if name in img_buffer:
            print "load", name
            palet_size, palet, pixels_size, pixels, rect = img_buffer[name]
            found = True
    elif filename in img_buffer:
        print "load", filename
        palet_size, palet, pixels_size, pixels, rect = img_buffer[filename]
        found = True

    if not found:
        im = Image.open(filename)
        rgb_im = im.convert("RGB")
        w, h = im.size

        rect = (0, 0, w, h)
        if actual_img:
            rect = img_diff(filename, actual_img)
            name = "%s_%s" % (actual_img, filename)
        else:
            name = filename
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]

        print "rect:", rect, w, h
        rgb_im = rgb_im.crop(rect)

        pixels = []
        palet = []

        for y in xrange(0, h):
            for x in xrange(0, w):
                r, g, b = rgb_im.getpixel((x, y))
                color = encode_color565(r, g, b)
                if color not in palet:
                    palet.append(color)
                pixels.append(palet.index(color))

        palet_size = len(palet)
        pixels_size = len(pixels)

        #use RLE
        pixels = compress_rle(pixels)
        pixels_size = len(pixels)

        print "save %s" % name
        img_buffer[name] = (palet_size, palet, pixels_size, pixels, rect)

    actual_img = filename

    args = struct.pack("H%s" % ("H" * palet_size), palet_size, *palet)
    print "len palet : %d" % palet_size
    print "len args : %d" % len(args)
    print "first color=", palet[0], " ", decode_color565(palet[0])

    client.send_command("send_palet", args=args, callback=print_cb)

    w = rect[2] - rect[0]
    args = struct.pack("HHHIB%s" % ("B" * pixels_size), rect[0], rect[1], w, pixels_size, Tools.C_RLE, *pixels)
    print "len pixels : %d" % pixels_size
    print "len args : %d" % len(args)

    client.send_command("draw_pixels", args=args, callback=print_cb)

#TEST FCT
def decode_color565(color):
    r = (color >> 8) & 0xF8
    g = (color >> 3) & 0xFC
    b = (color << 3) & 0xFF

    return (r, g, b);

#TEST FCT
def encode_color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);

#TEST FCT
def img_diff(img1, img2):
    im = Image.open(img1)
    rgb_im1 = im.convert("RGB")
    w, h = im.size

    im = Image.open(img2)
    rgb_im2 = im.convert("RGB")

    min_y = h
    max_y = 0
    min_x = w
    max_x = 0
    for y in xrange(0, h):
        for x in xrange(0, w):
            pix1 = rgb_im1.getpixel((x, y))
            pix2 = rgb_im2.getpixel((x, y))
            if pix1 != pix2:
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
    if min_x > max_x or min_y > max_y:
        return None
    return (min_x, min_y, max_x, max_y)


#TEST FCT
def compress_rle(pixels):
    res = []
    count = 0
    val = None
    for pix in pixels:
        if val != pix:
            if count:
                res.append(count)
                res.append(val)
            val = pix
            count = 1
        else:
            count += 1
            if count >= 255:
                res.append(count)
                res.append(val)
                count = 0
    if count:
        res.append(count)
        res.append(val)

    return res

def print_cb(data):
    cmd, args = data
    print ">> %s" % (cmd)
    if len(args) > 0:
        print Tools.str_to_hex2(args)

def on_touch_up(client, data):
    global actual_img

    x, y = struct.unpack("HH", data[0:4])
    print ">> click %d:%d" % (x, y)
    if actual_img == "off.png":
        send_img(client, "on.png")
    else:
        send_img(client, "off.png")

def on_description(data, client):
    print ">> description %s" % (data,)
    send_img(client, "off.png")

host = "0.0.0.0"
port = 7654

server = Server(host, port)
server.add_command_listener("touch_up", on_touch_up)
server.add_listener("connect", on_connect)
server.add_listener("disconnect", on_disconnect)
server.start()

import Image

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "\nOVER"
finally:
    server.stop()
    server.join()

