# $Id: Video.py,v 1.9 2007/11/23 07:38:39 ping Exp $

from pygame import display, image, FULLSCREEN

def loadimage(i):
    return image.fromstring(i.pixels, (i.width, i.height), 'RGB')

class Video:
    def __init__(self, il):
        display.init()
        self.screen = display.set_mode((il.width, il.height), FULLSCREEN)
        self.backgrounds = [loadimage(l.background) for l in il.layouts]
        self.layouts = [l.slots for l in il.layouts]
        self.sprites = [loadimage(sprite) for sprite in il.sprites]
        self.goto(0)

    def goto(self, layout_i):
        self.slots = self.layouts[layout_i] 
        self.screen.blit(self.backgrounds[layout_i], (0, 0))

    def paste(self, sprite_i, slot_i):
        slot = self.slots[slot_i]
        self.screen.blit(self.sprites[sprite_i], (slot.left, slot.top))

    def locate(self, x, y):
        for i, slot in enumerate(self.slots):
            if slot.left <= x < slot.left + slot.width:
                if slot.top <= y < slot.top + slot.height:
                    return i
