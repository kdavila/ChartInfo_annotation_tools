
import time
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.annotation.base_image_annotator import BaseImageAnnotator

from ChartInfo.data.line_data import LineData
from ChartInfo.data.line_values import LineValues

class LineChartAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeLineSelect = 2
    ModeLineEdit = 3
    ModeLineSwap = 4
    ModePointAdd = 5
    ModePointEdit = 6
    ModeConfirmNumberOverwrite = 7
    ModeConfirmExit = 8

    DoubleClickMaxPointDistance = 5

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Line Chart Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.data is None:
            # create default Line chart data ...
            self.data = LineData.CreateDefault(self.panel_info)
            self.data_changed = True
        else:
            # make a copy ...
            self.data = LineData.Copy(self.panel_info.data)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (150, 190, 20)
        self.text_color = (255, 255, 255)

        self.elements.back_color = self.general_background
        self.edition_mode = None

        self.last_shift_direction = None
        self.last_shift_time = None

        self.tempo_line_index = None
        self.tempo_point_index = None
        self.tempo_line_values = None
        self.tempo_canvas_name = None
        self.tempo_median_line_color = None
        self.hover_line_point_x = None
        self.hover_line_point_y = None

        self.label_title = None

        self.container_confirm_buttons = None
        self.lbl_confirm_message = None
        self.btn_confirm_cancel = None
        self.btn_confirm_accept = None

        self.container_annotation_buttons = None
        self.lbl_edit_title = None
        self.btn_edit_number = None
        self.btn_edit_data = None
        self.btn_return_accept = None
        self.btn_return_cancel = None

        self.container_number_buttons = None
        self.lbl_number_title = None
        self.lbl_number_series_title = None
        self.lbx_number_series_values = None
        self.btn_number_series_add = None
        self.btn_number_series_remove = None
        self.btn_number_return = None

        self.container_data_buttons = None
        self.lbl_data_title = None
        self.lbx_data_series_values = None
        self.btn_data_series_edit = None
        self.btn_data_series_swap = None
        self.btn_data_return = None

        self.container_swap_buttons = None
        self.lbl_swap_title = None
        self.lbl_swap_name = None
        self.lbl_swap_other = None
        self.lbx_swap_series_values = None
        self.btn_swap_return_cancel = None
        self.btn_swap_return_accept = None

        self.container_line_buttons = None
        self.lbl_line_title = None
        self.lbl_line_name = None
        self.lbx_line_points = None
        self.btn_line_point_edit = None
        self.btn_line_point_delete = None
        self.btn_line_point_add = None
        self.lbl_line_points_shift = None
        self.btn_line_point_shift_up = None
        self.btn_line_point_shift_down = None
        self.btn_line_point_shift_left = None
        self.btn_line_point_shift_right = None
        self.btn_line_return_accept = None
        self.btn_line_return_cancel = None

        self.container_preview_buttons = None
        self.lbl_preview_title = None
        self.img_preview = None

        self.create_controllers()

        # get the view ...
        self.update_current_view(True)

    def create_controllers(self):
        # add elements....
        button_text_color = (35, 50, 20)
        button_back_color = (228, 228, 228)

        # Main Title
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Line Chart Data Annotation", 28)
        self.label_title.background = self.general_background
        self.label_title.position = (int((self.width - self.label_title.width) / 2), 20)
        self.label_title.set_color(self.text_color)
        self.elements.append(self.label_title)

        container_top = 10 + self.label_title.get_bottom()
        container_width = 300

        button_width = 190
        button_left = (container_width - button_width) / 2

        button_2_width = 130
        button_2_left = int(container_width * 0.25) - button_2_width / 2
        button_2_right = int(container_width * 0.75) - button_2_width / 2

        button_4_width = 65
        button_4_x1 = int(container_width * 0.1400) - button_4_width / 2
        button_4_x2 = int(container_width * 0.3800) - button_4_width / 2
        button_4_x3 = int(container_width * 0.6200) - button_4_width / 2
        button_4_x4 = int(container_width * 0.8600) - button_4_width / 2
        

        # ===========================
        # View Options Panel
        self.create_image_annotator_controls(container_top, container_width, self.general_background, self.text_color,
                                             button_text_color, button_back_color)

        # ===========================
        # confirmation panel
        self.container_confirm_buttons = ScreenContainer("container_confirm_buttons", (container_width, 70),
                                                         back_color=self.general_background)
        self.container_confirm_buttons.position = (
            self.width - self.container_confirm_buttons.width - 10, self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_confirm_buttons)
        self.container_confirm_buttons.visible = False

        self.lbl_confirm_message = ScreenLabel("lbl_confirm_message", "Confirmation message goes here?", 21, 290, 1)
        self.lbl_confirm_message.position = (5, 5)
        self.lbl_confirm_message.set_background(self.general_background)
        self.lbl_confirm_message.set_color(self.text_color)
        self.container_confirm_buttons.append(self.lbl_confirm_message)

        self.btn_confirm_cancel = ScreenButton("btn_confirm_cancel", "Cancel", 21, 130)
        self.btn_confirm_cancel.set_colors(button_text_color, button_back_color)
        self.btn_confirm_cancel.position = (10, self.lbl_confirm_message.get_bottom() + 10)
        self.btn_confirm_cancel.click_callback = self.btn_confirm_cancel_click
        self.container_confirm_buttons.append(self.btn_confirm_cancel)

        self.btn_confirm_accept = ScreenButton("btn_confirm_accept", "Accept", 21, 130)
        self.btn_confirm_accept.set_colors(button_text_color, button_back_color)
        self.btn_confirm_accept.position = (self.container_confirm_buttons.width - self.btn_confirm_accept.width - 10,
                                            self.lbl_confirm_message.get_bottom() + 10)
        self.btn_confirm_accept.click_callback = self.btn_confirm_accept_click
        self.container_confirm_buttons.append(self.btn_confirm_accept)

        # ==============================
        # main annotation options
        darker_background = (100, 130, 15)

        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 180),
                                                            back_color=darker_background)
        self.container_annotation_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Line Chart Annotation Options", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        self.btn_edit_number = ScreenButton("btn_edit_number", "Edit Number of Lines", 21, button_width)
        self.btn_edit_number.set_colors(button_text_color, button_back_color)
        self.btn_edit_number.position = (button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_number.click_callback = self.btn_edit_number_click
        self.container_annotation_buttons.append(self.btn_edit_number)

        self.btn_edit_data = ScreenButton("btn_edit_data", "Edit Line Data", 21, button_width)
        self.btn_edit_data.set_colors(button_text_color, button_back_color)
        self.btn_edit_data.position = (button_left, self.btn_edit_number.get_bottom() + 10)
        self.btn_edit_data.click_callback = self.btn_edit_data_click
        self.container_annotation_buttons.append(self.btn_edit_data)

        self.btn_return_accept = ScreenButton("btn_return_accept", "Accept", 21, button_2_width)
        return_top = self.container_annotation_buttons.height - self.btn_return_accept.height - 10
        self.btn_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_return_accept.position = (button_2_left, return_top)
        self.btn_return_accept.click_callback = self.btn_return_accept_click
        self.container_annotation_buttons.append(self.btn_return_accept)

        self.btn_return_cancel = ScreenButton("btn_return_cancel", "Cancel", 21, button_2_width)
        self.btn_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_return_cancel.position = (button_2_right, return_top)
        self.btn_return_cancel.click_callback = self.btn_return_cancel_click
        self.container_annotation_buttons.append(self.btn_return_cancel)

        # ==================================
        # - options to define the total number of lines in the chart ....
        self.container_number_buttons = ScreenContainer("container_number_buttons", (container_width, 530),
                                                        back_color=darker_background)
        self.container_number_buttons.position = (self.container_view_buttons.get_left(),
                                                  self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_number_buttons)

        self.lbl_number_title = ScreenLabel("lbl_number_title ", "Lines in Chart: [0]", 25, 290, 1)
        self.lbl_number_title.position = (5, 5)
        self.lbl_number_title.set_background(darker_background)
        self.lbl_number_title.set_color(self.text_color)
        self.container_number_buttons.append(self.lbl_number_title)

        self.lbl_number_series_title = ScreenLabel("lbl_number_series_title", "Data Series", 21, 290, 1)
        self.lbl_number_series_title.position = (5, self.lbl_number_title.get_bottom() + 10)
        self.lbl_number_series_title.set_background(darker_background)
        self.lbl_number_series_title.set_color(self.text_color)
        self.container_number_buttons.append(self.lbl_number_series_title)

        self.lbx_number_series_values = ScreenTextlist("lbx_number_series_values", (container_width - 20, 290),
                                                       18, back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                       selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_number_series_values.position = (10, self.lbl_number_series_title.get_bottom() + 10)
        # self.lbx_number_categories_values.selected_value_change_callback = self.lbx_number_categories_values_changed
        self.container_number_buttons.append(self.lbx_number_series_values)

        self.btn_number_series_add = ScreenButton("btn_number_series_add", "Add", 21, button_2_width)
        self.btn_number_series_add.set_colors(button_text_color, button_back_color)
        self.btn_number_series_add.position = (button_2_left, self.lbx_number_series_values.get_bottom() + 10)
        self.btn_number_series_add.click_callback = self.btn_number_series_add_click
        self.container_number_buttons.append(self.btn_number_series_add)

        self.btn_number_series_remove = ScreenButton("btn_number_series_remove", "Remove", 21, button_2_width)
        self.btn_number_series_remove.set_colors(button_text_color, button_back_color)
        self.btn_number_series_remove.position = (button_2_right, self.lbx_number_series_values.get_bottom() + 10)
        self.btn_number_series_remove.click_callback = self.btn_number_series_remove_click
        self.container_number_buttons.append(self.btn_number_series_remove)

        self.btn_number_return = ScreenButton("btn_number_return", "Return", 21, button_width)
        self.btn_number_return.set_colors(button_text_color, button_back_color)
        self.btn_number_return.position = (button_left, self.btn_number_series_add.get_bottom() + 15)
        self.btn_number_return.click_callback = self.btn_number_return_click
        self.container_number_buttons.append(self.btn_number_return)
        self.container_number_buttons.visible = False

        # ==============================
        # data annotation options
        self.container_data_buttons = ScreenContainer("container_data_buttons", (container_width, 430),
                                                      back_color=darker_background)
        self.container_data_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_data_buttons)

        self.lbl_data_title = ScreenLabel("lbl_data_title ", "Lines in Chart", 25, 290, 1)
        self.lbl_data_title.position = (5, 5)
        self.lbl_data_title.set_background(darker_background)
        self.lbl_data_title.set_color(self.text_color)
        self.container_data_buttons.append(self.lbl_data_title)

        self.lbx_data_series_values = ScreenTextlist("lbx_data_series_values", (container_width - 20, 210), 18,
                                                     back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                     selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_data_series_values.position = (10, self.lbl_data_title.get_bottom() + 20)
        self.container_data_buttons.append(self.lbx_data_series_values)

        self.btn_data_series_edit = ScreenButton("btn_data_series_edit", "Edit Points", 21, button_width)
        self.btn_data_series_edit.set_colors(button_text_color, button_back_color)
        self.btn_data_series_edit.position = (button_left, self.lbx_data_series_values.get_bottom() + 10)
        self.btn_data_series_edit.click_callback = self.btn_data_series_edit_click
        self.container_data_buttons.append(self.btn_data_series_edit)

        self.btn_data_series_swap = ScreenButton("btn_data_series_swap", "Swap Points", 21, button_width)
        self.btn_data_series_swap.set_colors(button_text_color, button_back_color)
        self.btn_data_series_swap.position = (button_left, self.btn_data_series_edit.get_bottom() + 10)
        self.btn_data_series_swap.click_callback = self.btn_data_series_swap_click
        self.container_data_buttons.append(self.btn_data_series_swap)

        self.btn_data_return = ScreenButton("btn_data_return", "Return", 21, button_width)
        self.btn_data_return.set_colors(button_text_color, button_back_color)
        self.btn_data_return.position = (button_left, self.btn_data_series_swap.get_bottom() + 20)
        self.btn_data_return.click_callback = self.btn_data_return_click
        self.container_data_buttons.append(self.btn_data_return)

        self.container_data_buttons.visible = False

        # ==============================
        self.container_swap_buttons = ScreenContainer("container_swap_buttons", (container_width, 450),
                                                      back_color=darker_background)
        self.container_swap_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_swap_buttons)

        self.lbl_swap_title = ScreenLabel("lbl_swap_title", "Swap Line Points", 25, 290, 1)
        self.lbl_swap_title.position = (5, 5)
        self.lbl_swap_title.set_background(darker_background)
        self.lbl_swap_title.set_color(self.text_color)
        self.container_swap_buttons.append(self.lbl_swap_title)

        self.lbl_swap_name = ScreenLabel("lbl_swap_name", "[Data series]", 18, 290, 1)
        self.lbl_swap_name.position = (5, self.lbl_swap_title.get_bottom() + 20)
        self.lbl_swap_name.set_background(darker_background)
        self.lbl_swap_name.set_color(self.text_color)
        self.container_swap_buttons.append(self.lbl_swap_name)

        self.lbl_swap_other = ScreenLabel("lbl_swap_other", "Select Second Line", 18, 290, 1)
        self.lbl_swap_other.position = (5, self.lbl_swap_name.get_bottom() + 20)
        self.lbl_swap_other.set_background(darker_background)
        self.lbl_swap_other.set_color(self.text_color)
        self.container_swap_buttons.append(self.lbl_swap_other)

        self.lbx_swap_series_values = ScreenTextlist("lbx_swap_series_values", (container_width - 20, 210), 18,
                                                     back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                     selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_swap_series_values.position = (10, self.lbl_swap_other.get_bottom() + 10)
        # self.lbx_swap_series_values.selected_value_change_callback = self.lbx_swap_series_values_changed
        self.container_swap_buttons.append(self.lbx_swap_series_values)

        self.btn_swap_return_accept = ScreenButton("btn_swap_return_accept", "Accept", 21, button_2_width)
        self.btn_swap_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_swap_return_accept.position = (button_2_left, self.lbx_swap_series_values.get_bottom() + 20)
        self.btn_swap_return_accept.click_callback = self.btn_swap_return_accept_click
        self.container_swap_buttons.append(self.btn_swap_return_accept)

        self.btn_swap_return_cancel = ScreenButton("btn_swap_return_cancel", "Cancel", 21, button_2_width)
        self.btn_swap_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_swap_return_cancel.position = (button_2_right, self.lbx_swap_series_values.get_bottom() + 20)
        self.btn_swap_return_cancel.click_callback = self.btn_swap_return_cancel_click
        self.container_swap_buttons.append(self.btn_swap_return_cancel)


        # ==============================
        # line annotation options
        self.container_line_buttons = ScreenContainer("container_line_buttons", (container_width, 550),
                                                      back_color=darker_background)
        self.container_line_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_line_buttons)

        self.lbl_line_title = ScreenLabel("lbl_line_title", "Points in Line", 25, 290, 1)
        self.lbl_line_title.position = (5, 5)
        self.lbl_line_title.set_background(darker_background)
        self.lbl_line_title.set_color(self.text_color)
        self.container_line_buttons.append(self.lbl_line_title)

        self.lbl_line_name = ScreenLabel("lbl_line_name", "[Data series]", 18, 290, 1)
        self.lbl_line_name.position = (5, self.lbl_line_title.get_bottom() + 20)
        self.lbl_line_name.set_background(darker_background)
        self.lbl_line_name.set_color(self.text_color)
        self.container_line_buttons.append(self.lbl_line_name)

        self.lbx_line_points = ScreenTextlist("lbx_line_points", (container_width - 20, 210), 18,
                                              back_color=(255, 255, 255), option_color=(0, 0, 0),
                                              selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_line_points.position = (10, self.lbl_line_name.get_bottom() + 30)
        self.lbx_line_points.selected_value_change_callback = self.lbx_line_points_value_changed
        self.container_line_buttons.append(self.lbx_line_points)

        self.btn_line_point_add = ScreenButton("btn_line_point_add", "Add Points", 21, button_2_width)
        self.btn_line_point_add.set_colors(button_text_color, button_back_color)
        self.btn_line_point_add.position = (button_2_left, self.lbx_line_points.get_bottom() + 10)
        self.btn_line_point_add.click_callback = self.btn_line_point_add_click
        self.container_line_buttons.append(self.btn_line_point_add)

        self.btn_line_point_edit = ScreenButton("btn_line_point_edit", "Edit Points", 21, button_2_width)
        self.btn_line_point_edit.set_colors(button_text_color, button_back_color)
        self.btn_line_point_edit.position = (button_2_right, self.lbx_line_points.get_bottom() + 10)
        self.btn_line_point_edit.click_callback = self.btn_line_point_edit_click
        self.container_line_buttons.append(self.btn_line_point_edit)

        self.btn_line_point_delete = ScreenButton("btn_line_point_delete", "Remove Point", 21, button_width)
        self.btn_line_point_delete.set_colors(button_text_color, button_back_color)
        self.btn_line_point_delete.position = (button_left, self.btn_line_point_edit.get_bottom() + 10)
        self.btn_line_point_delete.click_callback = self.btn_line_point_delete_click
        self.container_line_buttons.append(self.btn_line_point_delete)

        self.lbl_line_points_shift = ScreenLabel("lbl_line_points_shift", "Shift All Points", 18, 290, 1)
        self.lbl_line_points_shift.position = (5, self.btn_line_point_delete.get_bottom() + 20)
        self.lbl_line_points_shift.set_background(darker_background)
        self.lbl_line_points_shift.set_color(self.text_color)
        self.container_line_buttons.append(self.lbl_line_points_shift)

        self.btn_line_point_shift_up = ScreenButton("btn_line_point_shift_up", "Up", 17, button_4_width)
        self.btn_line_point_shift_up.set_colors(button_text_color, button_back_color)
        self.btn_line_point_shift_up.position = (button_4_x1, self.lbl_line_points_shift.get_bottom() + 10)
        self.btn_line_point_shift_up.click_callback = self.btn_line_point_shift_up_click
        self.container_line_buttons.append(self.btn_line_point_shift_up)

        self.btn_line_point_shift_down = ScreenButton("btn_line_point_shift_down", "Down", 17, button_4_width)
        self.btn_line_point_shift_down.set_colors(button_text_color, button_back_color)
        self.btn_line_point_shift_down.position = (button_4_x2, self.lbl_line_points_shift.get_bottom() + 10)
        self.btn_line_point_shift_down.click_callback = self.btn_line_point_shift_down_click
        self.container_line_buttons.append(self.btn_line_point_shift_down)

        self.btn_line_point_shift_left = ScreenButton("btn_line_point_shift_left", "Left", 17, button_4_width)
        self.btn_line_point_shift_left.set_colors(button_text_color, button_back_color)
        self.btn_line_point_shift_left.position = (button_4_x3, self.lbl_line_points_shift.get_bottom() + 10)
        self.btn_line_point_shift_left.click_callback = self.btn_line_point_shift_left_click
        self.container_line_buttons.append(self.btn_line_point_shift_left)

        self.btn_line_point_shift_right = ScreenButton("btn_line_point_shift_right", "Right", 17, button_4_width)
        self.btn_line_point_shift_right.set_colors(button_text_color, button_back_color)
        self.btn_line_point_shift_right.position = (button_4_x4, self.lbl_line_points_shift.get_bottom() + 10)
        self.btn_line_point_shift_right.click_callback = self.btn_line_point_shift_right_click
        self.container_line_buttons.append(self.btn_line_point_shift_right)

        self.btn_line_return_accept = ScreenButton("btn_line_return_accept", "Accept", 21, button_2_width)
        self.btn_line_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_line_return_accept.position = (button_2_left, self.btn_line_point_shift_up.get_bottom() + 20)
        self.btn_line_return_accept.click_callback = self.btn_line_return_accept_click
        self.container_line_buttons.append(self.btn_line_return_accept)

        self.btn_line_return_cancel = ScreenButton("btn_line_return_cancel", "Cancel", 21, button_2_width)
        self.btn_line_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_line_return_cancel.position = (button_2_right, self.btn_line_point_shift_up.get_bottom() + 20)
        self.btn_line_return_cancel.click_callback = self.btn_line_return_cancel_click
        self.container_line_buttons.append(self.btn_line_return_cancel)

        self.container_line_buttons.visible = False

        # =====================
        # Preview of point to add

        self.container_preview_buttons = ScreenContainer("container_preview_buttons", (container_width, 280),
                                                         back_color=darker_background)
        self.container_preview_buttons.position = (self.container_confirm_buttons.get_left(),
                                                   self.container_confirm_buttons.get_bottom() + 20)
        self.elements.append(self.container_preview_buttons)

        self.lbl_preview_title = ScreenLabel("lbl_preview_title", "Right Click to add this Point", 25, 290, 1)
        self.lbl_preview_title.position = (5, 5)
        self.lbl_preview_title.set_background(darker_background)
        self.lbl_preview_title.set_color(self.text_color)
        self.container_preview_buttons.append(self.lbl_preview_title)

        tempo_blank = np.zeros((50, 50, 3), np.uint8)
        tempo_blank[:, :, :] = 255
        self.img_preview = ScreenImage("img_preview", tempo_blank, 200, 200, True, cv2.INTER_NEAREST)
        self.img_preview.position = (int(container_width / 2 - 100), self.lbl_preview_title.get_bottom() + 20)
        self.container_preview_buttons.append(self.img_preview)

        self.img_main.mouse_motion_callback = self.img_main_mouse_motion

        self.prepare_number_controls()

        self.set_editor_mode(LineChartAnnotator.ModeNavigate)

    def custom_view_update(self, modified_image):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # axes lines
        cv2.line(modified_image, (x1, y1), (x1, y2), (0, 255, 0), thickness=1)  # y = green
        cv2.line(modified_image, (x1, y2), (x2, y2), (0, 0, 255), thickness=1)  # x = blue
        # close the data area rectangle ?
        # cv2.line(modified_image, (x2, y1), (x2, y2), (0, 128, 0), thickness=1)
        # cv2.line(modified_image, (x1, y1), (x2, y1), (0, 0, 128), thickness=1)

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [LineChartAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(LineChartAnnotator.ModeNavigate)

        elif self.edition_mode in [LineChartAnnotator.ModePointAdd]:
            # return to line edition mode ...
            self.update_points_list()
            self.set_editor_mode(LineChartAnnotator.ModeLineEdit)
        elif self.edition_mode in [LineChartAnnotator.ModePointEdit]:
            # copy data from Canvas to the structure ....
            canvas_points = self.canvas_display.elements[self.tempo_canvas_name].points
            for point_idx, (px, py) in enumerate(canvas_points):
                # like clicks, canvas uses visual position,
                # convert coordinates from the canvas to image coordinate
                # using the same function used the mouse clicks
                rel_x, rel_y = self.from_pos_to_rel_click((px, py))
                # set new position for this point ...
                self.tempo_line_values.set_point(point_idx, rel_x, rel_y)
            # lock the canvas ...
            self.canvas_display.locked = True
            # return to line edition mode ...
            self.update_points_list()
            self.set_editor_mode(LineChartAnnotator.ModeLineEdit)
        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == LineChartAnnotator.ModeConfirmExit:
            print("-> Changes made to Line Data Annotations were lost")
            self.return_screen = self.parent_screen
        else:
            raise Exception("Not Implemented")

    def btn_edit_number_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModeNumberEdit)
        self.update_current_view()

    def btn_edit_data_click(self, button):
        self.fill_data_series_list(self.lbx_data_series_values)
        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)
        self.update_current_view()

    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing Line data ...
            self.panel_info.data = LineData.Copy(self.data)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(LineChartAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen

    def numbers_update_GUI(self, data_series_changed):
        n_lines = self.data.total_lines()
        self.lbl_number_title.set_text("Lines in Chart: {0:d}".format(n_lines))

        if data_series_changed:
            self.fill_data_series_list(self.lbx_number_series_values)

        self.create_canvas_lines()
        self.update_current_view()

    def btn_number_series_add_click(self, button):
        # add ... using general default values (based on axis info)
        p1, p2 = self.get_default_line_values()
        self.data.add_data_series(default_points=[p1, p2])

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(True)

    def btn_number_series_remove_click(self, button):
        if self.lbx_number_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        option_idx = int(self.lbx_number_series_values.selected_option_value)

        # remove ...
        self.data.remove_data_series(option_idx)

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(True)

    def get_default_line_values(self):
        a_x1, a_y1, a_x2, a_y2 = self.panel_info.axes.bounding_box
        a_x1 = int(a_x1)
        a_y1 = int(a_y1)
        a_x2 = int(a_x2)
        a_y2 = int(a_y2)

        axis_range = a_y2 - a_y1
        axis_domain = a_x2 - a_x1

        line_y = 0.5 * axis_range

        return (0, line_y), (axis_domain, line_y)

    def btn_number_return_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModeNavigate)
        self.update_current_view()

    def from_pos_to_rel_click(self, pos):
        # click pos ...
        click_x, click_y = pos
        click_x /= self.view_scale
        click_y /= self.view_scale

        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        # x1 = int(x1)
        # y2 = int(y2)

        rel_x = click_x - x1
        rel_y = y2 - click_y

        return rel_x, rel_y

    def img_main_mouse_button_down(self, img_object, pos, button):
        if self.edition_mode in [LineChartAnnotator.ModePointAdd, LineChartAnnotator.ModePointEdit]:
            if self.edition_mode == LineChartAnnotator.ModePointAdd:
                # Add the new point
                if button == 1:
                    # click pos ...
                    rel_x, rel_y = self.from_pos_to_rel_click(pos)
                elif button == 3:
                    if self.hover_line_point_x is not None:
                        # suggested position ...
                        pos = (self.hover_line_point_x * self.view_scale, self.hover_line_point_y * self.view_scale)
                        rel_x, rel_y = self.from_pos_to_rel_click(pos)
                    else:
                        rel_x, rel_y = None, None
                else:
                    rel_x, rel_y = None, None

                if rel_x is not None:
                    # add point ....
                    self.tempo_line_values.add_point(rel_x, rel_y, LineValues.InsertByXValue)

                    # update canvas ....
                    pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
                    self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)

                    # update the median color of the line ...
                    self.update_line_median_color()

                # .. and stay on current state until cancel is pressed.

            self.update_current_view()

    def prepare_number_controls(self):
        n_lines = self.data.total_lines()
        self.lbl_number_title.set_text("Lines in Chart: {0:d}".format(n_lines))

        self.fill_data_series_list(self.lbx_number_series_values)
        self.create_canvas_lines()

    def fill_data_series_list(self, text_list, exclude_values=None):
        text_list.clear_options()
        for idx, current_text in enumerate(self.data.data_series):
            if current_text is None:
                display_value = str(idx + 1)
            else:
                display_value = "{0:d}: {1:s}".format(idx + 1, current_text.value)

            if exclude_values is None or idx not in exclude_values:
                text_list.add_option(str(idx), display_value)

    def line_points_to_canvas_points(self, line_points):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        all_transformed_points = []
        for p_idx in range(len(line_points)):
            # transform current point from relative space to absolute pixel space (simple translation)
            c_x, c_y = line_points[p_idx]
            c_x += x1
            c_y = y2 - c_y
            current_point = (c_x, c_y)

            all_transformed_points.append(current_point)

        # now ... to numpy array ...
        all_transformed_points = np.array(all_transformed_points, np.float64)
        # apply current view scale ...
        all_transformed_points *= self.view_scale

        return all_transformed_points

    def create_canvas_lines(self):
        self.canvas_display.clear()

        for idx, line_values in enumerate(self.data.lines):
            # line_color = self.canvas_display.colors[idx % len(self.canvas_display.colors)]
            all_transformed_points = self.line_points_to_canvas_points(line_values.points)
            self.canvas_display.add_polyline_element("line_" + str(idx), all_transformed_points)

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_annotation_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeNavigate)

        # edit modes ...
        self.container_number_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeNumberEdit)
        self.container_data_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeLineSelect)
        self.container_line_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeLineEdit)
        self.container_preview_buttons.visible = (self.edition_mode == LineChartAnnotator.ModePointAdd)
        self.container_swap_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeLineSwap)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [LineChartAnnotator.ModeConfirmNumberOverwrite,
                                                                       LineChartAnnotator.ModePointAdd,
                                                                       LineChartAnnotator.ModePointEdit,
                                                                       LineChartAnnotator.ModeConfirmExit]

        if self.edition_mode == LineChartAnnotator.ModeConfirmNumberOverwrite:
            self.lbl_confirm_message.set_text("Discard Existing Line Data?")
        elif self.edition_mode == LineChartAnnotator.ModePointAdd:
            self.lbl_confirm_message.set_text("Click on New Point")
        elif self.edition_mode == LineChartAnnotator.ModePointEdit:
            self.lbl_confirm_message.set_text("Drag to New Position")
        elif self.edition_mode == LineChartAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Line Data?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode not in [LineChartAnnotator.ModePointAdd,
                                                                    LineChartAnnotator.ModePointEdit]

    def canvas_show_hide_lines(self, show_index):
        self.canvas_display.change_selected_element(None)
        self.tempo_canvas_name = None
        for element_name in self.canvas_display.elements:
            line_idx = int(element_name.split("_")[1])
            self.canvas_display.elements[element_name].visible = (show_index < 0 or show_index == line_idx)
            if show_index == line_idx:
                self.tempo_canvas_name = element_name
                self.canvas_display.change_selected_element(element_name)

    def btn_data_series_edit_click(self, button):
        if self.lbx_data_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        option_idx = int(self.lbx_data_series_values.selected_option_value)

        # prepare temporals
        self.tempo_line_index = option_idx
        self.tempo_line_values = LineValues.Copy(self.data.lines[option_idx])

        # series name ...
        display = self.lbx_data_series_values.option_display[self.lbx_data_series_values.selected_option_value]
        self.lbl_line_name.set_text(display)

        # ... list of points ...
        self.update_points_list()

        # canvas
        self.canvas_show_hide_lines(option_idx)
        self.canvas_display.locked = True

        self.set_editor_mode(LineChartAnnotator.ModeLineEdit)
        self.update_current_view(False)

    def btn_data_return_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModeNavigate)

    def update_points_list(self):
        self.lbx_line_points.clear_options()
        for idx, (p_x, p_y) in enumerate(self.tempo_line_values.points):
            display_value = "{0:d}: ({1:.1f}, {2:.1f})".format(idx + 1, p_x, p_y)
            self.lbx_line_points.add_option(str(idx), display_value)

    def btn_line_point_edit_click(self, button):
        # self.tempo_point_index = int(self.lbx_line_points.selected_option_value)
        self.canvas_display.locked = False
        self.set_editor_mode(LineChartAnnotator.ModePointEdit)

    def delete_tempo_line_point(self, del_idx):
        if self.tempo_line_values.remove_point(del_idx):
            # update GUI
            pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
            self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)

            self.update_points_list()
            self.update_current_view()

    def btn_line_point_delete_click(self, button):
        if self.lbx_line_points.selected_option_value is None:
            print("Must select a data point from list")
            return

        # try delete
        del_idx = int(self.lbx_line_points.selected_option_value)
        self.delete_tempo_line_point(del_idx)

    def update_line_median_color(self):
        # get the canvas based coordinates ....
        canvas_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
        # transform to image space
        canvas_points /= self.view_scale

        # get the colors of the pixels on the line
        colors = []
        for x, y in canvas_points:
            img_x = int(round(x))
            img_y = int(round(y))

            if 0 <= img_x < self.base_rgb_image.shape[1] and 0 <= img_y < self.base_rgb_image.shape[0]:
                colors.append(self.base_rgb_image[img_y, img_x])

        # get the average
        if len(colors) > 0:
            self.tempo_median_line_color = np.median(colors, axis=0)
        else:
            # default
            self.tempo_median_line_color = np.zeros(3, np.float64)

    def btn_line_point_add_click(self, button):
        self.update_line_median_color()
        self.set_editor_mode(LineChartAnnotator.ModePointAdd)

    def btn_line_return_accept_click(self, button):
        self.data.lines[self.tempo_line_index] = LineValues.Copy(self.tempo_line_values)
        self.data_changed = True
        # all lines must be displayed ... and nothing should be selected
        self.canvas_show_hide_lines(-1)
        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)
        self.update_current_view()

    def btn_line_return_cancel_click(self, button):
        # restore the line on the canvas to its previous  state
        pl_points = self.line_points_to_canvas_points(self.data.lines[self.tempo_line_index].points)
        self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
        # all lines must be displayed and nothing should be selected on the canvas
        self.canvas_show_hide_lines(-1)

        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)
        self.update_current_view(False)

    def lbx_line_points_value_changed(self, new_value, old_value):
        pass

    def img_main_mouse_double_click(self, img, position, button):
        if self.edition_mode == LineChartAnnotator.ModeLineEdit:
            # click relative position
            rel_x, rel_y = self.from_pos_to_rel_click(position)

            # find closest point ...
            distance, point_idx = self.tempo_line_values.closest_point(rel_x, rel_y)

            if button == 1:
                # left click
                if point_idx is not None and distance < LineChartAnnotator.DoubleClickMaxPointDistance:
                    # ... edit...
                    self.canvas_display.locked = False
                    self.set_editor_mode(LineChartAnnotator.ModePointEdit)
                else:
                    # ... add point ...
                    self.tempo_line_values.add_point(rel_x, rel_y, LineValues.InsertByXValue)
                    # update GUI
                    # ... canvas ....
                    pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
                    self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
                    # ... list of points ....
                    self.update_points_list()

                self.update_current_view(False)
            else:
                # right click ... delete ...
                if distance < LineChartAnnotator.DoubleClickMaxPointDistance:
                    self.delete_tempo_line_point(point_idx)

        elif self.edition_mode in [LineChartAnnotator.ModeNavigate, LineChartAnnotator.ModeLineSelect]:
            rel_x, rel_y = position
            rel_x /= self.view_scale
            rel_y /= self.view_scale

            for idx, current_text in enumerate(self.data.data_series):
                if current_text is not None:
                    # line_id = "line_" + str(idx)

                    if current_text.area_contains_point(rel_x, rel_y):
                        if self.edition_mode == LineChartAnnotator.ModeNavigate:
                            # simulate click on edit to move to ModeLineSelect
                            self.btn_edit_data_click(self.btn_edit_data)

                        self.lbx_data_series_values.change_option_selected(str(idx))
                        self.btn_data_series_edit_click(self.btn_data_series_edit)
                        break

                        # self.canvas_display.change_selected_element(line_id)

        elif self.edition_mode == LineChartAnnotator.ModePointEdit:
            if button == 3:
                # go back to previous mode ...
                self.btn_confirm_cancel_click(self.btn_confirm_cancel)

    def canvas_display_object_edited(self, canvas, element_name):
        pass

    def btn_data_series_swap_click(self, button):
        if self.lbx_data_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        if len(self.data.lines) < 2:
            print("There are no other lines to swap points with")
            return

        option_idx = int(self.lbx_data_series_values.selected_option_value)

        # prepare temporals
        self.tempo_line_index = option_idx

        # series name ...
        display = self.lbx_data_series_values.option_display[self.lbx_data_series_values.selected_option_value]
        self.lbl_swap_name.set_text(display)

        # ... list of other data series ...
        self.fill_data_series_list(self.lbx_swap_series_values, [option_idx])
        # self.update_points_list()

        # canvas
        # self.canvas_show_hide_lines(option_idx)
        # self.canvas_display.locked = True

        self.set_editor_mode(LineChartAnnotator.ModeLineSwap)
        self.update_current_view(False)

    def img_main_mouse_motion(self, screen_img, pos, rel, buttons):
        mouse_x, mouse_y = pos

        img_pixel_x = int(round(mouse_x / self.view_scale))
        img_pixel_y = int(round(mouse_y / self.view_scale))

        if self.edition_mode in [LineChartAnnotator.ModePointAdd]:
            zoom_pixels = 20
            zoom_border = 2
            blur_size = 5
            min_dist = 5
            if img_pixel_x + zoom_pixels > self.base_rgb_image.shape[1]:
                img_pixel_x = self.base_rgb_image.shape[1] - zoom_pixels
            elif img_pixel_x - zoom_pixels < 0:
                img_pixel_x = zoom_pixels

            if img_pixel_y + zoom_pixels > self.base_rgb_image.shape[0]:
                img_pixel_y = self.base_rgb_image.shape[0] - zoom_pixels
            elif img_pixel_y - zoom_pixels < 0:
                img_pixel_y = zoom_pixels

            cut_min_x = img_pixel_x - zoom_pixels
            cut_max_x = img_pixel_x + zoom_pixels
            cut_min_y = img_pixel_y - zoom_pixels
            cut_max_y = img_pixel_y + zoom_pixels
            zoom_cut = self.base_rgb_image[cut_min_y:cut_max_y, cut_min_x:cut_max_x].copy()

            raw_diff = zoom_cut - self.tempo_median_line_color
            sqr_diff = np.power(raw_diff, 2.0)
            # print("----")
            # print(self.tempo_median_line_color)
            # print(zoom_cut[:5, :5])
            # print(raw_diff[:5, :5])
            # print(sqr_diff[:5, :5])

            # get the raw distance ...
            sqr_diff = np.sum(sqr_diff, axis=2)

            # smooth distance ... this helps preferring the middle of lines instead of borders
            sqr_diff = cv2.blur(sqr_diff, (blur_size, blur_size))

            # remove any point too close to existing points ...
            canvas_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
            # transform to image space
            canvas_points /= self.view_scale

            # decrease color contrast
            zoom_cut = zoom_cut.astype(np.float64)
            zoom_cut /= 2
            zoom_cut += 63
            zoom_cut = zoom_cut.astype(np.uint8)

            # ...for each point in the line ...
            replacement_val = sqr_diff.max()
            for x, y in canvas_points:
                img_x = int(round(x))
                img_y = int(round(y))

                # check if it falls within the current patch ...
                if cut_min_x <= img_x < cut_max_x and cut_min_y <= img_y < cut_max_y:
                    # assign a value that will make it unlikely to be selected ...
                    p_min_y = max(0, img_y - min_dist - cut_min_y)
                    p_max_y = img_y + min_dist + 1 - cut_min_y
                    p_min_x = max(0, img_x - min_dist - cut_min_x)
                    p_max_x = img_x + min_dist + 1 - cut_min_x
                    # print("HERE! " + str((x, y, img_x, img_y, cut_min_x, cut_max_x, cut_min_y, cut_max_y, p_min_x, p_min_y)))
                    sqr_diff[p_min_y:p_max_y, p_min_x:p_max_x] = replacement_val + 1

                    # also, show a mark in the preview ...
                    zoom_cut[p_min_y:p_max_y, p_min_x:p_max_x] = (255, 0, 0)

            # eliminate the borders ...
            sqr_diff[:zoom_border, :] = replacement_val + 1
            sqr_diff[-zoom_border:, :] = replacement_val + 1
            sqr_diff[:, :zoom_border] = replacement_val + 1
            sqr_diff[:, -zoom_border:] = replacement_val + 1

            # cv2.imshow("test", ((sqr_diff / sqr_diff.max()) * 255).astype(np.uint8))

            min_idx = np.argmin(sqr_diff)
            rel_x = min_idx % zoom_cut.shape[1]
            rel_y = int(min_idx / zoom_cut.shape[0])

            # print((sqr_diff[rel_y, rel_x], zoom_cut[rel_y, rel_x], self.tempo_median_line_color))

            if sqr_diff[rel_y, rel_x] < 10000:
                # print("A")
                # the color is similar enough ... add suggestion

                self.hover_line_point_x = rel_x + cut_min_x
                self.hover_line_point_y = rel_y + cut_min_y

                # print(self.tempo_median_line_color)
                # print(sqr_diff[rel_y, rel_x])

                # highlight the suggested pixel
                zoom_cut[rel_y, :] = (0, 255, 0)
                zoom_cut[:, rel_x] = (0, 255, 0)
            else:
                # print("B")
                # the closest color is not similar enough, do not suggest anything
                self.hover_line_point_x = None
                self.hover_line_point_y = None

                # highlight the center pixel by default ...
                zoom_cut[int(zoom_cut.shape[0] / 2), :] = (255, 0, 0)
                zoom_cut[:, int(zoom_cut.shape[1] / 2)] = (255, 0, 0)

            self.img_preview.set_image(zoom_cut, 200, 200)

        elif self.edition_mode in [LineChartAnnotator.ModeNavigate, LineChartAnnotator.ModeLineSelect]:
            # determine if the mouse pointer is over sme specific line ...

            for idx, current_text in enumerate(self.data.data_series):
                if current_text is not None:
                    line_id = "line_" + str(idx)

                    if current_text.area_contains_point(img_pixel_x, img_pixel_y):
                        self.canvas_display.change_selected_element(line_id)

    def btn_swap_return_accept_click(self, button):
        if self.lbx_swap_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        src_idx = self.tempo_line_index
        dst_idx = int(self.lbx_swap_series_values.selected_option_value)

        # swap the line data ...
        print("Swapping line #{0:d} with #{1:d}".format(src_idx, dst_idx))

        copy_src = LineValues.Copy(self.data.lines[src_idx])
        copy_dst = LineValues.Copy(self.data.lines[dst_idx])

        self.data.lines[src_idx] = copy_dst
        self.data.lines[dst_idx] = copy_src

        self.data_changed = True

        # update the canvas
        pl_points = self.line_points_to_canvas_points(self.data.lines[src_idx].points)
        self.canvas_display.update_polyline_element("line_" + str(src_idx), pl_points, True)

        pl_points = self.line_points_to_canvas_points(self.data.lines[dst_idx].points)
        self.canvas_display.update_polyline_element("line_" + str(dst_idx), pl_points, True)

        self.canvas_show_hide_lines(-1)

        # go back to the main mode ...
        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)

    def btn_swap_return_cancel_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)


    def get_shift_button_delta(self, direction):
        current_time = time.time()
        # check
        if self.last_shift_direction != direction:
            # previous direction is different
            # (will always be different the first time the button is used)
            self.last_shift_direction = direction
            delta = 1.0
        else:
            # previous direction is the same, check for time between clicks
            if current_time - self.last_shift_time < 2.0:
                # go faster
                delta = 3.0
            else:
                # long time ago, just use precision
                delta = 1.0
        self.last_shift_time = current_time

        return delta

    def btn_line_point_shift_up_click(self, button):
        delta = self.get_shift_button_delta(1)

        # ... add point ...
        self.tempo_line_values.shift_all_points(0, delta)

        # update GUI
        # ... canvas ....
        pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
        self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
        # ... list of points ....
        self.update_points_list()

    def btn_line_point_shift_down_click(self, button):
        delta = self.get_shift_button_delta(2)

        # ... add point ...
        self.tempo_line_values.shift_all_points(0, -delta)

        # update GUI
        # ... canvas ....
        pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
        self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
        # ... list of points ....
        self.update_points_list()

    def btn_line_point_shift_left_click(self, button):
        delta = self.get_shift_button_delta(3)

        # ... add point ...
        self.tempo_line_values.shift_all_points(-delta, 0.0)

        # update GUI
        # ... canvas ....
        pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
        self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
        # ... list of points ....
        self.update_points_list()

    def btn_line_point_shift_right_click(self, button):
        delta = self.get_shift_button_delta(4)

        # ... add point ...
        self.tempo_line_values.shift_all_points(delta, 0.0)

        # update GUI
        # ... canvas ....
        pl_points = self.line_points_to_canvas_points(self.tempo_line_values.points)
        self.canvas_display.update_polyline_element(self.tempo_canvas_name, pl_points, True)
        # ... list of points ....
        self.update_points_list()
