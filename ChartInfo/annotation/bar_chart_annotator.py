
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.data.bar_data import BarData
from ChartInfo.data.series_sorting import SeriesSorting

class BarChartAnnotator(Screen):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeOrderEdit = 2
    ModeGroupingEdit = 3
    ModeParameterEdit = 4
    ModeDataEdit = 5
    ModeDataSelect = 6
    ModeConfirmNumberOverwrite = 7
    ModeConfirmExit = 8

    ViewModeRawData = 0
    ViewModeGrayData = 1
    ViewModeRawNoData = 2
    ViewModeGrayNoData = 3

    def __init__(self, size, panel_image, panel_info, parent_screen):
        Screen.__init__(self, "Bar Chart Ground Truth Annotation Interface", size)

        self.panel_image = panel_image
        self.panel_gray = np.zeros(self.panel_image.shape, self.panel_image.dtype)
        self.panel_gray[:, :, 0] = cv2.cvtColor(self.panel_image, cv2.COLOR_RGB2GRAY)
        self.panel_gray[:, :, 1] = self.panel_gray[:, :, 0].copy()
        self.panel_gray[:, :, 2] = self.panel_gray[:, :, 0].copy()

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

        self.tempo_ordering = None

        self.tempo_decimal_offset = None
        self.tempo_decimal_width = None
        self.tempo_decimal_inner_dist = None
        self.tempo_decimal_outer_dist = None

        self.tempo_data_layer = None

        self.tempo_bar_lengths = None
        self.tempo_bar_polygons = None
        self.tempo_bar_polygon_index = None

        self.view_mode = BarChartAnnotator.ViewModeRawData
        self.view_scale = 1.0

        self.label_title = None

        self.container_view_buttons = None
        self.lbl_zoom = None
        self.btn_zoom_reduce = None
        self.btn_zoom_increase = None
        self.btn_zoom_zero = None

        self.btn_view_raw_data = None
        self.btn_view_gray_data = None
        self.btn_view_raw_clear = None
        self.btn_view_gray_clear = None

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
        self.btn_data_return = None

        self.container_images = None
        self.canvas_display = None
        self.img_main = None

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

        # View panel with view control buttons
        self.container_view_buttons = ScreenContainer("container_view_buttons", (container_width, 160),
                                                      back_color=self.general_background)
        self.container_view_buttons.position = (self.width - self.container_view_buttons.width - 10, container_top)
        self.elements.append(self.container_view_buttons)

        # zoom ....
        self.lbl_zoom = ScreenLabel("lbl_zoom", "Zoom: 100%", 21, 290, 1)
        self.lbl_zoom.position = (5, 5)
        self.lbl_zoom.set_background(self.general_background)
        self.lbl_zoom.set_color(self.text_color)
        self.container_view_buttons.append(self.lbl_zoom)

        self.btn_zoom_reduce = ScreenButton("btn_zoom_reduce", "[ - ]", 21, 90)
        self.btn_zoom_reduce.set_colors(button_text_color, button_back_color)
        self.btn_zoom_reduce.position = (10, self.lbl_zoom.get_bottom() + 10)
        self.btn_zoom_reduce.click_callback = self.btn_zoom_reduce_click
        self.container_view_buttons.append(self.btn_zoom_reduce)

        self.btn_zoom_increase = ScreenButton("btn_zoom_increase", "[ + ]", 21, 90)
        self.btn_zoom_increase.set_colors(button_text_color, button_back_color)
        self.btn_zoom_increase.position = (self.container_view_buttons.width - self.btn_zoom_increase.width - 10,
                                           self.lbl_zoom.get_bottom() + 10)
        self.btn_zoom_increase.click_callback = self.btn_zoom_increase_click
        self.container_view_buttons.append(self.btn_zoom_increase)

        self.btn_zoom_zero = ScreenButton("btn_zoom_zero", "100%", 21, 90)
        self.btn_zoom_zero.set_colors(button_text_color, button_back_color)
        self.btn_zoom_zero.position = ((self.container_view_buttons.width - self.btn_zoom_zero.width) / 2,
                                       self.lbl_zoom.get_bottom() + 10)
        self.btn_zoom_zero.click_callback = self.btn_zoom_zero_click
        self.container_view_buttons.append(self.btn_zoom_zero)

        self.btn_view_raw_data = ScreenButton("btn_view_raw_data", "RGB Data", 21, button_2_width)
        self.btn_view_raw_data.set_colors(button_text_color, button_back_color)
        self.btn_view_raw_data.position = (button_2_left, self.btn_zoom_zero.get_bottom() + 10)
        self.btn_view_raw_data.click_callback = self.btn_view_raw_data_click
        self.container_view_buttons.append(self.btn_view_raw_data)

        self.btn_view_gray_data = ScreenButton("btn_view_gray", "Gray Data", 21, button_2_width)
        self.btn_view_gray_data.set_colors(button_text_color, button_back_color)
        self.btn_view_gray_data.position = (button_2_right, self.btn_zoom_zero.get_bottom() + 10)
        self.btn_view_gray_data.click_callback = self.btn_view_gray_data_click
        self.container_view_buttons.append(self.btn_view_gray_data)

        self.btn_view_raw_clear = ScreenButton("btn_view_raw_clear", "RGB Clear", 21, button_2_width)
        self.btn_view_raw_clear.set_colors(button_text_color, button_back_color)
        self.btn_view_raw_clear.position = (button_2_left, self.btn_view_raw_data.get_bottom() + 10)
        self.btn_view_raw_clear.click_callback = self.btn_view_raw_clear_click
        self.container_view_buttons.append(self.btn_view_raw_clear)

        self.btn_view_gray_clear = ScreenButton("btn_view_gray_clear", "Gray Clear", 21, button_2_width)
        self.btn_view_gray_clear.set_colors(button_text_color, button_back_color)
        self.btn_view_gray_clear.position = (button_2_right, self.btn_view_raw_data.get_bottom() + 10)
        self.btn_view_gray_clear.click_callback = self.btn_view_gray_clear_click
        self.container_view_buttons.append(self.btn_view_gray_clear)

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

        self.btn_data_manual = ScreenButton("btn_data_manual", "Manual Bar Adjustment", 21, button_width)
        self.btn_data_manual.set_colors(button_text_color, button_back_color)
        self.btn_data_manual.position = (button_left, self.lbx_data_layer_elements.get_bottom() + 20)
        self.btn_data_manual.click_callback = self.btn_data_manual_click
        self.container_data_buttons.append(self.btn_data_manual)

        self.btn_data_return = ScreenButton("btn_data_return", "Return", 21, button_width)
        self.btn_data_return.set_colors(button_text_color, button_back_color)
        self.btn_data_return.position = (button_left, self.btn_data_manual.get_bottom() + 30)
        self.btn_data_return.click_callback = self.btn_data_return_click
        self.container_data_buttons.append(self.btn_data_return)
        self.container_data_buttons.visible = True


        # ======================================
        # visuals
        # ===========================
        # Image

        image_width = self.width - self.container_view_buttons.width - 30
        image_height = self.height - container_top - 10
        self.container_images = ScreenContainer("container_images", (image_width, image_height), back_color=(0, 0, 0))
        self.container_images.position = (10, container_top)
        self.elements.append(self.container_images)

        # ... image objects ...
        tempo_blank = np.zeros((50, 50, 3), np.uint8)
        tempo_blank[:, :, :] = 255
        self.img_main = ScreenImage("img_main", tempo_blank, 0, 0, True, cv2.INTER_NEAREST)
        self.img_main.position = (0, 0)
        self.img_main.mouse_button_down_callback = self.img_mouse_down
        self.container_images.append(self.img_main)

        self.canvas_display = ScreenCanvas("canvas_display", 100, 100)
        self.canvas_display.position = (0, 0)
        self.canvas_display.locked = True
        self.container_images.append(self.canvas_display)

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

    def btn_zoom_reduce_click(self, button):
        self.update_view_scale(self.view_scale - 0.25)

    def btn_zoom_increase_click(self, button):
        self.update_view_scale(self.view_scale + 0.25)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = BarChartAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = BarChartAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = BarChartAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = BarChartAnnotator.ViewModeGrayNoData
        self.update_current_view()

    def get_bar_lines(self, bar_baseline, bar_start, bar_end, bar_length):
        if self.data.bar_vertical:
            bar_max = bar_baseline - bar_length

            left_axis = (bar_start, bar_baseline)
            left_top = (bar_start, bar_max)
            right_top = (bar_end, bar_max)
            right_axis = (bar_end, bar_baseline)

            return (left_axis, left_top, right_top, right_axis), bar_max
        else:
            bar_max = bar_baseline + bar_length

            top_axis = (bar_baseline, bar_start)
            top_right = (bar_max, bar_start)
            bottom_right = (bar_max, bar_end)
            bottom_axis = (bar_baseline, bar_end)

            return (top_axis, top_right, bottom_right, bottom_axis), bar_max

    def get_stacked_bar_lines(self, cat_idx, group, bar_lengths, bar_baseline, bar_start, bar_end):
        polygons = []
        polygon_index = []
        current_baseline = bar_baseline
        for stack_idx, series_idx in enumerate(group):
            # ...retrieve corresponding bar length ...
            bar_length = bar_lengths[series_idx][cat_idx]

            bar_lines, bar_max = self.get_bar_lines(current_baseline, bar_start, bar_end, bar_length)

            polygons.append(bar_lines)
            polygon_index.append((series_idx, cat_idx, stack_idx, current_baseline))

            current_baseline = bar_max

        return polygons, polygon_index

    def update_current_view(self, resized=False):
        if self.view_mode in [BarChartAnnotator.ViewModeGrayData, BarChartAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.panel_gray
        else:
            base_image = self.panel_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [BarChartAnnotator.ViewModeRawData, BarChartAnnotator.ViewModeGrayData]:
            # (for example, draw the polygons)
            self.canvas_display.visible = True

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
            self.tempo_bar_polygon_index = []

            if self.data.bar_grouping == BarData.GroupingByCategory:
                # bar are grouped by categorical value ...
                for cat_idx, category in enumerate(self.data.categories):
                    for group_idx, group in enumerate(self.data.bar_sorting.order):
                        bar_end = bar_start + bar_width

                        # add stacked bars ...
                        polygons, polygon_index = self.get_stacked_bar_lines(cat_idx, group, bar_lengths, bar_baseline,
                                                                             bar_start, bar_end)

                        current_lines += polygons
                        self.tempo_bar_polygon_index += polygon_index

                        # next stack of bars on same grouping
                        # bar width + distance between contiguous bars
                        bar_start += bar_width + bar_inner_dist

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

                        current_lines += polygons
                        self.tempo_bar_polygon_index += polygon_index

                        # next stack of bars on same grouping
                        bar_start += bar_width + bar_inner_dist

                    # next group of bars ...
                    bar_start += bar_outer_dist

            current_lines = np.array(current_lines).round().astype(np.int32)
            self.tempo_bar_polygons = current_lines
            modified_image = cv2.polylines(modified_image, current_lines, False, (255, 0, 0))
        else:
            self.canvas_display.visible = False

        # finally, resize ...
        modified_image = cv2.resize(modified_image, (int(w * self.view_scale), int(h * self.view_scale)),
                                    interpolation=cv2.INTER_NEAREST)

        # update canvas size ....
        self.canvas_display.height, self.canvas_display.width, _ = modified_image.shape

        # replace/update image
        self.img_main.set_image(modified_image, 0, 0, True, cv2.INTER_NEAREST)
        if resized:
            self.container_images.recalculate_size()

    def update_view_scale(self, new_scale):
        prev_scale = self.view_scale

        if 0.25 <= new_scale <= 4.0:
            self.view_scale = new_scale
        else:
            return

        # keep previous offsets ...
        scroll_offset_y = self.container_images.v_scroll.value if self.container_images.v_scroll.active else 0
        scroll_offset_x = self.container_images.h_scroll.value if self.container_images.h_scroll.active else 0

        prev_center_y = scroll_offset_y + self.container_images.height / 2
        prev_center_x = scroll_offset_x + self.container_images.width / 2

        # compute new scroll bar offsets
        scale_factor = (new_scale / prev_scale)
        new_off_y = prev_center_y * scale_factor - self.container_images.height / 2
        new_off_x = prev_center_x * scale_factor - self.container_images.width / 2

        # update view ....
        self.update_current_view(True)

        # set offsets
        if self.container_images.v_scroll.active and 0 <= new_off_y <= self.container_images.v_scroll.max:
            self.container_images.v_scroll.value = new_off_y
        if self.container_images.h_scroll.active and 0 <= new_off_x <= self.container_images.h_scroll.max:
            self.container_images.h_scroll.value = new_off_x

        # re-scale objects from both canvas
        # ... display ...
        for polygon_name in self.canvas_display.elements:
            display_polygon = self.canvas_display.elements[polygon_name]
            display_polygon.points *= scale_factor

        # update scale text ...
        self.lbl_zoom.set_text("Zoom: " + str(int(round(self.view_scale * 100,0))) + "%")

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

    def img_mouse_down(self, img_object, pos, button):
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

    def btn_edit_parameters_click(self, button):
        self.tempo_decimal_offset = int(round(self.data.bar_offset * 10))
        self.tempo_decimal_width = int(round(self.data.bar_width * 10))
        self.tempo_decimal_inner_dist = int(round(self.data.bar_inner_dist * 10))
        self.tempo_decimal_outer_dist = int(round(self.data.bar_outer_dist * 10))

        self.lbl_parameters_offset.set_text("Offset: {0:.1f}".format(self.tempo_decimal_offset / 10.0))
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))

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
        self.update_current_view()

    def btns_parameters_move_width_click(self, button):
        if self.tempo_decimal_width + button.tag >= 0:
            self.tempo_decimal_width += button.tag

        self.data_changed = True
        self.lbl_parameters_width.set_text("Width: {0:.1f}".format(self.tempo_decimal_width / 10.0))
        self.update_current_view()

    def btns_parameters_move_inner_dist_click(self, button):
        # this one allows negative values ...
        self.tempo_decimal_inner_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_inner_dist.set_text("Inner Distance: {0:.1f}".format(self.tempo_decimal_inner_dist / 10.0))
        self.update_current_view()

    def btns_parameters_move_outer_dist_click(self, button):
        if self.tempo_decimal_outer_dist + button.tag >= 0:
            self.tempo_decimal_outer_dist += button.tag

        self.data_changed = True
        self.lbl_parameters_outer_dist.set_text("Outer Distance: {0:.1f}".format(self.tempo_decimal_outer_dist / 10.0))
        self.update_current_view()

    def btn_parameters_return_accept_click(self, button):
        self.data.bar_offset = self.tempo_decimal_offset / 10
        self.data.bar_width = self.tempo_decimal_width / 10
        self.data.bar_inner_dist = self.tempo_decimal_inner_dist / 10
        self.data.bar_outer_dist = self.tempo_decimal_outer_dist / 10

        # return
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_parameters_return_cancel_click(self, button):
        # just return ...
        self.set_editor_mode(BarChartAnnotator.ModeNavigate)
        self.update_current_view()

    def btn_data_manual_click(self, button):
        # copy bar data to temporal ...
        self.tempo_bar_lengths = self.data.get_lengths()
        self.set_editor_mode(BarChartAnnotator.ModeDataSelect)
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

    def btn_data_layer_next_click(self, button):
        total_layers = self.data.total_layers()

        if self.tempo_data_layer + 1 < total_layers:
            self.tempo_data_layer += 1
            self.update_stack_bar_layer()

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


