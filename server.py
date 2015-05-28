#!/usr/bin/python

import socket
import threading
import time
import Queue

BUFFER_SIZE = 256
HEARTBEAT = 5

COMMANDS = {
    "ping" : 0x01,
    "pong" : 0x02,
    "who_are_you" : 0x03,
    "description" : 0x04,
    "set_pixel" : 0x05,
    "ack" : 0x06,
    "draw_pixels" : 0x07
}

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

        self.sock.settimeout(1.0)

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
                if data:
                    self.on_receive("".join(data))
                if not self.write_queue.empty():
                    data = self.write_queue.get()
                    """
                    if len(data) > 2:
                        print ">> %d %s %s" % (ord(data[0]), self.__get_command_by_num(data[1]), data[2:])
                    else:
                        print ">> %d %s" % (ord(data[0]), self.__get_command_by_num(data[1]))
                    """
                    self.sock.sendall(data)
                else:
                    self.check_alive()
        finally:
            self.sock.close()

    def __get_command_by_num(self, val):
        val = ord(val)
        return COMMANDS.keys()[COMMANDS.values().index(val)]

    def stop(self):
        self.is_running = False

    def write(self, data):
        self.write_queue.put(data)

    def on_receive(self, data):
        cmd_id = ord(data[0])
        cmd = self.__get_command_by_num(data[1])
        args = None
        if len(data) > 1:
            args = data[2:]

        """
        if args:
            print ">> %d %s %s" % (cmd_id, cmd, args)
        else:
            print ">> %d %s" % (cmd_id, cmd)
        """

        self.last_heartbeat = time.time()

        if cmd_id in self.commands:
            callback, callback_params = self.commands[cmd_id]
            if callback:
                if callback_params:
                    callback((cmd, args), callback_params)
                else:
                    callback((cmd, args))
            del self.commands[cmd_id]

    def on_disconnected(self):
        self.server.remove_client(self.id)

    def check_alive(self):
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
        if command not in COMMANDS:
            #TODO error
            print "Command '%s' is invalid" % command
            return
        cmd_id = self.__get_cmd_id()
        if cmd_id <= 0:
            #TODO error
            print "Command list is full !"
            return

        self.commands[cmd_id] = (callback, callback_params)
        if args:
            to_write = "%s%s%s" % (chr(cmd_id), chr(COMMANDS[command]), args)
        else:
            to_write = "%s%s" % (chr(cmd_id), chr(COMMANDS[command]))
        self.write(to_write)


class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = False
        self.clients = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)

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

    def stop(self):
        self.is_running = False

    def send_command(self, id, cmd, callback):
        if id in self.clients:
	    args = None
	    if " " in cmd:
	        cmd, args = cmd.split(" ", 1)
		if cmd == "set_pixel":
		    tmp = args.split(" ")
		    args = "%s%s" % (chr(int(tmp[0]) >> 8), chr(int(tmp[0]) & 0xFF))
		    args += "%s%s" % (chr(int(tmp[1]) >> 8), chr(int(tmp[1]) & 0xFF))
		    args += "%s" % (chr(int(tmp[2]) & 0xFF))
		    args += "%s" % (chr(int(tmp[3]) & 0xFF))
		    args += "%s" % (chr(int(tmp[4]) & 0xFF))
            self.clients[id].send_command(cmd, args=args, callback=callback)

def to_short(val):
    return "%s%s" % (chr((int(val) >> 8) & 0xFF) , chr(int(val) & 0xFF))

def send_img(server, id, filename):
    im = Image.open("tst.png")
    rgb_im = im.convert("RGB")
    w, h = im.size
    pixels = []
    palet = []

    for x in xrange(0, w):
	for y in xrange(0, h):
            r, g, b = rgb_im.getpixel((x, y))
	    color = "%s%s%s" % ((chr(r & 0xFF)), (chr(g & 0xFF)),(chr(b & 0xFF)))
	    if color not in palet:
                palet.append(color)
            pixels.append(palet.index(color))
    print "Nb colors : %d" % len(palet)

    args = []
    args.append(to_short(len(palet)))
    args += palet
    args.append(to_short(len(pixels)))
    for pixel in pixels:
        args.append(to_short(pixel))

    args = "".join(args)

    print "len args =", len(args)

    server.clients[id].send_command("draw_pixels", args=args, callback=print_cb)
	

def print_cb(data):
    cmd, args = data
    print ">> %s %s" % (cmd, args)

host = "0.0.0.0"
port = 5432

server = Server(host, port)
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
		if data == "draw_pixels":
		    send_img(server, id, "tst.png")
		else:
                    server.send_command(id, data, print_cb)
except KeyboardInterrupt:
    print "\nOVER"
finally:
    server.stop()
    server.join()

