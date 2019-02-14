// Like design-2, after factoring out layouts and slots into video.

// The number of option_areas in the ballot that have a given contest
// must match the number of options in the referenced contest.

// The size of the slot in every option_area that has a given contest,
// the sizes of all slots in review_areas that have the same contest,
// and the sizes of unsel_sprite and sel_sprite for all the options in
// the referenced contest must all be equal.

ballot:
    model model
    video video
    audio audio

model:
    contest contests[]
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

contest:
    int max_sels
    option options[]

// Each sprite_i must be in bounds of video.sprites.
// clip_i + maximum(segment.clip_i where type=1 or type=2) must be in bounds.

option:
    int unsel_sprite_i, sel_sprite_i
    int clip_i // beginning of array

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

// Each clear_contest_i must be in bounds of model.contests.
// Each select_option_ref must be valid.
// option_area_i must be -1 or in bounds of page.option_areas.
// option_area_action: 0=select, 1=deselect, 2=toggle
// next_page_i must be -1 or in bounds of model.pages.
// next_state_i must be -1 or in bounds of model.pages[next_page_i].states.

action:
    int clear_contest_is[]
    option_ref select_option_refs[]
    int option_area_i
    enum option_area_action
    sequence default_sequence
    sequence no_change_sequence
    sequence overvote_sequence
    sequence toggle_deselect_sequence
    int next_page_i, next_state_i

// Referenced contest_i must be in bounds of model.contests.
// Referenced option_i must be in bounds of model.contests[contest_i].options.

option_ref:
    int contest_i, option_i

// sprite_i must be in bounds of video.sprites.
// option_area_i must be -1 or in bounds of page.option_areas.
// timeout_page_i must be -1 or in bounds of model.pages.
// timeout_state_i must be -1 or in bounds of pages[timeout_page_i].states.

state:
    int sprite_i
    // slot* slot from layout's slots[] array
    int option_area_i
    sequence entry_sequence
    key_binding key_bindings[]
    sequence timeout_sequence
    int timeout_page_i, timeout_state_i

// contest_i must be in bounds of model.contests.

option_area:
    // slot* slot from layout's slots[] array
    int contest_i
    // after candidate rotation is determined, int option_i

// contest_i must be in bounds of model.contests.
// number_sprite_i + contest[contest_i].max_sels must be in bounds of sprites.

counter_area:
    // slot* slot from layout's slots[] array
    int contest_i
    int number_sprite_i

// contest_i must be in bounds of model.contests.

review_area:
    // slot* slots[max_sels] from layout's slots[] array
    int contest_i

sequence:
    segment segments[]

// type: 0=play clips[clip_i]; clip_i must be in bounds of clips
//     1=play clips[option.clip_i + clip_i] for state's current option
//     2=play clips[option.clip_i + clip_i] for action's current option
//     3=play clips[option.clip_i + clip_i] for selected options in contest
//     4=play clips[clip_i + n] for number of selected options in contest;
//         clip_i + contests[contest_i].max_sels must be in bounds of clips
//     5=play clips[clip_i + contests[contest_i].max_sels];
//         clip_i + contests[contest_i].max_sels must be in bounds of clips

segment:
    enum type
    int clip_i
    int contest_i

clip:
    sample samples[]

// Size of screen image must match video.width, video.height.
// targets must not overlap.  slots must not overlap.

layout:
    image screen
    rect targets[]
    rect slots[]

rect:
    int left, top
    int width, height

// Length of pixel array must equal width * height.

image:
    int width, height
    pixel pixels[]

int: primitive
enum: primitive
pixel: primitive
sample: primitive
