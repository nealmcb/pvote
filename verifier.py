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
            assert not verify_segments(ballot, page, state.segments)
            for binding in state.bindings:
                verify_binding(ballot, page, binding)
            assert not verify_segments(ballot, page, state.timeout_segments)
            verify_goto(ballot, state.timeout_page_i, state.timeout_state_i)
        slot_i = len(page.states)

        for area in page.option_areas:
            [group_i, group] = verify_option_ptr(ballot, page, area)
            option_sizes[group_i].append(layout.slots[slot_i])
            slot_i = slot_i + 1

        for area in page.counter_areas:
            for i in range(groups[area.group_i].max_sels):
                verify_size(sprites[area.sprite_i + i], layout.slots[slot_i])
            slot_i = slot_i + 1

        for area in page.review_areas:
            if area.cursor_sprite_i != None:
                option_sizes[area.group_i].append(sprites[area.cursor_sprite_i])
            option_sizes[area.group_i].append(layout.slots[slot_i])
            slot_i = slot_i + 1
            for i in range(groups[area.group_i].max_chars):
                char_sizes[area.group_i].append(layout.slots[slot_i])
                slot_i = slot_i + 1

    for [group_i, group] in enumerate(groups):
        for option in group.options:
            sprites[option.sprite_i + 1]
            option_sizes[group_i].append(sprites[option.sprite_i])
            option_sizes[group_i].append(sprites[option.sprite_i + 1])
            ballot.audio.clips[option.clip_i + group.option_clips - 1]
            if option.writein_group_i != None:
                writein_group = groups[option.writein_group_i]
                assert writein_group.max_sels == group.max_chars > 0
                assert writein_group.max_chars == 0
                char_sprite_i = writein_group.options[0].sprite_i
                char_sizes[group_i].append(sprites[char_sprite_i])
        for size in option_sizes[group_i]:
            verify_size(size, option_sizes[group_i][0])
        if len(char_sizes[group_i]):
            for size in char_sizes[group_i]:
                verify_size(size, char_sizes[group_i][0])

    for [group_i, group] in enumerate(ballot.text.groups):
        assert group.writein in [0, 1]
        assert len(group.options) == len(groups[group_i].options)

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
        verify_condition(ballot, page, condition)
    for step in binding.steps:
        assert step.op in [0, 1, 2, 3, 4]
        verify_option_ptr(ballot, page, step)
    if verify_segments(ballot, page, binding.segments):
        assert len(binding.steps) > 0
    verify_goto(ballot, binding.next_page_i, binding.next_state_i)

def verify_condition(ballot, page, condition):
    assert condition.predicate in [0, 1, 2]
    verify_option_ptr(ballot, page, condition)
    assert condition.invert in [0, 1]

def verify_goto(ballot, page_i, state_i):
    if page_i == None:
        return 1
    ballot.model.pages[page_i].states[state_i]

def verify_segments(ballot, page, segments):
    use_step = 0
    for segment in segments:
        for condition in segment.conditions:
            verify_condition(ballot, page, condition)
        assert segment.type in [0, 1, 2, 3, 4]
        if segment.type == 0 or segment.use_step:
            ballot.audio.clips[segment.clip_i]
        else:
            [group_i, group] = verify_option_ptr(ballot, page, segment)
            if segment.type in [1, 2]:
                assert segment.clip_i < group.option_clips
            else:
                ballot.audio.clips[segment.clip_i + group.max_sels]
        assert segment.use_step in [0, 1]
        use_step = use_step or segment.use_step
    return use_step

def verify_option_ptr(ballot, page, object):
    if object.group_i == None:
        area = page.option_areas[object.option_i]
        return [area.group_i, ballot.model.groups[area.group_i]]
    ballot.model.groups[object.group_i].options[object.option_i]
    return [object.group_i, ballot.model.groups[object.group_i]]

def verify_size(a, b):
    assert a.width == b.width and a.height == b.height
