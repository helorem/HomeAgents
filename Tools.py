COMMANDS = {
    "ping" : 0x01,
    "pong" : 0x02,
    "who_are_you" : 0x03,
    "description" : 0x04,
    "ack" : 0x05,
    "draw_pixels" : 0x06,
    "send_palet" : 0x07,
    "touch_down" : 0x08,
    "touch_up" : 0x09,
    "touch_move" : 0x0A,
    "fill_color" : 0x0B,
    "repeat_pixels_x" : 0x0C
}

def encode_img(img):
    w, h = img.size
    pixels = []
    palet = []

    for y in xrange(0, h):
        for x in xrange(0, w):
            r, g, b = img.getpixel((x, y))
            color = encode_color565(r, g, b)
            if color not in palet:
                palet.append(color)
            pixels.append(palet.index(color))

    #use RLE
    pixels = compress_rle(pixels)

    return (palet, pixels)

def compress_rle(data):
    res = []
    count = 0
    val = None
    for item in data:
        if val != item:
            if count:
                res.append(count)
                res.append(val)
            val = item
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

def encode_color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);

def str_to_hex2(val):
    res = []
    line = []
    line2 = []
    j = 0
    l = 0
    for i in val:
        ch = i
        if ord(ch) < 0x20 or ord(ch) > 0x7E:
            ch = "."
        line2.append(ch)
        hex_val = hex(ord(i)).replace("0x", "").zfill(2).upper()
        line.append(hex_val + " ")
        j += 1
        if j >= 32:
            res.append("%.3d  " % l)
            res += line
            res.append("  ")
            res += line2
            res.append("\n")
            line = []
            line2 = []
            j = 0
            l += 32
        elif j % 8 == 0:
            line2.append("  ")
            line.append(" ")
    if line:
        for k in xrange(j, 32):
            line2.append(" ")
            line.append("   ")
            if k % 8 == 0 and k < 32:
                line2.append("  ")
                line.append(" ")
        res.append("%.3d  " % l)
        res += line
        res.append("  ")
        res += line2
        res.append("\n")
    return "".join(res)

def str_to_hex(val):
    res = []
    for i in val:
        res.append(hex(ord(i)).replace("0x", "").zfill(2).upper())
    return " ".join(res)


