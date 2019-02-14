from layout import *

regular = Font('LucidaGrande.ttf')
bold = Font('LucidaGrandeBold.ttf')

# Navigation.

button_w, button_h = 200, 56
button_bg = blend(BLACK, WHITE, 0.8)
ButtonText = lambda t: Text(t.upper(), font=bold, size=16)

# Ballot contents.

warn_fg = Color(1, 0, 0)
contents_bg = Color(0.625, 0.75, 1)
item_current_bg = Color(0.8125, 0.875, 1)
item_inactive_fg = blend(contents_bg, BLACK, 0.4)
item_active_fg = Color(0, 0, 0)

NoteText = curry(Text, font=regular, size=10)
ItemText = curry(Text, font=regular, size=12)
StatusDoneText = curry(Text, font=regular, size=12)
StatusUndervoteText = curry(Text, font=bold, size=12, fill=warn_fg)

# Instruction pages.

TitleText = lambda t: Text(t.upper(), font=bold, size=24)
InstructionsText = lambda t: Paragraph(
    t, 600, font=regular, size=24, spacing=6, fe=600)

# Contest pages.

option_unselected_bg = blend(BLACK, WHITE, 0.8)
option_selected_bg = Color(0.625, 0.9375, 0.625)

option_w, option_h = 324, 56
option_radius = 18
option_hspace, option_vspace = 48, 24 # 24, 16 #, 52
OptionContent = curry(VBox, int=1, spacing=2, padding=(72, 1, 0, 0))

SectionHeadingText = lambda t: Text(t.upper(), font=bold, size=24)
ContestHeadingText = curry(Text, font=bold, size=24)
ContestSubtitleText = lambda t: Paragraph(
    t.upper(), 600, font=bold, size=16, spacing=4, fe=600)
ContestQuestionText = lambda t: Paragraph(
    t, 600, font=regular, size=16, spacing=4, fe=600)
DirectionsText = curry(Text, font=regular, size=24)
MainText = curry(Text, font=regular, size=16)

OptionText = lambda t: Text(t.upper(), font=bold, size=16)
DescriptionText = curry(Text, font=regular, size=12)

highlight_gap = 5
highlight_weight = 5
highlight_stroke = Color(0.8, 0.4, 0.4)
highlight_dash = [5, 2]

# Review pages.

ReviewLabel = curry(VBox, align='C', int=1, spacing=2)
ReviewTitleText = OptionText
ReviewSubtitleText = lambda t: Paragraph(
    t, 324, font=regular, size=12, spacing=3, align='C')
ReviewEmptyText = lambda t: Text(t.upper(), font=bold, size=16, fill=RED)
review_hspace = option_hspace
review_vspace = option_vspace
review_label_vspace = 4

# Completion page.

CompletionText = curry(Text, font=bold, size=24)
