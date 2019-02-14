# $Id: Video.py,v 1.5 2007/03/12 12:29:38 ping Exp $

import pygame

def make_image(im):
    return pygame.image.fromstring(im.pixels, (im.width, im.height), "RGB")

class Video:
    def __init__(self, video):
        size = [video.width, video.height]
        self.surface = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.layouts = video.layouts
        self.screens = [make_image(layout.screen) for layout in video.layouts]
        self.sprites = [make_image(sprite) for sprite in video.sprites]
        self.goto(0)

    def goto(self, layout_i):
        self.layout = self.layouts[layout_i]
        self.surface.blit(self.screens[layout_i], [0, 0])

    def paste(self, sprite_i, slot_i):
        slot = self.layout.slots[slot_i]
        self.surface.blit(self.sprites[sprite_i], [slot.left, slot.top])

    def locate(self, x, y):
        for [i, target] in enumerate(self.layout.targets):
            if target.left <= x and x < target.left + target.width:
                if target.top <= y and y < target.top + target.height:
                    return i
