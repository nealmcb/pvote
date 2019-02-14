# $Id: Recorder.py,v 1.2 2007/01/30 05:20:46 ping Exp $

import sha

class Recorder:
    def __init__(self, ballot):
        self.hash = sha.new(ballot.data).hexdigest()

    def write(self, selections):
        file = open('votes', 'r+')
        while file.read(4) != '\xff\xff\xff\xff':
            pass
        items = []
        size = getint(file)
        while size:
            items += [file.read(size)]
            size = getint(file)
        for i, contest in enumerate(selections):
            for selection in contest:
                item = self.hash + putint(i) + putint(selection)
                items += [item]
        items.sort()
        start = 0
        maxlength = max([len(item) for item in items] or [''])
        for i, item in enumerate(items):
            start += 4 + (4 + maxlength)*i + 4
        file.write('\0'*(start - file.tell()))
        file.seek(start)
        file.write('\xff\xff\xff\xff')
        for item in items:
            file.write(putint(len(item)) + item)
        file.write(putint(0))
        file.seek(0)
        file.write('\0'*start)

def getint(stream):
    bytes = [ord(char) for char in stream.read(4)]
    return (bytes[0]<<24) + (bytes[1]<<16) + (bytes[2]<<8) + bytes[3]

def putint(n):
    char = lambda n: chr(n & 255)
    return char(n>>24) + char(n>>16) + char(n>>8) + char(n)
