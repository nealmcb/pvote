# $Id: Navigator.py,v 1.6 2006/08/01 18:20:09 ping Exp $

class Navigator:
    def __init__(self, model, video, recorder):
        self.model, self.video, self.recorder = model, video, recorder
        self.selections = [[] for contest in model.contests]
        self.goto(0)
        self.update()

    def goto(self, page_i):
        if page_i == len(self.model.pages) - 1:
            self.recorder.write(self.selections)
        self.page_i, self.page = page_i, self.model.pages[page_i]
        self.writein, self.chars = None, []

    def update(self):
        if self.writein:
            contest = self.model.contests[self.writein.contest_i]
            subpage = self.model.subpages[contest.subpage_i]
            self.video.goto(len(self.model.pages) + contest.subpage_i)
            offset = len(subpage.subtargets)
            for i, sprite_i in enumerate(self.chars):
                self.video.paste(sprite_i, offset + i)
            if len(self.chars) < contest.max_chars:
                self.video.paste(subpage.cursor_i, offset + len(self.chars))
        else:
            self.video.goto(self.page_i)

            slot_i = len(self.page.targets)
            for option in self.page.options:
                if [option.sprite_i] in self.selections[option.contest_i]:
                    self.video.paste(option.sprite_i, slot_i)
                slot_i += 1

            for writein in self.page.writeins:
                for selection in self.selections[writein.contest_i]:
                    if selection[0] == writein.sprite_i:
                        self.video.paste(writein.sprite_i, slot_i)
                        for i, sprite_i in enumerate(selection[1:]):
                            self.video.paste(sprite_i, slot_i + 1 + i)
                slot_i += 1 + self.model.contests[writein.contest_i].max_chars

            for review in self.page.reviews:
                contest = self.model.contests[review.contest_i]
                selections = self.selections[review.contest_i]
                for i in range(contest.max_sels):
                    if i < len(selections):
                        self.video.paste(selections[i][0], slot_i)
                        for i, sprite_i in enumerate(selections[i][1:]):
                            self.video.paste(sprite_i, slot_i + 1 + i)
                    slot_i += 1 + contest.max_chars

    def activate(self, slot_i):
        if self.writein:
            contest = self.model.contests[self.writein.contest_i]
            subpage = self.model.subpages[contest.subpage_i]
            subtarget = subpage.subtargets[slot_i]
            if subtarget.action == 0 or subtarget.action == 1 and self.chars:
                if len(self.chars) < contest.max_chars:
                    self.chars += [subtarget.sprite_i]
            if subtarget.action == 2:
                self.chars[-1:] = []
            if subtarget.action == 3:
                self.chars = []
            if subtarget.action == 4:
                self.goto(self.page_i)
            if subtarget.action == 5 and self.chars:
                self.selections[self.writein.contest_i] += [
                    [self.writein.sprite_i] + self.chars]
                self.goto(self.page_i)

        elif slot_i < len(self.page.targets):
            target = self.page.targets[slot_i]
            if target.action == 1:
                self.selections[target.contest_i] = []
            if target.action == 2:
                self.selections = [[] for contest in self.model.contests]
            self.goto(target.page_i)

        elif slot_i < len(self.page.targets) + len(self.page.options):
            option = self.page.options[slot_i - len(self.page.targets)]
            selections = self.selections[option.contest_i]
            contest = self.model.contests[option.contest_i]
            if [option.sprite_i] in selections:
                selections.remove([option.sprite_i])
            elif len(selections) < contest.max_sels:
                selections += [[option.sprite_i]]

        else:
            slot_i -= len(self.page.targets) + len(self.page.options)
            for writein in self.page.writeins:
                contest = self.model.contests[writein.contest_i]
                if slot_i < 1 + contest.max_chars:
                    selections = self.selections[writein.contest_i]
                    for i, selection in enumerate(selections):
                        if selection[0] == writein.sprite_i:
                            self.writein, self.chars = writein, selection[1:]
                            selections[i:i+1] = []
                            break
                    else:
                        if len(selections) < contest.max_sels:
                            self.writein = writein
                    break
                slot_i -= 1 + contest.max_chars

        self.update()
