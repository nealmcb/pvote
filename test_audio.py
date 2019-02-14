#!/usr/bin/python

import aifc, array, Audio
from pygame import display, event, KEYDOWN, USEREVENT

def read_aiff(filename):
    aiff = aifc.open(filename)
    samples = array.array('h', aiff.readframes(aiff.getnframes()))
    samples.byteswap()
    return samples.tostring()

class Struct:
    def __init__(self, **args):
        for name, value in args.items(): setattr(self, name, value)

audio = Struct(sample_rate=44100,
               clips=[Struct(samples=read_aiff('clips/%d.aiff' % i))
                      for i in range(1, 6)])
a = Audio.Audio(audio)
display.init()
display.set_mode((100, 100), 0)
while 1:
    display.update()
    e = event.wait()
    if e.type == KEYDOWN:
        if e.key == 27:
            break
        if chr(e.key) in '12345':
            a.play('12345'.index(chr(e.key)))
        if chr(e.key) in '67890':
            a.stop()
            a.play('67890'.index(chr(e.key)))
    if e.type == USEREVENT: 
        a.next()
