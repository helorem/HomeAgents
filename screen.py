import pygame
import socket
import threading
import select
import datetime
import struct

import Tools
import Consumers

CONSUMERS = []

def on_cmd_ping(consumer):
    resp_cmd = "pong"
    print "[%s] << %d %s" % (datetime.datetime.now(), consumer.cmd_id, resp_cmd)
    consumer.output = struct.pack("BB", consumer.cmd_id, Tools.COMMANDS[resp_cmd])

def on_cmd_who_are_you(consumer):
    resp_cmd = "description"
    args = "%s" % (("python_client", "1.0.0", []),)
    print "[%s] << %d %s" % (datetime.datetime.now(), consumer.cmd_id, resp_cmd)
    consumer.output = struct.pack("BBB%ds" % (len(args)), consumer.cmd_id, Tools.COMMANDS[resp_cmd], len(args), args)

def rep(data, sock):
    global CONSUMERS

    res = True
    while res and len(data) >= 2:
        res = False
        for cons in CONSUMERS:
            res, data = cons.try_consume(data)
            if res:
                if cons.get_output():
                    sock.sendall(cons.get_output())
                break

def on_new_palet(consumer, param):
    pixel_consumer = param
    pixel_consumer.palet = consumer.palet

def on_draw_pixel(consumer, index, val):
    global screen

    if consumer.palet:
        x = consumer.x + (index % consumer.w)
        y = consumer.y + (index / consumer.w)
        color = consumer.palet[val]
        screen.set_at((x, y), color)

def on_draw_end(consumer):
    pygame.display.flip()


obj = Consumers.PixelConsumer()
obj.add_listener("process_item", on_draw_pixel)
obj.add_listener("end", on_draw_end)
CONSUMERS.append(obj)
pixel_consumer = obj

obj = Consumers.PaletConsumer()
obj.add_listener("end", on_new_palet, pixel_consumer)
CONSUMERS.append(obj)

obj = Consumers.BaseConsumer("ping")
obj.add_listener("end", on_cmd_ping)
CONSUMERS.append(obj)

obj = Consumers.BaseConsumer("who_are_you")
obj.add_listener("end", on_cmd_who_are_you)
CONSUMERS.append(obj)


width = 240
height = 320

pygame.init()
screen = pygame.display.set_mode((width, height))

master="127.0.0.1"
port=7654

POLL_ERR = (select.POLLERR | select.POLLHUP | select.POLLNVAL)
POLL_READ = (select.POLLIN | select.POLLPRI)
TIMEOUT = 0.0001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((master, port))
sock.setblocking(0)

print "connected"

poller = select.poll()
poller.register(sock, POLL_READ | POLL_ERR)
run = True

while run:
    for fd, flag in poller.poll(TIMEOUT):
        #print fd, flag
        if flag & POLL_ERR:
            print "sock error"
            run = False
            break
        if flag & POLL_READ:
            msg = sock.recv(512)
            print Tools.str_to_hex2(msg)
            if not msg:
                print "over"
                run = False
                break
            rep(msg, sock)
    if run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                resp_cmd = "click"
                #TODO improve
                cmd_id = 50
                print "[%s] << %d %s" % (datetime.datetime.now(), cmd_id, resp_cmd)
                output = struct.pack("BBHH", cmd_id, Tools.COMMANDS[resp_cmd], x, y)
                sock.sendall(output)

