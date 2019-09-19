
from .screen_container import *
from .screen_label import ScreenLabel
from .screen_button import ScreenButton

class ScreenTextlist(ScreenContainer):
    def __init__(self, name, size, option_size, back_color=(0, 0, 0), option_color=(255, 255, 255),
                 selected_back=(192, 192, 192), selected_color=(0, 0, 0)):
        ScreenContainer.__init__(self, name, size, back_color)

        self.option_size = option_size
        self.option_color = option_color

        self.selected_back = selected_back
        self.selected_color = selected_color

        self.left_padding = 10
        self.top_padding = 10
        self.option_padding = 5

        self.option_offsets = []
        self.option_display = {}

        self.labels_refs = {}

        self.selected_option_value = None

        self.selected_value_change_callback = None

    def clear_options(self):
        # remove all the object references ...
        self.option_offsets = []
        self.option_display = {}
        self.labels_refs = {}
        self.selected_option_value = None
        self.elements = []
        # ... re-compute visuals ...
        self.recalculate_size()


    def add_option(self, option_value, option_display, index=None):
        if option_value in self.option_display:
            raise Exception("Cannot add option, key already in use")

        if index is None:
            # append ...
            self.option_offsets.append(option_value)
        else:
            # insert
            self.option_offsets.insert(index, option_value)

        self.option_display[option_value] = option_display

        self.labels_refs[option_value] = ScreenButton(self.name + "_label_" + option_value, option_display,
                                                      self.option_size, self.width - self.v_scroll.width,
                                                      text_color=self.option_color, back_color=self.back_color,
                                                      centered=0)

        self.labels_refs[option_value].click_callback = self.on_option_click

        # self-reference
        self.labels_refs[option_value].tag = option_value

        self.append(self.labels_refs[option_value])

        # update display
        self.update_labels()

    def rename_option(self, option_value, new_option_value, new_option_display):
        if option_value not in self.option_display:
            raise Exception("Cannot rename option, old key not found")

        # replace name in offset
        pos = self.option_offsets.index(option_value)
        self.option_offsets[pos] = new_option_value

        # if selected option is the renamed object
        if self.selected_option_value == option_value:
            self.selected_option_value = new_option_value

        # update label ....
        # ...  copy ref ...
        self.labels_refs[new_option_value] = self.labels_refs[option_value]
        # ... delete old ref ...
        del self.labels_refs[option_value]
        # ... update text ...
        self.labels_refs[new_option_value].updateText(new_option_display)
        # ... update self-reference ...
        self.labels_refs[new_option_value].tag = new_option_value

        # Update object value ...
        del self.option_display[option_value]
        self.option_display[new_option_value] = new_option_display

        # update display
        self.update_labels()

    def update_option_display(self, option_value, new_option_display):
        if option_value not in self.option_display:
            raise Exception("Cannot update option, key not found")

        # ... update text ...
        self.labels_refs[option_value].updateText(new_option_display)
        self.option_display[option_value] = new_option_display


    def remove_option(self, option_value):
        if option_value not in self.option_display:
            raise Exception("Cannot remove option, key not found")

        # delete offset
        pos = self.option_offsets.index(option_value)
        del self.option_offsets[pos]

        # if selected option is the removed object
        if self.selected_option_value == option_value:
            self.selected_option_value = None

        # remove button from container ...
        self.elements.remove(self.labels_refs[option_value])

        # remove reference of button
        del self.labels_refs[option_value]

        # remove from dictionary of values
        del self.option_display[option_value]

        # update display
        self.update_labels()

    def update_labels(self):
        current_top = self.top_padding

        for idx, option_value in enumerate(self.option_offsets):
            self.labels_refs[option_value].position = (self.left_padding, current_top)

            current_top = self.labels_refs[option_value].get_bottom() + self.option_padding

        self.recalculate_size()

    def on_option_click(self, option_button):
        if self.selected_option_value != option_button.tag:
            # mark the new option as selected
            option_button.set_colors(self.selected_color, self.selected_back)

            # remove mark from previous option (if any)
            if self.selected_option_value is not None:
                self.labels_refs[self.selected_option_value].set_colors(self.option_color, self.back_color)

            # copy old ...
            old_value = self.selected_option_value
            # set new ...
            self.selected_option_value = option_button.tag

            # call callback function
            if self.selected_value_change_callback is not None:
                self.selected_value_change_callback(option_button.tag, old_value)



    def change_option_selected(self, new_option_selected):
        if new_option_selected == self.selected_option_value:
            # no change will be performed
            return

        # de-select previous selected option (if any)
        if self.selected_option_value is not None:
            self.labels_refs[self.selected_option_value].set_colors(self.option_color, self.back_color)

        if new_option_selected is None:
            self.selected_option_value = None
        else:
            if new_option_selected in self.labels_refs:
                self.labels_refs[new_option_selected].set_colors(self.selected_color, self.selected_back)
                self.selected_option_value = new_option_selected
