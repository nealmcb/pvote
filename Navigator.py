[OP_ADD, OP_REMOVE, OP_APPEND, OP_POP, OP_CLEAR] = range(5)
[SG_CLIP, SG_OPTION, SG_LIST_SELS, SG_COUNT_SELS, SG_MAX_SELS] = range(5)
[PR_GROUP_EMPTY, PR_GROUP_FULL, PR_OPTION_SELECTED] = range(3)

class Navigator:
    def __init__(self, model, audio, video, printer):
        self.model = model
        [self.audio, self.video, self.printer] = [audio, video, printer]
        self.selections = [[] for group in model.groups]
        self.page_i = None
        self.goto(0, 0)

    def goto(self, page_i, state_i):
        if page_i != None and self.page_i != len(self.model.pages) - 1:
            if page_i == len(self.model.pages) - 1:
                self.printer.write(self.selections)
            [self.page_i, self.page] = [page_i, self.model.pages[page_i]]
            [self.state_i, self.state] = [state_i, self.page.states[state_i]]
            self.play(self.state.segments)
        self.update()

    def update(self):
        self.video.goto(self.page_i)
        self.video.paste(self.state.sprite_i, self.state_i)

        slot_i = len(self.page.states) 
        for area in self.page.option_areas:
            unselected = area.option_i not in self.selections[area.group_i]
            group = self.model.groups[area.group_i]
            option = group.options[area.option_i]
            self.video.paste(option.sprite_i + unselected, slot_i)
            slot_i = slot_i + 1

        for area in self.page.counter_areas:
            count = len(self.selections[area.group_i])
            self.video.paste(area.sprite_i + count, slot_i)
            slot_i = slot_i + 1

        for area in self.page.review_areas:
            slot_i = self.review(area.group_i, slot_i, area.cursor_sprite_i)

    def review(self, group_i, slot_i, cursor_sprite_i):
        group = self.model.groups[group_i]
        selections = self.selections[group_i]
        for i in range(group.max_sels):
            if i < len(selections):
                option = group.options[selections[i]]
                self.video.paste(option.sprite_i, slot_i)
                if option.writein_group_i != None:
                    self.review(option.writein_group_i, slot_i + 1, None)
            if i == len(selections) and cursor_sprite_i != None:
                self.video.paste(cursor_sprite_i, slot_i)
            slot_i = slot_i + 1 + group.max_chars
        return slot_i

    def press(self, key):
        for binding in self.state.bindings + self.page.bindings:
            if key == binding.key and self.test(binding.conditions):
                return self.invoke(binding)

    def touch(self, target_i):
        for binding in self.state.bindings + self.page.bindings:
            if target_i == binding.target_i and self.test(binding.conditions):
                return self.invoke(binding)

    def test(self, conditions):
        for cond in conditions:
            [group_i, option_i] = self.get_option(cond)
            if cond.predicate == PR_GROUP_EMPTY:
                result = len(self.selections[group_i]) == 0
            if cond.predicate == PR_GROUP_FULL:
                max = self.model.groups[group_i].max_sels
                result = len(self.selections[group_i]) == max
            if cond.predicate == PR_OPTION_SELECTED:
                result = option_i in self.selections[group_i]
            if cond.invert == result:
                return 0
        return 1

    def invoke(self, binding):
        for step in binding.steps:
            self.execute(step)
        self.audio.stop()
        self.play(binding.segments)
        self.goto(binding.next_page_i, binding.next_state_i)

    def execute(self, step):
        [group_i, option_i] = self.get_option(step)
        group = self.model.groups[group_i]
        selections = self.selections[group_i]
        selected = option_i in selections

        if step.op == OP_ADD and not selected or step.op == OP_APPEND:
            if len(selections) < group.max_sels:
                selections.append(option_i)
        if step.op == OP_REMOVE and selected:
            selections.remove(option_i)

        if step.op == OP_POP and len(selections) > 0:
            selections.pop()
        if step.op == OP_CLEAR:
            self.selections[group_i] = []

    def timeout(self):
        self.play(self.state.timeout_segments)
        self.goto(self.state.timeout_page_i, self.state.timeout_state_i)

    def play(self, segments):
        for segment in segments:
            if self.test(segment.conditions):
                if segment.type == SG_CLIP:
                    self.audio.play(segment.clip_i)
                else:
                    [group_i, option_i] = self.get_option(segment)
                    group = self.model.groups[group_i]
                    selections = self.selections[group_i]

                if segment.type == SG_OPTION:
                    self.play_option(group.options[option_i], segment.clip_i)
                if segment.type == SG_LIST_SELS:
                    for option_i in selections:
                        self.play_option(group.options[option_i], segment.clip_i)
                if segment.type == SG_COUNT_SELS:
                    self.audio.play(segment.clip_i + len(selections))
                if segment.type == SG_MAX_SELS:
                    self.audio.play(segment.clip_i + group.max_sels)

    def play_option(self, option, offset):
        self.audio.play(option.clip_i + offset)
        if option.writein_group_i != None:
            writein_group = self.model.groups[option.writein_group_i]
            for option_i in self.selections[option.writein_group_i]:
                self.audio.play(writein_group.options[option_i].clip_i)

    def get_option(self, object):
        if object.group_i == None:
            area = self.page.option_areas[object.option_i]
            return [area.group_i, area.option_i]
        return [object.group_i, object.option_i]
