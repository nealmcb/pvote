# $Id: Audio.py,v 1.5 2007/01/30 05:05:53 ping Exp $

from pygame import mixer, USEREVENT
import StringIO, struct

def chunk(type, contents):
    return type + struct.pack('<L', len(contents)) + contents

def make_sound(rate, samples):
    format = chunk('fmt ', struct.pack('<hHLLHH', 1, 1, rate, rate*2, 2, 16))
    buffer = StringIO.StringIO()
    buffer.write(chunk('RIFF', 'WAVE' + format + chunk('data', samples)))
    buffer.seek(0)
    return mixer.Sound(buffer)

class Audio:
    def __init__(self, audio):
        rate = audio.sample_rate
        mixer.init(rate, -16, 0)
        self.clips = [make_sound(rate, clip.samples) for clip in audio.clips]
        self.pending = []
        self.playing = 0

    def play(self, clip_i):
        self.pending.append(clip_i)
        if not self.playing:
            self.next()

    def next(self):
        self.playing = len(self.pending) > 0
        if self.pending:
            self.clips[self.pending.pop(0)].play().set_endevent(USEREVENT)
        return self.playing

    def stop(self):
        self.pending = []
        mixer.stop()
