# $Id: Ballot.py,v 1.16 2007/01/30 07:26:43 ping Exp $

class Ballot:
    def __init__(self, filename, rotate=0):
        self.data = open(filename).read()
        stream = open(filename)
        self.model = Model(stream)
        self.video = Video(stream)
        self.audio = Audio(stream)

        rotated = []
        for contest in self.model.contests:
            rotated.append(range(len(contest.options)))
            if rotate:
                import random
                random.shuffle(rotated[-1])
        for page in self.model.pages:
            for area in page.option_areas:
                area.option_i = i = rotated[area.contest_i].pop(0)
                area.option = self.model.contests[area.contest_i].options[i]

class Model:
    def __init__(self, stream):
        self.contests = getlist(stream, Contest)
        self.pages = getlist(stream, Page)
        self.timeout_milliseconds = getint(stream)

class Video:
    def __init__(self, stream):
        self.size = self.width, self.height = getint(stream), getint(stream)
        self.layouts = getlist(stream, Layout)
        self.sprites = getlist(stream, Image)

class Audio:
    def __init__(self, stream):
        self.sample_rate = getint(stream)
        self.clips = getlist(stream, Clip)

class Contest:
    def __init__(self, stream):
        self.max_sels = getint(stream)
        self.options = getlist(stream, Option)

class Option:
    def __init__(self, stream):
        self.unsel_sprite_i = getint(stream)
        self.sel_sprite_i = getint(stream)
        self.clip_i = getint(stream)

class Page:
    def __init__(self, stream):
        self.key_bindings = getlist(stream, KeyBinding)
        self.target_bindings = getlist(stream, TargetBinding)
        self.states = getlist(stream, State)
        self.option_areas = getlist(stream, OptionArea)
        self.counter_areas = getlist(stream, CounterArea)
        self.review_areas = getlist(stream, ReviewArea)

class KeyBinding:
    def __init__(self, stream):
        self.key = getint(stream)
        self.action = Action(stream)

class TargetBinding:
    def __init__(self, stream):
        self.action = Action(stream)

class Action:
    def __init__(self, stream):
        self.clear_contest_is = getlist(stream, getint)
        self.select_option_refs = getlist(stream, OptionRef)
        self.option_area_i = getint(stream)
        self.option_area_action = getint(stream)
        self.default_sequence = Sequence(stream)
        self.no_change_sequence = Sequence(stream)
        self.overvote_sequence = Sequence(stream)
        self.toggle_deselect_sequence = Sequence(stream)
        self.next_page_i = getint(stream)
        self.next_state_i = getint(stream)

class OptionRef:
    def __init__(self, stream):
        self.contest_i = getint(stream)
        self.option_i = getint(stream)

class State:
    def __init__(self, stream):
        self.sprite_i = getint(stream)
        self.option_area_i = getint(stream)
        self.entry_sequence = Sequence(stream)
        self.key_bindings = getlist(stream, KeyBinding)
        self.timeout_sequence = Sequence(stream)
        self.timeout_page_i = getint(stream)
        self.timeout_state_i = getint(stream)

class OptionArea:
    def __init__(self, stream):
        self.contest_i = getint(stream)

class CounterArea:
    def __init__(self, stream):
        self.contest_i = getint(stream)
        self.number_sprite_i = getint(stream)

class ReviewArea:
    def __init__(self, stream):
        self.contest_i = getint(stream)

class Sequence:
    def __init__(self, stream):
        self.segments = getlist(stream, Segment)

class Segment:
    def __init__(self, stream):
        self.type = getint(stream)
        self.clip_i = getint(stream)
        self.contest_i = getint(stream)
        self.option_i = getint(stream)

class Clip:
    def __init__(self, stream):
        self.length = getint(stream)
        self.samples = stream.read(self.length * 2)

class Layout:
    def __init__(self, stream):
        self.screen = Image(stream)
        self.targets = getlist(stream, Rect)
        self.slots = getlist(stream, Rect)

class Rect:
    def __init__(self, stream):
        self.left = getint(stream)
        self.top = getint(stream)
        self.width = getint(stream)
        self.height = getint(stream)

class Image:
    def __init__(self, stream):
        self.size = self.width, self.height = getint(stream), getint(stream)
        self.pixels = stream.read(self.width * self.height * 3)

def getlist(stream, Class):
    return [Class(stream) for i in range(getint(stream))]

def getint(stream):
    import struct
    return struct.unpack('>l', stream.read(4))[0]
