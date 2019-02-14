# $Id: Ballot.py,v 1.20 2007/02/13 23:22:42 ping Exp $

class Ballot:
    def __init__(self, filename, rotate=0):
        self.data = open(filename).read()
        stream = open(filename)
        self.model = model = Model(stream)
        self.video = Video(stream)
        self.audio = Audio(stream)

        area_option_is = [[] for group_i in range(len(model.groups))]
        for page in model.pages:
            for area in page.option_areas:
                area_option_is[area.group_i].append(area.option_i)
        group_option_is = []
        for group_i, group in enumerate(model.groups):
            option_is = []
            for option_i in range(len(group.options)):
                if option_i not in area_option_is[group_i]:
                    option_is.append(option_i)
            if rotate:
                random.shuffle(option_is)
            group_option_is.append(option_is)
        for page in model.pages:
            for area in page.option_areas:
                if area.option_i == -1:
                    area.option_i = group_option_is[area.group_i].pop(0)
                area.option = model.groups[area.group_i].options[area.option_i]

class Model:
    def __init__(self, stream):
        self.groups = getlist(stream, Group)
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

class Group:
    def __init__(self, stream):
        self.type = getint(stream)
        self.max_sels = getint(stream)
        self.max_chars = getint(stream)
        self.options = getlist(stream, Option)

class Option:
    def __init__(self, stream):
        self.unsel_sprite_i = getint(stream)
        self.sel_sprite_i = getint(stream)
        self.clip_i = getint(stream)
        self.writein_group_i = getint(stream)

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
        self.next_page_i = getint(stream)
        self.next_state_i = getint(stream)
        self.clear_group_is = getlist(stream, getint)
        self.option_op = getint(stream)
        self.option_refs = getlist(stream, OptionRef)
        self.option_area_op = getint(stream)
        self.option_area_i = getint(stream)
        self.default_feedback = Sequence(stream)
        self.toggle_off_feedback = Sequence(stream)
        self.no_effect_feedback = Sequence(stream)
        self.full_feedback = Sequence(stream)
        self.empty_feedback = Sequence(stream)

class OptionRef:
    def __init__(self, stream):
        self.group_i = getint(stream)
        self.option_i = getint(stream)

class State:
    def __init__(self, stream):
        self.sprite_i = getint(stream)
        self.option_area_i = getint(stream)
        self.entry_feedback = Sequence(stream)
        self.key_bindings = getlist(stream, KeyBinding)
        self.timeout_page_i = getint(stream)
        self.timeout_state_i = getint(stream)
        self.timeout_feedback = Sequence(stream)

class OptionArea:
    def __init__(self, stream):
        self.group_i = getint(stream)
        self.option_i = getint(stream)

class CounterArea:
    def __init__(self, stream):
        self.group_i = getint(stream)
        self.sprite_i = getint(stream)

class ReviewArea:
    def __init__(self, stream):
        self.group_i = getint(stream)
        self.cursor_sprite_i = getint(stream)

class Sequence:
    def __init__(self, stream):
        self.segments = getlist(stream, Segment)

class Segment:
    def __init__(self, stream):
        self.type = getint(stream)
        self.clip_i = getint(stream)
        self.group_i = getint(stream)
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

class Image:
    def __init__(self, stream):
        self.size = self.width, self.height = getint(stream), getint(stream)
        self.pixels = stream.read(self.width * self.height * 3)

class Rect:
    def __init__(self, stream):
        self.left = getint(stream)
        self.top = getint(stream)
        self.width = getint(stream)
        self.height = getint(stream)

def getlist(stream, Class):
    return [Class(stream) for i in range(getint(stream))]

def getint(stream):
    import struct
    return struct.unpack('>l', stream.read(4))[0]
