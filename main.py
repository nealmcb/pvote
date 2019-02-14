#!/usr/bin/python
# $Id: main.py,v 1.2 2007/03/28 22:36:28 ping Exp $

import Ballot, verifier, Audio, Video, Printer, Navigator, pygame

AUDIO_DONE = pygame.USEREVENT
TIMER_DONE = pygame.USEREVENT + 1

ballot = Ballot.Ballot(open("ballot"))
verifier.verify(ballot)
audio = Audio.Audio(ballot.audio)
video = Video.Video(ballot.video)
printer = Printer.Printer(ballot.text)
navigator = Navigator.Navigator(ballot.model, audio, video, printer)

while 1:
    pygame.display.update()
    pygame.time.set_timer(TIMER_DONE, ballot.model.timeout_ms)
    event = pygame.event.wait()
    pygame.time.set_timer(TIMER_DONE, 0)

    if event.type == pygame.KEYDOWN:
        navigator.press(event.key)
    if event.type == pygame.MOUSEBUTTONDOWN:
        [x, y] = event.pos
        target_i = video.locate(x, y)
        if target_i != None:
            navigator.touch(target_i)
    if event.type == AUDIO_DONE:
        audio.next()
    if event.type == TIMER_DONE and not audio.playing:
        navigator.timeout()
