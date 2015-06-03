import Image
import struct
import Tools

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

def encode_img(img):
    w, h = img.size
    pixels = []
    palet = []

    for y in xrange(0, h):
        for x in xrange(0, w):
            r, g, b = img.getpixel((x, y))
            color = Tools.encode_color565(r, g, b)
            if color not in palet:
                palet.append(color)
            pixels.append(palet.index(color))

    #use RLE
    pixels = compress_rle(pixels)

    return (palet, pixels)

def send_img(client, x, y, w, palet, pixels):
    palet_size = len(palet)
    pixels_size = len(pixels)

    args = struct.pack("H%s" % ("H" * palet_size), palet_size, *palet)
    client.send_command("send_palet", args=args)

    args = struct.pack("HHHI%s" % ("B" * pixels_size), x, y, w, pixels_size, *pixels)
    client.send_command("draw_pixels", args=args)


g_img_buffer = {}
g_mask = None

def init(img_off, img_on, mask):
    global g_img_buffer
    global g_mask

    g_img_buffer["off"] = encode_img(img_off)
    g_img_buffer["on"] = encode_img(img_on)

    g_mask = mask


class CtrlButton:
    def __init__(self, client, x, y):
        self.client = client
        self.x = x
        self.y = y
        self.w, self.h = g_mask.size
        self.state = "off"

    def contains(self, x, y):
        if x >= self.x and y >= self.y and x <= self.x + self.w and y <= self.y + self.h:
            rel_x = x - self.x
            rel_y = y - self.y

            r, g, b = g_mask.getpixel((rel_x, rel_y))
            if r == 0 and g == 0 and b == 0:
                return True
        return False

    def onTouchUp(self, x, y):
        if self.contains(x, y):
            self.switch()
            return True
        return False

    def switch(self):
        if self.state == "on":
            self.state = "off"
        else:
            self.state = "on"
        self.show()

    def show(self):
        palet, pixels = g_img_buffer[self.state]
        send_img(self.client, self.x, self.y, self.w, palet, pixels)

