import reportlab.pdfbase.pdfmetrics
import reportlab.pdfbase.ttfonts
import reportlab.pdfbase._fontdata
import reportlab.graphics.renderPM
from reportlab.graphics import shapes
from reportlab.lib.colors import Color

def blend(origin, target, fraction=0.5):
    r = origin.red*(1.0 - fraction) + target.red*fraction
    g = origin.green*(1.0 - fraction) + target.green*fraction
    b = origin.blue*(1.0 - fraction) + target.blue*fraction
    return Color(r, g, b)

BLACK = Color(0, 0, 0)
GREY = Color(0.5, 0.5, 0.5)
WHITE = Color(1, 1, 1)
RED = Color(1, 0, 0)
ORANGE = Color(1, 0.5, 0)
YELLOW = Color(1, 1, 0)
GREEN = Color(0, 1, 0)
CYAN = Color(0, 1, 1)
BLUE = Color(0, 0, 1)
MAGENTA = Color(1, 0, 1)

def curry(function, **defaults):
    def curried(*args, **kw):
        for key, value in defaults.items():
            if key not in kw:
                kw[key] = value
        return function(*args, **kw)
    return curried

class Font:
    map = {}
    dbounds = (0, 0.2, 0, 0) # adjust top bound down by 0.2 em

    def __init__(self, filename, dbounds=None, encoding='StandardEncoding'):
        self.name = 'font-%d' % (len(Font.map) + 1)
        self.dbounds = dbounds or Font.dbounds
        self.ttf = reportlab.pdfbase.ttfonts.TTFont(self.name, filename)
        self.ttf.encoding.vector = \
            reportlab.pdfbase._fontdata.encodings[encoding]
        reportlab.pdfbase.pdfmetrics.registerFont(self.ttf)
        Font.map[self.name] = self

    def measure(self, text, size):
        return self.ttf.stringWidth(text, size)

REGULAR_FONT = Font('LucidaGrande.ttf')
BOLD_FONT = Font('LucidaGrandeBold.ttf')
shapes.STATE_DEFAULTS['fontName'] = REGULAR_FONT.name

# An anchor or alignment specification is a string of these characters:
#     'n': north edge (min y)
#     's': south edge (max y)
#     'm': vertical middle (avg y)
#     'y': y axis (x = 0, default)
#     'w': west edge (min x)
#     'e': east edge (max x)
#     'c': horizontal center (avg x)
#     'x': x axis or baseline (y = 0, default)
#     'a': starting point (lines only)
#     'z': ending point (lines only)
# A lowercase letter indicates the exact location; an uppercase letter
# rounds the anchor coordinate to the nearest integer.

class Block:
    """The basic component of a drawing."""

    __version__ = 0

    def __init__(self, **props):
        for name in props:
            setattr(self, name, props[name])

    def __getattr__(self, name):
        if hasattr(self.__class__, 'get_' + name):
            return getattr(self, 'get_' + name)()
        elif hasattr(self.__class__, 'update_' + name):
            cache = self.__dict__.setdefault('__cache__', {})
            updates, value = cache.get(name, (0, None))
            if self.__version__ > updates:
                value = getattr(self, 'update_' + name)()
                cache[name] = self.__version__, value
            return value
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if hasattr(self.__class__, 'set_' + name):
            getattr(self, 'set_' + name)(value)
        elif hasattr(self.__class__, name):
            self.__dict__[name] = value
        else:
            raise AttributeError(name)
        self.__dict__['__version__'] = self.__version__ + 1

    def update_bounds(self):
        return 0, 0, 0, 0

    def locate(self, child):
        if child is self:
            return self.bounds

    def anchor(self, anchor='', ax=0, ay=0):
        """Locate an anchor according to this block's bounding box."""
        if isinstance(anchor, tuple) and len(anchor) == 2:
            return anchor
        if anchor == 0:
            return (0, 0)
        bw, bn, be, bs = self.bounds
        xvalues = {'w': bw, 'e': be, 'c': (bw + be)/2.0, 'y': 0}
        for code, x in xvalues.items():
            if code in anchor:
                ax = x
            if code.upper() in anchor:
                ax = round(x)
        yvalues = {'n': bn, 's': bs, 'm': (bn + bs)/2.0, 'x': 0}
        for code, y in yvalues.items():
            if code in anchor:
                ay = y
            if code.upper() in anchor:
                ay = round(y)
        return ax, ay

    def put(self, d, x, y):
        pass

    def draw(self, width=None, height=None, x=0, y=0, anchor='xy'):
        bw, bn, be, bs = self.bounds
        drawing = shapes.Drawing(width or be, height or bs)
        ax, ay = self.anchor(anchor)
        self.put(drawing, x - ax, y - ay)
        return drawing

    def render(self, width=None, height=None, x=0, y=0, anchor='xy'):
        return reportlab.graphics.renderPM.drawToPIL(
            self.draw(width, height, x, y, anchor))

    def write(self, filename, width=None, height=None, x=0, y=0, anchor='xy'):
        reportlab.graphics.renderPM.drawToFile(
            self.draw(width, height, x, y, anchor), filename, 'PNG')

class Shape(Block):
    """A block consisting of a single reportlab.graphics.shapes.Shape."""

    __propmap__ = {}
    __shape__ = None

    def __init__(self, shape, **props):
        self.__shape__ = shape
        Block.__init__(self, **props)

    def __getattr__(self, name):
        if name in self.__propmap__:
            return getattr(self.__shape__, self.__propmap__[name])
        return Block.__getattr__(self, name)

    def __setattr__(self, name, value):
        if name in self.__propmap__:
            self.__shape__.__dict__[self.__propmap__[name]] = value
            self.__dict__['__version__'] = self.__version__ + 1
        else:
            Block.__setattr__(self, name, value)

    def update_bounds(self):
        xl, yl, xh, yh = self.__shape__.getBounds()
        return xl, -yh, xh, -yl

    def put(self, d, x, y):
        shape = self.__shape__.copy()
        shape.x, shape.y = x, d.height - y
        d.add(shape)

class Text(Shape):
    __propmap__ = {'text': 'text', 'size': 'fontSize', 'fill': 'fillColor'}

    def __init__(self, text, **props):
        Shape.__init__(self, shapes.String(0, 0, text), **props)

    def __repr__(self):
        return 'Text(%r)' % self.text

    def update_bounds(self):
        xl, yl, xh, yh = self.__shape__.getBounds()
        dw, dn, de, ds = [ems * self.size for ems in self.font.dbounds]
        return xl + dw, -yh + dn, xh + de, -yl + ds

    def get_font(self):
        return Font.map[self.__shape__.fontName]

    def set_font(self, font):
        self.__shape__.fontName = font.name

class Circle(Shape):
    __propmap__ = {'radius': 'r', 'fill': 'fillColor', 'stroke': 'strokeColor',
                   'weight': 'strokeWidth', 'dash': 'strokeDashArray'}

    def __init__(self, radius, **props):
        Shape.__init__(self, shapes.Circle(0, 0, radius), **props)

    def __repr__(self):
        return 'Circle(%s)' % self.radius

    def put(self, d, x, y):
        shape = self.__shape__.copy()
        shape.cx, shape.cy = x, d.height - y
        d.add(shape)

class FlippedShape(Shape):
    __group__ = None

    def __init__(self, shape, **props):
        self.__group__ = shapes.Group(shape, transform=(1, 0, 0, -1, 0, 0))
        Shape.__init__(self, shape, **props)

    def update_bounds(self):
        xl, yl, xh, yh = self.__group__.getBounds()
        return xl, -yh, xh, -yl

    def put(self, d, x, y):
        group = self.__group__.copy()
        group.transform = self.__group__.transform[:4] + (x, d.height - y)
        d.add(group)

class Rect(FlippedShape):
    __propmap__ = {'width': 'width', 'height': 'height', 'fill': 'fillColor',
                   'stroke': 'strokeColor', 'weight': 'strokeWidth',
                   'dash': 'strokeDashArray', 'join': 'strokeLineJoin'}

    def __init__(self, width, height, **props):
        FlippedShape.__init__(self, shapes.Rect(0, 0, width, height), **props)

    def __repr__(self):
        return 'Rect(%s, %s%s)' % (
            self.width, self.height,
            self.radius > 0 and (', radius=%s' % self.radius) or '')

    def get_radius(self):
        return self.__shape__.rx

    def set_radius(self, radius):
        self.__shape__.rx = self.__shape__.ry = radius

class Line(FlippedShape):
    __propmap__ = {'stroke': 'strokeColor', 'cap': 'strokeLineCap',
                   'weight': 'strokeWidth', 'dash': 'strokeDashArray',
                   'fill': 'fillColor'}

    def __init__(self, vx, vy, **props):
        FlippedShape.__init__(self, shapes.Line(0, 0, vx, vy), **props)

    def __repr__(self):
        return 'Line(%s, %s)' % self.vector

    def get_vector(self):
        return self.__shape__.x2, -self.__shape__.y2

    def set_vector(self, (vx, vy)):
        self.__shape__.x2, self.__shape__.y2 = vx, -vy

    def anchor(self, anchor=''):
        ax, ay = 0, 0
        values = {'a': (0, 0), 'z': self.vector}
        for code, (x, y) in values.items():
            if code in anchor:
                ax, ay = x, y
            if code.upper() in anchor:
                ax, ay = round(x), round(y)
        return Shape.anchor(self, anchor, ax, ay)

class Polygon(FlippedShape):
    __propmap__ = {'fill': 'fillColor', 'stroke': 'strokeColor',
                   'weight': 'strokeWidth', 'dash': 'strokeDashArray',
                   'join': 'strokeLineJoin', 'miter': 'strokeMiterLimit'}

    scale = (1, 1)

    def __init__(self, vertices=[(0, 0)], **props):
        points = sum([[x, y] for (x, y) in vertices], [])
        FlippedShape.__init__(self, shapes.Polygon(points), **props)

    def __repr__(self):
        return 'Polygon(<%d vertices>)' % len(self.vertices)

    def get_vertices(self):
        points = self.__shape__.points
        xs = map(points.__getitem__, range(0, len(points), 2))
        ys = map(points.__getitem__, range(1, len(points), 2))
        return zip(xs, ys)

    def set_vertices(self, vertices):
        self.__shape__.points = sum([[x, y] for (x, y) in vertices], [])

    def set_scale(self, scale):
        if isinstance(scale, (int, long, float)):
            scale = (scale, scale)
        self.__dict__['scale'] = xscale, yscale = tuple(scale)
        self.__group__.transform = (xscale, 0, 0, -yscale, 0, 0)

class Space(Block):
    """An empty space."""
    width = 0
    height = 0

    def __init__(self, width=0, height=0):
        self.width, self.height = width, height

    def __repr__(self):
        return 'Space(%s, %s)' % (self.width, self.height)

    def get_bounds(self):
        return (0, 0, self.width, self.height)

class Box(Block):
    """A Block containing other explicitly positioned blocks."""
    frame = None, None, None, None
    padding = (0, 0, 0, 0)

    def __init__(self, children=[], fw=None, fn=None, fe=None, fs=None,
                       **props):
        self.__dict__['children'] = []
        self.frame = (fw, fn, fe, fs)
        if not isinstance(children, list):
            children = [children]
        for child in children:
            if not isinstance(child, tuple):
                child = (child,)
            self.add(*child)
        Block.__init__(self, **props)

    def __repr__(self):
        return 'Box(<%d child%s>)' % (
            len(self.children), len(self.children) != 1 and 'ren' or '')

    def add(self, block, xy=0, anchor='xy', under=None, over=None):
        assert isinstance(block, Block)
        position = len(self.children)
        if under is not None:
            position = self.index(under)
        elif over is not None:
            position = self.index(over) + 1
        self.children.insert(position, (block, self.anchor(xy), anchor))
        self.__version__ += 1

    def remove(self, block):
        self.children.pop(self.index(block))

    def index(self, block):
        if isinstance(block, int):
            return block
        for i, child in enumerate(self.children):
            if child[0] is block:
                return i
        raise ValueError('%r not among children' % block)

    def update_bounds(self):
        xexts, yexts = [], []
        for block, (x, y), anchor in self.children:
            bw, bn, be, bs = block.bounds
            ax, ay = block.anchor(anchor)
            xexts += [bw + x - ax, be + x - ax]
            yexts += [bn + y - ay, bs + y - ay]
        xexts, yexts = xexts or [0], yexts or [0]
        pw, pn, pe, ps = self.padding
        bw, bn, be, bs = self.frame
        if bw is None: bw = min(xexts) - pw
        if bn is None: bn = min(yexts) - pn
        if be is None: be = max(xexts) + pe
        if bs is None: bs = max(yexts) + ps
        return bw, bn, be, bs

    def locate(self, child):
        if child is self:
            return self.bounds
        for block in self.children:
            for block, (x, y), anchor in self.children:
                bounds = block.locate(child)
                if bounds:
                    bw, bn, be, bs = bounds
                    ax, ay = block.anchor(anchor)
                    return bw + x - ax, bn + y - ay, be + x - ax, bs + y - ay

    def put(self, d, xx, yy):
        for block, (x, y), anchor in self.children:
            ax, ay = block.anchor(anchor)
            # print self, 'put (%s, %s):' % (xx + x - ax, yy + y - ay), block
            block.put(d, xx + x - ax, yy + y - ay)

    def set_padding(self, spec):
        if isinstance(spec, (int, long, float)):
            spec = [spec]
        spec = list(spec)
        if len(spec) < 2:
            spec.append(spec[0])
        if len(spec) < 3:
            spec.append(spec[0])
        if len(spec) < 4:
            spec.append(spec[1])
        self.__dict__['padding'] = tuple(spec)

class HBox(Box):
    """A Box that places its children left to right in a row."""
    int = False
    align = 'x'
    spacing = 0

    def __init__(self, blocks=[], **props):
        self.__dict__['blocks'] = blocks
        Box.__init__(self, [], **props)
        del self.__dict__['children']

    def __repr__(self):
        return 'HBox(<%d child%s>)' % (
            len(self.blocks), len(self.blocks) != 1 and 'ren' or '')

    def add(self, block, before=None, after=None):
        assert isinstance(block, Block)
        position = len(self.blocks)
        if before is not None:
            position = self.index(before)
        elif after is not None:
            position = self.index(after) + 1
        self.blocks.insert(position, block)
        self.__version__ += 1

    def index(self, block):
        if isinstance(block, int):
            return block
        return self.blocks.index(block)

    def update_children(self):
        align = self.align + (self.int and 'W' or 'w')
        children = []
        x = 0
        first = True
        for block in self.blocks:
            if not first:
                x += self.spacing
            children.append((block, (x, 0), align))
            bw, bn, be, bs = block.bounds
            x += self.int and round(be - bw) or be - bw
            first = False
        return children

class VBox(HBox):
    """A Box that places its children top to bottom in a column."""
    align = 'y'

    def __init__(self, blocks=[], **props):
        HBox.__init__(self, blocks, **props)

    def __repr__(self):
        return 'VBox(<%d child%s>)' % (
            len(self.blocks), len(self.blocks) != 1 and 'ren' or '')

    def update_children(self):
        align = self.align + (self.int and 'N' or 'n')
        children = []
        y = 0
        first = True
        for block in self.blocks:
            if not first:
                y += self.spacing
            children.append((block, (0, y), align))
            bw, bn, be, bs = block.bounds
            y += self.int and round(bs - bn) or bs - bn
            first = False
        return children

class Paragraph(VBox):
    text = ''
    width = 0
    font = Font.map[shapes.String(0, 0, '').fontName]
    size = shapes.String(0, 0, '').fontSize
    fill = BLACK

    def __init__(self, text, width, **props):
        self.text = text
        self.width = width
        VBox.__init__(self, [], **props)
        del self.__dict__['blocks']

    def __repr__(self):
        return 'Text(%r)' % self.text

    def add(self, *args):
        raise TypeError('cannot add children to paragraphs')

    def update_blocks(self):
        Row = curry(Text, font=self.font, size=self.size, fill=self.fill)
        blocks = []
        row = ''
        for word in self.text.split():
            newrow = row and (row + ' ' + word) or word
            if self.font.measure(newrow, self.size) > self.width:
                blocks.append(Row(row))
                row = word
            else:
                row = newrow
        if row:
            blocks.append(Row(row))
        return blocks

if __name__ == '__main__':
    Regular = curry(Text, font=Font('LucidaGrande.ttf'))
    Bold = curry(Text, font=Font('LucidaGrandeBold.ttf'))

    b = Box()
    b.add(Regular('center'), (100, 100), 'mc')
    b.add(Bold('SE', size=24), (200, 200), 'se')
    b.add(Regular('blargh', size=18), (0, 200), 'xw')
    b.add(VBox([HBox([Regular('abc'),
                      Regular('def', size=24),
                      Bold('ghi', fill=RED, size=18)]),
                Regular('This is a long sentence'),
                HBox([Space(20), Regular('with its second line indented.')])]))
    b.add(Circle(30, stroke=BLUE, fill=ORANGE), (50, 150), 'mc')
    b.add(Rect(40, 20, fill=GREEN), (150, 50), 'nc')
    b.add(Line(20, -10, weight=2), (150, 150), 'SE')
    b.add(Polygon([(0, 0), (20, 0), (10, 20)], scale=2, fill=MAGENTA),
          (50, 50), 'nc')
    b.add(Circle(2), (50, 50))
    b.add(Circle(2), (50, 150))
    b.add(Circle(2), (150, 50))
    b.add(Circle(2), (150, 150))
    b.add(Paragraph('Here is a flowed paragraph of text that should '
                    'be wrapped over several lines.', 100), (50, 150))
    b.write('output/layout.png', 200, 200)
