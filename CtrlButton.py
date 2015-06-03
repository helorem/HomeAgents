import Tools
import ICtrl

g_img_buffer = {}
g_mask = None

def init(img_off, img_on, mask):
    global g_img_buffer
    global g_mask

    g_img_buffer["off"] = Tools.encode_img(img_off)
    g_img_buffer["on"] = Tools.encode_img(img_on)

    g_mask = mask


class CtrlButton(ICtrl.ICtrl):
    def __init__(self, client, x, y):
        ICtrl.ICtrl.__init__(self, client, x, y, g_img_buffer, g_mask)
        self.state = "off"

    def on_touch_up(self, x, y):
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

