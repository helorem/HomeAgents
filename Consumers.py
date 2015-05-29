import struct
import datetime

import Tools

class BaseConsumer():
    def __init__(self, command, buffer_item_size = 1):
        self.buffer_item_size = buffer_item_size
        self.command = command
        self.cmd_num = Tools.COMMANDS[command]
        self.buffer_size = 0
        self.offset = 0
        self.overflow = ""
        self.cmd_id = 0
        self.output = ""
        self.header_readed = False
        self.callbacks = {
            "process_item" : [],
            "end" : []
        }

    def add_listener(self, event, callback, param=None):
        if event in self.callbacks:
            self.callbacks[event].append((callback, param))

    def get_output(self):
        return self.output

    def get_remaining(self):
        res = 0
        if self.buffer_size:
            res = self.buffer_size - self.offset
        return res

    def try_consume(self, data):
        res = False
        if self.get_remaining() > 0:
            self.consume(data)
            data = self.overflow
            res = True
        else:
            cmd_id, cmd = struct.unpack("BB", data[0:2])
            if cmd == self.cmd_num:
                self.cmd_id = cmd_id
                self.overflow = ""
                self.consume(data[2:])
                data = self.overflow
                res = True
        return (res, data)

    def consume(self, data):
        print self.command

        data = self.overflow + data
        self.overflow = ""

        res = True
        if not self.header_readed:
            res, data = self.read_header(data)
        if res:
            to_read = len(data)
            remain = self.get_remaining() * self.buffer_item_size
            if remain < to_read:
                to_read = remain

            if to_read < len(data):
                self.overflow = data[to_read:]

            if to_read:
                self.consume_process(data[0:to_read])

                if self.get_remaining() <= 0:
                    self.end()

    def read_header(self, data):
        #to override
        return (False, data)

    def consume_process(self, data):
        #to override
        pass

    def end(self):
        self.buffer_size = 0
        self.offset = 0
        self.header_readed = False
        for callback, param in self.callbacks["end"]:
            if param:
                callback(self, param)
            else:
                callback(self)

    def process_item(self, index, val):
        for callback, param in self.callbacks["process_item"]:
            if param:
                callback(self, index, val, param)
            else:
                callback(self, index, val)


class PixelConsumer(BaseConsumer):
    def __init__(self):
        BaseConsumer.__init__(self, "draw_pixels")
        self.palet = None
        self.add_listener("end", self.on_end)
        self.real_offset = 0 #used in case a compression

    def read_header(self, data):
        header_size = 13
        res = False
        if len(data) >= header_size:
            self.x, self.y, self.w, self.buffer_size, self.compression = struct.unpack("HHHIB", data[0:header_size])
            self.header_readed = True
            data = data[header_size:]
            res = True
        else:
            self.buffer_size = header_size
        return (res, data)

    def consume_process(self, data):
        args = struct.unpack("%s" % ("B" * len(data)), data)
        if self.compression & Tools.C_RLE:
            if len(args) % 2 != 0:
                self.overflow = data[-1:] + self.overflow
                args = args[0:-1]
            count = 0
            val = None
            for i in xrange(0, len(args)):
                if i % 2 == 0:
                    count = args[i]
                else:
                    val = args[i]
                    for j in xrange(0, count):
                        self.process_item(self.real_offset, val)
                        self.real_offset += 1
                self.offset += 1
        else:
            for item in args:
                self.process_item(self.offset, item)
                self.offset += 1

    def on_end(self, consumer):
        self.real_offset = 0
        resp_cmd = "ack"
        print "[%s] << %d %s" % (datetime.datetime.now(), consumer.cmd_id, resp_cmd)
        consumer.output = struct.pack("BB", consumer.cmd_id, Tools.COMMANDS[resp_cmd])


class PaletConsumer(BaseConsumer):
    def __init__(self):
        BaseConsumer.__init__(self, "send_palet", 3)
        self.palet = []
        self.add_listener("end", self.on_end)
        self.add_listener("process_item", self.on_process_item)

    def read_header(self, data):
        res = False
        header_size = 2
        if len(data) >= header_size:
            self.buffer_size, = struct.unpack("H", data[0:header_size])
            self.palet = self.buffer_size * [None]
            self.header_readed = True
            data = data[header_size:]
            res = True
        else:
            self.buffer_size = header_size
        return (res, data)

    def consume_process(self, data):
        nb_items = len(data) / 3
        count_elm = nb_items * 3
        if count_elm < len(data):
            self.overflow = data[count_elm:] + self.overflow
            data = data[0:count_elm]
        args = struct.unpack("%s" % ("3s" * nb_items), data)
        for item in args:
            r = ord(item[0])
            g = ord(item[1])
            b = ord(item[2])
            self.process_item(self.offset, (r, g, b))
            self.offset += 1

    def on_end(self, consumer):

        resp_cmd = "ack"
        print "[%s] << %d %s" % (datetime.datetime.now(), consumer.cmd_id, resp_cmd)
        consumer.output = struct.pack("BB", consumer.cmd_id, Tools.COMMANDS[resp_cmd])

    def on_process_item(self, consumer, index, val):
        self.palet[index] = val


