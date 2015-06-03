import Tools
import ICtrl
import struct

g_img_buffer = {}
g_rel_pos = {}

def init(img_btn, img_bar, mask):
    global g_img_buffer

    g_img_buffer["btn"] = Tools.encode_img(img_btn)
    g_img_buffer["bar"] = Tools.encode_img(img_bar)

    w_bar, h_bar = img_bar.size
    w_btn, h_btn = img_btn.size
    g_rel_pos["btn"] = (0, 0, w_btn, h_btn)
    g_rel_pos["bar"] = (0, (h_btn / 2) - (h_bar / 2), w_bar, h_bar)


class CtrlSlide(ICtrl.ICtrl):
    def __init__(self, client, x, y, w):
        ICtrl.ICtrl.__init__(self, client, x, y)
        self.w = w
        self.h = g_rel_pos["btn"][3]
        self.val = 50

    def contains(self, x, y):
        if x >= self.x and y >= self.y and x <= self.x + self.w and y <= self.y + self.h:
            return True
        return False

    def on_touch_move(self, x, y):
        return self.on_touch_up(x, y)

    def on_touch_up(self, x, y):
        if self.contains(x, y):
            btn_w = g_rel_pos["btn"][2]
            self.val = ((x - self.x - btn_w / 2) * 100) / (self.w - btn_w)
            if self.val > 100:
                self.val = 100;
            elif self.val < 0:
                self.val = 0
            self.show()
            return True
        return False

    def show(self):
        palet, pixels = g_img_buffer["bar"]
        rel_x, rel_y, _item_w, _item_h = g_rel_pos["bar"]
        palet_size = len(palet)
        pixels_size = len(pixels)

        args = struct.pack("H%s" % ("H" * palet_size), palet_size, *palet)
        self.client.send_command("send_palet", args=args)

        args = struct.pack("HHHI%s" % ("B" * pixels_size), self.x + rel_x, self.y + rel_y, self.w, pixels_size, *pixels)
        self.client.send_command("repeat_pixels_x", args=args)

        palet, pixels = g_img_buffer["btn"]
        rel_x, rel_y, item_w, _item_h = g_rel_pos["btn"]
        rel_x = ((self.val * (self.w - item_w)) / 100)

        palet_size = len(palet)
        pixels_size = len(pixels)

        args = struct.pack("H%s" % ("H" * palet_size), palet_size, *palet)
        self.client.send_command("send_palet", args=args)

        args = struct.pack("HHHI%s" % ("B" * pixels_size), self.x + rel_x, self.y + rel_y, item_w, pixels_size, *pixels)
        self.client.send_command("draw_pixels", args=args)

