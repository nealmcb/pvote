import pygame; pygame.FULLSCREEN = 0
import Audio, Ballot, Navigator, Recorder, Video

class Dummy: pass
classtype = type(Dummy)

opnames = 'add remove toggle append append2 pop'.split()

def simple_repr(self):
    return '<%s>' % self.__class__.__name__

def action_repr(self):
    desc = ''
    if self.next_page_i != -1:
        desc += ' %d:%d' % (self.next_page_i, self.next_state_i)
    if self.clear_group_is:
        desc += ' clear [%s]' % (' '.join(map(str, self.clear_group_is)))
    if self.option_op != -1:
        desc += ' %s [%s]' % (opnames[self.option_op], ' '.join([  
            '%d/%d' % (r.group_i, r.option_i) for r in self.option_refs]))
    if self.option_area_op != -1:
        desc += ' %s area %r' % (opnames[self.option_area_op],
                                 self.option_area_i)
    return '<Action%s>' % desc

typenames = ['clip', 'option', 'state', 'action', 'option?',
             'state?', 'action?', 'listsels', 'countsels', 'maxsels']

def segment_desc(self):
    desc = typenames[self.type]
    if self.type == 0:
        desc += ' %d' % self.clip_i
    if self.type in [1, 4]:
        desc += ' %d/%d + %d' % (self.group_i, self.option_i, self.clip_i)
    if self.type in [2, 3, 5, 6]:
        desc += ' + %d' % self.clip_i
    if self.type in [7, 8, 9]:
        desc += ' %d + %d' % (self.group_i, self.clip_i)
    return desc

def segment_repr(self):
    return '<Segment %s>' % segment_desc(self)

def rect_repr(self):
    return '<(%d, %d) %dx%d>' % (self.left, self.top, self.width, self.height)

def keybinding_repr(self):
    return '<%d: %s' % (
        self.key, action_repr(self.action).replace('<Action ', ''))

def targetbinding_repr(self):
    return action_repr(self.action).replace('<Action', '<Target')

original_update = Navigator.Navigator.update
def navigator_update(self):
    print 'update:', self.selections
    original_update(self)

original_execute = Navigator.Navigator.execute
def navigator_execute(self, action):
    print 'execute:', action
    original_execute(self, action)

original_play = Navigator.Navigator.play
def navigator_play(self, sequence, action_option_area_i):
    print 'play:', ', '.join([segment_desc(s) for s in sequence.segments])
    original_play(self, sequence, action_option_area_i)

for module in Audio, Ballot, Navigator, Recorder, Video:
    for name, value in module.__dict__.items():
        if type(value) is classtype:
            value.__repr__ = simple_repr

Ballot.Action.__repr__ = action_repr
Ballot.Segment.__repr__ = segment_repr
Ballot.Rect.__repr__ = rect_repr
Ballot.KeyBinding.__repr__ = keybinding_repr
Ballot.TargetBinding.__repr__ = targetbinding_repr
Navigator.Navigator.update = navigator_update
Navigator.Navigator.execute = navigator_execute
Navigator.Navigator.play = navigator_play
