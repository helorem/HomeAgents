import Image
import struct
import Tools

class ICtrl:
    def __init__(self, client, x, y, img_buffer, mask):
        self.client = client
        self.x = x
        self.y = y
        self.w, self.h = mask.size
        self.img_buffer = img_buffer
        self.mask = mask

    def on_touch_down(self, x, y):
        return False

    def on_touch_up(self, x, y):
        return False

    def on_touch_move(self, x, y):
        return False

    def contains(self, x, y):
        if x >= self.x and y >= self.y and x <= self.x + self.w and y <= self.y + self.h:
            rel_x = x - self.x
            rel_y = y - self.y

            r, g, b = self.mask.getpixel((rel_x, rel_y))
            if r == 0 and g == 0 and b == 0:
                return True
        return False

    def show(self):
        palet, pixels = self.img_buffer[self.state]
        palet_size = len(palet)
        pixels_size = len(pixels)

        args = struct.pack("H%s" % ("H" * palet_size), palet_size, *palet)
        self.client.send_command("send_palet", args=args)

        args = struct.pack("HHHI%s" % ("B" * pixels_size), self.x, self.y, self.w, pixels_size, *pixels)
        self.client.send_command("draw_pixels", args=args)

