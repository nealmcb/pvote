"""Use this module to examine and modify ballot definition files.
Call load(filename) to read a ballot definition from a file.  The
result is a ballot object, which you can explore and change as a
Python data structure in memory.  If you want to write out a ballot
definition file, call save(filename, ballot).  Example:

>>> b = load('ballot')
>>> b
<Ballot: model, text, audio, video>
>>> b.model
<Model: groups[10], pages[17], timeout_ms=15000>
>>> b.model.timeout_ms = 20000
>>> b.model
<Model: groups[10], pages[17], timeout_ms=20000>
>>> save('ballot2', b)
>>> 
"""

import sha, struct

sha_type = type(sha.sha())

[OP_ADD, OP_REMOVE, OP_APPEND, OP_POP, OP_CLEAR] = range(5)
[SG_CLIP, SG_OPTION, SG_LIST_SELS, SG_COUNT_SELS, SG_MAX_SELS] = range(5)
[PR_GROUP_EMPTY, PR_GROUP_FULL, PR_OPTION_SELECTED] = range(3)

OP_NAMES = 'OP_ADD OP_REMOVE OP_APPEND OP_POP OP_CLEAR'.split()
SG_NAMES = 'SG_CLIP SG_OPTION SG_LIST_SELS SG_COUNT_SELS SG_MAX_SELS'.split()
PR_NAMES = 'PR_GROUP_EMPTY PR_GROUP_FULL PR_OPTION_SELECTED'.split()

def indent(text):
    return ('\n' + text).rstrip().replace('\n', '\n  ') + '\n'

def describe(*thing):
    if len(thing) == 1:
        thing = thing[0]
    if thing is None:
        return 'null'
    if isinstance(thing, int):
        return str(thing)
    if isinstance(thing, str):
        if len(thing) > 80:
            return '<long string>'
        return repr(thing)
    if isinstance(thing, list):
        items = [describe(item).rstrip() for item in thing
                 if item not in [None, []]]
        if len(', '.join(items)) < 70:
            return '[' + ', '.join(items) + ']'
        else:
            return '[' + indent(',\n'.join(items)) + ']'
    if hasattr(thing, '__members__'):
        items = ['%s=%s' % (name, describe(getattr(thing, name)).rstrip())
                 for name in thing.__members__
                 if getattr(thing, name) not in [None, []]]
        if len(', '.join(items)) < 70:
            return '{' + ', '.join(items) + '}'
        else:
            return '{' + indent(',\n'.join(items)) + '}'
    raise ValueError

def serialize(*thing):
    if len(thing) == 1:
        thing = thing[0]
    if thing is None:
        return '\xff\xff\xff\xff'
    if isinstance(thing, int):
        return struct.pack('>l', thing)
    if isinstance(thing, list):
        return (serialize(len(thing)) + 
                ''.join([serialize(item) for item in thing]))
    if isinstance(thing, str):
        return serialize(len(thing)) + thing
    if hasattr(thing, 'serialize'):
        return thing.serialize()
    if hasattr(thing, '__members__'):
        return ''.join([serialize(getattr(thing, name))
                        for name in thing.__members__])
    raise ValueError

def deserializer(Class):
    def deserialize(stream):
        thing = Class()
        thing.load(stream)
        return thing
    return deserialize

class Struct:
    def __init__(self, *args, **kw):
        for i, value in enumerate(args):
            self.__dict__[self.__members__[i]] = value
        for key, value in kw.items():
            self.__dict__[key] = value

    def __repr__(self):
        info = []
        type = self.__class__.__name__
        for name in self.__members__:
            if name not in self.__dict__:
                info.append(name + '=(missing)')
                continue
            value = self.__dict__[name]
            if not callable(value):
                if isinstance(value, list) or isinstance(value, str):
                    info.append(name + '[%d]' % len(value))
                elif isinstance(value, int) or value is None:
                    if (type + '.' + name == 'Step.op' and
                        0 <= value < len(OP_NAMES)):
                        info.append(name + '=' + OP_NAMES[value])
                    elif (type + '.' + name == 'Segment.type' and
                        0 <= value < len(SG_NAMES)):
                        info.append(name + '=' + SG_NAMES[value])
                    elif (type + '.' + name == 'Condition.predicate' and
                        0 <= value < len(PR_NAMES)):
                        info.append(name + '=' + PR_NAMES[value])
                    else:
                        info.append(name + '=' + str(value))
                else:
                    info.append(name)
        return '<%s: %s>' % (type, ', '.join(info))

    def save(self, filename):
        file = open(filename, 'wb')
        file.write(serialize(self))
        file.close()

class Ballot(Struct):
    def load(self, stream):
        assert stream.read(8) == "Pvote\x00\x01\x00"
        [self.stream, self.sha] = [stream, sha.sha()]
        self.model = deserializer(Model)(self)
        self.text = deserializer(Text)(self)
        self.audio = deserializer(Audio)(self)
        self.video = deserializer(Video)(self)
        assert self.sha.digest() == stream.read(20)

    def read(self, length):
        data = self.stream.read(length)
        self.sha.update(data)
        return data

    def save(self, filename):
        file = open(filename, 'wb')
        file.write('Pvote\x00\x01\x00')
        data = serialize(self)
        file.write(data)
        file.write(sha.sha(data).digest())
        file.close()

class Model(Struct):
    def load(self, stream):
        self.groups = get_list(stream, deserializer(Group))
        self.pages = get_list(stream, deserializer(Page))
        self.timeout_ms = get_int(stream, 0)

class Group(Struct):
    def load(self, stream):
        self.max_sels = get_int(stream, 0)
        self.max_chars = get_int(stream, 0)
        self.option_clips = get_int(stream, 0)
        self.options = get_list(stream, deserializer(Option))

class Option(Struct):
    def load(self, stream):
        self.sprite_i = get_int(stream, 0)
        self.clip_i = get_int(stream, 0)
        self.writein_group_i = get_int(stream, 1)

class Page(Struct):
    def load(self, stream):
        self.bindings = get_list(stream, deserializer(Binding))
        self.states = get_list(stream, deserializer(State))
        self.option_areas = get_list(stream, deserializer(OptionArea))
        self.counter_areas = get_list(stream, deserializer(CounterArea))
        self.review_areas = get_list(stream, deserializer(ReviewArea))

class State(Struct):
    def load(self, stream):
        self.sprite_i = get_int(stream, 0)
        self.segments = get_list(stream, deserializer(Segment))
        self.bindings = get_list(stream, deserializer(Binding))
        self.timeout_segments = get_list(stream, deserializer(Segment))
        self.timeout_page_i = get_int(stream, 1)
        self.timeout_state_i = get_int(stream, 0)

class OptionArea(Struct):
    def load(self, stream):
        self.group_i = get_int(stream, 0)
        self.option_i = get_int(stream, 0)

class CounterArea(Struct):
    def load(self, stream):
        self.group_i = get_int(stream, 0)
        self.sprite_i = get_int(stream, 0)

class ReviewArea(Struct):
    def load(self, stream):
        self.group_i = get_int(stream, 0)
        self.cursor_sprite_i = get_int(stream, 1)

class Binding(Struct):
    def load(self, stream):
        self.key = get_int(stream, 1)
        self.target_i = get_int(stream, 1)
        self.conditions = get_list(stream, deserializer(Condition))
        self.steps = get_list(stream, deserializer(Step))
        self.segments = get_list(stream, deserializer(Segment))
        self.next_page_i = get_int(stream, 1)
        self.next_state_i = get_int(stream, 0)

class Condition(Struct):
    def load(self, stream):
        self.predicate = get_enum(stream, 3)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)
        self.invert = get_enum(stream, 2)

class Step(Struct):
    def load(self, stream):
        self.op = get_enum(stream, 5)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)

class Segment(Struct):
    def load(self, stream):
        self.conditions = get_list(stream, deserializer(Condition))
        self.type = get_enum(stream, 5)
        self.clip_i = get_int(stream, 0)
        self.group_i = get_int(stream, 1)
        self.option_i = get_int(stream, 0)

class Text(Struct):
    def load(self, stream):
        self.groups = get_list(stream, deserializer(TextGroup))

class TextGroup(Struct):
    def load(self, stream):
        self.name = get_str(stream)
        self.writein = get_enum(stream, 2)
        self.options = get_list(stream, get_str)

class Audio(Struct):
    def load(self, stream):
        self.sample_rate = get_int(stream, 0)
        self.clips = get_list(stream, deserializer(Clip))

class Clip(Struct):
    def load(self, stream):
        self.samples = stream.read(get_int(stream, 0)*2)

    def serialize(self):
        return serialize(len(self.samples)/2) + self.samples

class Video(Struct):
    def load(self, stream):
        self.width = get_int(stream, 0)
        self.height = get_int(stream, 0)
        self.layouts = get_list(stream, deserializer(Layout))
        self.sprites = get_list(stream, deserializer(Image))

class Layout(Struct):
    def load(self, stream):
        self.screen = deserializer(Image)(stream)
        self.targets = get_list(stream, deserializer(Rect))
        self.slots = get_list(stream, deserializer(Rect))

class Image(Struct):
    def load(self, stream):
        self.width = get_int(stream, 0)
        self.height = get_int(stream, 0)
        self.pixels = stream.read(self.width*self.height*3)

    def serialize(self):
        return serialize(self.width) + serialize(self.height) + self.pixels

class Rect(Struct):
    def load(self, stream):
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

Ballot.__members__ = 'model text audio video'.split()
Model.__members__ = 'groups pages timeout_ms'.split()
Group.__members__ = 'max_sels max_chars option_clips options'.split()
Option.__members__ = 'sprite_i clip_i writein_group_i'.split()
Page.__members__ = 'bindings states option_areas counter_areas review_areas'.split()
State.__members__ = 'sprite_i segments bindings timeout_segments timeout_page_i timeout_state_i'.split()
OptionArea.__members__ = 'group_i option_i'.split()
CounterArea.__members__ = 'group_i sprite_i'.split()
ReviewArea.__members__ = 'group_i cursor_sprite_i'.split()
Binding.__members__ = 'key target_i conditions steps segments next_page_i next_state_i'.split()
Condition.__members__ = 'predicate group_i option_i invert'.split()
Step.__members__ = 'op group_i option_i'.split()
Segment.__members__ = 'conditions type clip_i group_i option_i'.split()
Text.__members__ = 'groups'.split()
TextGroup.__members__ = 'name writein options'.split()
Audio.__members__ = 'sample_rate clips'.split()
Clip.__members__ = 'samples'.split()
Video.__members__ = 'width height layouts sprites'.split()
Layout.__members__ = 'screen targets slots'.split()
Image.__members__ = 'width height pixels'.split()
Rect.__members__ = 'left top width height'.split()

def load(filename):
    """Read in a ballot definition file to get a ballot object."""
    ballot = Ballot()
    ballot.load(open(filename))
    return ballot

def save(filename, ballot):
    """Write out a ballot object to a ballot definition file."""
    ballot.save(filename)
