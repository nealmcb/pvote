class Navigator:
    def __init__(self, model, video, audio, recorder):
        self.model, self.video, self.audio = model, video, audio
        self.recorder = recorder
        self.selections = [[] for group in model.groups]
        self.goto(0, 0)
        self.update()

    def goto(self, page_i, state_i):
        if page_i == len(self.model.pages) - 1:
            self.recorder.write(self.selections)
        self.page_i, self.page = page_i, self.model.pages[page_i]
        self.state_i, self.state = state_i, self.page.states[state_i]
        self.play(self.state.entry_feedback, -1)

    def update_writein(self, group_i, slot_i):
        if group_i != -1:
            group = self.model.groups[group_i]
            selections = self.selections[group_i]
            for i in range(group.max_sels):
                if i < len(selections):
                    option = group.options[selections[i]]
                    self.video.paste(option.sel_sprite_i, slot_i + i)

    def update(self):
        self.video.goto(self.page_i)
        if self.state.sprite_i != -1:
            self.video.paste(self.state.sprite_i, self.state_i)

        slot_i = len(self.page.states) 
        for area in self.page.option_areas:
            if area.option_i in self.selections[area.group_i]:
                self.video.paste(area.option.sel_sprite_i, slot_i)
                self.update_writein(area.option.writein_group_i, slot_i + 1)
            else:
                self.video.paste(area.option.unsel_sprite_i, slot_i)
            slot_i += 1
            if area.option.writein_group_i != -1:
                slot_i += self.model.groups[area.group_i].max_chars

        for area in self.page.counter_areas:
            count = len(self.selections[area.group_i])
            self.video.paste(area.number_sprite_i + count, slot_i)
            slot_i += 1

        for area in self.page.review_areas:
            group = self.model.groups[area.group_i]
            selections = self.selections[area.group_i]
            for i in range(group.max_sels):
                if i < len(selections):
                    option = group.options[selections[i]]
                    self.video.paste(option.sel_sprite_i, slot_i)
                    self.update_writein(option.writein_group_i, slot_i + 1)
                if i == len(selections) and area.cursor_sprite_i != -1:
                    self.video.paste(area.cursor_sprite_i, slot_i)
                slot_i += 1 + group.max_chars

    def key(self, key):
        for key_binding in self.state.key_bindings + self.page.key_bindings:
            if key_binding.key == key:
                return self.execute(key_binding.action)

    def touch(self, target_i):
        self.execute(self.page.target_bindings[target_i].action)

    def select(self, action, op, group_i, option_i):
        feedback = action.default_feedback
        group = self.model.groups[group_i]
        selections = self.selections[group_i]
        present = option_i in selections

        if op == 0 and present:
            feedback = action.no_effect_feedback
        elif op == 1 and present:
            selections.remove(option_i)
        elif op == 2 and present:
            selections.remove(option_i)
            feedback = action.toggle_off_feedback
        elif op == 0 or op == 2 and not present:
            if len(selections) == group.max_sels:
                feedback = action.full_feedback
            else:
                selections.append(option_i)
        elif op == 1 and not present:
            feedback = action.no_effect_feedback
        elif op == 3:
            if len(selections) == group.max_sels:
                feedback = action.full_feedback
            else:
                selections.append(option_i)
        elif op == 4:
            if len(selections) == group.max_sels:
                feedback = action.full_feedback
            elif len(selections) == 0:
                feedback = action.empty_feedback
            else:
                selections.append(option_i)
        elif op == 5:
            if len(selections) == 0:
                feedback = action.empty_feedback
            else:
                selections.pop()
        return feedback

    def execute(self, action):
        feedback = action.default_feedback

        if action.clear_group_is:
            feedback = action.no_effect_feedback
            for group_i in action.clear_group_is:
                if self.selections[group_i]:
                    self.selections[group_i] = []
                    feedback = action.default_feedback

        if action.option_op != -1:
            for ref in action.option_refs:
                feedback = self.select(action, action.option_op,
                                       ref.group_i, ref.option_i)

        if action.option_area_op != -1:
            area = self.page.option_areas[action.option_area_i]
            feedback = self.select(action, action.option_area_op,
                                   area.group_i, area.option_i)

        self.audio.stop()
        self.play(feedback, action.option_area_i)
        if action.next_page_i != -1:
            self.goto(action.next_page_i, action.next_state_i)
        self.update()

    def timeout(self):
        self.play(self.state.timeout_feedback, -1)
        if self.state.timeout_page_i != -1:
            self.goto(self.state.timeout_page_i, self.state.timeout_state_i)
        self.update()

    def play_option(self, option, offset):
        self.audio.play(option.clip_i + offset)
        if option.writein_group_i != -1:
            writein_group = self.model.groups[option.writein_group_i]
            for option_i in self.selections[option.writein_group_i]:
                self.audio.play(writein_group.options[option_i].clip_i)

    def play(self, sequence, action_option_area_i):
        for segment in sequence.segments:
            if segment.type == 0:
                self.audio.play(segment.clip_i)
            elif segment.type == 1:
                group = self.model.groups[segment.group_i]
                option = group.options[segment.option_i]
                self.audio.play(option.clip_i + segment.clip_i)
            elif segment.type == 2:
                area = self.page.option_areas[self.state.option_area_i]
                self.play_option(area.option, segment.clip_i)
            elif segment.type == 3:
                area = self.page.option_areas[action_option_area_i]
                self.play_option(area.option, segment.clip_i)
            elif segment.type == 4:
                flag = segment.option_i in self.selections[segment.group_i]
                self.audio.play(segment.clip_i + flag)
            elif segment.type == 5:
                area = self.page.option_areas[self.state.option_area_i]
                flag = area.option_i in self.selections[area.group_i]
                self.audio.play(segment.clip_i + flag)
            elif segment.type == 6:
                area = self.page.option_areas[action_option_area_i]
                flag = area.option_i in self.selections[area.group_i]
                self.audio.play(segment.clip_i + flag)
            elif segment.type == 7:
                group = self.model.groups[segment.group_i]
                for selection in self.selections[segment.group_i]:
                    option = group.options[selection]
                    self.play_option(option, segment.clip_i)
            elif segment.type == 8:
                count = len(self.selections[segment.group_i])
                self.audio.play(segment.clip_i + count)
            elif segment.type == 9:
                group = self.model.groups[segment.group_i]
                self.audio.play(segment.clip_i + group.max_sels)
