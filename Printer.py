# $Id: Printer.py,v 1.5 2007/03/12 09:28:34 ping Exp $

class Printer:
    def __init__(self, text):
        self.text = text

    def write(self, selections):
        for [group_i, options] in enumerate(selections):
            if len(options):
                group = self.text.groups[group_i]
                line = group.name + ':'
                while len(line) < 55:
                    line = line + ' '
                if group.writein:
                    for option in options:
                        line = line + group.options[option]
                    print line
                else:
                    for option in options:
                        print line + group.options[option]
                        line = ' '*55
                print
        print '\f'
