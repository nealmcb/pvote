#!/usr/bin/python
# $Id: run,v 1.10 2007/11/23 07:38:39 ping Exp $

import Ballot, Navigator, Recorder, Video
from pygame import display, event, MOUSEBUTTONDOWN, KEYDOWN

ballot = Ballot.Ballot('ballot')
video = Video.Video(ballot.imagelib)
recorder = Recorder.Recorder(ballot)
navigator = Navigator.Navigator(ballot.model, video, recorder)
while 1:
    display.update()
    e = event.wait()
    if e.type == MOUSEBUTTONDOWN:
        slot = video.locate(*e.pos)
        if slot is not None:
            navigator.activate(slot)
