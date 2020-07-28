
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

from ChartInfo.data.box_data import BoxData
from ChartInfo.data.box_values import BoxValues
from ChartInfo.data.series_sorting import SeriesSorting

class BoxChartAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeOrderEdit = 2
    ModeGroupingEdit = 3
    ModeParameterEdit = 4
    ModeDataEdit = 5
    ModeDataSelect = 6
    ModeConfirmNumberOverwrite = 7
    ModeConfirmExit = 8

    DataBoxMinimum = 0
    DataBoxMedian = 1
    DataBoxMaximum = 2
    DataWhiskerMinimum = 3
    DataWhiskerMaximum = 4
    DataBoxSliders = 5

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Box Chart Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.data is None:
            # create default Box chart data ...
            self.data = BoxData.CreateDefault(self.panel_info)
            self.data_changed = True
        else:
            # make a copy ...
            self.data = BoxData.Copy(self.panel_info.data)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (80, 80, 80)
        self.text_color = (255, 255, 255)

        self.elements.back_color = self.general_background
        self.edition_mode = None

        self.tempo_ordering = None

        self.tempo_decimal_offset = None
        self.tempo_decimal_width = None
        self.tempo_decimal_inner_dist = None
        self.tempo_decimal_outer_dist = None

        self.tempo_data_editing = None
        self.tempo_box_values = None

        self.tempo_box_polygons = None
        self.tempo_medians_lines = None
        self.tempo_bottom_whiskers = None
        self.tempo_top_whiskers = None
        self.tempo_box_polygon_index = None

        self.label_title = None

        self.container_confirm_buttons = None
        self.lbl_confirm_message = None
        self.btn_confirm_cancel = None
        self.btn_confirm_accept = None

        self.container_annotation_buttons = None
        self.lbl_edit_title = None
        self.btn_edit_number = None
        self.btn_edit_order = None
        self.btn_edit_grouping = None
        self.btn_edit_parameters = None
        self.btn_edit_data = None
        self.btn_return_accept = None
        self.btn_return_cancel = None

        self.container_number_buttons = None
        self.lbl_number_title = None
        self.lbl_number_categories_title = None
        self.lbx_number_categories_values = None
        self.btn_number_categories_add = None
        self.btn_number_categories_remove = None
        self.lbl_number_series_title = None
        self.lbx_number_series_values = None
        self.btn_number_series_add = None
        self.btn_number_series_remove = None
        self.btn_number_return = None

        self.container_order_buttons = None
        self.lbl_order_title = None
        self.lbx_order_list = None
        self.btn_order_move_up = None
        self.btn_order_move_down = None
        self.btn_order_return_accept = None
        self.btn_order_return_cancel = None

        self.container_grouping_buttons = None
        self.lbl_grouping_title = None
        self.lbl_grouping_description = None
        self.btn_grouping_by_categories = None
        self.btn_grouping_by_data_series = None
        self.btn_grouping_return = None

        self.container_parameters_buttons = None
        self.lbl_parameters_title = None
        self.lbl_parameters_offset = None
        self.btns_parameters_move_offset = None
        self.lbl_parameters_width = None
        self.btns_parameters_move_width = None
        self.lbl_parameters_inner_dist = None
        self.btns_parameters_move_inner_dist = None
        self.lbl_parameters_outer_dist = None
        self.btns_parameters_move_outer_dist = None
        self.btn_parameters_return_accept = None
        self.btn_parameters_return_cancel = None

        self.container_data_buttons = None
        self.lbl_data_title = None
        self.btn_data_box_minimum = None
        self.btn_data_box_median = None
        self.btn_data_box_maximum = None
        self.btn_data_whisker_minimum = None
        self.btn_data_whisker_maximum = None
        self.btn_data_boxes_sliders = None
        self.btn_data_return = None

        self.create_controllers()

        # get the view ...
        self.update_current_view(True)


    def create_controllers(self):
        # add elements....
        button_text_color = (35, 50, 20)
        button_back_color = (228, 228, 228)

        # Main Title
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Box Chart Data Annotation", 28)
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
        darker_background = (30, 30, 30)

        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 380),
                                                            back_color=darker_background)
        self.container_annotation_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Box Chart Annotation Options", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        self.btn_edit_number = ScreenButton("btn_edit_number", "Edit Number of Boxes", 21, button_width)
        self.btn_edit_number.set_colors(button_text_color, button_back_color)
        self.btn_edit_number.position = (button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_number.click_callback = self.btn_edit_number_click
        self.container_annotation_buttons.append(self.btn_edit_number)

        self.btn_edit_order = ScreenButton("btn_edit_order", "Edit Order", 21, button_width)
        self.btn_edit_order.set_colors(button_text_color, button_back_color)
        self.btn_edit_order.position = (button_left, self.btn_edit_number.get_bottom() + 10)
        self.btn_edit_order.click_callback = self.btn_edit_order_click
        self.container_annotation_buttons.append(self.btn_edit_order)

        self.btn_edit_grouping = ScreenButton("btn_edit_grouping", "Edit Box Grouping", 21, button_width)
        self.btn_edit_grouping.set_colors(button_text_color, button_back_color)
        self.btn_edit_grouping.position = (button_left, self.btn_edit_order.get_bottom() + 10)
        self.btn_edit_grouping.click_callback = self.btn_edit_grouping_click
        self.container_annotation_buttons.append(self.btn_edit_grouping)

        self.btn_edit_parameters = ScreenButton("btn_edit_parameters", "Edit Box Parameters", 21, button_width)
        self.btn_edit_parameters.set_colors(button_text_color, button_back_color)
        self.btn_edit_parameters.position = (button_left, self.btn_edit_grouping.get_bottom() + 10)
        self.btn_edit_parameters.click_callback = self.btn_edit_parameters_click
        self.container_annotation_buttons.append(self.btn_edit_parameters)

        self.btn_edit_data = ScreenButton("btn_edit_data", "Edit Box Data", 21, button_width)
        self.btn_edit_data.set_colors(button_text_color, button_back_color)
        self.btn_edit_data.position = (button_left, self.btn_edit_parameters.get_bottom() + 10)
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
        # - options to define the total number of boxes in the chart ....
        self.container_number_buttons = ScreenContainer("container_number_buttons", (container_width, 530),
                                                            back_color=darker_background)
        self.container_number_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_number_buttons)

        self.lbl_number_title = ScreenLabel("lbl_number_title ", "Boxes in Chart: [0]", 25, 290, 1)
        self.lbl_number_title.position = (5, 5)
        self.lbl_number_title.set_background(darker_background)
        self.lbl_number_title.set_color(self.text_color)
        self.container_number_buttons.append(self.lbl_number_title)

        self.lbl_number_categories_title = ScreenLabel("lbl_number_categories_title", "Categories", 21, 290, 1)
        self.lbl_number_categories_title.position = (5, self.lbl_number_title.get_bottom() + 15)
        self.lbl_number_categories_title.set_background(darker_background)
        self.lbl_number_categories_title.set_color(self.text_color)
        self.container_number_buttons.append(self.lbl_number_categories_title)

        self.lbx_number_categories_values = ScreenTextlist("lbx_number_categories_values", (container_width - 20, 140),
                                                           18, back_color=(255,255,255), option_color=(0, 0, 0),
                                                           selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_number_categories_values.position = (10, self.lbl_number_categories_title.get_bottom() + 10)
        # self.lbx_number_categories_values.selected_value_change_callback = self.lbx_number_categories_values_changed
        self.container_number_buttons.append(self.lbx_number_categories_values)

        self.btn_number_categories_add = ScreenButton("btn_number_categories_add", "Add", 21, button_2_width)
        self.btn_number_categories_add.set_colors(button_text_color, button_back_color)
        self.btn_number_categories_add.position = (button_2_left, self.lbx_number_categories_values.get_bottom() + 10)
        self.btn_number_categories_add.click_callback = self.btn_number_categories_add_click
        self.container_number_buttons.append(self.btn_number_categories_add)

        self.btn_number_categories_remove = ScreenButton("btn_number_categories_remove", "Remove", 21, button_2_width)
        self.btn_number_categories_remove.set_colors(button_text_color, button_back_color)
        self.btn_number_categories_remove.position = (button_2_right, self.lbx_number_categories_values.get_bottom() + 10)
        self.btn_number_categories_remove.click_callback = self.btn_number_categories_remove_click
        self.container_number_buttons.append(self.btn_number_categories_remove)

        self.lbl_number_series_title = ScreenLabel("lbl_number_series_title", "Data Series", 21, 290, 1)
        self.lbl_number_series_title.position = (5, self.btn_number_categories_add.get_bottom() + 10)
        self.lbl_number_series_title.set_background(darker_background)
        self.lbl_number_series_title.set_color(self.text_color)
        self.container_number_buttons.append(self.lbl_number_series_title)

        self.lbx_number_series_values = ScreenTextlist("lbx_number_series_values", (container_width - 20, 140),
                                                       18, back_color=(255,255,255), option_color=(0, 0, 0),
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

        # =========================================================
        # container with options to change box ordering (no stacking for box charts)...
        self.container_order_buttons = ScreenContainer("container_order_buttons", (container_width, 500),
                                                       back_color=darker_background)
        self.container_order_buttons.position = (self.container_view_buttons.get_left(),
                                                 self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_order_buttons)

        self.lbl_order_title = ScreenLabel("lbl_order_title", "Box Ordering", 21, 290, 1)
        self.lbl_order_title.position = (5, 5)
        self.lbl_order_title.set_background(darker_background)
        self.lbl_order_title.set_color(self.text_color)
        self.container_order_buttons.append(self.lbl_order_title)

        self.lbx_order_list = ScreenTextlist("lbx_order_list", (container_width - 20, 350),
                                                           18, back_color=(255,255,255), option_color=(0, 0, 0),
                                                           selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_order_list.position = (10, self.lbl_order_title.get_bottom() + 20)
        # self.lbx_order_list.selected_value_change_callback = self.lbx_order_list_values_changed
        self.container_order_buttons.append(self.lbx_order_list)

        self.btn_order_move_up = ScreenButton("btn_order_move_up", "Move Up", 21, button_2_width)
        self.btn_order_move_up.set_colors(button_text_color, button_back_color)
        self.btn_order_move_up.position = (button_2_left, self.lbx_order_list.get_bottom() + 10)
        self.btn_order_move_up.click_callback = self.btn_order_move_up_click
        self.container_order_buttons.append(self.btn_order_move_up)

        self.btn_order_move_down = ScreenButton("btn_order_move_down", "Move Dowm", 21, button_2_width)
        self.btn_order_move_down.set_colors(button_text_color, button_back_color)
        self.btn_order_move_down.position = (button_2_right, self.lbx_order_list.get_bottom() + 10)
        self.btn_order_move_down.click_callback = self.btn_order_move_down_click
        self.container_order_buttons.append(self.btn_order_move_down)

        self.btn_order_return_accept = ScreenButton("btn_order_return_accept", "Accept", 21, button_2_width)
        return_top = self.container_order_buttons.height - self.btn_order_return_accept.height - 10
        self.btn_order_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_order_return_accept.position = (button_2_left, return_top)
        self.btn_order_return_accept.click_callback = self.btn_order_return_accept_click
        self.container_order_buttons.append(self.btn_order_return_accept)

        self.btn_order_return_cancel = ScreenButton("btn_order_return_cancel", "Cancel", 21, button_2_width)
        self.btn_order_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_order_return_cancel.position = (button_2_right, return_top)
        self.btn_order_return_cancel.click_callback = self.btn_order_return_cancel_click
        self.container_order_buttons.append(self.btn_order_return_cancel)

        self.container_order_buttons.visible = False

        # =========================================================
        # container with options to change box grouping type ....

        self.container_grouping_buttons = ScreenContainer("container_grouping_buttons", (container_width, 230),
                                                            back_color=darker_background)
        self.container_grouping_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_grouping_buttons)
        self.lbl_grouping_title = ScreenLabel("lbl_grouping_title", "Box Grouping Options", 21, 290, 1)
        self.lbl_grouping_title.position = (5, 5)
        self.lbl_grouping_title.set_background(darker_background)
        self.lbl_grouping_title.set_color(self.text_color)
        self.container_grouping_buttons.append(self.lbl_grouping_title)

        self.lbl_grouping_description = ScreenLabel("lbl_grouping_description", "Group Boxes by ??", 21, 290, 1)
        self.lbl_grouping_description.position = (5, self.lbl_grouping_title.get_bottom() + 20)
        self.lbl_grouping_description.set_background(darker_background)
        self.lbl_grouping_description.set_color(self.text_color)
        self.container_grouping_buttons.append(self.lbl_grouping_description)

        self.btn_grouping_by_categories = ScreenButton("btn_grouping_by_categories", "Group By Categories", 21, button_width)
        self.btn_grouping_by_categories.set_colors(button_text_color, button_back_color)
        self.btn_grouping_by_categories.position = (button_left, self.lbl_grouping_description.get_bottom() + 10)
        self.btn_grouping_by_categories.click_callback = self.btn_grouping_by_categories_click
        self.container_grouping_buttons.append(self.btn_grouping_by_categories)

        self.btn_grouping_by_data_series = ScreenButton("btn_grouping_by_data_series", "Group By Data Series", 21, button_width)
        self.btn_grouping_by_data_series.set_colors(button_text_color, button_back_color)
        self.btn_grouping_by_data_series.position = (button_left, self.btn_grouping_by_categories.get_bottom() + 10)
        self.btn_grouping_by_data_series.click_callback = self.btn_grouping_by_data_series_click
        self.container_grouping_buttons.append(self.btn_grouping_by_data_series)

        self.btn_grouping_return = ScreenButton("btn_grouping_return", "Return", 21, button_width)
        self.btn_grouping_return.set_colors(button_text_color, button_back_color)
        self.btn_grouping_return.position = (button_left, self.btn_grouping_by_data_series.get_bottom() + 30)
        self.btn_grouping_return.click_callback = self.btn_grouping_return_click
        self.container_grouping_buttons.append(self.btn_grouping_return)
        self.container_grouping_buttons.visible = False

        # =========================================================
        # container with options to change boxes parameters ....
        self.container_parameters_buttons = ScreenContainer("container_parameters_buttons", (container_width, 430),
                                                            back_color=darker_background)
        self.container_parameters_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_parameters_buttons)

        self.lbl_parameters_title = ScreenLabel("lbl_parameters_title", "Box Parameters", 21, 290, 1)
        self.lbl_parameters_title.position = (5, 5)
        self.lbl_parameters_title.set_background(darker_background)
        self.lbl_parameters_title.set_color(self.text_color)
        self.container_parameters_buttons.append(self.lbl_parameters_title)

        self.lbl_parameters_offset = ScreenLabel("lbl_parameters_offset", "Offset: [0]", 21, 290, 1)
        self.lbl_parameters_offset.position = (5, self.lbl_parameters_title.get_bottom() + 20)
        self.lbl_parameters_offset.set_background(darker_background)
        self.lbl_parameters_offset.set_color(self.text_color)
        self.container_parameters_buttons.append(self.lbl_parameters_offset)

        # precise_btn_info = [("-10.0", -100), ("-1.0", -10), ("-0.1", -1), ("+0.1", 1), ("+1.0", 10), ("+10.0", 100)]
        precise_btn_info = [("-1.0", -10), ("-0.1", -1), ("+0.1", 1), ("+1.0", 10)]
        precise_btn_space = (container_width / len(precise_btn_info))
        precise_btn_width = int(precise_btn_space * 0.80)
        precise_btn_offset = int((precise_btn_space - precise_btn_width) / 2)

        self.btns_parameters_move_offset = []
        for idx, (caption, tag) in enumerate(precise_btn_info):
            left = precise_btn_space * idx + precise_btn_offset

            button = ScreenButton("btns_parameters_move_offset_" + str(idx), caption, 16, precise_btn_width)
            button.set_colors(button_text_color, button_back_color)
            button.position = (left, self.lbl_parameters_offset.get_bottom() + 10)
            button.click_callback = self.btns_parameters_move_offset_click
            button.tag = tag
            self.btns_parameters_move_offset.append(button)

            self.container_parameters_buttons.append(button)

        self.lbl_parameters_width = ScreenLabel("lbl_parameters_width", "Width: [0]", 21, 290, 1)
        self.lbl_parameters_width.position = (5, self.btns_parameters_move_offset[-1].get_bottom() + 20)
        self.lbl_parameters_width.set_background(darker_background)
        self.lbl_parameters_width.set_color(self.text_color)
        self.container_parameters_buttons.append(self.lbl_parameters_width)

        self.btns_parameters_move_width = []
        for idx, (caption, tag) in enumerate(precise_btn_info):
            left = precise_btn_space * idx + precise_btn_offset

            button = ScreenButton("btns_parameters_move_width_" + str(idx), caption, 16, precise_btn_width)
            button.set_colors(button_text_color, button_back_color)
            button.position = (left, self.lbl_parameters_width.get_bottom() + 10)
            button.click_callback = self.btns_parameters_move_width_click
            button.tag = tag
            self.btns_parameters_move_width.append(button)

            self.container_parameters_buttons.append(button)

        self.lbl_parameters_inner_dist = ScreenLabel("lbl_parameters_inner_dist", "Inner Distance: [0]", 21, 290, 1)
        self.lbl_parameters_inner_dist.position = (5, self.btns_parameters_move_width[-1].get_bottom() + 20)
        self.lbl_parameters_inner_dist.set_background(darker_background)
        self.lbl_parameters_inner_dist.set_color(self.text_color)
        self.container_parameters_buttons.append(self.lbl_parameters_inner_dist)

        self.btns_parameters_move_inner_dist = []
        for idx, (caption, tag) in enumerate(precise_btn_info):
            left = precise_btn_space * idx + precise_btn_offset

            button = ScreenButton("btns_parameters_move_inner_dist_" + str(idx), caption, 16, precise_btn_width)
            button.set_colors(button_text_color, button_back_color)
            button.position = (left, self.lbl_parameters_inner_dist.get_bottom() + 10)
            button.click_callback = self.btns_parameters_move_inner_dist_click
            button.tag = tag
            self.btns_parameters_move_inner_dist.append(button)

            self.container_parameters_buttons.append(button)

        self.lbl_parameters_outer_dist = ScreenLabel("lbl_parameters_outer_dist", "Outer Distance: [0]", 21, 290, 1)
        self.lbl_parameters_outer_dist.position = (5, self.btns_parameters_move_inner_dist[-1].get_bottom() + 20)
        self.lbl_parameters_outer_dist.set_background(darker_background)
        self.lbl_parameters_outer_dist.set_color(self.text_color)
        self.container_parameters_buttons.append(self.lbl_parameters_outer_dist)

        self.btns_parameters_move_outer_dist = []
        for idx, (caption, tag) in enumerate(precise_btn_info):
            left = precise_btn_space * idx + precise_btn_offset

            button = ScreenButton("btns_parameters_move_outer_dist_" + str(idx), caption, 16, precise_btn_width)
            button.set_colors(button_text_color, button_back_color)
            button.position = (left, self.lbl_parameters_outer_dist.get_bottom() + 10)
            button.click_callback = self.btns_parameters_move_outer_dist_click
            button.tag = tag
            self.btns_parameters_move_outer_dist.append(button)

            self.container_parameters_buttons.append(button)

        self.btn_parameters_return_accept = ScreenButton("btn_parameters_return_accept", "Accept", 21, button_2_width)
        return_top = self.container_parameters_buttons.height - self.btn_parameters_return_accept.height - 10
        self.btn_parameters_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_parameters_return_accept.position = (button_2_left, return_top)
        self.btn_parameters_return_accept.click_callback = self.btn_parameters_return_accept_click
        self.container_parameters_buttons.append(self.btn_parameters_return_accept)

        self.btn_parameters_return_cancel = ScreenButton("btn_parameters_return_cancel", "Cancel", 21, button_2_width)
        self.btn_parameters_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_parameters_return_cancel.position = (button_2_right, return_top)
        self.btn_parameters_return_cancel.click_callback = self.btn_parameters_return_cancel_click
        self.container_parameters_buttons.append(self.btn_parameters_return_cancel)
        self.container_parameters_buttons.visible = False

        # ==========================================
        # Data annotation options ....

        self.container_data_buttons = ScreenContainer("container_data_buttons", (container_width, 410),
                                                      back_color=darker_background)
        self.container_data_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_data_buttons)

        self.lbl_data_title = ScreenLabel("lbl_data_title", "Box Data", 21, 290, 1)
        self.lbl_data_title.position = (5, 5)
        self.lbl_data_title.set_background(darker_background)
        self.lbl_data_title.set_color(self.text_color)
        self.container_data_buttons.append(self.lbl_data_title)

        self.btn_data_boxes_sliders = ScreenButton("btn_data_boxes_sliders", "Adjust All by Dragging", 21, button_width)
        self.btn_data_boxes_sliders.set_colors(button_text_color, button_back_color)
        self.btn_data_boxes_sliders.position = (button_left, self.lbl_data_title.get_bottom() + 20)
        self.btn_data_boxes_sliders.click_callback = self.btn_data_boxes_sliders_click
        self.container_data_buttons.append(self.btn_data_boxes_sliders)

        self.btn_data_whisker_maximum = ScreenButton("btn_data_whisker_maximum", "Adjust Whiskers Maxs", 21, button_width)
        self.btn_data_whisker_maximum.set_colors(button_text_color, button_back_color)
        self.btn_data_whisker_maximum.position = (button_left, self.btn_data_boxes_sliders.get_bottom() + 20)
        self.btn_data_whisker_maximum.click_callback = self.btn_data_whisker_maximum_click
        self.container_data_buttons.append(self.btn_data_whisker_maximum)

        self.btn_data_box_maximum = ScreenButton("btn_data_box_maximum", "Adjust Boxes Maxs", 21, button_width)
        self.btn_data_box_maximum.set_colors(button_text_color, button_back_color)
        self.btn_data_box_maximum.position = (button_left, self.btn_data_whisker_maximum.get_bottom() + 10)
        self.btn_data_box_maximum.click_callback = self.btn_data_box_maximum_click
        self.container_data_buttons.append(self.btn_data_box_maximum)

        self.btn_data_box_median = ScreenButton("btn_data_box_median", "Adjust Boxes Medians", 21, button_width)
        self.btn_data_box_median.set_colors(button_text_color, button_back_color)
        self.btn_data_box_median.position = (button_left, self.btn_data_box_maximum.get_bottom() + 10)
        self.btn_data_box_median.click_callback = self.btn_data_box_median_click
        self.container_data_buttons.append(self.btn_data_box_median)

        self.btn_data_box_minimum = ScreenButton("btn_data_box_minimum", "Adjust Boxes Mins", 21, button_width)
        self.btn_data_box_minimum.set_colors(button_text_color, button_back_color)
        self.btn_data_box_minimum.position = (button_left, self.btn_data_box_median.get_bottom() + 10)
        self.btn_data_box_minimum.click_callback = self.btn_data_box_minimum_click
        self.container_data_buttons.append(self.btn_data_box_minimum)

        self.btn_data_whisker_minimum = ScreenButton("btn_data_whisker_minimum", "Adjust Whiskers Mins", 21, button_width)
        self.btn_data_whisker_minimum.set_colors(button_text_color, button_back_color)
        self.btn_data_whisker_minimum.position = (button_left, self.btn_data_box_minimum.get_bottom() + 10)
        self.btn_data_whisker_minimum.click_callback = self.btn_data_whisker_minimum_click
        self.container_data_buttons.append(self.btn_data_whisker_minimum)


        self.btn_data_return = ScreenButton("btn_data_return", "Return", 21, button_width)
        self.btn_data_return.set_colors(button_text_color, button_back_color)
        self.btn_data_return.position = (button_left, self.btn_data_whisker_minimum.get_bottom() + 30)
        self.btn_data_return.click_callback = self.btn_data_return_click
        self.container_data_buttons.append(self.btn_data_return)
        self.container_data_buttons.visible = True

        # ======================================
        # visuals
        # ===========================

        self.prepare_number_controls()

        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)

    def compute_box_polygons(self):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # close the data area rectangle ?
        # cv2.line(modified_image, (x2, y1), (x2, y2), (0, 128, 0), thickness=1)
        # cv2.line(modified_image, (x1, y1), (x2, y1), (0, 0, 128), thickness=1)

        # Boxes
        if self.edition_mode == BoxChartAnnotator.ModeParameterEdit:
            box_offset = self.tempo_decimal_offset / 10
            box_width = self.tempo_decimal_width / 10
            box_inner_dist = self.tempo_decimal_inner_dist / 10
            box_outer_dist = self.tempo_decimal_outer_dist / 10
        else:
            box_offset = self.data.box_offset
            box_width = self.data.box_width
            box_inner_dist = self.data.box_inner_dist
            box_outer_dist = self.data.box_outer_dist

        if self.edition_mode == BoxChartAnnotator.ModeDataSelect:
            boxes = self.tempo_box_values
        else:
            boxes = self.data.boxes

        if self.data.box_vertical:
            # assume left to right
            box_start = x1 + box_offset
            # assume they start at the bottom
            box_baseline = y2
        else:
            # assume top to bottom
            box_start = y1 + box_offset
            # assume they start at the left
            box_baseline = x1

        boxes_lines = []
        medians_lines = []
        top_whiskers = []
        bottom_whiskers = []

        self.tempo_box_polygon_index = []

        if self.data.box_grouping == BoxData.GroupingByCategory:
            # boxes are grouped by categorical value ...
            for cat_idx, category in enumerate(self.data.categories):
                for group_idx, group in enumerate(self.data.box_sorting.order):
                    box_end = box_start + box_width

                    # No stacking for box plots ... the group should contain only one data series ...
                    series_idx = group[0]

                    # ...retrieve corresponding box values ...
                    box = boxes[series_idx][cat_idx]

                    # ... get drawing info ...
                    all_box_lines = box.get_box_lines(box_baseline, box_start, box_end, self.data.box_vertical)
                    box_polygon, box_median, whisker_bottom, whisker_top = all_box_lines

                    #  ... add drawing info ....
                    boxes_lines.append(box_polygon)
                    medians_lines.append(box_median)
                    bottom_whiskers.append(whisker_bottom)
                    top_whiskers.append(whisker_top)

                    # ... index for quicker mapping between boxes to click positions ....
                    self.tempo_box_polygon_index.append((series_idx, cat_idx))

                    # move to end of the box ... (+ width)
                    box_start += box_width
                    # check if move to the next box on same grouping
                    if group_idx + 1 < len(self.data.box_sorting.order):
                        # + distance between contiguous bars
                        box_start += box_inner_dist

                # next group of boxes ...
                box_start += box_outer_dist

        else:
            # boxes are grouped by data series
            for group_idx, group in enumerate(self.data.box_sorting.order):
                for cat_idx, category in enumerate(self.data.categories):
                    box_end = box_start + box_width

                    # No stacking for box plots ... the group should contain only one data series ...
                    series_idx = group[0]

                    # ...retrieve corresponding box values ...
                    box = boxes[series_idx][cat_idx]

                    # ... get drawing info ...
                    all_box_lines = box.get_box_lines(box_baseline, box_start, box_end, self.data.box_vertical)
                    box_polygon, box_median, whisker_bottom, whisker_top = all_box_lines

                    #  ... add drawing info ....
                    boxes_lines.append(box_polygon)
                    medians_lines.append(box_median)
                    bottom_whiskers.append(whisker_bottom)
                    top_whiskers.append(whisker_top)

                    # ... index for quicker mapping between boxes to click positions ....
                    self.tempo_box_polygon_index.append((series_idx, cat_idx))

                    # move to the end of the box
                    box_start += box_width
                    # check if move to the next box on same grouping
                    if cat_idx + 1 < len(self.data.categories):
                        box_start += box_inner_dist

                # next group of boxes ...
                box_start += box_outer_dist

        boxes_lines = np.array(boxes_lines).round().astype(np.int32)
        medians_lines = np.array(medians_lines).round().astype(np.int32)
        bottom_whiskers = np.array(bottom_whiskers).round().astype(np.int32)
        top_whiskers = np.array(top_whiskers).round().astype(np.int32)

        self.tempo_box_polygons = boxes_lines
        self.tempo_medians_lines = medians_lines
        self.tempo_bottom_whiskers = bottom_whiskers
        self.tempo_top_whiskers = top_whiskers

    def custom_view_update(self, modified_image):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # axes lines
        cv2.line(modified_image, (x1, y1), (x1, y2), (0, 255, 0), thickness=1)  # y = green
        cv2.line(modified_image, (x1, y2), (x2, y2), (0, 0, 255), thickness=1)  # x = blue

        if (self.edition_mode == BoxChartAnnotator.ModeDataSelect and
            self.tempo_data_editing == BoxChartAnnotator.DataBoxSliders):
            col_val = 128
        else:
            col_val = 255

        modified_image = cv2.polylines(modified_image, self.tempo_box_polygons, True, (col_val, 0, 0))
        modified_image = cv2.polylines(modified_image, self.tempo_medians_lines, False, (0, col_val, 0))
        modified_image = cv2.polylines(modified_image, self.tempo_bottom_whiskers, False, (0, 0, col_val))
        modified_image = cv2.polylines(modified_image, self.tempo_top_whiskers, False, (0, 0, col_val))

    def update_current_view(self, resized=False):
        # first, update the boxes drawing data (also used on mouse events)
        # do this regardless of whether they will be drawn or not (view-mode independent)
        self.compute_box_polygons()
        # now do the usual drawing using parent class method ...
        BaseImageAnnotator.update_current_view(self, resized)

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [BoxChartAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(BoxChartAnnotator.ModeNavigate)

        elif self.edition_mode == BoxChartAnnotator.ModeDataSelect:
            # remove any canvas objects and lock the canvas
            self.canvas_display.clear()
            self.canvas_display.locked = True

            # back to regular data edit ...
            self.set_editor_mode(BoxChartAnnotator.ModeDataEdit)
            self.update_current_view()

        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == BoxChartAnnotator.ModeConfirmExit:
            print("-> Changes made to Box Data Annotations were lost")
            self.return_screen = self.parent_screen

        elif self.edition_mode == BoxChartAnnotator.ModeDataSelect:
            # remove any canvas objects and lock the canvas
            self.canvas_display.clear()
            self.canvas_display.locked = True

            # copy temporal information ... overwrite previous
            self.data.boxes = self.tempo_box_values
            self.data_changed = True
            # return ...
            self.set_editor_mode(BoxChartAnnotator.ModeDataEdit)
            self.update_current_view()

        else:
            raise Exception("Not Implemented")

    def btn_edit_number_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeNumberEdit)
        self.update_current_view()

    def btn_edit_order_click(self, button):
        self.tempo_ordering = SeriesSorting.Copy(self.data.box_sorting)
        self.update_ordering_list()
        self.set_editor_mode(BoxChartAnnotator.ModeOrderEdit)
        self.update_current_view()

    def btn_edit_grouping_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeGroupingEdit)
        self.update_grouping()

    def update_tempo_box_params_labels(self):
        self.lbl_parameters_offset.set_text("Offset: {0:.1f}".format(self.tempo_decimal_offset / 10.0))
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))

    def get_slider_positions_from_box_params(self):
        box_offset = self.tempo_decimal_offset / 10
        box_width = self.tempo_decimal_width / 10
        box_inner_dist = self.tempo_decimal_inner_dist / 10
        box_outer_dist = self.tempo_decimal_outer_dist / 10

        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        if self.data.box_vertical:
            # assume left to right
            box_start = x1 + box_offset
        else:
            # assume top to bottom
            box_start = y1 + box_offset

        if self.data.box_grouping == BoxData.GroupingByCategory:
            # boxes are grouped by categorical value ...
            n_groups = len(self.data.categories)
            n_boxes_per_group = len(self.data.box_sorting.order)
        else:
            # boxes are grouped by stacks of data series
            n_groups = len(self.data.box_sorting.order)
            n_boxes_per_group = len(self.data.categories)

        group_size = box_width * n_boxes_per_group + box_inner_dist * (n_boxes_per_group - 1)

        first_group_end = box_start + group_size
        last_group_end = box_start + group_size * n_groups + box_outer_dist * (n_groups - 1)

        slider_positions = [box_start, box_start + box_width, first_group_end, last_group_end]

        return slider_positions

    def update_slider_from_box_params(self, add=False):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        if self.data.box_vertical:
            # position at middle left
            slide_p_y = (y1 + y2) / 2
            slide_p_x = x1
            base_length = (x2 - x1) * self.view_scale
        else:
            # position at top middle
            slide_p_y = y1
            slide_p_x = (x1 + x2) / 2
            base_length = (y2 - y1) * self.view_scale
        slide_p = slide_p_x * self.view_scale, slide_p_y * self.view_scale
        slider_length = 100
        slider_positions = [val * self.view_scale for val in self.get_slider_positions_from_box_params()]

        if add:
            # add new slider controller ...
            self.canvas_display.add_slider_element("box_params", slide_p, not self.data.box_vertical, base_length,
                                                   slider_length, slider_positions, (164, 192,0), (92, 128,0))
            self.canvas_display.elements["box_params"].visible = True
        else:
            # update slider controller ...
            self.canvas_display.update_slider_element("box_params", slide_p, not self.data.box_vertical, base_length,
                                                      slider_length, slider_positions, True)

    def update_box_params_from_slider(self):
        # get slider positions (on screen space)
        raw_positions = self.canvas_display.elements["box_params"].get_slider_positions()
        # convert from screen space to image space ...
        img_positions = [val / self.view_scale for val in raw_positions]
        # split ...
        first_box_start, first_box_end, first_group_end, last_group_end = img_positions

        # get the four parameters ...
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        if self.data.box_vertical:
            # assume left to right
            box_offset = first_box_start - x1
        else:
            # assume top to bottom
            box_offset = first_box_start - y1

        if self.data.box_grouping == BoxData.GroupingByCategory:
            # boxes are grouped by categorical value ...
            n_groups = len(self.data.categories)
            n_boxes_per_group = len(self.data.box_sorting.order)
        else:
            # boxes are grouped by stacks of data series
            n_groups = len(self.data.box_sorting.order)
            n_boxes_per_group = len(self.data.categories)

        # compute the width (easy)
        box_width = first_box_end - first_box_start

        # compute the space between boxes of the same group
        # (given width, num of boxes per group and ending of the first group)
        group_size = first_group_end - first_box_start
        if n_boxes_per_group > 1:
            box_inner_dist = (group_size - box_width * n_boxes_per_group) / (n_boxes_per_group - 1)
        else:
            box_inner_dist = 0

        # compute the space between groups
        # (given the group size, number of groups and ending of last group)
        all_boxes_size = last_group_end - first_box_start
        if n_groups > 1:
            box_outer_dist = (all_boxes_size - group_size * n_groups) / (n_groups - 1)
        else:
            box_outer_dist = 0

        self.tempo_decimal_offset = int(round(box_offset * 10))
        self.tempo_decimal_width = int(round(box_width * 10))
        self.tempo_decimal_inner_dist = int(round(box_inner_dist * 10))
        self.tempo_decimal_outer_dist = int(round(box_outer_dist * 10))
        self.data_changed = True

        self.update_tempo_box_params_labels()

    def btn_edit_parameters_click(self, button):
        self.tempo_decimal_offset = int(round(self.data.box_offset * 10))
        self.tempo_decimal_width = int(round(self.data.box_width * 10))
        self.tempo_decimal_inner_dist = int(round(self.data.box_inner_dist * 10))
        self.tempo_decimal_outer_dist = int(round(self.data.box_outer_dist * 10))

        self.update_tempo_box_params_labels()

        # convert the parameters of the bar into slider positions ...
        # and show the slider in the canvas
        self.update_slider_from_box_params(True)
        # allow edition ...
        self.canvas_display.locked = False

        self.set_editor_mode(BoxChartAnnotator.ModeParameterEdit)
        self.update_current_view()

    def btn_edit_data_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeDataEdit)
        self.update_current_view()

    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing Box data ...
            self.panel_info.data = BoxData.Copy(self.data)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(BoxChartAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_annotation_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeNavigate)

        # edit modes ...
        self.container_number_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeNumberEdit)
        self.container_order_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeOrderEdit)
        self.container_grouping_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeGroupingEdit)
        self.container_parameters_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeParameterEdit)
        self.container_data_buttons.visible = (self.edition_mode == BoxChartAnnotator.ModeDataEdit)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [BoxChartAnnotator.ModeConfirmNumberOverwrite,
                                                                       BoxChartAnnotator.ModeDataSelect,
                                                                       BoxChartAnnotator.ModeConfirmExit]

        if self.edition_mode == BoxChartAnnotator.ModeConfirmNumberOverwrite:
            self.lbl_confirm_message.set_text("Discard Existing Box Data?")
        elif self.edition_mode == BoxChartAnnotator.ModeDataSelect:
            if self.tempo_data_editing == BoxChartAnnotator.DataBoxMaximum:
                self.lbl_confirm_message.set_text("Click on Box Maximums")
            elif self.tempo_data_editing == BoxChartAnnotator.DataBoxMedian:
                self.lbl_confirm_message.set_text("Click on Box Medians")
            elif self.tempo_data_editing == BoxChartAnnotator.DataBoxMinimum:
                self.lbl_confirm_message.set_text("Click on Box Minimums")
            elif self.tempo_data_editing == BoxChartAnnotator.DataWhiskerMinimum:
                self.lbl_confirm_message.set_text("Click on Whiskers Minimums")
            elif self.tempo_data_editing == BoxChartAnnotator.DataWhiskerMaximum:
                self.lbl_confirm_message.set_text("Click on Whiskers Maximums")
            elif self.tempo_data_editing == BoxChartAnnotator.DataBoxSliders:
                self.lbl_confirm_message.set_text("Drag Box Elements")
            else:
                raise Exception("Invalid Data Edition Element Selected")

        elif self.edition_mode == BoxChartAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Box Data?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        # self.btn_confirm_accept.visible = self.edition_mode not in [BarChartAnnotator.ModeDataSelect]

    def img_main_mouse_button_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode == BoxChartAnnotator.ModeDataSelect:
                if self.tempo_data_editing == BoxChartAnnotator.DataBoxSliders:
                    # ignore clicks in this mode ....
                    return

                # click pos ...
                click_x, click_y = pos
                click_x /= self.view_scale
                click_y /= self.view_scale

                x1, y1, x2, y2 = self.panel_info.axes.bounding_box
                x1 = int(x1)
                # y1 = int(y1)
                # x2 = int(x2)
                y2 = int(y2)

                if self.data.box_vertical:
                    click_range = click_x
                    click_length = click_y
                    # assume they start at the bottom
                    box_baseline = y2
                else:
                    click_range = click_y
                    click_length = click_x
                    # assume they start at the left
                    box_baseline = x1

                for box_idx, polygon in enumerate(self.tempo_box_polygons):
                    # get box meta-data
                    series_idx, cat_idx = self.tempo_box_polygon_index[box_idx]

                    if self.data.box_vertical:
                        # Min and max on Dim 0 (X Coord)
                        box_start = polygon[:, 0].min()
                        box_end = polygon[:, 0].max()
                    else:
                        # Min and max on Dim 1 (Y Coord)
                        box_start = polygon[:, 1].min()
                        box_end = polygon[:, 1].max()

                    if box_start <= click_range <= box_end:
                        if self.data.box_vertical:
                            click_value = box_baseline - click_length
                        else:
                            click_value = click_length - box_baseline

                        # update box value ...
                        box = self.tempo_box_values[series_idx][cat_idx]
                        if self.tempo_data_editing == BoxChartAnnotator.DataWhiskerMaximum:
                            box.set_whisker_max(click_value)
                        elif self.tempo_data_editing == BoxChartAnnotator.DataBoxMaximum:
                            box.set_box_max(click_value)
                        elif self.tempo_data_editing == BoxChartAnnotator.DataBoxMedian:
                            box.set_box_median(click_value)
                        elif self.tempo_data_editing == BoxChartAnnotator.DataBoxMinimum:
                            box.set_box_min(click_value)
                        elif self.tempo_data_editing == BoxChartAnnotator.DataWhiskerMinimum:
                            box.set_whisker_min(click_value)

                        self.update_current_view()
                        break

    def prepare_number_controls(self):
        n_boxes = self.data.total_boxes()
        self.lbl_number_title.set_text("Boxes in Chart: {0:d}".format(n_boxes))

        self.fill_categories_list()
        self.fill_data_series_list()

    def fill_categories_list(self):
        for idx, current_text in enumerate(self.data.categories):
            if current_text is None:
                display_value = str(idx + 1)
            else:
                display_value = "{0:d}: {1:s}".format(idx + 1, current_text.value)

            self.lbx_number_categories_values.add_option(str(idx), display_value)

    def fill_data_series_list(self):
        for idx, current_text in enumerate(self.data.data_series):
            if current_text is None:
                display_value = str(idx + 1)
            else:
                display_value = "{0:d}: {1:s}".format(idx + 1, current_text.value)

            self.lbx_number_series_values.add_option(str(idx), display_value)

    def btn_number_categories_add_click(self, button):
        # add ... using general default values (based on axis info)
        def_box_min, def_box_median, def_box_max, def_whiskers_min, def_whiskers_max = self.get_default_box_values()

        self.data.add_category(default_box_min=def_box_min, default_box_median=def_box_median,
                               default_box_max=def_box_max, default_whisker_min=def_whiskers_min,
                               default_whisker_max=def_whiskers_max)

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(True, False)

    def btn_number_categories_remove_click(self, button):
        if self.lbx_number_categories_values.selected_option_value is None:
            print("Must select a category")
            return

        option_idx = int(self.lbx_number_categories_values.selected_option_value)

        # remove ...
        self.data.remove_category(option_idx)

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(True, False)

    def btn_number_series_add_click(self, button):
        # add ... using general default values (based on axis info)
        def_box_min, def_box_median, def_box_max, def_whiskers_min, def_whiskers_max = self.get_default_box_values()
        self.data.add_data_series(default_box_min=def_box_min, default_box_median=def_box_median,
                                  default_box_max=def_box_max, default_whisker_min=def_whiskers_min,
                                  default_whisker_max=def_whiskers_max)

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(False, True)

    def btn_number_series_remove_click(self, button):
        if self.lbx_number_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        option_idx = int(self.lbx_number_series_values.selected_option_value)

        # remove ...
        self.data.remove_data_series(option_idx)

        self.data_changed = True

        # update GUI
        self.numbers_update_GUI(False, True)

    def get_default_box_values(self):
        a_x1, a_y1, a_x2, a_y2 = self.panel_info.axes.bounding_box
        a_x1 = int(a_x1)
        a_y1 = int(a_y1)
        a_x2 = int(a_x2)
        a_y2 = int(a_y2)

        if self.data.box_vertical:
            # vertical boxes... X axis has the data series ...
            axis_range = a_y2 - a_y1
        else:
            # horizontal boxes ... Y axis has the data series ...
            axis_range = a_x2 - a_x1

        default_whiskers_min = int(axis_range * (1 / 6))
        default_box_min = int(axis_range * (2 / 6))
        default_box_median = int(axis_range * (3 / 6))
        default_box_max = int(axis_range * (4 / 6))
        default_whiskers_max = int(axis_range * (5 / 6))

        return default_box_min, default_box_median, default_box_max, default_whiskers_min, default_whiskers_max

    def numbers_update_GUI(self, categories_changed, data_series_changed):
        n_boxes = self.data.total_boxes()
        self.lbl_number_title.set_text("Boxes in Chart: {0:d}".format(n_boxes))

        if categories_changed:
            self.lbx_number_categories_values.clear_options()
            self.fill_categories_list()

        if data_series_changed:
            self.lbx_number_series_values.clear_options()
            self.fill_data_series_list()

        self.update_current_view()

    def btn_number_return_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def update_ordering_list(self):
        self.lbx_order_list.clear_options()

        for group_idx, group in enumerate(self.tempo_ordering.order):
            # self.lbx_order_list.add_option("g-{0:d}".format(group_idx), "Box Stack #{0:d}".format(group_idx + 1))

            for series_idx in group:
                if self.data.data_series[series_idx] is None:
                    display = "[Unnamed]"
                else:
                    display = self.data.data_series[series_idx].value

                # self.lbx_order_list.add_option("s-{0:d}".format(series_idx), "-> {0:s}".format(display))
                self.lbx_order_list.add_option("s-{0:d}".format(group_idx), "{0:s}".format(display))

    def btn_order_move_up_click(self, button):
        if self.lbx_order_list.selected_option_value is None:
            print("Must select a data series or box group")
            return

        value_type, value_idx = self.lbx_order_list.selected_option_value.split("-")
        value_idx = int(value_idx)

        # try moving group ...
        success = self.tempo_ordering.move_group_up(value_idx)

        if success:
            self.update_ordering_list()

            # select same element again
            new_key = "s-{0:d}".format(value_idx)
            self.lbx_order_list.change_option_selected(new_key)
        else:
            print("The selected element cannot move further up")

    def btn_order_move_down_click(self, button):
        if self.lbx_order_list.selected_option_value is None:
            print("Must select a data series or box group")
            return

        value_type, value_idx = self.lbx_order_list.selected_option_value.split("-")
        value_idx = int(value_idx)

        # try moving
        success = self.tempo_ordering.move_group_down(value_idx)

        if success:
            self.update_ordering_list()

            # select same element again
            new_key = "s-{0:d}".format(value_idx)
            self.lbx_order_list.change_option_selected(new_key)
        else:
            print("The selected element cannot move further down")

    def btn_order_return_accept_click(self, button):
        self.data.box_sorting = SeriesSorting.Copy(self.tempo_ordering)
        self.data_changed = True

        # return ...
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_order_return_cancel_click(self, button):
        # just return ...
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def update_grouping(self):
        if self.data.box_grouping == BoxData.GroupingByCategory:
            self.lbl_grouping_description.set_text("Group Boxes by Category")
        else:
            self.lbl_grouping_description.set_text("Group Boxes by Data Series")

        self.update_current_view()

    def btn_grouping_by_categories_click(self, button):
        self.data.box_grouping = BoxData.GroupingByCategory
        self.data_changed = True
        self.update_grouping()

    def btn_grouping_by_data_series_click(self, button):
        self.data.box_grouping = BoxData.GroupingByDataSeries
        self.data_changed = True
        self.update_grouping()

    def btn_grouping_return_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)

    def btns_parameters_move_offset_click(self, button):
        if self.tempo_decimal_offset + button.tag >= 0:
            self.tempo_decimal_offset += button.tag

        self.data_changed = True
        self.lbl_parameters_offset.set_text("Offset: {0:.1f}".format(self.tempo_decimal_offset / 10.0))
        self.update_slider_from_box_params(False)
        self.update_current_view()

    def btns_parameters_move_width_click(self, button):
        if self.tempo_decimal_width + button.tag >= 0:
            self.tempo_decimal_width += button.tag

        self.data_changed = True
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.update_slider_from_box_params(False)
        self.update_current_view()

    def btns_parameters_move_inner_dist_click(self, button):
        # this one allows negative values ...
        self.tempo_decimal_inner_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.update_slider_from_box_params(False)
        self.update_current_view()

    def btns_parameters_move_outer_dist_click(self, button):
        if self.tempo_decimal_outer_dist + button.tag >= 0:
            self.tempo_decimal_outer_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))
        self.update_slider_from_box_params(False)
        self.update_current_view()

    def btn_parameters_return_accept_click(self, button):
        self.data.box_offset = self.tempo_decimal_offset / 10
        self.data.box_width = self.tempo_decimal_width / 10
        self.data.box_inner_dist = self.tempo_decimal_inner_dist / 10
        self.data.box_outer_dist = self.tempo_decimal_outer_dist / 10

        # remove box_params slider
        self.canvas_display.clear()
        self.canvas_display.locked = True

        # return
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_parameters_return_cancel_click(self, button):
        # remove box_params slider
        self.canvas_display.clear()
        self.canvas_display.locked = True

        # just return ...
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def prepare_sliders_for_boxes(self):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        for box_idx, polygon in enumerate(self.tempo_box_polygons):
            # get box and it's meta-data
            series_idx, cat_idx = self.tempo_box_polygon_index[box_idx]
            box = self.tempo_box_values[series_idx][cat_idx]

            if self.data.box_vertical:
                # Min and max on Dim 0 (X Coord)
                box_start = polygon[:, 0].min()
                box_end = polygon[:, 0].max()

                # vertical boxes ... create from top to bottom
                slide_p_x = (box_start + box_end) / 2.0
                slide_p_y = y1
                base_length = (y2 - y1) * self.view_scale

                # the raw values assume that they start at the bottom
                # but the slider starts from the top ... invert the order of the box elements
                # whisker top, box max, box med, box min, whisker bottom
                pos_1 = y2 - box.whiskers_max
                pos_2 = y2 - box.box_max
                pos_3 = y2 - box.box_median
                pos_4 = y2 - box.box_min
                pos_5 = y2 - box.whiskers_min
            else:
                # Min and max on Dim 1 (Y Coord)
                box_start = polygon[:, 1].min()
                box_end = polygon[:, 1].max()

                # horizontal boxes ... create from left to right
                slide_p_x = x1
                slide_p_y = (box_start + box_end) / 2.0
                base_length = (x2 - x1) * self.view_scale

                # assume they start at the left
                box_baseline = x1
                # use the original order of elements
                # whisker min, box min, box median, box max, whisker top
                pos_1 = x1 + box.whiskers_min
                pos_2 = x1 + box.box_min
                pos_3 = x1 + box.box_median
                pos_4 = x1 + box.box_max
                pos_5 = x1 + box.whiskers_max

            slide_p = slide_p_x * self.view_scale, slide_p_y * self.view_scale
            slider_length = (box_end - box_start) * self.view_scale

            slider_positions = [val * self.view_scale for val in [pos_1, pos_2, pos_3, pos_4, pos_5]]

            slider_name = "box_data_{0:d}_{1:d}".format(series_idx, cat_idx)
            self.canvas_display.add_slider_element(slider_name, slide_p, self.data.box_vertical, base_length,
                                               slider_length, slider_positions, (0, 255, 255), (0, 192, 192))
            self.canvas_display.elements[slider_name].visible = True

    def btn_data_boxes_sliders_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()

        # add sliders for all boxes ...
        self.prepare_sliders_for_boxes()
        self.canvas_display.locked = False

        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataBoxSliders
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_whisker_maximum_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()
        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataWhiskerMaximum
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_whisker_minimum_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()
        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataWhiskerMinimum
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_box_minimum_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()
        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataBoxMinimum
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_box_median_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()
        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataBoxMedian
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_box_maximum_click(self, button):
        # copy box data to temporal ...
        self.tempo_box_values = self.data.get_boxes()
        # set edit mode ....
        self.tempo_data_editing = BoxChartAnnotator.DataBoxMaximum
        self.set_editor_mode(BoxChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def btn_data_return_click(self, button):
        self.set_editor_mode(BoxChartAnnotator.ModeNavigate)
        self.update_current_view()

    def canvas_display_object_edited(self, canvas, element_name):
        if element_name == "box_params":
            self.update_box_params_from_slider()
            self.update_current_view()
        elif element_name[:8] == "box_data":
            _, _, series_idx, cat_idx = element_name.split("_")
            series_idx = int(series_idx)
            cat_idx = int(cat_idx)

            box = self.tempo_box_values[series_idx][cat_idx]

            # get raw values ... on screen space
            raw_values = self.canvas_display.elements[element_name].get_slider_positions()
            # convert to image space ...
            img_values = [(val / self.view_scale) for val in raw_values]

            x1, y1, x2, y2 = self.panel_info.axes.bounding_box
            if self.data.box_vertical:
                # slider starts from top to bottom ... and box elements are inverted ...
                # whisker top, box max, box med, box min, whisker bottom
                box.set_whisker_max(y2 - img_values[0])
                box.set_box_max(y2 - img_values[1])
                box.set_box_median(y2 - img_values[2])
                box.set_box_min(y2 - img_values[3])
                box.set_whisker_min(y2 - img_values[4])
            else:
                # assume they start at the left
                # use the original order of elements
                # whisker min, box min, box median, box max, whisker top
                box.set_whisker_min(img_values[0] - x1)
                box.set_box_min(img_values[1] - x1)
                box.set_box_median(img_values[2] - x1)
                box.set_box_max(img_values[3] - x1)
                box.set_whisker_max(img_values[4] - x1)

            self.update_current_view()
