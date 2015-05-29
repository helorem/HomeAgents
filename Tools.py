COMMANDS = {
    "ping" : 0x01,
    "pong" : 0x02,
    "who_are_you" : 0x03,
    "description" : 0x04,
    "ack" : 0x05,
    "draw_pixels" : 0x06,
    "send_palet" : 0x07,
    "click" : 0x08
}

C_NONE = 0x00
C_RLE = 0x01

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


