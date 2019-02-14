#!/usr/bin/env python

from layout import *
from checkmark import Checkmark
from styles import *
import os, struct, re, aifc, array, audioop

# ---------------------------------------- arbitrary links among objects

class Namespace:
    def __contains__(self, name): return name in self.__dict__
    def __getitem__(self, name): return getattr(self, name)
    def __setitem__(self, name, value): setattr(self, name, value)

class LinkMap:
    def __init__(self): self.map = {}
    def __getitem__(self, key): return self.map.setdefault(key, Namespace())

links = LinkMap()

# ------------------------------------ serialized ballot definition file

# Constants for hardware keys.
# TODO: audio speed control keys
KUP, KDOWN, KLEFT, KRIGHT = map(ord, '8kuo')
KSELECT, KYES, KNO, KBACK, KCAST, KREAD = map(ord, 'ijl7,9')

# Constants for audio segment types.
[SCLIP, SOPTION, SSTATE, SACTION, SOPTIONP, SSTATEP, SACTIONP,
 SSELECTED, SNUMSELECTED, SMAXSELS] = range(10)

# Constants for selection operators.
OADD, OREMOVE, OTOGGLE, OAPPEND, OAPPEND2, OPOP = range(6)

def serialize(*thing):
    if len(thing) == 1:
        thing = thing[0]
    if isinstance(thing, int):
        return struct.pack('>l', thing)
    if isinstance(thing, tuple):
        return ''.join([serialize(item) for item in thing])
    if isinstance(thing, list):
        return serialize(len(thing), *thing)
    if isinstance(thing, str):
        return thing
    if hasattr(thing, '__members__'):
        return ''.join([serialize(getattr(thing, name))
                        for name in thing.__members__])
    return thing.serialize()

class Struct:
    def __init__(self, members='', *values):
        self.__members__ = members.split()
        for name, value in zip(self.__members__, values):
            setattr(self, name, value)

    def __repr__(self):
        return 'Struct(%s)' % ', '.join(
            ['%s=%r' % (n, getattr(self, n)) for n in self.__members__])

class Model(Struct):
    def __init__(self, groups=None, pages=None, timeout_milliseconds=-1):
        Struct.__init__(self, 'groups pages timeout_milliseconds',
                        groups or [], pages or [], timeout_milliseconds)

class Video(Struct):
    def __init__(self, width, height, layouts=None, sprites=None):
        Struct.__init__(self, 'width height layouts sprites',
                        width, height, layouts or [], sprites or [])

class Audio(Struct):
    def __init__(self, sample_rate, clips=None):
        Struct.__init__(self, 'sample_rate clips', sample_rate, clips or [])

class Contest(Struct):
    def __init__(self, max_sels, max_chars=0, options=None):
        Struct.__init__(self, 'type max_sels max_chars options',
                        0, max_sels, max_chars, options or [])

class Writein(Struct):
    def __init__(self, max_sels, options=None):
        Struct.__init__(self, 'type max_sels max_chars options',
                        1, max_sels, 0, options or [])

class Option(Struct):
    __members__ = 'unsel_sprite_i sel_sprite_i clip_i writein_group_i'.split()
    def __init__(self, unsel_sprite_i, sel_sprite_i, clip_i,
                 writein_group_i=-1):
        self.unsel_sprite_i = unsel_sprite_i
        self.sel_sprite_i = sel_sprite_i
        self.clip_i = clip_i
        self.writein_group_i = writein_group_i

class Page(Struct):
    __members__ = ('key_bindings target_bindings states '
                   'option_areas counter_areas review_areas').split()

    def __init__(self, key_bindings=None, target_bindings=None, states=None,
                 option_areas=None, counter_areas=None, review_areas=None):
        self.key_bindings = key_bindings or []
        self.target_bindings = target_bindings or []
        self.states = states or []
        self.option_areas = option_areas or []
        self.counter_areas = counter_areas or []
        self.review_areas = review_areas or []

class KeyBinding(Struct):
    __members__ = 'key action'.split()
    
    def __init__(self, key, action):
        self.key = key
        self.action = action

class Action(Struct):
    __members__ = ('next_page_i next_state_i clear_group_is '
                   'option_op option_refs option_area_op option_area_i '
                   'default_feedback toggle_off_feedback no_effect_feedback '
                   'full_feedback empty_feedback').split()

    def __init__(self, next_page_i=-1, next_state_i=-1, clear_group_is=None,
                 option_op=-1, option_refs=None, option_area_op=-1,
                 option_area_i=-1, default_feedback=None,
                 toggle_off_feedback=None, no_effect_feedback=None,
                 full_feedback=None, empty_feedback=None):
        self.next_page_i = next_page_i
        self.next_state_i = next_state_i
        self.clear_group_is = clear_group_is or []
        self.option_op = option_op
        self.option_refs = option_refs or []
        self.option_area_op = option_area_op
        self.option_area_i = option_area_i
        self.default_feedback = default_feedback or Sequence()
        self.toggle_off_feedback = toggle_off_feedback or Sequence()
        self.no_effect_feedback = no_effect_feedback or Sequence()
        self.full_feedback = full_feedback or Sequence()
        self.empty_feedback = empty_feedback or Sequence()

class State(Struct):
    __members__ = ('sprite_i option_area_i entry_feedback key_bindings '
                   'timeout_page_i timeout_state_i timeout_feedback').split()

    def __init__(self, sprite_i, option_area_i, entry_feedback,
                       key_bindings=None, timeout_feedback=None,
                       timeout_page_i=-1, timeout_state_i=-1):
        self.sprite_i = sprite_i
        self.option_area_i = option_area_i
        self.entry_feedback = entry_feedback
        self.key_bindings = key_bindings or []
        self.timeout_page_i = timeout_page_i
        self.timeout_state_i = timeout_state_i
        self.timeout_feedback = timeout_feedback or Sequence()

class Sequence(Struct):
    __members__ = 'segments'.split()

    def __init__(self, audio=None, *args):
        segments = []
        text = ''
        for arg in args:
            if isinstance(arg, (str, int)):
                text += ' ' + str(arg)
            else:
                if text:
                    segments.append(Segment(0, add_clip(audio, text)))
                segments.append(Segment(*arg))
                text = ''
        if text:
            segments.append(Segment(0, add_clip(audio, text)))
        self.segments = segments

class Segment(Struct):
    def __init__(self, type, clip_i, group_i=-1, option_i=-1):
        Struct.__init__(self, 'type clip_i group_i option_i',
                              type, clip_i, group_i, option_i)

class Clip:
    clips = [re.sub('.aiff$', '', name) for name in os.listdir('clips')]

    def __init__(self, text, sample_rate):
        self.pieces = []
        words = text.lower().split()
        while words:
            possibilities = []
            for i in range(1, len(words) + 1):
                prefix = ' '.join(words[:i])
                nopunc = ' '.join(
                    re.sub('[/();:,-]|\. +|\.$', ' ', prefix).split())
                if nopunc in self.clips:
                    possibilities.append((i, nopunc))
                if prefix in self.clips:
                    possibilities.append((i, prefix))
            if not possibilities:
                raise ValueError('no match for %r' % ' '.join(words))
            used, piece = possibilities[-1]
            self.pieces.append(piece)
            words[:used] = []
        self.sample_rate = sample_rate

    def __repr__(self):
        return '<Clip: %s>' % '/'.join(self.pieces)

    def serialize(self):
        data = []
        for piece in self.pieces:
            aiff = aifc.open('clips/%s.aiff' % piece)
            data.append(aiff.readframes(aiff.getnframes()))
        data = ''.join(data)
        if data:
            data = audioop.lin2lin(data, aiff.getsampwidth(), 2)
            if aiff.getnchannels() == 2:
                data = audioop.tomono(data, 2, 0.5, 0.5)
            data, state = audioop.ratecv(
                data, 2, 1, aiff.getframerate(), self.sample_rate, None)
            a = array.array('h', data)
            a.byteswap()
            data = a.tostring()
        else:
            data = '\x00\x00'
        return serialize(int(len(data)/2), data)

class Layout(Struct):
    __members__ = 'screen targets slots'.split()

    def __init__(self, screen, targets=None, slots=None):
        self.screen = screen
        self.targets = targets or []
        self.slots = slots or []

class Image:
    def __init__(self, box, *args, **kw):
        self.image = box.render(*args, **kw)

    def __repr__(self):
        return '<Image: %d by %d>' % self.image.size

    def serialize(self):
        width, height = self.image.size
        return serialize(width, height, self.image.tostring())

# -------------------------------------------- visual ballot page layout

def layout_check():
    return Box([(Circle(20, stroke=None, fill=WHITE), 0, 'MW'),
                (Checkmark(scale=40), (8, 0), 'MW')], 0, -20, 40, 20)

def layout_option_box(selected=1):
    if selected:
        rect = Rect(option_w - 1, option_h - 1, radius=option_radius,
                    stroke=BLACK, weight=3, fill=option_selected_bg)
    else:
        rect = Rect(option_w - 1, option_h - 1, radius=option_radius,
                    stroke=GREY, weight=1, fill=option_unselected_bg)
    return Box((rect, (0.5, 0.5)), padding=0.5)

def layout_highlight_box(w, h):
    offset = highlight_weight/2.0 + highlight_gap
    radius = option_radius + offset
    rect = Rect(w - 1 + offset*2, h - 1 + offset*2,
                weight=highlight_weight, stroke=highlight_stroke,
                radius=radius*0, dash=highlight_dash, fill=None)
    return Box((rect, (0.5 - offset, 0.5 - offset)))

def layout_option(option, selected=1):
    lines = [OptionText(option.name)]
    if option.description:
        for line in option.description.split('\n'):
            lines.append(DescriptionText(line))
    parts = [(layout_option_box(selected), 0, 'MW'),
             (OptionContent(lines), 0, 'Mw')]
    if selected:
        parts.append((layout_check(), (16, 0), 'MW'))
    return Box((Box(parts), 0, 'NW'))

def layout_writein_option(selected, key=None, length=0):
    chars = [Box([], 0, 0, char_w, char_h) for i in range(length)]
    blocks = dict(zip([(key, i) for i in range(length)], chars))

    parts = [(layout_option_box(selected), 0, 'MW'),
             ((OptionContent([HBox(chars)]), 0, 'MW'))]
    if not selected:
        lines = [OptionText('Write-In Candidate'),
                 DescriptionText('Touch this box to write in a name.')]
        parts.append((OptionContent(lines), 0, 'MW'))
    if selected:
        parts.append((layout_check(), (16, 0), 'MW'))
    return Box((Box(parts), 0, 'NW')), blocks

def layout_columns(elements, hspace, vspace, columns=1):
    elements = elements[:]
    n = rows = 0
    while n < len(elements):
        n += columns
        rows += 1
    vboxes = []
    while elements:
        vboxes.append(VBox(elements[:rows], int=1, spacing=vspace))
        elements[:rows] = []
    return HBox(vboxes, int=1, spacing=hspace)

def layout_selection_page(section, contest):
    headings = VBox([SectionHeadingText(section.name),
                     ContestHeadingText(contest.name),
                     DirectionsText(contest.directions)],
                    int=1, align='C', spacing=12)
    if contest.question:
        details = VBox([ContestSubtitleText(contest.subtitle),
                        ContestQuestionText(contest.question)],
                       spacing=24, fs=250)
        headings = VBox([headings, details],
                        int=1, align='C', spacing=48)
    blocks = {}
    elements = []
    for option in contest.options:
        blocks[option] = layout_option(option, 0)
        elements.append(blocks[option])
    if contest.maxchars > 0:
        for i in range(contest.maxsels):
            writein_option, writein_blocks = layout_writein_option(
                0, ('writein', i), contest.maxchars)
            blocks[('writein', i)] = writein_option
            blocks.update(writein_blocks)
            elements.append(blocks[('writein', i)])
    options = layout_columns(elements, option_hspace, option_vspace, 1)
    return VBox([Space(0, 48), headings, Space(0, 48), options],
                int=1, align='C'), blocks

def layout_key(char):
    w, h = key_w, key_h
    if char == ' ':
        w = key_w*2 + key_hspace
        text = (ButtonText('Space'), 'CM', 'CM')
    else:
        text = (WriteinKeyText(char), (0, key_char_y), 'CX')
    rect = Rect(w - 1, h - 1, radius=key_radius,
                stroke=key_stroke, fill=key_bg)
    box = Box((rect, (0.5, 0.5)), padding=0.5)
    return Box([(box, 0, 'CM'), text])

def layout_writein_page(title, chars, length):
    headings = WriteinHeadingText(title)
    headings = VBox([SectionHeadingText('Write-In'),
                     ContestHeadingText(title),
                     DirectionsText(
                        'Spell out the name using the letters below.')],
                    int=1, align='C', spacing=12)
    review, blocks = layout_writein_option(1, 'review', length)
    rows = []
    while chars:
        rowkeys = []
        for c in chars[:10]:
            blocks[('key', c)] = layout_key(c)
            rowkeys.append(blocks[('key', c)])
        row = HBox(rowkeys, int=1, spacing=key_hspace)
        rows.append(row)
        chars = chars[10:]
    keys = VBox(rows, int=1, spacing=key_vspace)

    blocks['clear'] = layout_button('Clear')
    blocks['backspace'] = layout_button('Backspace')
    buttons = HBox([blocks['clear'], blocks['backspace']], spacing=60)

    return VBox([Space(0, 48), headings, Space(0, 32), review, 
                 Space(0, 48), buttons, Space(0, 32), keys],
                int=1, align='C'), blocks

def layout_review():
    lines = [ReviewEmptyText('No selection made'),
             DescriptionText('Touch this box to make a selection.')]
    text = OptionContent(lines)
    box = layout_option_box(0)
    return Box((Box([(box, 0, 'MW'), (text, 0, 'MW')]), 0, 'NW'))
    
def layout_review_page(section):
    headings = VBox([SectionHeadingText(section.name),
                     ContestHeadingText('Review Your Selections'),
                     DirectionsText(
                        'Touch any contest to change your selections.')],
                    int=1, align='C', spacing=12)
    blocks = {}
    elements = []
    for contest in section.contests:
        lines = [ReviewTitleText(contest.name)]
        if contest.subtitle:
            lines.append(ReviewSubtitleText(contest.subtitle))
        label = ReviewLabel(lines)
        review_box = layout_review()
        element = VBox([label, review_box],
                       int=1, align='C', spacing=review_label_vspace)
        elements.append(element)
        blocks[(contest, 'slot')] = review_box
        blocks[contest] = element
    reviews = layout_columns(elements, review_hspace, review_vspace, 1)
    return VBox([Space(0, 48), headings, Space(0, 48), reviews],
                int=1, align='C'), blocks

blockmaps = {}

def update_blockmap(canvas, dict={}, **blocks):
    if canvas not in blockmaps:
        blockmaps[canvas] = {}
    dict = dict.copy()
    dict.update(blocks)
    for key in dict:
        bw, bn, be, bs = map(int, canvas.locate(dict[key]))
        blockmaps[canvas][key] = (bw, bn, be - bw, bs - bn)

def place_selection_page(canvas, contest):
    content, blocks = layout_selection_page(contest.section, contest)
    canvas.add(content, 'NC', 'NC')
    update_blockmap(canvas, blocks)

def place_writein_page(canvas, title, chars, length):
    content, blocks = layout_writein_page(title, chars, length)
    canvas.add(content, 'NC', 'NC')
    update_blockmap(canvas, blocks)

def place_review_page(canvas, section):
    content, blocks = layout_review_page(section)
    canvas.add(content, 'NC', 'NC')
    update_blockmap(canvas, blocks)

def layout_button(text):
    rect = Rect(button_w - 1, button_h - 1, radius=button_radius,
                stroke=button_stroke, weight=1, fill=button_bg)
    box = Box((rect, (0.5, 0.5)), padding=0.5)
    return Box([(box, 0, 'MC'), (ButtonText(text), 0, 'MC')])

def place_ballot_label(canvas, ballot):
    canvas.add(Box(NoteText(ballot.name), padding=6), 'SC', 'SC')

def place_navigation(canvas, previous=True, next=True):
    if previous:
        button = layout_button('Previous')
        canvas.add(Box(button, padding=40), 'SW', 'SW')
        update_blockmap(canvas, previous=button)
    if next:
        button = layout_button('Next')
        canvas.add(Box(button, padding=40), 'SE', 'SE')
        update_blockmap(canvas, next=button)

def place_instructions(canvas, title, text):
    paragraphs = text.replace('\n\n', '\n~\n').split('\n')
    canvas.add(VBox([Space(0, 48), TitleText(title), Space(0, 32),
                     VBox([InstructionsText(paragraph)
                           for paragraph in paragraphs], spacing=6)]),
               'NC', 'NC')

def place_highlight(canvas, key):
    x, y, w, h = blockmaps[canvas][key]
    highlight = layout_highlight_box(w, h)
    canvas.add(highlight, (x, y), under=0)
    update_blockmap(canvas, highlight=highlight)
    return highlight

def render_with_highlight(canvas, key):
    highlight = place_highlight(canvas, key)
    left, top, width, height = blockmaps[canvas][key]
    radius = highlight_gap + highlight_weight/2 + 1
    x, y = int(left - radius), int(top - radius)
    w, h = width + radius*2, height + radius*2
    image = Image(canvas, x=-x, y=-y, width=w, height=h)
    canvas.remove(highlight)
    return image, (x, y, w, h)

def place_writein_option(canvas, option, key, length):
    x, y, w, h = blockmaps[canvas][option]
    writein_option, blocks = layout_writein_option(1, key, length)
    canvas.add(writein_option, (x, y))
    update_blockmap(canvas, blocks)
    return writein_option

def place_confirmation(canvas):
    rbutton = layout_button('Review')
    cbutton = layout_button('Cast Ballot')
    canvas.add(HBox([rbutton, cbutton], spacing=60), 'MC', 'MC')
    update_blockmap(canvas, review=rbutton)
    update_blockmap(canvas, cast=cbutton)

def render_charset(chars):
    w, h = char_w*len(chars), char_h
    box = Box()
    box.add(Rect(width=w, height=h, fill=option_selected_bg, stroke=None))
    x = 0
    images = []
    for char in chars:
        box.add(WriteinText(char), (x + char_w/2, char_y), 'cX')
        images.append(Image(box, x=-x, y=0, width=char_w, height=char_h))
        x += char_w
    return images

def render_cursor():
    w, h = char_w, char_h
    box = Box()
    box.add(Rect(width=w, height=h, fill=option_selected_bg, stroke=None))
    box.add(Rect(width=char_w - 2, height=char_h - 6,
                 fill=WHITE, stroke=BLACK, weight=2),
            (char_w/2, char_h/2), 'CM')
    return Image(box, width=char_w, height=char_h)

# -------------------------------------------------- ballot instructions

instructions = [('2006 General Election',
                 'Tuesday, November 7, 2006\n'
                 'Contra Costa County, California\n\n'
                 'To begin, touch NEXT. ',
                 'This is the general election for Tuesday, November 7, 2006, '
                 'Contra Costa County, California. '
                 '@@ To begin, touch NEXT '
                 'in the lower-right corner of the screen. '
                 '@@ @@ '
                 'There is also a number keypad directly below the screen. '
                 'The numbers are arranged like a telephone, '
                 '@ with 1, 2, and 3 in the top row, '
                 '@ 4, 5, and 6 in the second row, '
                 '@ 7, 8, and 9 in the third row, '
                 '@ and 0 in the bottom row. '
                 '@ To begin, press 6.'),
                ('Instructions',
                 'Touch the screen to make your selections. '
                 'Use the NEXT and PREVIOUS buttons below '
                 'to move from page to page.\n\n'
                 'To continue, touch NEXT.',
                 '@ Touch the screen to make your selections. '
                 '@ Use the NEXT and PREVIOUS buttons below '
                 'to move from page to page. '
                 '@ To continue, touch NEXT, '
                 'or press 6 on the number keypad.')]

# --------------------------------------------------- ballot compilation

def add(list, item):
    index = len(list)
    list.append(item)
    return index

def add_clip(audio, text):
    return add(audio.clips, Clip(text, audio.sample_rate))

def add_slot(layout, canvas, block, radius):
    (x, y, w, h), r = blockmaps[canvas][block], radius
    print 'slot', len(layout.slots), block, (x, y, w, h)
    layout.slots.append((x - r, y - r, w + r*2, h + r*2))

def add_target(layout, canvas, block, radius, action):
    (x, y, w, h), r = blockmaps[canvas][block], radius
    print 'target', len(layout.targets), block, (x, y, w, h)
    layout.targets.append((x - r, y - r, w + r*2, h + r*2))
    links[layout].page.target_bindings.append(action)

def compile(ballot):
    model = Model(timeout_milliseconds=15000)
    video = Video(1024, 768)
    audio = Audio(22050)

    # Stage 0: Set up the contests and their options.

    cursor_sprite_i = add(video.sprites, render_cursor())
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-' "
    char_images = render_charset(chars)
    char_sprite_is = [add(video.sprites, image) for image in char_images]
    char_names = list(chars)
    char_names[char_names.index('-')] = 'hyphen'
    char_names[char_names.index("'")] = 'apostrophe'
    char_names[char_names.index(' ')] = 'space'
    char_clip_is = [add_clip(audio, name) for name in char_names]
    writein_options = [Option(-1, sprite_i, clip_i, -1)
        for sprite_i, clip_i in zip(char_sprite_is, char_clip_is)]

    contest_i = 0
    for section in ballot.sections:
        for contest in section.contests:
            print 'contest:', contest.name
            group = Contest(contest.maxsels, contest.maxchars)
            links[contest].group_i = group_i = add(model.groups, group)
            links[contest].contest_i = contest_i
            contest_i += 1

            # Add regular options to the contest.
            for option_i, option in enumerate(contest.options):
                print 'option:', option
                unsel = Box((layout_option(option, 0), (4, 4)), padding=4)
                sel = Box((layout_option(option, 1), (4, 4)), padding=4)
                add(group.options,
                    Option(add(video.sprites, Image(unsel)),
                           add(video.sprites, Image(sel)),
                           add_clip(audio, option.name)))
                add_clip(audio, option.name + ' @ ' +
                                option.description.replace('\n', ' party @ '))

            # Add write-in options to the contest.
            links[contest].writein_option_is = []
            links[contest].writein_group_is = []

            if contest.maxchars == 0:
                continue

            for writein_i in range(contest.maxsels):
                writein_group_i = add(
                    model.groups, Writein(contest.maxchars, writein_options))
                links[contest].writein_group_is.append(writein_group_i)

                unsel = Box((layout_writein_option(0)[0], (4, 4)), padding=4)
                sel = Box((layout_writein_option(1)[0], (4, 4)), padding=4)
                links[contest].writein_option_is.append(
                    add(group.options,
                        Option(add(video.sprites, Image(unsel)),
                               add(video.sprites, Image(sel)),
                               add_clip(audio, 'Write-in candidate'),
                               writein_group_i)))
                add_clip(audio, 'Write-in candidate')

    num_contests = contest_i

    # Stage 1: Lay out the canvases.

    canvases = []

    # Add the instruction pages.
    for title, text, spoken in instructions:
        canvas = Box([], 0, 0, 1024, 768)
        place_instructions(canvas, title, text)
        links[canvas].i = len(canvases)
        links[canvas].instructions = (title, text, spoken)
        canvases.append(canvas)

    # Add the selection pages.
    for section in ballot.sections:
        for contest in section.contests:
            canvas = Box([], 0, 0, 1024, 768)
            place_selection_page(canvas, contest)
            canvases.append(canvas)
            links[canvas].contest = contest
            links[contest].canvas = canvas

    # Add the review pages.
    review_page_i = len(canvases)
    for section in ballot.sections:
        canvas = Box([], 0, 0, 1024, 768)
        place_review_page(canvas, section)
        canvases.append(canvas)
        links[canvas].section = section
        links[section].canvas = canvas

    # Add the confirmation page.
    canvas = Box([], 0, 0, 1024, 768)
    place_instructions(canvas, 'Are You Ready to Cast Your Ballot?',
                       'This is your last chance to review your selections '
                       'before casting your ballot.')
    place_confirmation(canvas)
    confirmation_page_i = add(canvases, canvas)

    # Add navigation buttons to the pages so far.
    for canvas_i, canvas in enumerate(canvases):
        previous = 0 < canvas_i
        next = canvas_i < len(canvases) - 1
        place_navigation(canvas, previous, next)

    # Add the write-in pages.
    for section in ballot.sections:
        for contest in section.contests:
            links[contest].writein_page_is = []

            for writein_option_i in links[contest].writein_option_is:
                # Construct the write-in page.
                canvas = Box([], 0, 0, 1024, 768)
                links[canvas].writein = (contest, writein_option_i)
                group = model.groups[links[contest].group_i]
                writein_option = group.options[writein_option_i]
                links[canvas].group_i = writein_option.writein_group_i

                place_writein_page(
                    canvas, contest.name, chars, contest.maxchars)
                abutton = layout_button('Accept')
                cbutton = layout_button('Cancel')
                hbox = HBox([abutton, cbutton], spacing=60, padding=40)
                canvas.add(hbox, 'SC', 'SC')
                update_blockmap(canvas, accept=abutton)
                update_blockmap(canvas, cancel=cbutton)
                links[contest].writein_page_is.append(add(canvases, canvas))

    # Add the completion page.
    canvas = Box([], 0, 0, 1024, 768)
    canvas.add(VBox([CompletionText('Thank you for voting.'),
                     CompletionText('Your ballot has been recorded.')],
                    spacing=6, align='C'), 'MC', 'MC')
    completion_page_i = add(canvases, canvas)

    # Stage 2: Create pages and layouts for each canvas.

    for page_i, canvas in enumerate(canvases):
        print 'render page:', page_i
        place_ballot_label(canvas, ballot)
        page, layout = Page(), Layout(Image(canvas))
        links[page].i = add(model.pages, page)
        links[layout].i = add(video.layouts, layout)

        # Hook up the page, layout, canvas, and possible contest.
        links[layout].page = page
        links[layout].canvas = canvas
        links[page].canvas = canvas
        links[page].layout = layout
        links[canvas].page = page
        links[canvas].layout = layout
        for key in 'contest instructions section writein group_i'.split():
            if key in links[canvas]:
                links[page][key] = links[canvas][key]
                value = links[canvas][key]
                links[value].page = page
                links[value].page_i = page_i

    # Stage 3: Add states, key bindings, and areas to pages.

    for page_i, page in enumerate(model.pages):
        # Create the default state for each page.
        print '\npage:', page_i
        canvas = links[page].canvas
        layout = links[page].layout
        state = State(-1, -1, Sequence())
        layout.slots.append((0, 0, 0, 0))
        state_i = add(page.states, state)
        state.timeout_page_i = page_i
        state.timeout_state_i = state_i

        # Instruction pages.
        if 'instructions' in links[page]:
            print 'instructions'
            title, text, spoken = links[page].instructions
            state.entry_feedback = Sequence(audio, spoken)

        # Selection pages.
        if 'contest' in links[page]:
            contest = links[page].contest
            section = contest.section
            group_i = links[contest].group_i
            group = model.groups[group_i]
            contest_i = links[contest].contest_i
            print 'contest %d:' % contest_i, contest, 'group', group_i

            if contest.question:
                print 'question'
                add(state.key_bindings, (KDOWN, Action(page_i, 1)))

                # Add the default state's entrance sound.
                text = [section.name, '@', contest.name, '@']
                sel_zero = add_clip(audio, '')
                sel_one = add_clip(audio, 'Your current selection is')
                text = [section.name, '@', contest.name, '@']
                text += ['@', (SNUMSELECTED, sel_zero, group_i),
                         (SSELECTED, 0, group_i)]
                text += ['@ To hear the full text of this proposition, ',
                         'press 8. @ Touch your selection on the screen, or '
                         '@ to select yes, press 7; to select no, press 9.']
                state.entry_feedback = Sequence(audio, *text)
            else:
                print 'race'
                # Add the default state's entrance sound.
                sel_zero = add_clip(audio, '')
                sel_one = add_clip(audio, 'Your current selection is')
                text = [section.name, '@', contest.name, '@']
                if len(contest.options) == 1:
                    text += ['There is 1 candidate.']
                else:
                    text += ['There are', len(contest.options), 'candidates.']
                if contest.maxsels == 1:
                    text += ['@ Please vote for 1.']
                else:
                    text += ['@ Please vote for up to', contest.maxsels]
                text += ['@', (SNUMSELECTED, sel_zero, group_i),
                         (SSELECTED, 0, group_i)]
                text += ['@ Touch the screen to make selections',
                         'or press 8 to hear the choices.']
                if contest_i < num_contests - 1:
                    text += ['@@ To skip to the next contest, press 6.']
                if contest_i > 0:
                    text += ['@@ To go back to the previous contest, press 4.']
                state.entry_feedback = Sequence(audio, *text)

                # Add the default state's navigation behaviour.
                add(state.key_bindings, (KDOWN, Action(page_i, 1)))

            if contest.question:
                # Add key bindings for yes and no.
                add(page.key_bindings, (KYES, Action(
                    -1, -1, [group_i], OADD, [(group_i, 0)], -1, -1,
                    Sequence(audio, 'Selected', (SOPTION, 0, group_i, 0),
                             'on', contest.name))))
                add(page.key_bindings, (KNO, Action(
                    -1, -1, [group_i], OADD, [(group_i, 1)], -1, -1,
                    Sequence(audio, 'Selected', (SOPTION, 0, group_i, 1),
                             'on', contest.name))))

                # Add a state for reading out the question text.
                state = State(-1, -1, Sequence(
                    audio, contest.subtitle, '@@', contest.question,
                    '@ To hear the text of this proposition again, '
                    'press 8. @ Touch your selection on the screen, '
                    'or @ to select yes, press 7; to select no, press 9.'))
                state_i = add(page.states, state)
                state.timeout_page_i = page_i
                state.timeout_state_i = state_i
                layout.slots.append((0, 0, 0, 0))
                add(state.key_bindings, (KDOWN, Action(page_i, 1)))

            else:
                # Add a state for each option area.
                for option_i in range(len(group.options)):
                    if option_i < len(contest.options):
                        writein_i = -1
                        key = contest.options[option_i]
                    else:
                        writein_i = option_i - len(contest.options)
                        key = ('writein', writein_i)
                    image, slot = render_with_highlight(canvas, key)
                    add(layout.slots, slot)
                    sprite_i = add(video.sprites, image)

                    # Create the state's entrance sound.
                    select = (writein_i < 0 and 'To vote for this candidate'
                              or 'To write in a name for ' + contest.name)
                    sequence = Sequence(
                        audio, (SSTATE, 1), '@', select, 'press 5.',
                        (option_i < len(group.options) - 1) and
                        '@ To hear the next choice, press 8.' or
                        '@ To hear all the choices again, press 4.')

                    state = State(sprite_i, option_i, sequence)
                    state_i = add(page.states, state)
                    state.timeout_page_i = page_i
                    state.timeout_state_i = state_i
                    print 'state:', state_i

                    # Add the state's navigation behaviours.
                    if option_i > 0:
                        add(state.key_bindings,
                            (KUP, Action(page_i, state_i - 1)))
                    if option_i < len(group.options) - 1:
                        add(state.key_bindings,
                            (KDOWN, Action(page_i, state_i + 1)))
                    add(state.key_bindings, (KLEFT, Action(page_i, 0)))

                    # Add the state's selection behaviour.
                    if writein_i >= 0:
                        add(state.key_bindings, (KSELECT, Action(
                            links[contest].writein_page_is[writein_i], 0)))
                    else:
                        add(state.key_bindings, (KSELECT, Action(
                            -1, -1, [group_i] + links[contest].writein_group_is,
                            -1, [], OADD, option_i,
                            Sequence(audio, 'Selected', (SACTION, 0),
                                     'for', contest.name))))

            # Add the option areas to the page.
            for option_i, option in enumerate(contest.options):
                add(page.option_areas, (group_i, -1))
                add_slot(layout, canvas, option, 4)
                add_target(layout, canvas, option, 4, Action(
                    -1, -1, [group_i] + links[contest].writein_group_is,
                    -1, [], OADD, option_i,
                    Sequence(audio, 'Selected', (SACTION, 0),
                             contest.question and 'on' or 'for',
                             contest.name)))

            # Add write-in options to the contest.
            for i, writein_page_i in enumerate(links[contest].writein_page_is):
                add(page.option_areas, (group_i, -1))
                add_slot(layout, canvas, ('writein', i), 4)
                for c in range(contest.maxchars):
                    add_slot(layout, canvas, (('writein', i), c), 0)
                add_target(layout, canvas, ('writein', i), 4,
                           Action(writein_page_i, 0))

        # Write-in pages.
        if 'writein' in links[page]:
            print 'write-in'
            contest, writein_option_i = links[page].writein
            group_i = links[page].group_i
            contest_group_i = links[contest].group_i
            contest_page_i = links[links[contest].page].i

            state.entry_feedback = Sequence(
                audio, 'Write-in candidate for ', contest.name,
                '@ To write in a name, touch the letters on the screen.',
                'Touch Accept when you are finished,',
                'or touch Cancel to cancel your write-in.',
                '@ Or, to advance through the alphabet',
                'using the keypad, press 6.')

            add(state.key_bindings, (KRIGHT, Action(page_i, 1)))

            full_feedback = Sequence(
                audio, 'There is no room for more letters.')

            # Add a state for each character.
            for option_i, (c, char_name) in enumerate(zip(chars, char_names)):
                image, slot = render_with_highlight(canvas, ('key', c))
                add(layout.slots, slot)
                sprite_i = add(video.sprites, image)

                # Create the state's entrance sound.
                sequence = Sequence(
                    audio, char_name, '@ To add this letter, @ press 5.',
                    '@ To delete the last letter, press 1.',
                    '@ To advance to the next letter of the alphabet, press 6.',
                    '@ For the previous letter, press 4.',
                    '@ To read back the letters you have entered, press 3.',
                    '@ To accept this write-in, press 7.',
                    '@ To cancel this write-in, press 9.')

                state = State(sprite_i, option_i, sequence)
                state_i = add(page.states, state)
                state.timeout_page_i = page_i
                state.timeout_state_i = state_i
                print 'state:', state_i

                next_state_i = state_i + 1
                if option_i == len(chars) - 1:
                    next_state_i = 1
                add(state.key_bindings, (KRIGHT, Action(page_i, next_state_i)))
                prev_state_i = state_i - 1
                if option_i == 0:
                    prev_state_i = len(chars)
                add(state.key_bindings, (KLEFT, Action(page_i, prev_state_i)))
                add(state.key_bindings, (KSELECT, Action(
                    -1, -1, [], OAPPEND, [(group_i, option_i)],
                    default_feedback=Sequence(audio, char_name),
                    full_feedback=full_feedback)))

            add(page.key_bindings, (KREAD, Action(
                default_feedback=Sequence(audio, (SSELECTED, 0, group_i)))))

            # Add the review area.
            page.review_areas.append((group_i, cursor_sprite_i))
            for j in range(contest.maxchars):
                add_slot(layout, canvas, ('review', j), 0)

            # Add the typing targets to the write-in page.
            for c, char in enumerate(chars):
                feedback = Sequence(audio, (SOPTION, 0, group_i, c))
                add_target(layout, canvas, ('key', char), 0,
                           Action(-1, -1, [], OAPPEND, [(group_i, c)],
                                  default_feedback=feedback,
                                  full_feedback=full_feedback))

            add_target(layout, canvas, 'clear', 4, Action(-1, -1, [group_i]))
            add_target(layout, canvas, 'backspace', 4,
                       Action(-1, -1, [], OPOP, [(group_i, 0)]))
            add(page.key_bindings,
                (KBACK, Action(-1, -1, [], OPOP, [(group_i, 0)])))

            # Add the navigation targets to the write-in page.
            add_target(layout, canvas, 'accept', 4, Action(
                contest_page_i, 0, [contest_group_i],
                OADD, [(contest_group_i, writein_option_i)]))
            add(page.key_bindings, (KYES, Action(
                contest_page_i, 0, [contest_group_i],
                OADD, [(contest_group_i, writein_option_i)])))
            add_target(layout, canvas, 'cancel', 4, Action(
                contest_page_i, 0, [group_i],
                OREMOVE, [(contest_group_i, writein_option_i)]))
            add(page.key_bindings, (KNO, Action(
                contest_page_i, 0, [group_i],
                OREMOVE, [(contest_group_i, writein_option_i)])))

        # Review pages.
        if 'section' in links[page]:
            print 'review'
            section = links[page].section

            # Add the default state's entrance sound.
            state.entry_feedback = Sequence(
                audio, 'Review your selections before casting your ballot. ',
                '@ To change your selections for any contest, ',
                'touch that contest on the screen. ',
                '@ Use the NEXT and PREVIOUS buttons ',
                'to move from page to page. ',
                '@ Or, to hear your selections read back to you, press 8.')

            # Add the key binding for reading review areas.
            add(state.key_bindings, (KDOWN, Action(page_i, 1)))

            for i, contest in enumerate(section.contests):
                # Add a state for each contest.
                image, slot = render_with_highlight(canvas, contest)
                add(layout.slots, slot)
                sprite_i = add(video.sprites, image)
                group_i = links[contest].group_i
                contest_i = links[contest].contest_i

                # Create the state's entrance sound.
                sel_zero = add_clip(
                    audio, 'You have not made a selection for ' + contest.name)
                sel_one = add_clip(audio, 'Your current selection is')
                edit_zero = add_clip(audio, 'To make a selection')
                edit_one = add_clip(audio, 'To change your selection')
                text = [contest.name, (SNUMSELECTED, sel_zero, group_i),
                        (SSELECTED, 0, group_i), '@',
                        (SNUMSELECTED, edit_zero, group_i), 'press 5.']
                if contest_i < num_contests - 1:
                    text += ['@ For the next contest, press 8.']
                else:
                    text += ['@ To proceed with casting your ballot, press 6.']
                if contest_i > 0:
                    text += ['@ For the previous contest, press 2.']

                state = State(sprite_i, -1, Sequence(audio, *text))
                state_i = add(page.states, state)
                state.timeout_page_i = page_i
                state.timeout_state_i = state_i

                # Add the state's navigation behaviours.
                if i > 0:
                    add(state.key_bindings, (KUP, Action(page_i, state_i-1)))
                elif contest_i > 0:
                    add(state.key_bindings, (KUP, Action(
                        page_i - 1, len(model.pages[page_i - 1].states) - 1)))
                if i < len(section.contests) - 1:
                    add(state.key_bindings,
                        (KDOWN, Action(page_i, state_i + 1)))
                elif contest_i < num_contests - 1:
                    add(state.key_bindings, (KDOWN, Action(page_i + 1, 1)))
                else:
                    add(state.key_bindings, (KDOWN, Action(
                        -1, -1, default_feedback=Sequence(
                            audio, 'This is the last contest. @',
                            'To proceed with casting your ballot, press 6.'))))

                # Add the state's selection behaviour.
                add(state.key_bindings, (KSELECT, Action(
                    links[links[contest].page].i, 0)))

            for contest in section.contests:
                # Add the review area to the page.
                add_slot(layout, canvas, (contest, 'slot'), 4)
                page.review_areas.append((links[contest].group_i, -1))

                if contest.maxchars > 0:
                    writein = place_writein_option(
                        canvas, (contest, 'slot'), 'review', contest.maxchars)
                    for j in range(contest.maxchars):
                        add_slot(layout, canvas, ('review', j), 0)
                    canvas.remove(writein)

                add_target(layout, canvas, contest, 4,
                           Action(links[links[contest].page].i, 0))

        if page_i == confirmation_page_i:
            print 'confirmation'
            state.entry_feedback = Sequence(
                audio, 'This is your last chance to review your selections ',
                'before casting your ballot. @ To review your selections, ',
                'press 1.  To cast your ballot now, press 0.')

            add_target(layout, canvas, 'review', 0, Action(review_page_i, 0))
            add_target(layout, canvas, 'cast', 0, Action(completion_page_i, 0))
            add(state.key_bindings, (KBACK, Action(review_page_i, 0)))
            add(state.key_bindings, (KCAST, Action(completion_page_i, 0)))

        if page_i == completion_page_i:
            print 'completion'
            state.entry_feedback = Sequence(
                audio, '@ Thank you for voting.',
                '@ Your ballot has been recorded.')

        # Add targets for the generic navigation buttons.
        if 'previous' in blockmaps.get(canvas, {}):
            add_target(layout, canvas, 'previous', 0, Action(page_i - 1, 0))
            page.key_bindings.append((KLEFT, Action(page_i - 1, 0)))
        if 'next' in blockmaps.get(canvas, {}):
            add_target(layout, canvas, 'next', 0, Action(page_i + 1, 0))
            page.key_bindings.append((KRIGHT, Action(page_i + 1, 0)))

    ballot = Struct('model video audio', model, video, audio)
    return serialize(ballot)

from contra_costa_167 import ballot

def test_render(ballot):
    for i, (title, text) in enumerate(instructions[:0]):
        page = Box([], 0, 0, 1024, 768)
        place_instructions(page, title, text)
        place_navigation(page)
        page.write('output/%d-%d.png' % (0, i + 1))
    for si, section in enumerate(ballot.sections[:1]):
        for ci, contest in enumerate(section.contests):
            page = Box([], 0, 0, 1024, 768)
            place_selection_page(page, contest)
            place_navigation(page)
            x, y, w, h = blockmaps[page][contest.options[0]]
            highlight = layout_highlight_box(w, h)
            page.add(highlight, (x, y), under=0)
            page.write('output/%d-%d.png' % (si + 1, ci + 1))

def test_render_writein(title):
    box, blocks = layout_writein_page(title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ-' ", 1)
    page = Box([], 0, 0, 1024, 768)
    page.add(box, 'NC', 'NC')
    page.write('output/writein.png')

def test_compile(ballot):
    model = Model(timeout_milliseconds=2000)
    video = Video(1024, 768)
    audio = Audio(44100)

    def add(list, item):
        index = len(list)
        list.append(item)
        return index

    canvases = []

    # Add the instruction pages.
    for title, text in instructions:
        canvas = Box([], 0, 0, 1024, 768)
        place_instructions(canvas, title, text)
        canvases.append(canvas)

    model.groups.append(Contest(1))

    layout = Layout(Image(canvases[0]), [], [])
    video.layouts.append(layout)

    layout = Layout(Image(canvases[1]), [], [])
    video.layouts.append(layout)

    entry_feedback = Sequence(audio, '6 5 4')
    timeout_feedback = Sequence(audio, '3 2 1')

    page = Page()
    state = State(-1, entry_feedback, timeout_feedback=timeout_feedback)
    page.states.append(state)
    model.pages.append(page)

    page = Page()
    state = State(-1, Sequence())
    page.states.append(state)
    model.pages.append(page)

    ballot = Struct('model video audio', model, video, audio)
    return serialize(ballot)

if __name__ == '__main__':
    # test_render(ballot)
    # test_render_writein('Governor')
    open('ballot', 'w').write(compile(ballot))
    # Clip('There are 3 candidates for governor.').serialize()
    # open('output/ballot', 'w').write(test_compile(ballot))
