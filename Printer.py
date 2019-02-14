# $Id: Printer.py,v 1.9 2007/03/28 22:36:28 ping Exp $

class Printer:
    def __init__(self, text):
        self.text = text

    def write(self, selections):
        for [group_i, selection] in enumerate(selections):
            group = self.text.groups[group_i]
            if group.writein:
                if len(selection):
                    print "\n+ " + group.name
                    line = ""
                    for option_i in selection:
                        if len(line) + len(group.options[option_i]) + 1 > 60:
                            print "= " + line
                            line = ""
                        line = line + group.options[option_i] + "~"
                    print "= " + line
            else:
                if len(selection):
                    print "\n* " + group.name
                    for [option_i, option] in enumerate(group.options):
                        if option_i in selection:
                            print "- " + option
                else:
                    print "\n* " + group.name + " ~ NO SELECTION"
        print "\n~\f"
