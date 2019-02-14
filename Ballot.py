# $Id: Ballot.py,v 1.15 2007/11/23 07:38:39 ping Exp $

class Ballot:
    def __init__(self, filename):
        self.data = open(filename).read()
        stream = open(filename)
        self.sprite_n = subpage_n = 0
        self.model = m = Model(self, stream)
        self.imagelib = il = Imagelib(self, stream)
        assert stream.read(1) == ''

        assert m.pages and m.contests
        assert len(m.pages) + len(m.subpages) == len(il.layouts)
        assert len(il.sprites) == self.sprite_n

        items = [[] for c in m.contests]
        chars = [[] for c in m.contests]
        for i, p in enumerate(m.pages):
            for t in p.targets:
                assert t.action in [0, 1, 2]
                assert 0 <= t.page_i < len(m.pages)
            for x in p.targets + p.options + p.writeins + p.reviews:
                assert 0 <= x.contest_i < len(m.contests)

            slots = il.layouts[i].slots
            slot = len(p.targets)
            for i, o in enumerate(p.options):
                items[o.contest_i] += [slots[slot + i], il.sprites[o.sprite_i]]

            slot += len(p.options)
            for w in p.writeins:
                items[w.contest_i] += [slots[slot], il.sprites[w.sprite_i]]
                max_chars = m.contests[w.contest_i].max_chars
                chars[w.contest_i] += slots[slot + 1:slot + 1 + max_chars]
                slot += 1 + max_chars

            for r in p.reviews:
                max_chars = m.contests[r.contest_i].max_chars
                for i in range(m.contests[r.contest_i].max_sels):
                    items[r.contest_i] += [slots[slot]]
                    chars[r.contest_i] += slots[slot + 1:slot + 1 + max_chars]
                    slot += 1 + max_chars

        flags = [0 for c in m.contests]
        for p in m.pages:
            for w in p.writeins:
                flags[w.contest_i] = 1
        for i, c in enumerate(m.contests):
            if flags[i]:
                c.subpage_i, subpage_n = subpage_n, subpage_n + 1
                p = m.subpages[c.subpage_i]
                slots = il.layouts[len(m.pages) + c.subpage_i].slots
                assert len(p.subtargets) + c.max_chars == len(slots)
                chars[i] += slots[len(p.subtargets):]
                for t in p.subtargets:
                    assert t.action in [0, 1, 2, 3, 4, 5]
                    if t.action in [0, 1]:
                        chars[i] += [il.sprites[t.sprite_i]]
                chars[i] += [il.sprites[p.cursor_i]]
        assert len(m.subpages) == subpage_n

        for l, b in [(l, l.background) for l in il.layouts]:
            assert (b.width, b.height) == (il.width, il.height)
            for slot in l.slots:
                assert 0 <= slot.left < slot.left + slot.width < il.width
                assert 0 <= slot.top < slot.top + slot.height < il.height

        for list in items + chars:
            for x in list:
                assert (x.width, x.height) == (list[0].width, list[0].height)

class Model:
    def __init__(self, ballot, stream):
        self.contests = getlist(ballot, stream, Contest)
        self.pages = getlist(ballot, stream, Page)
        self.subpages = getlist(ballot, stream, Subpage)

class Contest:
    def __init__(self, ballot, stream):
        self.max_sels = getint(stream)
        self.max_chars = getint(stream)

class Page:
    def __init__(self, ballot, stream):
        self.targets = getlist(ballot, stream, Target)
        self.options = getlist(ballot, stream, Option)
        self.writeins = getlist(ballot, stream, Writein)
        self.reviews = getlist(ballot, stream, Review)

class Target:
    def __init__(self, ballot, stream):
        self.action = getint(stream)
        self.page_i = getint(stream)
        self.contest_i = (self.action == 1 and [getint(stream)] or [0])[0]

class Option:
    def __init__(self, ballot, stream):
        self.contest_i = getint(stream)
        self.sprite_i, ballot.sprite_n = ballot.sprite_n, ballot.sprite_n + 1

class Writein:
    def __init__(self, ballot, stream):
        self.contest_i = getint(stream)
        self.sprite_i, ballot.sprite_n = ballot.sprite_n, ballot.sprite_n + 1

class Review:
    def __init__(self, ballot, stream):
        self.contest_i = getint(stream)

class Subpage:
    def __init__(self, ballot, stream):
        self.subtargets = getlist(ballot, stream, Subtarget)
        self.cursor_i, ballot.sprite_n = ballot.sprite_n, ballot.sprite_n + 1
    
class Subtarget:
    def __init__(self, ballot, stream):
        self.action = getint(stream)
        if self.action in [0, 1]:
            self.sprite_i, ballot.sprite_n = ballot.sprite_n, ballot.sprite_n + 1

class Imagelib:
    def __init__(self, ballot, stream):
        self.width = getint(stream)
        self.height = getint(stream)
        self.layouts = getlist(ballot, stream, Layout)
        self.sprites = getlist(ballot, stream, Image)

class Layout:
    def __init__(self, ballot, stream):
        self.background = Image(ballot, stream)
        self.slots = getlist(ballot, stream, Slot)

class Slot:
    def __init__(self, ballot, stream):
        self.left = getint(stream)
        self.top = getint(stream)
        self.width = getint(stream)
        self.height = getint(stream)

class Image:
    def __init__(self, ballot, stream):
        self.width = getint(stream)
        self.height = getint(stream)
        self.pixels = stream.read(self.width * self.height * 3)

def getlist(ballot, stream, Class):
    return [Class(ballot, stream) for i in range(getint(stream))]

def getint(stream):
    bytes = [ord(char) for char in stream.read(4)]
    return (bytes[0]<<24) + (bytes[1]<<16) + (bytes[2]<<8) + bytes[3]
