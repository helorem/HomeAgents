#!/usr/bin/python

import socket
import threading
import select
import datetime

COMMANDS = {
    "ping" : 0x01,
    "pong" : 0x02,
    "who_are_you" : 0x03,
    "description" : 0x04
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

        if res:
            sock.sendall(res)

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

