class Navigator:
    def __init__(self, model, video, audio, recorder):
        self.model, self.video, self.audio = model, video, audio
        self.recorder = recorder
        self.selections = [[] for contest in model.contests]
        self.goto(0, 0)
        self.update()

    def goto(self, page_i, state_i):
        if page_i == len(self.model.pages) - 1:
            self.recorder.write(self.selections)
        self.page_i, self.page = page_i, self.model.pages[page_i]
        self.state_i, self.state = state_i, self.page.states[state_i]
        self.play(self.state.entry_sequence, -1)

    def update(self):
        self.video.goto(self.page_i)
        if self.state.sprite_i != -1:
            self.video.paste(self.state.sprite_i, self.state_i)

        slot_i = len(self.page.states) 
        for area in self.page.option_areas:
            if area.option_i in self.selections[area.contest_i]:
                self.video.paste(area.option.sel_sprite_i, slot_i)
            else:
                self.video.paste(area.option.unsel_sprite_i, slot_i)
            slot_i += 1

        for area in self.page.counter_areas:
            count = len(self.selections[area.contest_i])
            self.video.paste(area.number_sprite_i + count, slot_i)
            slot_i += 1

        for area in self.page.review_areas:
            contest = self.model.contest[area.contest_i]
            selections = self.selections[area.contest_i]
            for i in range(contest.max_sels):
                if i < len(selections):
                    option = contest.options[selections[i]]
                    self.video.paste(option.sel_sprite_i, slot_i)
                slot_i += 1

    def key(self, key):
        for key_binding in self.state.key_bindings + self.page.key_bindings:
            if key_binding.key == key:
                return self.execute(key_binding.action)

    def touch(self, target_i):
        self.execute(self.page.target_bindings[target_i].action)

    def execute(self, action):
        for contest_i in action.clear_contest_is:
            self.selections[contest_i] = []
        for option_ref in action.select_option_refs:
            self.selections[option_ref.contest_i].append(option_ref.option_i)

        sequence = action.default_sequence
        if action.option_area_i != -1:
            area = self.page.option_areas[action.option_area_i]
            if area.option_i in self.selections[area.contest_i]:
                if action.option_area_action == 0:
                    sequence = no_change_sequence
                elif action.option_area_action == 1:
                    self.selections[area.contest_i].remove(area.option_i)
                elif action.option_area_action == 2:
                    self.selections[area.contest_i].remove(area.option_i)
                    sequence = action.toggle_deselect_sequence
            else:
                if action.option_area_action in [0, 2]:
                    self.selections[area.contest_i].append(area.option_i)
                elif action.option_area_action == 1:
                    sequence = action.no_change_sequence

        self.audio.stop()
        self.play(sequence, action.option_area_i)
        if action.next_page_i != -1:
            self.goto(action.next_page_i, action.next_state_i)
        self.update()

    def timeout(self):
        self.play(self.state.timeout_sequence, -1)
        if self.state.timeout_page_i != -1:
            self.goto(self.state.timeout_page_i, self.state.timeout_state_i)
        self.update()

    def play(self, sequence, action_option_area_i):
        for segment in sequence.segments:
            if segment.type == 0:
                self.audio.play(segment.clip_i)
            elif segment.type == 1:
                area = self.page.option_areas[self.state.option_area_i]
                self.audio.play(area.option.clip_i + segment.clip_i)
            elif segment.type == 2:
                area = self.page.option_areas[action_option_area_i]
                self.audio.play(area.option.clip_i + segment.clip_i)
            elif segment.type == 3:
                contest = self.model.contests[segment.contest_i]
                for selection in self.selections[segment.contest_i]:
                    option = contest.options[selection]
                    self.audio.play(option.clip_i + segment.clip_i)
            elif segment.type == 4:
                count = len(self.selections[segment.contest_i])
                self.audio.play(segment.clip_i + count)
            elif segment.type == 5:
                contest = self.model.contests[segment.contest_i]
                self.audio.play(segment.clip_i + contest.max_sels)
