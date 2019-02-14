def verify(ballot):
    [groups, sprites] = [ballot.model.groups, ballot.video.sprites]
    option_sizes = [[] for group in groups]
    char_sizes = [[] for group in groups]

    assert len(ballot.model.groups) == len(ballot.text.groups) > 0
    assert len(ballot.model.pages) == len(ballot.video.layouts) > 0

    for [page_i, page] in enumerate(ballot.model.pages):
        layout = ballot.video.layouts[page_i]

        for binding in page.bindings:
            verify_binding(ballot, page, binding)
        assert len(page.states) > 0

        for [state_i, state] in enumerate(page.states):
            verify_size(sprites[state.sprite_i], layout.slots[state_i])
            verify_segments(ballot, page, state.segments)
            for binding in state.bindings:
                verify_binding(ballot, page, binding)
            verify_segments(ballot, page, state.timeout_segments)
            verify_goto(ballot, state.timeout_page_i, state.timeout_state_i)
        slot_i = len(page.states)

        for area in page.option_areas:
            verify_option_ref(ballot, page, area)
            option_sizes[area.group_i].append(layout.slots[slot_i])
            slot_i = slot_i + 1

        for area in page.counter_areas:
            for i in range(groups[area.group_i].max_sels + 1):
                verify_size(sprites[area.sprite_i + i], layout.slots[slot_i])
            slot_i = slot_i + 1

        for area in page.review_areas:
            for i in range(groups[area.group_i].max_sels):
                option_sizes[area.group_i].append(layout.slots[slot_i])
                slot_i = slot_i + 1
                for j in range(groups[area.group_i].max_chars):
                    char_sizes[area.group_i].append(layout.slots[slot_i])
                    slot_i = slot_i + 1
            if area.cursor_sprite_i != None:
                option_sizes[area.group_i].append(sprites[area.cursor_sprite_i])

    for [group_i, group] in enumerate(groups):
        for option in group.options:
            option_sizes[group_i].append(sprites[option.sprite_i])
            option_sizes[group_i].append(sprites[option.sprite_i + 1])
            assert group.option_clips > 0
            ballot.audio.clips[option.clip_i + group.option_clips - 1]
            if option.writein_group_i != None:
                writein_group = groups[option.writein_group_i]
                assert writein_group.max_chars == 0
                assert writein_group.max_sels == group.max_chars > 0
                for option in writein_group.options:
                    char_sizes[group_i].append(sprites[option.sprite_i])
        for object in option_sizes[group_i]:
            verify_size(object, option_sizes[group_i][0])
        for object in char_sizes[group_i]:
            verify_size(object, char_sizes[group_i][0])

    for [group_i, group] in enumerate(ballot.text.groups):
        assert len(group.name) <= 50
        assert len(group.options) == len(groups[group_i].options)
        for option in group.options:
            assert len(option) <= 50

    for clip in ballot.audio.clips:
        assert len(clip.samples) > 0

    assert ballot.video.width*ballot.video.height > 0
    for layout in ballot.video.layouts:
        verify_size(layout.screen, ballot.video)
        for rect in layout.targets + layout.slots:
            assert rect.left + rect.width <= ballot.video.width
            assert rect.top + rect.height <= ballot.video.height
    for sprite in ballot.video.sprites:
        assert len(sprite.pixels) == sprite.width*sprite.height*3 > 0

def verify_binding(ballot, page, binding):
    for condition in binding.conditions:
        verify_option_ref(ballot, page, condition)
    for step in binding.steps:
        verify_option_ref(ballot, page, step)
    verify_segments(ballot, page, binding.segments)
    verify_goto(ballot, binding.next_page_i, binding.next_state_i)

def verify_goto(ballot, page_i, state_i):
    if page_i != None:
        ballot.model.pages[page_i].states[state_i]

def verify_segments(ballot, page, segments):
    for segment in segments:
        for condition in segment.conditions:
            verify_option_ref(ballot, page, condition)
        ballot.audio.clips[segment.clip_i]
        if segment.type in [1, 2, 3, 4]:
            group = verify_option_ref(ballot, page, segment)
            if segment.type in [1, 2]:
                assert segment.clip_i < group.option_clips
            if segment.type in [3, 4]:
                ballot.audio.clips[segment.clip_i + group.max_sels]

def verify_option_ref(ballot, page, object):
    if object.group_i == None:
        area = page.option_areas[object.option_i]
        return ballot.model.groups[area.group_i]
    ballot.model.groups[object.group_i].options[object.option_i]
    return ballot.model.groups[object.group_i]

def verify_size(a, b):
    assert a.width == b.width and a.height == b.height
