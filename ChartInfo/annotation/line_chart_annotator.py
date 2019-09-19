
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.data.line_data import LineData
from ChartInfo.data.line_values import LineValues

class LineChartAnnotator(Screen):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeLineSelect = 2
    ModeLineEdit = 3
    ModePointAdd = 4
    ModePointEdit = 5
    ModeConfirmNumberOverwrite = 6
    ModeConfirmExit = 7

    ViewModeRawData = 0
    ViewModeGrayData = 1
    ViewModeRawNoData = 2
    ViewModeGrayNoData = 3

    DoubleClickMaxPointDistance = 5

    def __init__(self, size, panel_image, panel_info, parent_screen):
        Screen.__init__(self, "Line Chart Ground Truth Annotation Interface", size)

        self.panel_image = panel_image
        self.panel_gray = np.zeros(self.panel_image.shape, self.panel_image.dtype)
        self.panel_gray[:, :, 0] = cv2.cvtColor(self.panel_image, cv2.COLOR_RGB2GRAY)
        self.panel_gray[:, :, 1] = self.panel_gray[:, :, 0].copy()
        self.panel_gray[:, :, 2] = self.panel_gray[:, :, 0].copy()

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

        self.tempo_line_index = None
        self.tempo_point_index = None
        self.tempo_line_values = None

        self.view_mode = LineChartAnnotator.ViewModeRawData
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
        self.btn_data_return = None

        self.container_line_buttons = None
        self.lbl_line_title = None
        self.lbl_line_name = None
        self.lbx_line_points = None
        self.btn_line_point_edit = None
        self.btn_line_point_delete = None
        self.btn_line_point_add = None
        self.btn_line_return_accept = None
        self.btn_line_return_cancel = None


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
        self.container_data_buttons = ScreenContainer("container_data_buttons", (container_width, 380),
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

        self.btn_data_return = ScreenButton("btn_data_return", "Return", 21, button_width)
        self.btn_data_return.set_colors(button_text_color, button_back_color)
        self.btn_data_return.position = (button_left, self.btn_data_series_edit.get_bottom() + 20)
        self.btn_data_return.click_callback = self.btn_data_return_click
        self.container_data_buttons.append(self.btn_data_return)

        self.container_data_buttons.visible = False

        # ==============================
        # line annotation options
        self.container_line_buttons = ScreenContainer("container_line_buttons", (container_width, 450),
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

        self.btn_line_point_edit = ScreenButton("btn_line_point_edit", "Edit Point", 21, button_2_width)
        self.btn_line_point_edit.set_colors(button_text_color, button_back_color)
        self.btn_line_point_edit.position = (button_2_left, self.lbx_line_points.get_bottom() + 10)
        self.btn_line_point_edit.click_callback = self.btn_line_point_edit_click
        self.container_line_buttons.append(self.btn_line_point_edit)

        self.btn_line_point_delete = ScreenButton("btn_line_point_delete", "Remove Point", 21, button_2_width)
        self.btn_line_point_delete.set_colors(button_text_color, button_back_color)
        self.btn_line_point_delete.position = (button_2_right, self.lbx_line_points.get_bottom() + 10)
        self.btn_line_point_delete.click_callback = self.btn_line_point_delete_click
        self.container_line_buttons.append(self.btn_line_point_delete)

        self.btn_line_point_add = ScreenButton("btn_line_point_add", "Add Points", 21, button_width)
        self.btn_line_point_add.set_colors(button_text_color, button_back_color)
        self.btn_line_point_add.position = (button_left, self.btn_line_point_edit.get_bottom() + 10)
        self.btn_line_point_add.click_callback = self.btn_line_point_add_click
        self.container_line_buttons.append(self.btn_line_point_add)

        self.btn_line_return_accept = ScreenButton("btn_line_return_accept", "Accept", 21, button_2_width)
        self.btn_line_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_line_return_accept.position = (button_2_left, self.btn_line_point_add.get_bottom() + 20)
        self.btn_line_return_accept.click_callback = self.btn_line_return_accept_click
        self.container_line_buttons.append(self.btn_line_return_accept)

        self.btn_line_return_cancel = ScreenButton("btn_line_return_cancel", "Cancel", 21, button_2_width)
        self.btn_line_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_line_return_cancel.position = (button_2_right, self.btn_line_point_add.get_bottom() + 20)
        self.btn_line_return_cancel.click_callback = self.btn_line_return_cancel_click
        self.container_line_buttons.append(self.btn_line_return_cancel)

        self.container_line_buttons.visible = False

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
        self.img_main.double_click_callback = self.img_mouse_double_click
        self.container_images.append(self.img_main)

        self.canvas_display = ScreenCanvas("canvas_display", 100, 100)
        self.canvas_display.position = (0, 0)
        self.canvas_display.locked = True
        self.container_images.append(self.canvas_display)

        self.prepare_number_controls()

        self.set_editor_mode(LineChartAnnotator.ModeNavigate)

    def btn_zoom_reduce_click(self, button):
        self.update_view_scale(self.view_scale - 0.25)

    def btn_zoom_increase_click(self, button):
        self.update_view_scale(self.view_scale + 0.25)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = LineChartAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = LineChartAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = LineChartAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = LineChartAnnotator.ViewModeGrayNoData
        self.update_current_view()

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

        # compute new scroll box offsets
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

    def update_current_view(self, resized=False):
        if self.view_mode in [LineChartAnnotator.ViewModeGrayData, LineChartAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.panel_gray
        else:
            base_image = self.panel_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [LineChartAnnotator.ViewModeRawData, LineChartAnnotator.ViewModeGrayData]:
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

            # check which lines will be drawn ...
            if self.edition_mode in [LineChartAnnotator.ModeLineEdit,
                                     LineChartAnnotator.ModePointAdd,
                                     LineChartAnnotator.ModePointEdit]:
                # Only draw the line being edited ... based on its temporary changes ...
                lines_to_drawing = [self.tempo_line_values]
            else:
                # draw everything ...
                lines_to_drawing = self.data.lines

            # for each line to drawn ...
            for idx, line_values in enumerate(lines_to_drawing):
                line_color = self.canvas_display.colors[idx % len(self.canvas_display.colors)]

                all_transformed_points = []
                for p_idx in range(len(line_values.points)):
                    # transform current point from relative space to absolute pixel space
                    c_x, c_y = line_values.points[p_idx]
                    c_x += x1
                    c_y = y2 - c_y
                    current_point = (int(round(c_x)), int(round(c_y)))

                    all_transformed_points.append(current_point)

                    # Draw the points as small circles ...
                    if (self.edition_mode == LineChartAnnotator.ModeLineEdit and
                        self.lbx_line_points.selected_option_value is not None and
                        int(self.lbx_line_points.selected_option_value) == p_idx):
                        # empty large circle for selected option
                        cv2.circle(modified_image, current_point, 5, line_color, thickness=2)
                    else:
                        # filled small circle
                        cv2.circle(modified_image, current_point, 3, line_color,thickness=-1)

                # Draw the line ...
                all_transformed_points = np.array(all_transformed_points).astype(np.int32)
                modified_image = cv2.polylines(modified_image, [all_transformed_points], False, line_color)

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


    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [LineChartAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(LineChartAnnotator.ModeNavigate)

        elif self.edition_mode in [LineChartAnnotator.ModePointAdd, LineChartAnnotator.ModePointEdit]:
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
        x1 = int(x1)
        y2 = int(y2)

        rel_x = click_x - x1
        rel_y = y2 - click_y

        return rel_x, rel_y

    def img_mouse_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode in [LineChartAnnotator.ModePointAdd, LineChartAnnotator.ModePointEdit]:
                # click pos ...
                rel_x, rel_y = self.from_pos_to_rel_click(pos)

                if self.edition_mode == LineChartAnnotator.ModePointEdit:
                    # set new position for point being edited ...
                    self.tempo_line_values.set_point(self.tempo_point_index, rel_x, rel_y)
                    # go back to previous mode
                    self.update_points_list()
                    self.set_editor_mode(LineChartAnnotator.ModeLineEdit)
                elif self.edition_mode == LineChartAnnotator.ModePointAdd:
                    # Add the new point
                    self.tempo_line_values.add_point(rel_x, rel_y, LineValues.InsertByXValue)
                    # .. and stay on current state until cancel is pressed.

                self.update_current_view()

    def prepare_number_controls(self):
        n_lines = self.data.total_lines()
        self.lbl_number_title.set_text("Lines in Chart: {0:d}".format(n_lines))

        self.fill_data_series_list(self.lbx_number_series_values)

    def fill_data_series_list(self, text_list):
        text_list.clear_options()
        for idx, current_text in enumerate(self.data.data_series):
            if current_text is None:
                display_value = str(idx + 1)
            else:
                display_value = "{0:d}: {1:s}".format(idx + 1, current_text.value)

            text_list.add_option(str(idx), display_value)

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_annotation_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeNavigate)

        # edit modes ...
        self.container_number_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeNumberEdit)
        self.container_data_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeLineSelect)
        self.container_line_buttons.visible = (self.edition_mode == LineChartAnnotator.ModeLineEdit)

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
            self.lbl_confirm_message.set_text("Click on New Position")
        elif self.edition_mode == LineChartAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Line Data?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode not in [LineChartAnnotator.ModePointAdd,
                                                                    LineChartAnnotator.ModePointEdit]

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
        if self.lbx_line_points.selected_option_value is None:
            print("Must select a data point from list")
            return

        self.tempo_point_index = int(self.lbx_line_points.selected_option_value)
        self.set_editor_mode(LineChartAnnotator.ModePointEdit)

    def delete_tempo_line_point(self, del_idx):
        if self.tempo_line_values.remove_point(del_idx):
            # update GUI
            self.update_points_list()
            self.update_current_view()

    def btn_line_point_delete_click(self, button):
        if self.lbx_line_points.selected_option_value is None:
            print("Must select a data point from list")
            return

        # try delete
        del_idx = int(self.lbx_line_points.selected_option_value)
        self.delete_tempo_line_point(del_idx)

    def btn_line_point_add_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModePointAdd)

    def btn_line_return_accept_click(self, button):
        self.data.lines[self.tempo_line_index] = LineValues.Copy(self.tempo_line_values)
        self.data_changed = True

        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)
        self.update_current_view()

    def btn_line_return_cancel_click(self, button):
        self.set_editor_mode(LineChartAnnotator.ModeLineSelect)
        self.update_current_view(False)

    def lbx_line_points_value_changed(self, new_value, old_value):
        self.update_current_view(False)

    def img_mouse_double_click(self, img, position, button):
        if self.edition_mode == LineChartAnnotator.ModeLineEdit:
            # click relative position
            rel_x, rel_y = self.from_pos_to_rel_click(position)

            # find closest point ...
            distance, point_idx = self.tempo_line_values.closest_point(rel_x, rel_y)

            if button == 1:
                # left click
                if point_idx is not None and distance < LineChartAnnotator.DoubleClickMaxPointDistance:
                    # ... edit...
                    self.tempo_point_index = point_idx
                    self.set_editor_mode(LineChartAnnotator.ModePointEdit)
                else:
                    # ... add point ...
                    self.tempo_line_values.add_point(rel_x, rel_y, LineValues.InsertByXValue)
                    # update GUI
                    self.update_points_list()

                self.update_current_view(False)
            else:
                # right click ... delete ...
                if distance < LineChartAnnotator.DoubleClickMaxPointDistance:
                    self.delete_tempo_line_point(point_idx)

