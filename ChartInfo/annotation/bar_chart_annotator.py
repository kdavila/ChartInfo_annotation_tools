
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

from ChartInfo.data.bar_data import BarData
from ChartInfo.data.series_sorting import SeriesSorting

class BarChartAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeOrderEdit = 2
    ModeGroupingEdit = 3
    ModeParameterEdit = 4
    ModeDataEdit = 5
    ModeDataSelect = 6
    ModeConfirmNumberOverwrite = 7
    ModeConfirmExit = 8

    AutoBarProfile = 0
    AutoBarColorVariance = 1
    AutoBarLegendColorAlignment = 2

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Bar Chart Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.data is None:
            # create default bar chart data ...
            self.data = BarData.CreateDefault(self.panel_info)
            self.data_changed = True
        else:
            # make a copy ...
            self.data = BarData.Copy(self.panel_info.data)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (230, 120, 80)
        self.text_color = (255, 255, 255)

        self.elements.back_color = self.general_background
        self.edition_mode = None

        self.auto_bar_adjust_mode = BarChartAnnotator.AutoBarLegendColorAlignment

        self.tempo_ordering = None

        self.tempo_decimal_offset = None
        self.tempo_decimal_width = None
        self.tempo_decimal_inner_dist = None
        self.tempo_decimal_outer_dist = None

        self.tempo_data_layer = None

        self.tempo_bar_lengths = None
        self.tempo_bar_polygons = None
        self.tempo_red_lines = None
        self.tempo_green_lines = None
        self.tempo_bar_polygon_index = None

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
        self.lbl_data_layer_title = None
        self.btn_data_layer_prev = None
        self.btn_data_layer_next = None
        self.lbx_data_layer_elements = None
        self.btn_data_manual = None
        self.btn_data_auto = None
        self.btn_data_return = None

        self.create_controllers()

        # get the view ...
        self.update_current_view(True)


    def create_controllers(self):
        # add elements....
        button_text_color = (35, 50, 20)
        button_back_color = (228, 228, 228)

        # Main Title
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Bar Chart Data Annotation", 28)
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
        darker_background = (153, 80, 53)

        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 380),
                                                            back_color=darker_background)
        self.container_annotation_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Bar Chart Annotation Options", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        self.btn_edit_number = ScreenButton("btn_edit_number", "Edit Number of Bars", 21, button_width)
        self.btn_edit_number.set_colors(button_text_color, button_back_color)
        self.btn_edit_number.position = (button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_number.click_callback = self.btn_edit_number_click
        self.container_annotation_buttons.append(self.btn_edit_number)

        self.btn_edit_order = ScreenButton("btn_edit_order", "Edit Order / Stacking", 21, button_width)
        self.btn_edit_order.set_colors(button_text_color, button_back_color)
        self.btn_edit_order.position = (button_left, self.btn_edit_number.get_bottom() + 10)
        self.btn_edit_order.click_callback = self.btn_edit_order_click
        self.container_annotation_buttons.append(self.btn_edit_order)

        self.btn_edit_grouping = ScreenButton("btn_edit_grouping", "Edit Bar Grouping", 21, button_width)
        self.btn_edit_grouping.set_colors(button_text_color, button_back_color)
        self.btn_edit_grouping.position = (button_left, self.btn_edit_order.get_bottom() + 10)
        self.btn_edit_grouping.click_callback = self.btn_edit_grouping_click
        self.container_annotation_buttons.append(self.btn_edit_grouping)

        self.btn_edit_parameters = ScreenButton("btn_edit_parameters", "Edit Bar Parameters", 21, button_width)
        self.btn_edit_parameters.set_colors(button_text_color, button_back_color)
        self.btn_edit_parameters.position = (button_left, self.btn_edit_grouping.get_bottom() + 10)
        self.btn_edit_parameters.click_callback = self.btn_edit_parameters_click
        self.container_annotation_buttons.append(self.btn_edit_parameters)

        self.btn_edit_data = ScreenButton("btn_edit_data", "Edit Bar Data", 21, button_width)
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
        # - options to define the total number of bars in the chart ....
        self.container_number_buttons = ScreenContainer("container_number_buttons", (container_width, 530),
                                                            back_color=darker_background)
        self.container_number_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_number_buttons)

        self.lbl_number_title = ScreenLabel("lbl_number_title ", "Bars in Chart: [0]", 25, 290, 1)
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
        # container with options to change bar ordering and define bar stacking ...
        self.container_order_buttons = ScreenContainer("container_order_buttons", (container_width, 500),
                                                       back_color=darker_background)
        self.container_order_buttons.position = (self.container_view_buttons.get_left(),
                                                 self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_order_buttons)

        self.lbl_order_title = ScreenLabel("lbl_order_title", "Bar Ordering and Stacking", 21, 290, 1)
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
        # container with options to change bar grouping type ....

        self.container_grouping_buttons = ScreenContainer("container_grouping_buttons", (container_width, 230),
                                                            back_color=darker_background)
        self.container_grouping_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_grouping_buttons)

        self.lbl_grouping_title = ScreenLabel("lbl_grouping_title", "Bar Grouping Options", 21, 290, 1)
        self.lbl_grouping_title.position = (5, 5)
        self.lbl_grouping_title.set_background(darker_background)
        self.lbl_grouping_title.set_color(self.text_color)
        self.container_grouping_buttons.append(self.lbl_grouping_title)

        self.lbl_grouping_description = ScreenLabel("lbl_grouping_description", "Group Bars by ??", 21, 290, 1)
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
        # container with options to change bar parameters ....
        self.container_parameters_buttons = ScreenContainer("container_parameters_buttons", (container_width, 430),
                                                            back_color=darker_background)
        self.container_parameters_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 15)
        self.elements.append(self.container_parameters_buttons)

        self.lbl_parameters_title = ScreenLabel("lbl_parameters_title", "Bar Parameters", 21, 290, 1)
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

        self.lbl_data_title = ScreenLabel("lbl_data_title", "Bar Data", 21, 290, 1)
        self.lbl_data_title.position = (5, 5)
        self.lbl_data_title.set_background(darker_background)
        self.lbl_data_title.set_color(self.text_color)
        self.container_data_buttons.append(self.lbl_data_title)

        self.lbl_data_layer_title = ScreenLabel("lbl_data_layer_title", "Bar Stack Layer: ??? of ???", 21, 290, 1)
        self.lbl_data_layer_title.position = (5, self.lbl_data_title.get_bottom() + 20)
        self.lbl_data_layer_title.set_background(darker_background)
        self.lbl_data_layer_title.set_color(self.text_color)
        self.container_data_buttons.append(self.lbl_data_layer_title)

        self.btn_data_layer_prev = ScreenButton("btn_data_layer_prev", "Previous", 21, button_2_width)
        self.btn_data_layer_prev.set_colors(button_text_color, button_back_color)
        self.btn_data_layer_prev.position = (button_2_left, self.lbl_data_layer_title.get_bottom() + 10)
        self.btn_data_layer_prev.click_callback = self.btn_data_layer_prev_click
        self.container_data_buttons.append(self.btn_data_layer_prev)

        self.btn_data_layer_next = ScreenButton("btn_data_layer_next", "Next", 21, button_2_width)
        self.btn_data_layer_next.set_colors(button_text_color, button_back_color)
        self.btn_data_layer_next.position = (button_2_right, self.lbl_data_layer_title.get_bottom() + 10)
        self.btn_data_layer_next.click_callback = self.btn_data_layer_next_click
        self.container_data_buttons.append(self.btn_data_layer_next)

        self.lbx_data_layer_elements = ScreenTextlist("lbx_data_layer_elements", (container_width - 20, 140),
                                                       18, back_color=(255,255,255), option_color=(0, 0, 0),
                                                       selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_data_layer_elements.position = (10, self.btn_data_layer_prev.get_bottom() + 10)
        self.container_data_buttons.append(self.lbx_data_layer_elements)

        self.btn_data_manual = ScreenButton("btn_data_manual", "Manual Bar Adjustment", 21, button_2_width)
        self.btn_data_manual.set_colors(button_text_color, button_back_color)
        self.btn_data_manual.position = (button_2_left, self.lbx_data_layer_elements.get_bottom() + 20)
        self.btn_data_manual.click_callback = self.btn_data_manual_click
        self.container_data_buttons.append(self.btn_data_manual)

        self.btn_data_auto = ScreenButton("btn_data_auto", "Auto Bar Adjustment", 21, button_2_width)
        self.btn_data_auto.set_colors(button_text_color, button_back_color)
        self.btn_data_auto.position = (button_2_right, self.lbx_data_layer_elements.get_bottom() + 20)
        self.btn_data_auto.click_callback = self.btn_data_auto_click
        self.container_data_buttons.append(self.btn_data_auto)

        self.btn_data_return = ScreenButton("btn_data_return", "Return", 21, button_width)
        self.btn_data_return.set_colors(button_text_color, button_back_color)
        self.btn_data_return.position = (button_left, self.btn_data_manual.get_bottom() + 30)
        self.btn_data_return.click_callback = self.btn_data_return_click
        self.container_data_buttons.append(self.btn_data_return)
        self.container_data_buttons.visible = True


        # ======================================
        # visuals
        # ===========================

        # ... image objects ...
        self.canvas_display.add_slider_element("bar_params", (0, 0), not self.data.bar_vertical, 100, 50, [0],
                                               (164, 192,0), (92, 128,0))
        self.canvas_display.elements["bar_params"].visible = False

        self.prepare_number_controls()

        self.set_editor_mode(BarChartAnnotator.ModeNavigate)


    def prepare_number_controls(self):
        n_bars = self.data.total_bars()
        self.lbl_number_title.set_text("Bars in Chart: {0:d}".format(n_bars))

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

    def compute_bar_polygons(self):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # Bars
        if self.edition_mode == BarChartAnnotator.ModeParameterEdit:
            bar_offset = self.tempo_decimal_offset / 10
            bar_width = self.tempo_decimal_width / 10
            bar_inner_dist = self.tempo_decimal_inner_dist / 10
            bar_outer_dist = self.tempo_decimal_outer_dist / 10
        else:
            bar_offset = self.data.bar_offset
            bar_width = self.data.bar_width
            bar_inner_dist = self.data.bar_inner_dist
            bar_outer_dist = self.data.bar_outer_dist

        if self.edition_mode == BarChartAnnotator.ModeDataSelect:
            bar_lengths = self.tempo_bar_lengths
        else:
            bar_lengths = self.data.bar_lengths

        if self.data.bar_vertical:
            # assume left to right
            bar_start = x1 + bar_offset
            # assume they start at the bottom
            bar_baseline = y2
        else:
            # assume top to bottom
            bar_start = y1 + bar_offset
            # assume they start at the left
            bar_baseline = x1

        current_lines = []
        self.tempo_red_lines = []
        self.tempo_green_lines = []
        self.tempo_bar_polygon_index = []

        if self.data.bar_grouping == BarData.GroupingByCategory:
            # bar are grouped by categorical value ...
            for cat_idx, category in enumerate(self.data.categories):
                for group_idx, group in enumerate(self.data.bar_sorting.order):
                    bar_end = bar_start + bar_width

                    # add stacked bars ...
                    polygons, polygon_index = BarData.get_stacked_bar_lines(self.data.bar_vertical, cat_idx, group,
                                                                            bar_lengths, bar_baseline, bar_start,
                                                                            bar_end)

                    # For drawing ...
                    if self.edition_mode in [BarChartAnnotator.ModeDataEdit, BarChartAnnotator.ModeDataSelect]:
                        self.tempo_green_lines += [polygons[self.tempo_data_layer]]
                        self.tempo_red_lines += polygons[:self.tempo_data_layer]
                        self.tempo_red_lines += polygons[self.tempo_data_layer + 1:]
                    else:
                        self.tempo_red_lines += polygons

                    # for mapping clicks ...
                    current_lines += polygons
                    self.tempo_bar_polygon_index += polygon_index

                    # move to end of the bar ... (+ width)
                    bar_start += bar_width
                    # check if move to the next stack of bars on same grouping
                    if group_idx + 1 < len(self.data.bar_sorting.order):
                        # + distance between contiguous bars
                        bar_start += bar_inner_dist

                # next group of bars ...
                bar_start += bar_outer_dist
        else:
            # bar are grouped by data series
            for group_idx, group in enumerate(self.data.bar_sorting.order):
                for cat_idx, category in enumerate(self.data.categories):
                    bar_end = bar_start + bar_width

                    # draw stacked bars ...
                    polygons, polygon_index = self.get_stacked_bar_lines(cat_idx, group, bar_lengths, bar_baseline,
                                                                         bar_start, bar_end)

                    # for drawing ...
                    if self.edition_mode in [BarChartAnnotator.ModeDataEdit, BarChartAnnotator.ModeDataSelect]:
                        self.tempo_green_lines += [polygons[self.tempo_data_layer]]
                        self.tempo_red_lines += polygons[:self.tempo_data_layer]
                        self.tempo_red_lines += polygons[self.tempo_data_layer + 1:]
                    else:
                        self.tempo_red_lines += polygons

                    # for click processing ...
                    current_lines += polygons
                    self.tempo_bar_polygon_index += polygon_index

                    # move to the end of the bar
                    bar_start += bar_width
                    # check if move to the next stack of bars on same grouping
                    if cat_idx + 1 < len(self.data.categories):
                        bar_start += bar_inner_dist

                # next group of bars ...
                bar_start += bar_outer_dist

        current_lines = np.array(current_lines).round().astype(np.int32)
        self.tempo_bar_polygons = current_lines

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

        # modified_image = cv2.polylines(modified_image, current_lines, False, (255, 0, 0))
        if len(self.tempo_red_lines) > 0:
            red_lines = np.array(self.tempo_red_lines).round().astype(np.int32)
            modified_image = cv2.polylines(modified_image, red_lines, False, (255, 0, 0))
        if len(self.tempo_green_lines) > 0:
            green_lines = np.array(self.tempo_green_lines).round().astype(np.int32)
            modified_image = cv2.polylines(modified_image, green_lines, False, (0, 255, 0))

    def update_current_view(self, resized=False):
        # update the bar polygons ...
        self.compute_bar_polygons()
        # call parent update view ...
        BaseImageAnnotator.update_current_view(self, resized)

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_annotation_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeNavigate)

        # edit modes ...
        self.container_number_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeNumberEdit)
        self.container_order_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeOrderEdit)
        self.container_grouping_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeGroupingEdit)
        self.container_parameters_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeParameterEdit)
        self.container_data_buttons.visible = (self.edition_mode == BarChartAnnotator.ModeDataEdit)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [BarChartAnnotator.ModeConfirmNumberOverwrite,
                                                                       BarChartAnnotator.ModeDataSelect,
                                                                       BarChartAnnotator.ModeConfirmExit]

        if self.edition_mode == BarChartAnnotator.ModeConfirmNumberOverwrite:
            self.lbl_confirm_message.set_text("Discard Existing Bar Data?")
        elif self.edition_mode == BarChartAnnotator.ModeDataSelect:
            self.lbl_confirm_message.set_text("Click on Bar Lengths")
        elif self.edition_mode == BarChartAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Bar Data?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        # self.btn_confirm_accept.visible = self.edition_mode not in [BarChartAnnotator.ModeDataSelect]

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [BarChartAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(BarChartAnnotator.ModeNavigate)

        elif self.edition_mode == BarChartAnnotator.ModeDataSelect:
            # back to regular data edit ...
            self.set_editor_mode(BarChartAnnotator.ModeDataEdit)

        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == BarChartAnnotator.ModeConfirmExit:
            print("-> Changes made to Bar Data Annotations were lost")
            self.return_screen = self.parent_screen

        elif self.edition_mode == BarChartAnnotator.ModeDataSelect:
            # copy temporal information ... overwrite previous
            self.data.bar_lengths = self.tempo_bar_lengths
            self.data_changed = True
            # return ...
            self.set_editor_mode(BarChartAnnotator.ModeDataEdit)

        else:
            raise Exception("Not Implemented")

    def img_main_mouse_button_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode == BarChartAnnotator.ModeDataSelect:
                # click pos ...
                click_x, click_y = pos
                click_x /= self.view_scale
                click_y /= self.view_scale

                # TODO: this could be faster if tempo_bar_polygons is indexed by stack_idx
                for bar_idx, polygon in enumerate(self.tempo_bar_polygons):
                    # get bar meta-data
                    series_idx, cat_idx, stack_idx, bar_baseline = self.tempo_bar_polygon_index[bar_idx]

                    # check if belongs to current layer ...
                    if stack_idx != self.tempo_data_layer:
                        # ignore this bar
                        continue

                    if self.data.bar_vertical:
                        bar_start = polygon[:, 0].min()
                        bar_end = polygon[:, 0].max()
                        click_range = click_x
                        click_length = click_y
                    else:
                        bar_start = polygon[:, 1].min()
                        bar_end = polygon[:, 1].max()
                        click_range = click_y
                        click_length = click_x

                    if bar_start <= click_range <= bar_end:
                        if self.data.bar_vertical:
                            bar_length = bar_baseline - click_length
                        else:
                            bar_length = click_length - bar_baseline

                        # update bar value ...
                        self.tempo_bar_lengths[series_idx][cat_idx] = bar_length
                        self.update_current_view()
                        break

                # print(self.tempo_bar_polygons)

    def btn_edit_number_click(self, button):
        self.set_editor_mode(BarChartAnnotator.ModeNumberEdit)
        self.update_current_view()

    def get_slider_positions_from_bar_params(self):
        bar_offset = self.tempo_decimal_offset / 10
        bar_width = self.tempo_decimal_width / 10
        bar_inner_dist = self.tempo_decimal_inner_dist / 10
        bar_outer_dist = self.tempo_decimal_outer_dist / 10

        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        if self.data.bar_vertical:
            # assume left to right
            bar_start = x1 + bar_offset
        else:
            # assume top to bottom
            bar_start = y1 + bar_offset

        if self.data.bar_grouping == BarData.GroupingByCategory:
            # bar are grouped by categorical value ...
            n_groups = len(self.data.categories)
            n_bars_per_group = len(self.data.bar_sorting.order)
        else:
            # bar are grouped by stacks of data series
            n_groups = len(self.data.bar_sorting.order)
            n_bars_per_group = len(self.data.categories)

        group_size = bar_width * n_bars_per_group + bar_inner_dist * (n_bars_per_group - 1)

        first_group_end = bar_start + group_size
        last_group_end = bar_start + group_size * n_groups + bar_outer_dist * (n_groups - 1)

        slider_positions = [bar_start, bar_start + bar_width, first_group_end, last_group_end]

        return slider_positions

    def update_slider_from_bar_params(self):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        if self.data.bar_vertical:
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
        slider_positions = [val * self.view_scale for val in self.get_slider_positions_from_bar_params()]

        self.canvas_display.update_slider_element("bar_params", slide_p, not self.data.bar_vertical, base_length,
                                                  slider_length, slider_positions, True)

    def update_bar_params_from_slider(self):
        # get slider positions (on screen space)
        raw_positions = self.canvas_display.elements["bar_params"].get_slider_positions()
        # convert from screen space to image space ...
        img_positions = [val / self.view_scale for val in raw_positions]
        # split ...
        first_bar_start, first_bar_end, first_group_end, last_group_end = img_positions

        # get the four parameters ...
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        if self.data.bar_vertical:
            # assume left to right
            bar_offset = first_bar_start - x1
        else:
            # assume top to bottom
            bar_offset = first_bar_start - y1

        if self.data.bar_grouping == BarData.GroupingByCategory:
            # bar are grouped by categorical value ...
            n_groups = len(self.data.categories)
            n_bars_per_group = len(self.data.bar_sorting.order)
        else:
            # bar are grouped by stacks of data series
            n_groups = len(self.data.bar_sorting.order)
            n_bars_per_group = len(self.data.categories)

        # compute the width (easy)
        bar_width = first_bar_end - first_bar_start

        # compute the space between bars of the same group
        # (given width, num of bars per group and ending of the first group)
        group_size = first_group_end - first_bar_start
        if n_bars_per_group > 1:
            bar_inner_dist = (group_size - bar_width * n_bars_per_group) / (n_bars_per_group - 1)
        else:
            bar_inner_dist = 0

        # compute the space between groups
        # (given the group size, number of groups and ending of last group)
        all_bars_size = last_group_end - first_bar_start
        if n_groups > 1:
            bar_outer_dist = (all_bars_size - group_size * n_groups) / (n_groups - 1)
        else:
            bar_outer_dist = 0

        self.tempo_decimal_offset = int(round(bar_offset * 10))
        self.tempo_decimal_width = int(round(bar_width * 10))
        self.tempo_decimal_inner_dist = int(round(bar_inner_dist * 10))
        self.tempo_decimal_outer_dist = int(round(bar_outer_dist * 10))
        self.data_changed = True

        self.update_tempo_bar_params_labels()

    def update_tempo_bar_params_labels(self):
        self.lbl_parameters_offset.set_text("Offset: {0:.1f}".format(self.tempo_decimal_offset / 10.0))
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))

    def btn_edit_parameters_click(self, button):
        self.tempo_decimal_offset = int(round(self.data.bar_offset * 10))
        self.tempo_decimal_width = int(round(self.data.bar_width * 10))
        self.tempo_decimal_inner_dist = int(round(self.data.bar_inner_dist * 10))
        self.tempo_decimal_outer_dist = int(round(self.data.bar_outer_dist * 10))

        self.update_tempo_bar_params_labels()

        # convert the parameters of the bar into slider positions ...
        self.update_slider_from_bar_params()

        # show in the canvas
        self.canvas_display.elements["bar_params"].visible = True
        self.canvas_display.locked = False

        self.set_editor_mode(BarChartAnnotator.ModeParameterEdit)
        self.update_current_view()

    def btn_edit_data_click(self, button):
        self.tempo_data_layer = 0
        self.set_editor_mode(BarChartAnnotator.ModeDataEdit)
        self.update_current_view()
        self.update_stack_bar_layer()

    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing bar data ...
            self.panel_info.data = BarData.Copy(self.data)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(BarChartAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen

    def get_default_length(self):
        if self.data.total_bars() == 0:
            a_x1, a_y1, a_x2, a_y2 = self.panel_info.axes.bounding_box
            a_x1 = int(a_x1)
            a_y1 = int(a_y1)
            a_x2 = int(a_x2)
            a_y2 = int(a_y2)

            if self.data.bar_vertical:
                # vertical bars ... X axis has the categories ...
                return int((a_y2 - a_y1) * 0.5)
            else:
                # horizontal bars ... Y axis has the categories ...
                return int((a_x2 - a_x1) * 0.5)
        else:
            return int(self.data.mean_length())

    def btn_number_series_add_click(self, button):
        # add ... using current mean length as default length
        default_length = self.get_default_length()
        self.data.add_data_series(default_length=default_length)

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

    def numbers_update_GUI(self, categories_changed, data_series_changed):
        n_bars = self.data.total_bars()
        self.lbl_number_title.set_text("Bars in Chart: {0:d}".format(n_bars))

        if categories_changed:
            self.lbx_number_categories_values.clear_options()
            self.fill_categories_list()

        if data_series_changed:
            self.lbx_number_series_values.clear_options()
            self.fill_data_series_list()

        self.update_current_view()

    def btn_number_return_click(self, button):
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btns_parameters_move_offset_click(self, button):
        if self.tempo_decimal_offset + button.tag >= 0:
            self.tempo_decimal_offset += button.tag

        self.data_changed = True
        self.lbl_parameters_offset.set_text("Offset: {0:.1f}".format(self.tempo_decimal_offset / 10.0))
        self.update_slider_from_bar_params()
        self.update_current_view()

    def btns_parameters_move_width_click(self, button):
        if self.tempo_decimal_width + button.tag >= 0:
            self.tempo_decimal_width += button.tag

        self.data_changed = True
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.update_slider_from_bar_params()
        self.update_current_view()

    def btns_parameters_move_inner_dist_click(self, button):
        # this one allows negative values ...
        self.tempo_decimal_inner_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.update_slider_from_bar_params()
        self.update_current_view()

    def btns_parameters_move_outer_dist_click(self, button):
        if self.tempo_decimal_outer_dist + button.tag >= 0:
            self.tempo_decimal_outer_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))
        self.update_slider_from_bar_params()
        self.update_current_view()

    def btn_parameters_return_accept_click(self, button):
        self.data.bar_offset = self.tempo_decimal_offset / 10
        self.data.bar_width = self.tempo_decimal_width / 10
        self.data.bar_inner_dist = self.tempo_decimal_inner_dist / 10
        self.data.bar_outer_dist = self.tempo_decimal_outer_dist / 10

        # hide bar_params slider
        self.canvas_display.elements["bar_params"].visible = False
        self.canvas_display.locked = True

        # return
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_parameters_return_cancel_click(self, button):
        # hide bar_params slider
        self.canvas_display.elements["bar_params"].visible = False
        self.canvas_display.locked = True

        # just return ...
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_data_manual_click(self, button):
        # copy bar data to temporal ...
        self.tempo_bar_lengths = self.data.get_lengths()
        self.set_editor_mode(BarChartAnnotator.ModeDataSelect)
        self.update_current_view()

    def cluster_by_small_color_diff(self, feature_array, min_dist):
        # automatically group contiguous lines with very little color variance ...
        distances = np.linalg.norm(feature_array[:-1, :] - feature_array[1:, :], axis=1)

        clusters = []
        current_start = 0
        next_end = 1
        while next_end < feature_array.shape[0]:
            if distances[next_end - 1] > min_dist:
                clusters.append((current_start, next_end))
                current_start = next_end

            next_end += 1
        clusters.append((current_start, next_end))

        return clusters

    def cluster_by_small_variance(self, feature_array, K, min_dist):
        # assume n rows x m features
        clusters = self.cluster_by_small_color_diff(feature_array, min_dist)

        if len(clusters) <= K:
            # base case, no further clustering required ...
            return clusters

        # compute the variance of merge candidates ...
        merge_cost = []
        for idx in range(len(clusters) - 1):
            prev_start, prev_end = clusters[idx]
            next_start, next_end = clusters[idx + 1]

            cost = np.var(feature_array[prev_start:next_end], axis=0).sum()
            merge_cost.append(cost)

        while len(clusters) > K:
            # print(clusters)
            # print(merge_cost)
            cheapest_merge = np.argmin(merge_cost)
            # print(cheapest_merge)
            # print(clusters[cheapest_merge])
            # merge clusters ...
            new_start = clusters[cheapest_merge][0]
            new_end = clusters[cheapest_merge + 1][1]
            clusters[cheapest_merge] = (new_start, new_end)
            del clusters[cheapest_merge + 1]
            del merge_cost[cheapest_merge]

            if cheapest_merge > 0:
                # update previous to current ...
                prev_start, prev_end = clusters[cheapest_merge - 1]
                cost = np.var(feature_array[prev_start:new_end], axis=0).sum()
                merge_cost[cheapest_merge - 1] = cost
            if cheapest_merge + 1 < len(clusters):
                # update current to next ...
                next_start, next_end = clusters[cheapest_merge + 1]
                cost = np.var(feature_array[new_start:next_end], axis=0).sum()
                merge_cost[cheapest_merge] = cost

            # print(clusters)
        return clusters

    def estimate_plot_region_bg_color(self):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        data_region_img = self.base_rgb_image[y1:y2, x1:x2]
        mask = np.ones((self.base_rgb_image.shape[0], self.base_rgb_image.shape[1]), dtype=np.bool)

        for bar_idx, polygon in enumerate(self.tempo_bar_polygons):
            # get bar meta-data
            series_idx, cat_idx, stack_idx, bar_baseline = self.tempo_bar_polygon_index[bar_idx]

            if self.data.bar_vertical:
                # vertical bar charts ...
                bar_start = polygon[:, 0].min()
                bar_end = polygon[:, 0].max()
                mask[y1:y2, bar_start:bar_end] = 0
            else:
                # horizontal bar charts ...
                bar_start = polygon[:, 1].min()
                bar_end = polygon[:, 1].max()
                mask[bar_start:bar_end, x1:x2] = 0

        mask = mask[y1:y2, x1:x2]

        median_color = np.median(data_region_img[mask], axis=0)

        return median_color


    def stack_to_legend_alignment(self, feature_array, min_dist, sorted_bars):
        # part one: pre-cluster together contiguous lines with very similar color
        # assume n rows x m features
        clusters = self.cluster_by_small_color_diff(feature_array, min_dist)

        # Part two: compute the median colors of the legend marks present on this bar
        valid_stack = True
        legend_colors = []
        for stack_idx, bar_idx in sorted_bars:
            # get bar meta-data
            series_idx, cat_idx, stack_idx, _ = self.tempo_bar_polygon_index[bar_idx]

            if self.data.data_series[series_idx] is None:
                valid_stack = False
                break
            else:
                marker_id = self.data.data_series[series_idx].id
                marker_median = self.panel_info.legend.get_marker_median_color(self.base_rgb_image, marker_id)
                legend_colors.append(marker_median)

        if not valid_stack:
            return []

        # part three: compute the median colors of each cluster and the cost to match them to each legend entry
        base_cost_matrix = np.zeros((len(legend_colors) + 1, len(clusters)), np.float64)

        img_array = feature_array.reshape((feature_array.shape[0], int(feature_array.shape[1] / 3), 3))
        all_cluster_medians = []
        for cluster_idx, (row_start, row_end) in enumerate(clusters):
            # compute the median color of the cluster ...
            cluster_median_r = np.median(img_array[row_start:row_end, :, 0])
            cluster_median_g = np.median(img_array[row_start:row_end, :, 1])
            cluster_median_b = np.median(img_array[row_start:row_end, :, 2])

            all_cluster_medians.append((cluster_median_r, cluster_median_g, cluster_median_b))

            # compute the cost of aligning the cluster to each legend element ...
            for legend_idx, (marker_median_r, marker_median_g, marker_median_b) in enumerate(legend_colors):
                # cost is the distance in RGB space ...
                cost = np.sqrt(pow(cluster_median_r - marker_median_r, 2) +
                               pow(cluster_median_g - marker_median_g, 2) +
                               pow(cluster_median_b - marker_median_b, 2))

                base_cost_matrix[legend_idx, cluster_idx] = cost

        # part four: compute the cost of matching clusters to a dummy legend entry
        # to detect parts that are beyond the end of the bar stack
        """
        # V1 - using split by colors (current cluster vs merging everything on its right side)... 
        all_cluster_medians = np.array(all_cluster_medians)
        for cluster_idx in range(len(clusters) - 1):
            cluster_median_r, cluster_median_g, cluster_median_b = all_cluster_medians[cluster_idx]
            marker_median_r = np.mean(all_cluster_medians[cluster_idx + 1:, 0])
            marker_median_g = np.mean(all_cluster_medians[cluster_idx + 1:, 1])
            marker_median_b = np.mean(all_cluster_medians[cluster_idx + 1:, 2])

            cost = np.sqrt(pow(cluster_median_r - marker_median_r, 2) +
                           pow(cluster_median_g - marker_median_g, 2) +
                           pow(cluster_median_b - marker_median_b, 2))

            base_cost_matrix[-1, cluster_idx] = cost

        # the last row should represent the cost of merging each element to the rest of clusters on the right side
        # as such, it is unclear what should be the ideal cost of aligning the last element to nothing
        if len(clusters) > 1:
            min_cost = np.min(base_cost_matrix[-1, :-1])
            base_cost_matrix[len(legend_colors), -1] = min_cost
        """
        # V2 - use an estimation of the background color of the data region ...
        bg_median_r, bg_median_g, bg_median_b = self.estimate_plot_region_bg_color()
        all_cluster_medians = np.array(all_cluster_medians)
        for cluster_idx in range(len(clusters)):
            cluster_median_r, cluster_median_g, cluster_median_b = all_cluster_medians[cluster_idx]

            cost = np.sqrt(pow(cluster_median_r - bg_median_r, 2) +
                           pow(cluster_median_g - bg_median_g, 2) +
                           pow(cluster_median_b - bg_median_b, 2))

            base_cost_matrix[-1, cluster_idx] = cost

        # part five: find optimal alignment between clusters (bar segments) and the expected sequence of legend entries
        # use dynamic programming ...
        final_costs = np.zeros((len(legend_colors) + 1, len(clusters)), np.float64)
        path_trace = np.zeros((len(legend_colors) + 1, len(clusters)), np.int8)

        # special case: first element
        final_costs[0, 0] = base_cost_matrix[0, 0]

        # special case: first row
        for cluster_idx in range(1, final_costs.shape[1]):
            # only connections to the element on the left
            # cost = local cost + path cost (from the left)
            final_costs[0, cluster_idx] = base_cost_matrix[0, cluster_idx] + final_costs[0, cluster_idx - 1]
            path_trace[0, cluster_idx] = 1 # left

        # special case: first column
        for legend_idx in range(1, final_costs.shape[0]):
            # only connections to the element from above
            # cost = local cost + path cost (from the top) - cost of top element (replacement)
            final_costs[legend_idx, 0] = (base_cost_matrix[legend_idx, 0] + final_costs[legend_idx - 1, 0] -
                                          base_cost_matrix[legend_idx - 1, 0])
            path_trace[legend_idx, 0] = 2 # top connection

        # all other cases ....
        for legend_idx in range(1, final_costs.shape[0]):
            for cluster_idx in range(1, final_costs.shape[1]):
                left_cost = base_cost_matrix[legend_idx, cluster_idx] + final_costs[legend_idx, cluster_idx - 1]
                top_cost = (base_cost_matrix[legend_idx, cluster_idx] + final_costs[legend_idx - 1, cluster_idx] -
                            base_cost_matrix[legend_idx - 1, cluster_idx])
                # diagonal cost (shortcut)
                diag_cost = base_cost_matrix[legend_idx, cluster_idx] + final_costs[legend_idx - 1, cluster_idx - 1]

                if diag_cost <= left_cost and diag_cost <= top_cost:
                    # prefer diagonal ...
                    final_costs[legend_idx, cluster_idx] = diag_cost
                    path_trace[legend_idx, cluster_idx] = 3
                elif left_cost <= top_cost:
                    # use left cost ...
                    final_costs[legend_idx, cluster_idx] = left_cost
                    path_trace[legend_idx, cluster_idx] = 1
                else:
                    # use top cost ...
                    final_costs[legend_idx, cluster_idx] = top_cost
                    path_trace[legend_idx, cluster_idx] = 2

        # do not force to match everything on legend + dummy ...
        # instead find the last alignment of the clusters with the minimal cost
        best_legend_idx = np.argmin(final_costs[:, - 1])

        # part six: retrieve the minimum cost path
        pos_row, pos_col = best_legend_idx, final_costs.shape[1] - 1
        final_path = [(pos_row, pos_col)]
        while pos_row != 0 or pos_col != 0:
            if path_trace[pos_row, pos_col] == 1:
                # path from left ... move left ...
                pos_col -= 1
            elif path_trace[pos_row, pos_col] == 2:
                # path from top ... move top ...
                pos_row -= 1
            elif path_trace[pos_row, pos_col] == 3:
                # path from diagonal ... move both top and left
                pos_col -= 1
                pos_row -= 1

            final_path.append((pos_row, pos_col))

        final_path = reversed(final_path)

        # final_assignments = np.zeros(feature_array.shape[0], np.int32)
        first_time_seen = {legend_idx: None for legend_idx in range(base_cost_matrix.shape[0])}
        last_time_seen = {legend_idx: None for legend_idx in range(base_cost_matrix.shape[0])}
        for legend_idx, cluster_idx in final_path:
            """
            cluster_start, cluster_end = clusters[cluster_idx]
            # note that elements that move "down" on the path will be automatically overriden by the highest legend_idx
            # assignment for that cluster_idx
            final_assignments[cluster_start:cluster_end] = legend_idx
            """
            if first_time_seen[legend_idx] is None:
                first_time_seen[legend_idx] = cluster_idx
            last_time_seen[legend_idx] = cluster_idx

        # print(final_assignments)
        final_clusters = []
        interval_start = 0
        for legend_idx in range(base_cost_matrix.shape[0]):
            cluster_idx = last_time_seen[legend_idx]

            if cluster_idx is None:
                # never saw this entry on the optimal path ... keep at the same position ...
                cluster_end = interval_start
            else:
                cluster_start, cluster_end = clusters[cluster_idx]

            final_clusters.append((interval_start, cluster_end))
            interval_start = cluster_end

        """
        tempo_img = img_array.copy()
        for row, col in final_path:
            cluster_start, cluster_end = clusters[col]
            if row < len(legend_colors):
                tempo_img[cluster_start:cluster_end, :] = legend_colors[row]
            else:
                tempo_img[cluster_start:cluster_end, :] = 255, 255, 255

        print(final_path)
        print(self.estimate_plot_region_bg_color())
        cv2.imshow("tempo", img_array)
        cv2.imshow("assignments", tempo_img)
        cv2.waitKey()
        """

        return final_clusters

    def btn_data_auto_click(self, button):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if self.data.total_layers() > 1:
            if self.auto_bar_adjust_mode in [BarChartAnnotator.AutoBarColorVariance,
                                             BarChartAnnotator.AutoBarLegendColorAlignment]:
                # for each bar ...get all the data ... group them by stack ...
                # ... and copy the features of each stack the first time it is seen
                reverse_bar_index = {}
                stack_features = {}
                for bar_idx, polygon in enumerate(self.tempo_bar_polygons):
                    # get bar meta-data
                    series_idx, cat_idx, stack_idx, bar_baseline = self.tempo_bar_polygon_index[bar_idx]

                    if self.data.bar_vertical:
                        # vertical bar charts ...
                        bar_start = polygon[:, 0].min()
                        bar_end = polygon[:, 0].max()
                    else:
                        # horizontal bar charts ...
                        bar_start = polygon[:, 1].min()
                        bar_end = polygon[:, 1].max()

                    stack_key = str(bar_start) + "-" + str(bar_end)
                    if not stack_key in reverse_bar_index:
                        # first time this stack is considered ...
                        reverse_bar_index[stack_key] = [(stack_idx, bar_idx)]

                        if self.data.bar_vertical:
                            sub_image = self.base_rgb_image[y1:y2, bar_start:bar_end]
                            features = sub_image[::-1].reshape(sub_image.shape[0], sub_image.shape[1] * 3)
                        else:
                            sub_image = self.base_rgb_image[bar_start:bar_end, x1:x2]
                            features = sub_image.transpose((1, 0, 2)).reshape(sub_image.shape[1], sub_image.shape[0] * 3)
                        stack_features[stack_key] = features
                    else:
                        # just add to the stack ...
                        reverse_bar_index[stack_key].append((stack_idx, bar_idx))

                # for each stack of bars on the reversed index ...
                for stack_key in reverse_bar_index:
                    sorted_bars = sorted(reverse_bar_index[stack_key])

                    if self.auto_bar_adjust_mode == BarChartAnnotator.AutoBarLegendColorAlignment:
                        # use legend to estimate bars ...
                        clusters = self.stack_to_legend_alignment(stack_features[stack_key], 5, sorted_bars)
                    else:
                        # assume cluster by variance mode
                        clusters = self.cluster_by_small_variance(stack_features[stack_key], len(sorted_bars), 5)

                    # apply bar lengths ....
                    for stack_idx, bar_idx in sorted_bars:
                        # get bar meta-data
                        series_idx, cat_idx, stack_idx, _ = self.tempo_bar_polygon_index[bar_idx]

                        if len(clusters) < len(sorted_bars):
                            self.data.bar_lengths[series_idx][cat_idx] = 0
                        else:
                            if stack_idx == 0:
                                if self.data.bar_vertical:
                                    # vertical bar charts ...
                                    bar_baseline = 0
                                else:
                                    # horizontal bar charts ...
                                    bar_baseline = 1
                            else:
                                bar_baseline = clusters[stack_idx -1][1]

                            self.data.bar_lengths[series_idx][cat_idx] = clusters[stack_idx][1] - bar_baseline
            else:
                print("This function does not support stacked bar charts at the moment")
                return
        else:
            # single-layer stacks .... simpler algorithms used ...
            if self.auto_bar_adjust_mode == BarChartAnnotator.AutoBarProfile:
                if self.data.bar_vertical:
                    # detect horizontal edges ....
                    edge_img = cv2.Sobel(self.base_gray_image, cv2.CV_64F, 0, 1, ksize=5)
                else:
                    # detect vertical edges
                    edge_img = cv2.Sobel(self.base_gray_image, cv2.CV_64F, 1, 0, ksize=5)

                edge_img = (np.abs(edge_img).astype(np.float64) / edge_img.max()) * 255
            else:
                edge_img = None

            # cv2.imshow("test", edge_img.astype(np.uint8))
            # cv2.waitKey()

            # for each bar ...
            for bar_idx, polygon in enumerate(self.tempo_bar_polygons):
                # get bar meta-data
                series_idx, cat_idx, stack_idx, bar_baseline = self.tempo_bar_polygon_index[bar_idx]

                if self.data.bar_vertical:
                    # vertical bar charts ...
                    bar_start = polygon[:, 0].min()
                    bar_end = polygon[:, 0].max()

                    if self.auto_bar_adjust_mode == BarChartAnnotator.AutoBarProfile:
                        sub_image = edge_img[y1:y2, bar_start:bar_end, 0]
                        profile = sub_image.sum(axis=1)
                        best_length = y2 - y1 - np.argmax(profile)
                    elif self.auto_bar_adjust_mode in [BarChartAnnotator.AutoBarColorVariance,
                                                       BarChartAnnotator.AutoBarLegendColorAlignment]:
                        sub_image = self.base_rgb_image[y1:y2, bar_start:bar_end]
                        features = sub_image[::-1].reshape(sub_image.shape[0], sub_image.shape[1] * 3)
                        clusters = self.cluster_by_small_variance(features, 2, 1)

                        if len(clusters) == 2:
                            best_length = clusters[0][1]
                        else:
                            best_length = 0
                    else:
                        best_length = 0
                else:
                    # horizontal bar charts ...
                    bar_start = polygon[:, 1].min()
                    bar_end = polygon[:, 1].max()

                    if self.auto_bar_adjust_mode == BarChartAnnotator.AutoBarProfile:
                        sub_image = edge_img[bar_start:bar_end, x1:x2, 0]
                        profile = sub_image.sum(axis=0)
                        best_length = np.argmax(profile)
                    elif self.auto_bar_adjust_mode in [BarChartAnnotator.AutoBarColorVariance,
                                                       BarChartAnnotator.AutoBarLegendColorAlignment]:
                        sub_image = self.base_rgb_image[bar_start:bar_end, x1:x2]
                        features = sub_image.transpose((1, 0, 2)).reshape(sub_image.shape[1], sub_image.shape[0] * 3)
                        clusters = self.cluster_by_small_variance(features, 2, 1)

                        if len(clusters) == 2:
                            best_length = clusters[0][1] - 1
                        else:
                            best_length = 0
                    else:
                        best_length = 0

                self.data.bar_lengths[series_idx][cat_idx] = best_length

        # cv2.waitKey()
        self.data_changed = True
        self.update_current_view()

    def btn_data_return_click(self, button):
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_edit_order_click(self, button):
        self.tempo_ordering = SeriesSorting.Copy(self.data.bar_sorting)

        self.update_ordering_list()
        self.set_editor_mode(BarChartAnnotator.ModeOrderEdit)
        self.update_current_view()

    def update_ordering_list(self):
        self.lbx_order_list.clear_options()

        for group_idx, group in enumerate(self.tempo_ordering.order):
            self.lbx_order_list.add_option("g-{0:d}".format(group_idx), "Bar Stack #{0:d}".format(group_idx + 1))

            for series_idx in group:
                if self.data.data_series[series_idx] is None:
                    display = "[Unnamed]"
                else:
                    display = self.data.data_series[series_idx].value

                self.lbx_order_list.add_option("s-{0:d}".format(series_idx), "-> {0:s}".format(display))

    def btn_order_move_up_click(self, button):
        if self.lbx_order_list.selected_option_value is None:
            print("Must select a data series or bar group")
            return

        value_type, value_idx = self.lbx_order_list.selected_option_value.split("-")
        value_idx = int(value_idx)

        # try moving
        if value_type == "g":
            # move group ...
            success = self.tempo_ordering.move_group_up(value_idx)
        else:
            # move individual data series ...
            success = self.tempo_ordering.move_series_up(value_idx)

        if success:
            self.update_ordering_list()

            if value_type == "g":
                new_key = "g-{0:d}".format(value_idx - 1)
            else:
                new_key = "s-{0:d}".format(value_idx)

            # select same element again
            self.lbx_order_list.change_option_selected(new_key)
        else:
            print("The selected element cannot move further up")

    def btn_order_move_down_click(self, button):
        if self.lbx_order_list.selected_option_value is None:
            print("Must select a data series or bar group")
            return

        value_type, value_idx = self.lbx_order_list.selected_option_value.split("-")
        value_idx = int(value_idx)

        # try moving
        if value_type == "g":
            # move group ...
            success = self.tempo_ordering.move_group_down(value_idx)
        else:
            # move individual data series ...
            success = self.tempo_ordering.move_series_down(value_idx)

        if success:
            self.update_ordering_list()

            if value_type == "g":
                new_key = "g-{0:d}".format(value_idx + 1)
            else:
                new_key = "s-{0:d}".format(value_idx)

            # select same element again
            self.lbx_order_list.change_option_selected(new_key)
        else:
            print("The selected element cannot move further down")

    def btn_order_return_accept_click(self, button):
        self.data.bar_sorting = SeriesSorting.Copy(self.tempo_ordering)
        self.data_changed = True

        # return ...
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_order_return_cancel_click(self, button):
        # just return ...
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_number_categories_add_click(self, button):
        # add ... using current mean length as default length
        default_length = self.get_default_length()
        self.data.add_category(default_length=default_length)

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

    def btn_edit_grouping_click(self, button):
        self.set_editor_mode(BarChartAnnotator.ModeGroupingEdit)
        self.update_grouping()

    def update_grouping(self):
        if self.data.bar_grouping == BarData.GroupingByCategory:
            self.lbl_grouping_description.set_text("Group Bars by Category")
        else:
            self.lbl_grouping_description.set_text("Group Bars by Data Series")

        self.update_current_view()

    def btn_grouping_by_categories_click(self, button):
        self.data.bar_grouping = BarData.GroupingByCategory
        self.data_changed = True
        self.update_grouping()

    def btn_grouping_by_data_series_click(self, button):
        self.data.bar_grouping = BarData.GroupingByDataSeries
        self.data_changed = True
        self.update_grouping()

    def btn_grouping_return_click(self, button):
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)

    def btn_data_layer_prev_click(self, button):
        if self.tempo_data_layer > 0:
            self.tempo_data_layer -= 1
            self.update_stack_bar_layer()
            self.update_current_view()

    def btn_data_layer_next_click(self, button):
        total_layers = self.data.total_layers()

        if self.tempo_data_layer + 1 < total_layers:
            self.tempo_data_layer += 1
            self.update_stack_bar_layer()
            self.update_current_view()

    def update_stack_bar_layer(self):
        total_layers = self.data.total_layers()
        if total_layers == 0:
            self.lbl_data_layer_title.set_text("Bar Stack Layer: None")
        else:
            self.lbl_data_layer_title.set_text("Bar Stack Layer: {0:d} of {1:d}".format(self.tempo_data_layer + 1, total_layers))

        self.lbx_data_layer_elements.clear_options()
        for idx, layer_element in enumerate(self.data.get_layer_elements(self.tempo_data_layer)):
            if layer_element is None:
                value_str = "[Un-named]"
            else:
                value_str = layer_element.value

            self.lbx_data_layer_elements.add_option(str(idx), "{0:d}: {1:s}".format(idx + 1, value_str))

    def canvas_display_object_edited(self, canvas, element_name):
        if element_name == "bar_params":
            self.update_bar_params_from_slider()
            self.update_current_view()
