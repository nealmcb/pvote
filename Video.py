# $Id: Video.py,v 1.4 2007/01/29 20:17:49 ping Exp $

from pygame import display, image, FULLSCREEN

def loadimage(i):
    return image.fromstring(i.pixels, (i.width, i.height), 'RGB')

class Video:
    def __init__(self, video):
        display.init()
        self.screen = display.set_mode(video.size, FULLSCREEN)
        self.video = video
        self.images = [loadimage(l.screen) for l in video.layouts]
        self.sprites = [loadimage(sprite) for sprite in video.sprites]
        self.goto(0)

    def goto(self, layout_i):
        self.layout = self.video.layouts[layout_i]
        self.screen.blit(self.images[layout_i], (0, 0))

    def paste(self, sprite_i, slot_i):
        slot = self.layout.slots[slot_i]
        self.screen.blit(self.sprites[sprite_i], (slot.left, slot.top))

    def locate(self, x, y):
        for i, target in enumerate(self.layout.targets):
            if target.left <= x < target.left + target.width:
                if target.top <= y < target.top + target.height:
                    return i
