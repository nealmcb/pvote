# $Id: Audio.py,v 1.7 2007/03/28 00:53:43 ping Exp $

import pygame
AUDIO_DONE = pygame.USEREVENT

class Audio:
    def __init__(self, audio):
        rate = audio.sample_rate
        pygame.mixer.init(rate, -16, 0)
        self.clips = [make_sound(rate, clip.samples) for clip in audio.clips]
        [self.queue, self.playing] = [[], 0]

    def play(self, clip_i):
        self.queue.append(clip_i)
        if not self.playing:
            self.next()

    def next(self):
        self.playing = len(self.queue)
        if len(self.queue):
            self.clips[self.queue.pop(0)].play().set_endevent(AUDIO_DONE)

    def stop(self):
        self.queue = []
        pygame.mixer.stop()

def make_sound(rate, data):
    [comp_channels, sample_size] = ["\x01\x00\x01\x00", "\x02\x00\x10\x00"]
    fmt = comp_channels + put_int(rate) + put_int(rate*2) + sample_size
    file = chunk("RIFF", "WAVE" + chunk("fmt ", fmt) + chunk("data", data))
    return pygame.mixer.Sound(Buffer(file))

def chunk(type, contents):
    return type + put_int(len(contents)) + contents

def put_int(n):
    [a, b, c, d] = [n/16777216, n/65536, n/256, n]
    return chr(d % 256) + chr(c % 256) + chr(b % 256) + chr(a % 256)

class Buffer:
    def __init__(self, data):
        [self.data, self.pos] = [data, 0]

    def read(self, length):
        self.pos = self.pos + length
        return self.data[self.pos - length:self.pos]
