# $Id: Ballot.py,v 1.26 2007/03/28 22:36:28 ping Exp $

import sha

class Ballot:
    def __init__(self, stream):
        assert stream.read(8) == "Pvote\x00\x01\x00"
        [self.stream, self.sha] = [stream, sha.sha()]
        self.model = Model(self)
        self.text = Text(self)
        self.audio = Audio(self)
        self.video = Video(self)
        assert self.sha.digest() == stream.read(20)

    def read(self, length):
        data = self.stream.read(length)
        self.sha.update(data)
        return data

class Model:
    def __init__(self, stream):
        self.groups = get_list(stream, Group)
        self.pages = get_list(stream, Page)
        self.timeout_ms = get_int(stream, 0)

class Group:
    def __init__(self, stream):
        self.max_sels = get_int(stream, 0)
        self.max_chars = get_int(stream, 0)
        self.option_clips = get_int(stream, 0)
        self.options = get_list(stream, Option)

class Option:
    def __init__(self, stream):
        self.sprite_i = get_int(stream, 0)
        self.clip_i = get_int(stream, 0)
        self.writein_group_i = get_int(stream, 1)

class Page:
    def __init__(self, stream):
        self.bindings = get_list(stream, Binding)
        self.states = get_list(stream, State)
        self.option_areas = get_list(stream, OptionArea)
        self.counter_areas = get_list(stream, CounterArea)
        self.review_areas = get_list(stream, ReviewArea)

class State:
    def __init__(self, stream):
        self.sprite_i = get_int(stream, 0)
        self.segments = get_list(stream, Segment)
        self.bindings = get_list(stream, Binding)
        self.timeout_segments = get_list(stream, Segment)
        self.timeout_page_i = get_int(stream, 1)
        self.timeout_state_i = get_int(stream, 0)

class OptionArea:
    def __init__(self, stream):
        self.group_i = get_int(stream, 0)
        self.option_i = get_int(stream, 0)

class CounterArea:
    def __init__(self, stream):
        self.group_i = get_int(stream, 0)
        self.sprite_i = get_int(stream, 0)

class ReviewArea:
    def __init__(self, stream):
        self.group_i = get_int(stream, 0)
        self.cursor_sprite_i = get_int(stream, 1)

class Binding:
    def __init__(self, stream):
        self.key = get_int(stream, 1)
        self.target_i = get_int(stream, 1)
        self.conditions = get_list(stream, Condition)
        self.steps = get_list(stream, Step)
        self.segments = get_list(stream, Segment)
        self.next_page_i = get_int(stream, 1)
        self.next_state_i = get_int(stream, 0)

class Condition:
    def __init__(self, stream):
        self.predicate = get_enum(stream, 3)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)
        self.invert = get_enum(stream, 2)

class Step:
    def __init__(self, stream):
        self.op = get_enum(stream, 5)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)

class Segment:
    def __init__(self, stream):
        self.conditions = get_list(stream, Condition)
        self.type = get_enum(stream, 5)
        self.clip_i = get_int(stream, 0)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)

class Text:
    def __init__(self, stream):
        self.groups = get_list(stream, TextGroup)

class TextGroup:
    def __init__(self, stream):
        self.name = get_str(stream)
        self.writein = get_enum(stream, 2)
        self.options = get_list(stream, get_str)

class Audio:
    def __init__(self, stream):
        self.sample_rate = get_int(stream, 0)
        self.clips = get_list(stream, Clip)

class Clip:
    def __init__(self, stream):
        self.samples = stream.read(get_int(stream, 0)*2)

class Video:
    def __init__(self, stream):
        self.width = get_int(stream, 0)
        self.height = get_int(stream, 0)
        self.layouts = get_list(stream, Layout)
        self.sprites = get_list(stream, Image)

class Layout:
    def __init__(self, stream):
        self.screen = Image(stream)
        self.targets = get_list(stream, Rect)
        self.slots = get_list(stream, Rect)

class Image:
    def __init__(self, stream):
        self.width = get_int(stream, 0)
        self.height = get_int(stream, 0)
        self.pixels = stream.read(self.width*self.height*3)

class Rect:
    def __init__(self, stream):
        self.left = get_int(stream, 0)
        self.top = get_int(stream, 0)
        self.width = get_int(stream, 0)
        self.height = get_int(stream, 0)

def get_int(stream, allow_none):
    [a, b, c, d] = list(stream.read(4))
    if ord(a) < 128:
        return ord(a)*16777216 + ord(b)*65536 + ord(c)*256 + ord(d)
    assert allow_none and a + b + c + d == "\xff\xff\xff\xff"

def get_enum(stream, cardinality):
    value = get_int(stream, 0)
    assert value < cardinality
    return value

def get_str(stream):
    str = stream.read(get_int(stream, 0))
    for ch in list(str):
        assert 32 <= ord(ch) <= 125
    return str

def get_list(stream, Class):
    return [Class(stream) for i in range(get_int(stream, 0))]
