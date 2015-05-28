import pygame
import socket
import threading
import select
import datetime

COMMANDS = {
    "ping" : 0x01,
    "pong" : 0x02,
    "who_are_you" : 0x03,
    "description" : 0x04,
    "set_pixel" : 0x05,
    "ack" : 0x06,
    "draw_pixels" : 0x07
}

def get_command_by_num(val):
    val = ord(val)
    return COMMANDS.keys()[COMMANDS.values().index(val)]

def cmd_who_are_you(cmd_id):
    resp_cmd = "description"
    args = "%s" % (("python_client", "1.0.0", []),)
    print "[%s] << %d %s %s" % (datetime.datetime.now(), ord(cmd_id), resp_cmd, args)
    res = "%s%s%s" % (cmd_id, chr(COMMANDS[resp_cmd]), args)
    return res

def cmd_draw_pixels(cmd_id, args):
    global screen

    resp_cmd = "ack"
    print "[%s] << %d %s" % (datetime.datetime.now(), ord(cmd_id), resp_cmd)

    print len(args)

    i = 0
    palet_size = ord(args[i + 0]) << 8 | ord(args[i + 1])
    i += 2
    palet = []
    for j in xrange(0, palet_size):
        r = ord(args[i + 0])
        g = ord(args[i + 1])
	b = ord(args[i + 2])
	palet.append((r, g, b))
	i += 3
    pixels_size = ord(args[i + 0]) << 8 | ord(args[i + 1])
    i += 2
    for j in xrange(0, pixels_size):
	index = ord(args[i + 0]) << 8 | ord(args[i + 1])
	color = palet(index)
	i += 2

	x = j % 240
	y = j / 240
	screen.set_at((x, y), color)

    pygame.display.flip()

    res = "%s%s" % (cmd_id, chr(COMMANDS[resp_cmd]))
    return res

def cmd_set_pixel(cmd_id, args):
    resp_cmd = "ack"
    print "[%s] << %d %s" % (datetime.datetime.now(), ord(cmd_id), resp_cmd)

    x = ord(args[0]) << 8 | ord(args[1])
    y = ord(args[2]) << 8 | ord(args[3])
    r = ord(args[4])
    g = ord(args[5])
    b = ord(args[6])

    print "set_pixel(%d, %d, (%d, %d, %d))" % (x, y, r, g, b)

    set_pixel(x, y, (r, g, b))

    res = "%s%s" % (cmd_id, chr(COMMANDS[resp_cmd]))
    return res

def cmd_ping(cmd_id):
    resp_cmd = "pong"
    print "[%s] << %d %s" % (datetime.datetime.now(), ord(cmd_id), resp_cmd)
    res = "%s%s" % (cmd_id, chr(COMMANDS[resp_cmd]))
    return res

def rep(code, sock):
    cmd_id = code[0]
    cmd = code[1]

    if ord(cmd) in COMMANDS.values():
        cmd_str = get_command_by_num(cmd)

        print "[%s] >> %d %s" % (datetime.datetime.now(), ord(cmd_id), cmd_str)
        res = None

        if cmd_str == "ping":
            res = cmd_ping(cmd_id)
        elif cmd_str == "who_are_you":
            res = cmd_who_are_you(cmd_id)
        elif cmd_str == "set_pixel":
            res = cmd_set_pixel(cmd_id, code[2:])
        elif cmd_str == "draw_pixels":
            res = cmd_draw_pixels(cmd_id, code[2:])

        if res:
            sock.sendall(res)

def set_pixel(x, y, color):
    global screen

    screen.set_at((x, y), color)
    pygame.display.flip()



width = 240
height = 320

pygame.init()
screen = pygame.display.set_mode((width, height))

master="127.0.0.1"
port=5432

POLL_ERR = (select.POLLERR | select.POLLHUP | select.POLLNVAL)
POLL_READ = (select.POLLIN | select.POLLPRI)
TIMEOUT = 100000

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
            msg = sock.recv(256)
            if not msg:
                print "over"
                run = False
                break
            rep(msg, sock)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
	    run = False
	    break


