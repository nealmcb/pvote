from layout import *
from checkmark import Checkmark
from styles import *
import os, struct, re, aifc, array, audioop

# ---------------------------------------- arbitrary links among objects

class Namespace:
    def __getattr__(self, name): return None

class LinkMap:
    def __init__(self): self.map = {}
    def __getitem__(self, key): return self.map.setdefault(key, Namespace())

links = LinkMap()

# ------------------------------------ serialized ballot definition file

# Constants for hardware keys.
# TODO: audio speed control keys
KUP, KDOWN, KLEFT, KRIGHT, KSELECT, KYES, KNO = map(ord, '8kuoijl')

# Constants for audio segment types.
SCLIP, SSTATE, SACTION, SSELECTED, SNUMSELECTED, SMAXSELS = range(6)

# Constants for option selection actions.
ASELECT, ADESELECT, ATOGGLE = range(3)

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

class Clip:
    clips = [re.sub('.aiff$', '', name) for name in os.listdir('clips')]

    def __init__(self, audio, text):
        self.pieces = []
        words = text.lower().split()
        while words:
            possibilities = []
            for i in range(1, len(words) + 1):
                prefix = ' '.join(words[:i])
                nopunc = ' '.join(re.sub('[;:,.-]', ' ', prefix).split())
                if nopunc in self.clips:
                    possibilities.append((i, nopunc))
                if prefix in self.clips:
                    possibilities.append((i, prefix))
            if not possibilities:
                raise ValueError('no match for %r' % ' '.join(words))
            used, piece = possibilities[-1]
            self.pieces.append(piece)
            words[:used] = []
        self.clip_i = len(audio.clips)
        self.sample_rate = audio.sample_rate
        audio.clips.append(self)
        print self

    def __repr__(self):
        return '<Clip %d: %s>' % (self.clip_i, '/'.join(self.pieces))

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

class Model(Struct):
    def __init__(self, contests=None, pages=None, timeout_milliseconds=-1):
        Struct.__init__(self, 'contests pages timeout_milliseconds',
                              contests or [], pages or [], timeout_milliseconds)

class Contest(Struct):
    def __init__(self, max_sels, options=None):
        Struct.__init__(self, 'max_sels options', max_sels, options or [])

class Video(Struct):
    def __init__(self, width, height, layouts=None, sprites=None):
        Struct.__init__(self, 'width height layouts sprites',
                              width, height, layouts or [], sprites or [])

class Audio(Struct):
    def __init__(self, sample_rate, clips=None):
        Struct.__init__(self, 'sample_rate clips', sample_rate, clips or [])

class Action(Struct):
    __members__ = ('clear_contest_is select_option_refs '
                   'option_area_i option_area_action '
                   'default_sequence no_change_sequence overvote_sequence '
                   'toggle_deselect_sequence next_page_i next_state_i').split()

    def __init__(self, next_page_i=-1, next_state_i=-1,
                       clear_contest_is=None, select_option_refs=None,
                       option_area_i=-1, option_area_action=0,
                       default_sequence=None, no_change_sequence=None,
                       overvote_sequence=None, toggle_deselect_sequence=None):
        self.next_page_i = next_page_i
        self.next_state_i = next_state_i
        self.clear_contest_is = clear_contest_is or []
        self.select_option_refs = select_option_refs or []
        self.option_area_i = option_area_i
        self.option_area_action = option_area_action
        self.default_sequence = default_sequence or Sequence()
        self.no_change_sequence = no_change_sequence or Sequence()
        self.overvote_sequence = overvote_sequence or Sequence()
        self.toggle_deselect_sequence = toggle_deselect_sequence or Sequence()

class KeyBinding(Struct):
    __members__ = 'key action'.split()
    
    def __init__(self, key, action):
        self.key = key
        self.action = action

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

class Option(Struct):
    def __init__(self, *args):
        Struct.__init__(self, 'unsel_sprite_i sel_sprite_i clip_i', *args)

class State(Struct):
    __members__ = ('sprite_i option_area_i entry_sequence key_bindings '
                   'timeout_sequence timeout_page_i timeout_state_i').split()

    def __init__(self, sprite_i, option_area_i, entry_sequence,
                       key_bindings=None, timeout_sequence=None,
                       timeout_page_i=-1, timeout_state_i=-1):
        self.sprite_i = sprite_i
        self.option_area_i = option_area_i
        self.entry_sequence = entry_sequence
        self.key_bindings = key_bindings or []
        self.timeout_sequence = timeout_sequence or Sequence()
        self.timeout_page_i = timeout_page_i
        self.timeout_state_i = timeout_state_i

class Segment(Struct):
    def __init__(self, type, clip_i, contest_i=-1):
        Struct.__init__(self, 'type clip_i contest_i', type, clip_i, contest_i)

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
                    segments.append(Segment(0, Clip(audio, text).clip_i))
                type, clip_i, contest_i = (arg + (-1,))[:3]
                segments.append(Segment(type, clip_i, contest_i))
                text = ''
        if text:
            segments.append(Segment(0, Clip(audio, text).clip_i))
        self.segments = segments

# -------------------------------------------- visual ballot page layout

def layout_check():
    return Box([(Circle(20, stroke=None, fill=WHITE), 0, 'MW'),
                (Checkmark(scale=40), (8, -3), 'MW')])

def layout_option_box(selected=1):
    if selected:
        rect = Rect(option_w - 1, option_h - 1, radius=option_radius,
                    stroke=BLACK, weight=3, fill=option_selected_bg)
    else:
        rect = Rect(option_w - 1, option_h - 1, radius=option_radius,
                    stroke=GREY, weight=1, fill=option_unselected_bg)
    return Box((rect, (0.5, 0.5)), padding=0.5)

def layout_option_highlight(w, h):
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
    text = OptionContent(lines)
    box = layout_option_box(selected)
    check = selected and [(layout_check(), (16, 0), 'MW')] or []
    return Box((Box([(box, 0, 'MW'), (text, 0, 'MW')] + check), 0, 'NW'))

def layout_options(options, columns=1, selected=0):
    blocks = {}
    options = options[:]
    n = rows = 0
    while n < len(options):
        n += columns
        rows += 1
    vboxes = []
    while options:
        boxes = []
        for o in options[:rows]:
            blocks[o] = optionbox = layout_option(o, selected)
            boxes.append(optionbox)
        vboxes.append(VBox(boxes, int=1, spacing=option_vspace))
        options = options[rows:]
    return HBox(vboxes, int=1, spacing=option_hspace), blocks

def layout_contest(section, contest):
    if contest.question:
        details = VBox([ContestSubtitleText(contest.subtitle),
                        ContestQuestionText(contest.question)],
                       spacing=24, fs=300)
        headings = VBox([SectionHeadingText(section.name),
                         ContestHeadingText(contest.name),
                         DirectionsText(''), details],
                        int=1, align='C', spacing=12)
    else:
        headings = VBox([SectionHeadingText(section.name),
                         ContestHeadingText(contest.name),
                         DirectionsText(contest.directions)],
                        int=1, align='C', spacing=12)
    options, blocks = layout_options(contest.options)
    return VBox([Space(0, 48), headings, Space(0, 32), options],
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

def place_contest(canvas, ballot, contest):
    for section in ballot.sections:
        if contest in section.contests:
            content, blocks = layout_contest(section, contest)
            canvas.add(content, 'NC', 'NC')
            update_blockmap(canvas, blocks)

def layout_button(text):
    rect = Rect(button_w - 1, button_h - 1, radius=18,
                stroke=GREY, weight=1, fill=button_bg)
    box = Box((rect, (0.5, 0.5)), padding=0.5)
    return Box([(box, 0, 'MC'), (ButtonText(text), 0, 'MC')])

def place_ballot_label(canvas, ballot):
    canvas.add(NoteText(ballot.name), (10, 10), 'NW')

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
    paragraphs = text.replace('\n\n', '\n.\n').split('\n')
    canvas.add(VBox([Space(0, 48), TitleText(title), Space(0, 32),
                     VBox([InstructionsText(paragraph)
                           for paragraph in paragraphs], spacing=6)]),
               'NC', 'NC')

def place_highlight(canvas, option):
    x, y, w, h = blockmaps[canvas][option]
    highlight = layout_option_highlight(w, h)
    canvas.add(highlight, (x, y), under=0)
    update_blockmap(canvas, highlight=highlight)
    return highlight

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

def compile(ballot):
    model = Model(timeout_milliseconds=10000)
    video = Video(1024, 768)
    audio = Audio(22050)

    for section in ballot.sections:
        for contest in section.contests:
            model.contests.append(Contest(contest.maxsels))

    def add(list, item):
        index = len(list)
        list.append(item)
        return index

    def add_slot(layout, canvas, block, radius):
        (x, y, w, h), r = blockmaps[canvas][block], radius
        print 'slot', len(layout.slots), block, (x, y, w, h)
        layout.slots.append((x - r, y - r, w + r*2, h + r*2))

    def add_target(layout, canvas, block, radius, action):
        (x, y, w, h), r = blockmaps[canvas][block], radius
        print 'target', len(layout.targets), block, (x, y, w, h)
        layout.targets.append((x - r, y - r, w + r*2, h + r*2))
        links[layout].page.target_bindings.append(action)

    canvases = []

    # Add the instruction pages.
    for title, text, spoken in instructions:
        canvas = Box([], 0, 0, 1024, 768)
        place_instructions(canvas, title, text)
        links[canvas].i = len(canvases)
        links[canvas].instructions = (title, text, spoken)
        canvases.append(canvas)

    # Add the selection pages.
    contest_i = 0
    for section in ballot.sections:
        for contest in section.contests:
            canvas = Box([], 0, 0, 1024, 768)
            place_contest(canvas, ballot, contest)
            canvases.append(canvas)
            links[canvas].contest = contest
            links[canvas].section = section
            links[contest].canvas = canvas
            links[contest].i = contest_i
            contest_i += 1
    num_contests = contest_i

    for page_i, canvas in enumerate(canvases):
        # Create a page and corresponding layout for each canvas.
        page, layout = Page(), Layout(None)
        links[page].i = links[layout].i = page_i
        model.pages.append(page)
        video.layouts.append(layout)

        # Hook up the page, layout, canvas, and possible contest.
        links[layout].page = page
        links[layout].canvas = canvas
        links[page].canvas = canvas
        links[page].layout = layout
        links[canvas].page = page
        links[canvas].layout = layout
        links[page].contest = links[canvas].contest
        links[page].instructions = links[canvas].instructions
        links[page].section = links[canvas].section

    for page_i, page in enumerate(model.pages):
        # Add the navigation buttons to each page.
        layout = links[page].layout
        canvas = links[page].canvas
        previous = page_i > 0
        next = page_i < len(model.pages) - 1
        place_navigation(canvas, previous, next)

        # Add the behaviours for the navigation buttons.
        if previous:
            add_target(layout, canvas, 'previous', 0, Action(page_i - 1, 0))
            page.key_bindings.append((KLEFT, Action(page_i - 1, 0)))
        if next:
            add_target(layout, canvas, 'next', 0, Action(page_i + 1, 0))
            page.key_bindings.append((KRIGHT, Action(page_i + 1, 0)))

        # Render the page image.
        print 'render page:', page_i
        place_ballot_label(canvas, ballot)
        video.layouts[page_i].screen = Image(canvas)

    sprite_i = 0
    for page_i, page in enumerate(model.pages):
        # Create the default state for each page.
        print 'page:', page_i
        canvas = links[page].canvas
        layout = links[page].layout
        state = State(-1, -1, Sequence())
        layout.slots.append((0, 0, 0, 0))
        page.states.append(state)

        if links[page].contest:
            section = links[page].section
            contest = links[page].contest
            contest_i = links[contest].i
            print 'contest:', contest, contest_i

            if contest.question:
                print 'question'
                add(state.key_bindings, (KDOWN, Action(page_i, 1)))

                # Add the default state's entrance sound.
                text = [section.name, '@', contest.name, '@']
                sel_zero = Clip(audio, '').clip_i
                sel_one = Clip(audio, 'Your current selection is').clip_i
                text = [section.name, '@', contest.name, '@']
                text += ['@', (SNUMSELECTED, sel_zero, contest_i),
                         (SSELECTED, 0, contest_i)]
                text += ['@ To hear the full text of this proposition, ',
                         'press 8. @ Touch your selection on the screen, or '
                         '@ to select yes, press 7; to select no, press 9.']
                state.entry_sequence = Sequence(audio, *text)
            else:
                print 'race'
                # Add the default state's navigation behaviour.
                add(state.key_bindings, (KDOWN, Action(page_i, 1)))

                # Add the default state's entrance sound.
                sel_zero = Clip(audio, '').clip_i
                sel_one = Clip(audio, 'Your current selection is').clip_i
                text = [section.name, '@', contest.name, '@']
                if len(contest.options) == 1:
                    text += ['There is 1 candidate.']
                else:
                    text += ['There are', len(contest.options), 'candidates.']
                if contest.maxsels == 1:
                    text += ['@ Please vote for 1.']
                else:
                    text += ['@ Please vote for up to', contest.maxsels]
                text += ['@', (SNUMSELECTED, sel_zero, contest_i),
                         (SSELECTED, 0, contest_i)]
                text += ['@ Touch the screen to make selections',
                         'or press 8 to hear the choices.']

                if contest_i < num_contests - 1:
                    text += ['@@ To skip to the next contest, press 6.']
                if contest_i > 0:
                    text += ['@@ To go back to the previous contest, press 4.']
                state.entry_sequence = Sequence(audio, *text)

        elif links[page].instructions:
            title, text, spoken = links[page].instructions
            state.entry_sequence = Sequence(audio, spoken)
            state.timeout_page_i = page_i
            state.timeout_state_i = 0

        else:
            # non-instruction, non-selection pages
            pass

        if links[page].contest:
            for option_i, option in enumerate(contest.options):
                # Add the option.
                print 'option:', option
                unsel = Box((layout_option(option, 0), (4, 4)), padding=4)
                sel = Box((layout_option(option, 1), (4, 4)), padding=4)
                model.contests[contest_i].options.append(
                    Option(add(video.sprites, Image(unsel)),
                           add(video.sprites, Image(sel)),
                           Clip(audio, option.name).clip_i))

                Clip(audio, option.name + ' @ ' +
                            option.description.replace('\n', ' party @ '))

                # Add the option's target.
                add_target(layout, canvas, option, 4, Action(
                    -1, -1, [contest_i], [], option_i, ASELECT,
                    Sequence(audio, 'Selected', (SACTION, 0),
                             contest.question and 'on' or 'for', contest.name)))

        if links[page].contest and contest.question:
            add(state.key_bindings, (KYES, Action(
                -1, -1, [contest_i], [], 0, ASELECT,
                Sequence(audio, 'Selected', (SACTION, 0),
                         'on', contest.name))))
            add(state.key_bindings, (KNO, Action(
                -1, -1, [contest_i], [], 1, ASELECT,
                Sequence(audio, 'Selected', (SACTION, 0),
                         'on', contest.name))))
            state = State(-1, -1, Sequence(audio, contest.question,
                '@ To hear the text of this proposition again, '
                'press 8. @ Touch your selection on the screen, '
                'or @ to select yes, press 7; to select no, press 9.'))
            add(page.states, state)
            layout.slots.append((0, 0, 0, 0))
            add(state.key_bindings, (KDOWN, Action(page_i, 1)))
            add(state.key_bindings, (KYES, Action(
                -1, -1, [contest_i], [], 0, ASELECT,
                Sequence(audio, 'Selected', (SACTION, 0),
                         'on', contest.name))))
            add(state.key_bindings, (KNO, Action(
                -1, -1, [contest_i], [], 1, ASELECT,
                Sequence(audio, 'Selected', (SACTION, 0),
                         'on', contest.name))))

            for option_i, option in enumerate(contest.options):
                # Add the option area to the page.
                page.option_areas.append(contest_i)
                add_slot(layout, canvas, option, 4)

        if links[page].contest and not contest.question:
            for option_i, option in enumerate(contest.options):
                # Create the state in which the option is highlighted.
                highlight = place_highlight(canvas, option)
                left, top, width, height = blockmaps[canvas][option]
                x, y = int(left - 8), int(top - 8)
                w, h = width + 16, height + 16
                layout.slots.append((x, y, w, h))
                image = Image(canvas, x=-x, y=-y, width=w, height=h)
                sprite_i = add(video.sprites, image)
                canvas.remove(highlight)

                # Add the state's entrance sound.
                sequence = Sequence(
                    audio, (SSTATE, 1),
                    '@ To vote for this candidate, press 5.',
                    (option_i < len(contest.options) - 1) and
                    '@ To hear the next choice, press 8.' or
                    '@ To hear all the choices again, press 4.')

                state = State(sprite_i, option_i, sequence)

                state_i = add(page.states, state)
                print 'state:', state_i

                # Add the state's navigation behaviours.
                if option_i > 0:
                    add(state.key_bindings, (KUP, Action(page_i, state_i-1)))
                if option_i < len(contest.options) - 1:
                    add(state.key_bindings, (KDOWN, Action(page_i, state_i+1)))
                add(state.key_bindings, (KLEFT, Action(page_i, 0)))

                # Add the state's selection behaviour.
                action = Action(-1, -1, [contest_i], [], option_i, ASELECT,
                    Sequence(audio, 'Selected', (SACTION, 0),
                             'for', contest.name))
                add(state.key_bindings, (KSELECT, action))

            for option_i, option in enumerate(contest.options):
                # Add the option area to the page.
                page.option_areas.append(contest_i)
                add_slot(layout, canvas, option, 4)

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
            place_contest(page, ballot, contest)
            place_navigation(page)
            x, y, w, h = blockmaps[page][contest.options[0]]
            highlight = layout_option_highlight(w, h)
            page.add(highlight, (x, y), under=0)
            page.write('output/%d-%d.png' % (si + 1, ci + 1))

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

    model.contests.append(Contest(1))

    layout = Layout(Image(canvases[0]), [], [])
    video.layouts.append(layout)

    layout = Layout(Image(canvases[1]), [], [])
    video.layouts.append(layout)

    entry_sequence = Sequence(audio, '6 5 4')
    timeout_sequence = Sequence(audio, '3 2 1')

    page = Page()
    state = State(-1, entry_sequence, timeout_sequence=timeout_sequence)
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
    open('ballot', 'w').write(compile(ballot))
    # Clip('There are 3 candidates for governor.').serialize()
    # open('output/ballot', 'w').write(test_compile(ballot))
