// Writeins and contests as the same data structure (groups).

// The number of option_areas in the ballot that have a given group
// must match the number of options in the referenced group.

// The size of the slot in every option_area that has a given group,
// the sizes of all slots in review_areas that have the same group,
// and the sizes of unsel_sprite and sel_sprite for all the options in
// the referenced group must all be equal.

ballot:
    model model
    video video
    audio audio

model:
    group groups[]
    page pages[]
    int timeout_milliseconds

// Length of video.layouts must match length of model.pages.

video:
    int width, height
    layout layouts[]
    image sprites[]

audio:
    int sample_rate
    clip clips[]

// Consider renaming "group" to "menu" or "roster"

// type: 0=contest, 1=writein
// For a contest, max_sels is the maximum number of selections.
// For a writein, max_sels is the maximum number of characters.

group:
    enum type
    int max_sels
    int max_chars // auto-copied onto max_sels of all options' writein groups
    option options[]

// Each sprite_i must be in bounds of video.sprites.
// clip_i + max(segment.clip_i where type=1,2,3) must be in bounds.
// For options belonging to a writein-group, unsel_sprite_i must be -1.
// If option belongs to a writein-group, writein_group_i must be -1.
// If option belongs to a contest-group, then writein_group_i may be -1 or
// the index of a valid writein-group.
// There must exist an option_area with this option_i if writein_group_i != -1.

option:
    int unsel_sprite_i, sel_sprite_i
    int clip_i // beginning of array
    int writein_group_i

page:
    // layout* layout from layouts[] array
    key_binding key_bindings[]
    target_binding target_bindings[]
    state states[]
    option_area option_areas[]
    counter_area counter_areas[]
    review_area review_areas[]

key_binding:
    int key
    action action

target_binding:
    // rect* target from layout's targets[] array
    action action

// Each clear_group_i must be in bounds of model.groups.
// Each select_option_ref must be valid.
// option_area_action: 0=add, 1=remove, 2=toggle, 3=append, 4=append2, 5=pop
// option_area_i must be -1 or in bounds of page.option_areas.
// next_page_i must be -1 or in bounds of model.pages.
// next_state_i must be -1 or in bounds of model.pages[next_page_i].states.
// Feedback is selected depending on the outcome of:
//     option_area_op, if option_area_op != -1
//     option_op, if option_op != -1 and option_area_op == -1
//     clear_group_is, if option_op == option_area_op == -1

action:
    int next_page_i, next_state_i
    int clear_group_is[]
    enum option_op
    option_ref option_refs[]
    enum option_area_op
    int option_area_i
    sequence default_feedback // action successful, or no action
    sequence toggle_off_feedback // last toggle removed a selection 
    sequence no_effect_feedback // idempotent action had no effect
    sequence full_feedback // action rejected due to full
    sequence empty_feedback // action rejected due to empty

// Referenced group_i must be in bounds of model.groups.
// Referenced option_i must be in bounds of model.groups[group_i].options.

option_ref:
    int group_i, option_i

// sprite_i must be in bounds of video.sprites.
// option_area_i must be -1 or in bounds of page.option_areas.
// timeout_page_i must be -1 or in bounds of model.pages.
// timeout_state_i must be -1 or in bounds of pages[timeout_page_i].states.

state:
    // slot* slot from layout's slots[] array
    int sprite_i
    int option_area_i // used only for sequence variables
    sequence entry_sequence
    key_binding key_bindings[]
    sequence timeout_sequence
    int timeout_page_i, timeout_state_i

// group_i must be in bounds of model.groups.

option_area:
    // slot* slot from layout's slots[] array
    // slot* slots[group.max_chars] if options[option_i].writein_group_i != -1
    int group_i
    int option_i // or -1 if to be filled in by rotation

// group_i must be in bounds of model.groups.
// sprite_i + group.max_sels must be in bounds of sprites.

counter_area:
    // slot* slot from layout's slots[] array
    int group_i
    int sprite_i // beginning of array

// group_i must be in bounds of model.groups.
// cursor_sprite_i must be -1 or in bounds of sprites, and
// cursor_sprite must match size of all option sprites in the group.

review_area:
    // slot* slots[max_sels*(1 + max_chars)] from layout's slots[] array
    int group_i
    int cursor_sprite_i

sequence:
    segment segments[]

// type: 0=play clips[clip_i]; clip_i must be in bounds of clips
//     1=play clips[groups[group_i].options[option_i].clip_i + clip_i]
//     2=play clips[option.clip_i + clip_i] for state's current option
//          if current option has a writein_group, then also play
//          clips[option.clip_i] for each selected option in writein_group
//     3=play clips[option.clip_i + clip_i] for action's current option
//          if current option has a writein_group, then also play
//          clips[option.clip_i] for each selected option in writein_group
//     4=play clips[clip_i + is_selected(group_i, option_i)]
//     5=play clips[clip_i + is_selected(state's current option)]
//     6=play clips[clip_i + is_selected(action's current option)]
//     7=play clips[option.clip_i + clip_i] for selected options in group
//          if any option has a writein_group, then also play
//          clips[option.clip_i] for each selected option in writein_group
//     8=play clips[clip_i + n] for number of selected options in group;
//         clip_i + groups[group_i].max_sels must be in bounds of clips
//     9=play clips[clip_i + groups[group_i].max_sels];
//         clip_i + groups[group_i].max_sels must be in bounds of clips

segment:
    enum type
    int clip_i
    int group_i
    int option_i

clip:
    sample samples[]

// Size of screen image must match video.width, video.height.
// targets must not overlap.  slots must not overlap.

layout:
    image screen
    rect targets[]
    rect slots[]

// Length of pixel array must equal width * height.

image:
    int width, height
    pixel pixels[]

rect:
    int left, top
    int width, height

int: primitive
enum: primitive
pixel: primitive
sample: primitive
