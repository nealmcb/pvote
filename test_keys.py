#!/usr/bin/python

from pygame import display, event, MOUSEBUTTONDOWN, KEYDOWN

display.init()
display.set_mode((100, 100), 0)
while 1:
    display.update()
    e = event.wait()
    if e.type == KEYDOWN:
        print e.key
        if e.key == 27:
            break
