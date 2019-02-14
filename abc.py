from layout import *
from styles import *

def layout_charset():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'  "
    w, h = char_w*len(chars), char_h
    box = Box()
    box.add(Rect(width=w, height=h, fill=option_selected_bg, stroke=None))
    x = 0
    for char in chars[:-1]:
        box.add(WriteinText(char), (x + char_w/2, char_y), 'cx')
        x += char_w
    box.add(Rect(width=char_w-2, height=char_h-6,
                 fill=WHITE, stroke=BLACK, weight=2),
            (x + char_w/2, char_h/2), 'cm')
    box.write('charset.png', width=w, height=h)

if __name__ == '__main__':
    layout_charset()
