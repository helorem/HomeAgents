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
        cmd_id, cmd = struct.unpack("BB", data[0:2])
        cmd = self.__get_command_by_num(cmd)
        data = data[2:]

        self.last_heartbeat = time.time()

        self.server.call_listeners(self, cmd, data)

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

    def send_command(self, command, args=None, callback=None, callback_params=None):
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

        self.commands[cmd_id] = (callback, callback_params)
        if args:
            if args:
                to_write = struct.pack("BB", cmd_id, Tools.COMMANDS[command])
                to_write = "%s%s" % (to_write, args)
                print Tools.str_to_hex2(to_write)
                print ""
                self.write(to_write)
        else:
            to_write = struct.pack("BB", cmd_id, Tools.COMMANDS[command])
            self.write(to_write)


class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = False
        self.clients = {}
        self.listeners = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)

    def add_listener(self, command, callback, params=None):
        if not command in self.listeners:
            self.listeners[command] = []
        self.listeners[command].append((callback, params))

    def call_listeners(self, client, command, data):
        if command in self.listeners:
            for callback, params in self.listeners[command]:
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
                    print "Client %s connected" % id
                    client = Client(clientsock, id, self)
                    self.clients[id] = client
                    client.start()
                    #TODO remove ############################
                    time.sleep(1)
                    send_img(self, id, "off.png")
                    ########################################
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
            client.stop()
            del self.clients[id]
            print "Client %s disconnected" % id
            #TODO remove #############
            global actual_img
            actual_img = None

    def stop(self):
        self.is_running = False

    def send_command(self, id, cmd, callback):
        if id in self.clients:
            args = None
            if " " in cmd:
                cmd, args = cmd.split(" ", 1)
            self.clients[id].send_command(cmd, args=args, callback=callback)

#TEST FCT
actual_img = None
def send_img(server, id, filename):
    global actual_img

    print "send_img", filename

    im = Image.open(filename)
    rgb_im = im.convert("RGB")
    w, h = im.size

    rect = (0, 0, w, h)
    if actual_img:
        rect = img_diff(filename, actual_img)
    actual_img = filename
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]

    print "rect:", rect, w, h
    rgb_im = rgb_im.crop(rect)

    pixels = []
    palet = []

    for y in xrange(0, h):
        for x in xrange(0, w):
            r, g, b = rgb_im.getpixel((x, y))
            color = struct.pack("BBB", (r & 0xFF), (g & 0xFF), (b & 0xFF))
            if color not in palet:
                palet.append(color)
            pixels.append(palet.index(color))

    palet_size = len(palet)
    pixels_size = len(pixels)

    args = struct.pack("H%s" % ("3s" * palet_size), palet_size, *palet)
    print "len palet : %d" % palet_size
    print "len args : %d" % len(args)

    server.clients[id].send_command("send_palet", args=args, callback=print_cb)

    compress = Tools.C_NONE

    #use RLE
    compress = Tools.C_RLE
    pixels = compress_rle(pixels)
    pixels_size = len(pixels)

    args = struct.pack("HHHIB%s" % ("B" * pixels_size), rect[0], rect[1], w, pixels_size, compress, *pixels)
    print "len pixels : %d" % pixels_size
    print "len args : %d" % len(args)
    print "size :", pixels_size, w * h

    server.clients[id].send_command("draw_pixels", args=args, callback=print_cb)

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
    print ">> %s %s" % (cmd, args)

def on_click(client, data):
    global actual_img

    x, y = struct.unpack("HH", data[0:4])
    print ">> click %d:%d" % (x, y)
    if actual_img == "off.png":
        send_img(client.server, client.id, "on.png")
    else:
        send_img(client.server, client.id, "off.png")

host = "0.0.0.0"
port = 7654

server = Server(host, port)
server.add_listener("click", on_click)
server.start()

import Image

try:
    while True:
        data = raw_input()
        if data:
            if data == "help":
                print "[client ip] [command]"
            else:
                id, data = data.split(" ", 1)
                server.send_command(id, data, print_cb)
except KeyboardInterrupt:
    print "\nOVER"
finally:
    server.stop()
    server.join()

