
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

from ChartInfo.data.scatter_values import ScatterValues
from ChartInfo.data.scatter_data import ScatterData

class ScatterChartAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeNumberEdit = 1
    ModeSeriesSelect = 2
    ModeSeriesEdit = 3
    ModePointAdd = 4
    ModePointEdit = 5
    ModeConfirmNumberOverwrite = 6
    ModeConfirmExit = 7

    DoubleClickMaxPointDistance = 5

    CrossHairs_0_90_180_270 = 0
    CrossHairs_45_135_225_315 = 1
    CrossHairs_30_150_270 = 2
    CrossHairs_90_210_330 = 3

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Scatter Chart Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.data is None:
            # create default Line chart data ...
            self.data = ScatterData.CreateDefault(self.panel_info)
            self.data_changed = True
        else:
            # make a copy ...
            self.data = ScatterData.Copy(self.panel_info.data)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (30, 125, 150)
        self.text_color = (255, 255, 255)

        self.mark_size = 50
        self.crosshairs_type = ScatterChartAnnotator.CrossHairs_0_90_180_270

        self.cc_num_labels = 0
        self.cc_labels = None
        self.cc_stats = None
        self.cc_centroids = None
        self.cc_zoom_size = 10
        self.cc_hover_idx = 0
        self.precompute_connected_components()
        self.padded_base_rgb_image = np.zeros((self.base_rgb_image.shape[0] + self.cc_zoom_size * 2,
                                               self.base_rgb_image.shape[1] + self.cc_zoom_size * 2, 3), np.uint8)
        self.padded_base_rgb_image[self.cc_zoom_size:-self.cc_zoom_size, self.cc_zoom_size:-self.cc_zoom_size] = self.base_rgb_image.copy()

        self.elements.back_color = self.general_background
        self.edition_mode = None

        self.tempo_scatter_index = None
        self.tempo_point_index = None
        self.tempo_scatter_values = None
        self.tempo_canvas_name = None

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
        self.btn_data_return = None

        self.container_scatter_buttons = None
        self.lbl_scatter_title = None
        self.lbl_scatter_cross_hairs = None
        self.img_scatter_cross_hairs_0_90_180_270 = None
        self.img_scatter_cross_hairs_45_135_225_315 = None
        self.img_scatter_cross_hairs_30_150_270 = None
        self.img_scatter_cross_hairs_90_210_330 = None
        self.lbl_scatter_name = None
        self.lbx_scatter_points = None
        self.btn_scatter_point_edit = None
        self.btn_scatter_point_delete = None
        self.btn_scatter_point_add = None
        self.btn_scatter_return_accept = None
        self.btn_scatter_return_cancel = None

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
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Scatter Chart Data Annotation", 28)
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
        darker_background = (15, 60, 75)

        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 180),
                                                            back_color=darker_background)
        self.container_annotation_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Scatter Chart Annotation Options", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        self.btn_edit_number = ScreenButton("btn_edit_number", "Edit Number of Series", 21, button_width)
        self.btn_edit_number.set_colors(button_text_color, button_back_color)
        self.btn_edit_number.position = (button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_number.click_callback = self.btn_edit_number_click
        self.container_annotation_buttons.append(self.btn_edit_number)

        self.btn_edit_data = ScreenButton("btn_edit_data", "Edit Scatter Data", 21, button_width)
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

        self.lbl_number_title = ScreenLabel("lbl_number_title ", "Series in Chart: [0]", 25, 290, 1)
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

        self.lbl_data_title = ScreenLabel("lbl_data_title ", "Series in Chart", 25, 290, 1)
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
        self.container_scatter_buttons = ScreenContainer("container_scatter_buttons", (container_width, 550),
                                                         back_color=darker_background)
        self.container_scatter_buttons.position = (self.container_view_buttons.get_left(),
                                                   self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_scatter_buttons)

        self.lbl_scatter_title = ScreenLabel("lbl_scatter_title", "Points in Scatter", 25, 290, 1)
        self.lbl_scatter_title.position = (5, 5)
        self.lbl_scatter_title.set_background(darker_background)
        self.lbl_scatter_title.set_color(self.text_color)
        self.container_scatter_buttons.append(self.lbl_scatter_title)

        self.lbl_scatter_cross_hairs = ScreenLabel("lbl_scatter_cross_hairs", "Available Crosshairs", 18, 290, 1)
        self.lbl_scatter_cross_hairs.position = (5, self.lbl_scatter_title.get_bottom() + 20)
        self.lbl_scatter_cross_hairs.set_background(darker_background)
        self.lbl_scatter_cross_hairs.set_color(self.text_color)
        self.container_scatter_buttons.append(self.lbl_scatter_cross_hairs)

        cross_hair_size = 61

        tempo_blank = np.zeros((cross_hair_size, cross_hair_size, 3), np.uint8)
        tempo_blank[:, :, :] = 255

        angles = self.get_crosshair_angles(ScatterChartAnnotator.CrossHairs_0_90_180_270)
        cross_hair_img = self.create_cross_hairs_image(cross_hair_size, angles, (255, 0, 0), (255, 255, 255))
        self.img_scatter_cross_hairs_0_90_180_270 = ScreenImage("img_scatter_cross_hairs_0_90_180_270", cross_hair_img,
                                                                0, 0, True, cv2.INTER_NEAREST)
        self.img_scatter_cross_hairs_0_90_180_270.position = (int(container_width * (3 / 18) - cross_hair_size / 2),
                                                              self.lbl_scatter_cross_hairs.get_bottom() + 10)
        self.img_scatter_cross_hairs_0_90_180_270.mouse_button_down_callback = self.img_scatter_cross_hairs_mouse_button_down
        self.container_scatter_buttons.append(self.img_scatter_cross_hairs_0_90_180_270)

        angles = self.get_crosshair_angles(ScatterChartAnnotator.CrossHairs_45_135_225_315)
        cross_hair_img = self.create_cross_hairs_image(cross_hair_size, angles, (255, 0, 0), (255, 255, 255))
        self.img_scatter_cross_hairs_45_135_225_315 = ScreenImage("img_scatter_cross_hairs_45_135_225_315",
                                                                  cross_hair_img, 0, 0, True, cv2.INTER_NEAREST)
        self.img_scatter_cross_hairs_45_135_225_315.position = (int(container_width * (7 / 18) - cross_hair_size / 2),
                                                                self.lbl_scatter_cross_hairs.get_bottom() + 10)
        self.img_scatter_cross_hairs_45_135_225_315.mouse_button_down_callback = self.img_scatter_cross_hairs_mouse_button_down
        self.container_scatter_buttons.append(self.img_scatter_cross_hairs_45_135_225_315)

        angles = self.get_crosshair_angles(ScatterChartAnnotator.CrossHairs_30_150_270)
        cross_hair_img = self.create_cross_hairs_image(cross_hair_size, angles, (255, 0, 0), (255, 255, 255))
        self.img_scatter_cross_hairs_30_150_270 = ScreenImage("img_scatter_cross_hairs_30_150_270", cross_hair_img,
                                                              0, 0, True, cv2.INTER_NEAREST)
        self.img_scatter_cross_hairs_30_150_270.position = (int(container_width * (11 / 18) - cross_hair_size / 2),
                                                            self.lbl_scatter_cross_hairs.get_bottom() + 10)
        self.img_scatter_cross_hairs_30_150_270.mouse_button_down_callback = self.img_scatter_cross_hairs_mouse_button_down
        self.container_scatter_buttons.append(self.img_scatter_cross_hairs_30_150_270)

        angles = self.get_crosshair_angles(ScatterChartAnnotator.CrossHairs_90_210_330)
        cross_hair_img = self.create_cross_hairs_image(cross_hair_size, angles, (255, 0, 0), (255, 255, 255))
        self.img_scatter_cross_hairs_90_210_330 = ScreenImage("img_scatter_cross_hairs_90_210_330", cross_hair_img,
                                                              0, 0, True, cv2.INTER_NEAREST)
        self.img_scatter_cross_hairs_90_210_330.position = (int(container_width * (15 / 18) - cross_hair_size / 2),
                                                            self.lbl_scatter_cross_hairs.get_bottom() + 10)
        self.img_scatter_cross_hairs_90_210_330.mouse_button_down_callback = self.img_scatter_cross_hairs_mouse_button_down
        self.container_scatter_buttons.append(self.img_scatter_cross_hairs_90_210_330)

        self.lbl_scatter_name = ScreenLabel("lbl_scatter_name", "[Data series]", 18, 290, 1)
        self.lbl_scatter_name.position = (5, self.img_scatter_cross_hairs_0_90_180_270.get_bottom() + 20)
        self.lbl_scatter_name.set_background(darker_background)
        self.lbl_scatter_name.set_color(self.text_color)
        self.container_scatter_buttons.append(self.lbl_scatter_name)

        self.lbx_scatter_points = ScreenTextlist("lbx_scatter_points", (container_width - 20, 210), 18,
                                                 back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                 selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_scatter_points.position = (10, self.lbl_scatter_name.get_bottom() + 30)
        self.lbx_scatter_points.selected_value_change_callback = self.lbx_scatter_points_value_changed
        self.container_scatter_buttons.append(self.lbx_scatter_points)

        self.btn_scatter_point_add = ScreenButton("btn_scatter_point_add", "Add Points", 21, button_2_width)
        self.btn_scatter_point_add.set_colors(button_text_color, button_back_color)
        self.btn_scatter_point_add.position = (button_2_left, self.lbx_scatter_points.get_bottom() + 10)
        self.btn_scatter_point_add.click_callback = self.btn_scatter_point_add_click
        self.container_scatter_buttons.append(self.btn_scatter_point_add)

        self.btn_scatter_point_edit = ScreenButton("btn_scatter_point_edit", "Edit Points", 21, button_2_width)
        self.btn_scatter_point_edit.set_colors(button_text_color, button_back_color)
        self.btn_scatter_point_edit.position = (button_2_right, self.lbx_scatter_points.get_bottom() + 10)
        self.btn_scatter_point_edit.click_callback = self.btn_scatter_point_edit_click
        self.container_scatter_buttons.append(self.btn_scatter_point_edit)

        self.btn_scatter_point_delete = ScreenButton("btn_scatter_point_delete", "Remove Point", 21, button_width)
        self.btn_scatter_point_delete.set_colors(button_text_color, button_back_color)
        self.btn_scatter_point_delete.position = (button_left, self.btn_scatter_point_add.get_bottom() + 10)
        self.btn_scatter_point_delete.click_callback = self.btn_scatter_point_delete_click
        self.container_scatter_buttons.append(self.btn_scatter_point_delete)

        self.btn_scatter_return_accept = ScreenButton("btn_scatter_return_accept", "Accept", 21, button_2_width)
        self.btn_scatter_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_scatter_return_accept.position = (button_2_left, self.btn_scatter_point_delete.get_bottom() + 20)
        self.btn_scatter_return_accept.click_callback = self.btn_scatter_return_accept_click
        self.container_scatter_buttons.append(self.btn_scatter_return_accept)

        self.btn_scatter_return_cancel = ScreenButton("btn_scatter_return_cancel", "Cancel", 21, button_2_width)
        self.btn_scatter_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_scatter_return_cancel.position = (button_2_right, self.btn_scatter_point_delete.get_bottom() + 20)
        self.btn_scatter_return_cancel.click_callback = self.btn_scatter_return_cancel_click
        self.container_scatter_buttons.append(self.btn_scatter_return_cancel)

        self.container_scatter_buttons.visible = False

        # ======================================
        # visuals
        # ===========================

        self.img_main.mouse_motion_callback = self.img_main_mouse_motion

        click_mark_points = np.array([[0, self.mark_size], [self.mark_size * 2, self.mark_size],
                                      [self.mark_size, self.mark_size], [self.mark_size, 0],
                                      [self.mark_size, self.mark_size * 2]], dtype=np.float64)
        self.canvas_select.add_polyline_element("click_mark", click_mark_points)
        self.canvas_select.elements["click_mark"].visible = False

        # -----------
        # ... preview of right click on add mode  ...
        self.container_preview_buttons = ScreenContainer("container_preview_buttons", (container_width, 180),
                                                         back_color=darker_background)
        self.container_preview_buttons.position = (self.container_confirm_buttons.get_left(),
                                                   self.container_confirm_buttons.get_bottom() + 20)
        self.elements.append(self.container_preview_buttons)
        self.container_preview_buttons.visible = False

        self.lbl_preview_title = ScreenLabel("lbl_preview_title", "Right Click to add this Point", 25, 290, 1)
        self.lbl_preview_title.position = (5, 5)
        self.lbl_preview_title.set_background(darker_background)
        self.lbl_preview_title.set_color(self.text_color)
        self.container_preview_buttons.append(self.lbl_preview_title)

        tempo_blank = np.zeros((105, 105, 3), np.uint8)
        tempo_blank[:, :, :] = 255
        self.img_preview = ScreenImage("img_preview", tempo_blank, 105, 105, True, cv2.INTER_NEAREST)
        self.img_preview.position = (int(container_width / 2 - 50), self.lbl_preview_title.get_bottom() + 20)
        self.container_preview_buttons.append(self.img_preview)

        self.prepare_number_controls()

        self.set_editor_mode(ScatterChartAnnotator.ModeNavigate)

    def precompute_connected_components(self):
        otsu_t, binarized = cv2.threshold(self.base_gray_image[:, :, 0], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv_binarized = 255 - binarized

        # get the CC on the raw binary
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binarized)
        # get the CC on the inverted binary
        inv_num_labels, inv_labels, inv_stats, inv_centroids = cv2.connectedComponentsWithStats(inv_binarized)

        self.cc_num_labels = num_labels + inv_num_labels
        self.cc_labels = labels
        self.cc_labels[inv_labels > 0] = inv_labels[inv_labels > 0] + num_labels
        self.cc_stats = np.vstack([stats, inv_stats])
        self.cc_centroids = np.vstack([centroids, inv_centroids])

    def get_crosshair_angles(self, crosshair_type):
        if crosshair_type == ScatterChartAnnotator.CrossHairs_0_90_180_270:
            return [0, np.pi / 2.0, np.pi, np.pi * 3 / 2.0]
        elif crosshair_type == ScatterChartAnnotator.CrossHairs_45_135_225_315:
            return [np.pi / 4.0, np.pi * 3.0 / 4.0, np.pi * 5.0 / 4.0, np.pi * 7.0 / 4.0]
        elif crosshair_type == ScatterChartAnnotator.CrossHairs_30_150_270:
            return [np.pi * 1.0 / 6.0, np.pi * 5.0 / 6.0, np.pi * 3.0 / 2.0]
        elif crosshair_type == ScatterChartAnnotator.CrossHairs_90_210_330:
            return [np.pi / 2.0, np.pi * 7.0 / 6.0, np.pi * 11.0 / 6.0]

        return []

    def create_cross_hairs_image(self, size, angles, main_color, bg_color):
        image = np.zeros((size, size, 3), dtype=np.uint8) * 255
        image[:, :] = bg_color
        radius = int(size / 2)

        # assume angle is on radians
        for angle in angles:
            p1 = (radius, radius)
            p2 = (radius + int(np.cos(angle) * radius), radius -int(np.sin(angle) * radius))

            cv2.line(image, p1, p2, main_color)

        return image

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
        if self.edition_mode in [ScatterChartAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(ScatterChartAnnotator.ModeNavigate)
        elif self.edition_mode in [ScatterChartAnnotator.ModePointAdd]:
            # return to series edition mode ...
            self.update_points_list()
            self.set_editor_mode(ScatterChartAnnotator.ModeSeriesEdit)
        elif self.edition_mode in [ScatterChartAnnotator.ModePointEdit]:
            # copy data from Canvas to the structure ....
            canvas_points = self.canvas_display.elements[self.tempo_canvas_name].points
            # print(self.tempo_scatter_values.points)
            for point_idx, (px, py) in enumerate(canvas_points):
                # like clicks, canvas uses visual position,
                # convert coordinates from the canvas to image coordinate
                # using the same function used the mouse clicks
                rel_x, rel_y = self.from_pos_to_rel_click((px, py))
                # set new position for this point ...
                self.tempo_scatter_values.set_point(point_idx, rel_x, rel_y)
            # print(self.tempo_scatter_values.points)
            # lock the canvas ...
            self.canvas_display.locked = True
            # return to series edition mode ...
            self.update_points_list()
            self.set_editor_mode(ScatterChartAnnotator.ModeSeriesEdit)
        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == ScatterChartAnnotator.ModeConfirmExit:
            print("-> Changes made to Scatter Data Annotations were lost")
            self.return_screen = self.parent_screen
        else:
            raise Exception("Not Implemented")

    def btn_edit_number_click(self, button):
        self.set_editor_mode(ScatterChartAnnotator.ModeNumberEdit)
        self.update_current_view()

    def btn_edit_data_click(self, button):
        self.fill_data_series_list(self.lbx_data_series_values)
        self.set_editor_mode(ScatterChartAnnotator.ModeSeriesSelect)
        self.update_current_view()

    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing Line data ...
            self.panel_info.data = ScatterData.Copy(self.data)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(ScatterChartAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen

    def numbers_update_GUI(self, data_series_changed):
        n_series = self.data.total_series()
        self.lbl_number_title.set_text("Series in Chart: {0:d}".format(n_series))

        if data_series_changed:
            self.fill_data_series_list(self.lbx_number_series_values)

        self.create_canvas_point_sets()
        self.update_current_view()

    def btn_number_series_add_click(self, button):
        # add ...
        self.data.add_data_series()

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

    def btn_number_return_click(self, button):
        self.set_editor_mode(ScatterChartAnnotator.ModeNavigate)
        self.update_current_view()

    def from_pos_to_rel_click(self, pos):
        # click pos ...
        click_x, click_y = pos
        click_x /= self.view_scale
        click_y /= self.view_scale

        x1, y1, x2, y2 = self.panel_info.axes.bounding_box
        # x1 = int(x1)
        # y2 = int(y2)
        # print((x1, x2))

        rel_x = click_x - x1
        rel_y = y2 - click_y

        return rel_x, rel_y

    def img_main_mouse_button_down(self, img_object, pos, button):
        if self.edition_mode == ScatterChartAnnotator.ModePointAdd and button in [1, 3]:
            # Add the new point
            if button == 1:
                # click pos ...
                rel_x, rel_y = self.from_pos_to_rel_click(pos)
            elif button == 3 and self.cc_hover_idx is not None:
                # use hover CC location instead of actual click location
                rel_x, rel_y = self.cc_centroids[self.cc_hover_idx]
                x1, y1, x2, y2 = self.panel_info.axes.bounding_box
                rel_x = rel_x - x1
                rel_y = y2 - rel_y
            else:
                return

            # exact click location
            self.tempo_scatter_values.add_point(rel_x, rel_y)
            # update canvas ....
            ps_points = self.scatter_points_to_canvas_points(self.tempo_scatter_values.points)
            self.canvas_display.update_point_set_element(self.tempo_canvas_name, ps_points, True)
            # .. and stay on current state until cancel is pressed.

        self.update_current_view()

    def prepare_number_controls(self):
        n_series = self.data.total_series()
        self.lbl_number_title.set_text("Series in Chart: {0:d}".format(n_series))

        self.fill_data_series_list(self.lbx_number_series_values)
        self.create_canvas_point_sets()

    def create_canvas_point_sets(self):
        self.canvas_display.clear()

        for idx, scatter_values in enumerate(self.data.scatter_values):
            # line_color = self.canvas_display.colors[idx % len(self.canvas_display.colors)]
            all_transformed_points = self.scatter_points_to_canvas_points(scatter_values.points)
            self.canvas_display.add_point_set_element("scatter_" + str(idx), all_transformed_points)

    def scatter_points_to_canvas_points(self, point_set):
        x1, y1, x2, y2 = self.panel_info.axes.bounding_box

        all_transformed_points = []
        for p_idx in range(len(point_set)):
            # transform current point from relative space to absolute pixel space (simple translation)
            c_x, c_y = point_set[p_idx]
            c_x += x1
            c_y = y2 - c_y
            current_point = (c_x, c_y)

            all_transformed_points.append(current_point)

        # now ... to numpy array ...
        all_transformed_points = np.array(all_transformed_points, np.float64)
        # apply current view scale ...
        all_transformed_points *= self.view_scale

        return all_transformed_points

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
        self.container_annotation_buttons.visible = (self.edition_mode == ScatterChartAnnotator.ModeNavigate)

        # edit modes ...
        self.container_number_buttons.visible = (self.edition_mode == ScatterChartAnnotator.ModeNumberEdit)
        self.container_data_buttons.visible = (self.edition_mode == ScatterChartAnnotator.ModeSeriesSelect)
        self.container_scatter_buttons.visible = (self.edition_mode == ScatterChartAnnotator.ModeSeriesEdit)
        self.container_preview_buttons.visible = (self.edition_mode == ScatterChartAnnotator.ModePointAdd)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ScatterChartAnnotator.ModeConfirmNumberOverwrite,
                                                                       ScatterChartAnnotator.ModePointAdd,
                                                                       ScatterChartAnnotator.ModePointEdit,
                                                                       ScatterChartAnnotator.ModeConfirmExit]

        if self.edition_mode == ScatterChartAnnotator.ModeConfirmNumberOverwrite:
            self.lbl_confirm_message.set_text("Discard Existing Series Data?")
        elif self.edition_mode == ScatterChartAnnotator.ModePointAdd:
            self.lbl_confirm_message.set_text("Click on New Point")
        elif self.edition_mode == ScatterChartAnnotator.ModePointEdit:
            self.lbl_confirm_message.set_text("Drag Points")
        elif self.edition_mode == ScatterChartAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Scatter Data?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode not in [ScatterChartAnnotator.ModePointAdd,
                                                                    ScatterChartAnnotator.ModePointEdit]

    def btn_data_series_edit_click(self, button):
        if self.lbx_data_series_values.selected_option_value is None:
            print("Must select a data series")
            return

        option_idx = int(self.lbx_data_series_values.selected_option_value)

        # prepare temporals
        self.tempo_scatter_index = option_idx
        self.tempo_scatter_values = ScatterValues.Copy(self.data.scatter_values[option_idx])

        # series name ...
        display = self.lbx_data_series_values.option_display[self.lbx_data_series_values.selected_option_value]
        self.lbl_scatter_name.set_text(display)

        # ... list of points ...
        self.update_points_list()

        # canvas
        self.canvas_show_hide_scatters(option_idx)
        self.canvas_display.locked = True

        self.set_editor_mode(ScatterChartAnnotator.ModeSeriesEdit)
        self.update_current_view(False)

    def canvas_show_hide_scatters(self, show_index):
        self.canvas_display.change_selected_element(None)
        self.tempo_canvas_name = None
        for element_name in self.canvas_display.elements:
            scatter_idx = int(element_name.split("_")[1])
            self.canvas_display.elements[element_name].visible = (show_index < 0 or show_index == scatter_idx)
            if show_index == scatter_idx:
                self.tempo_canvas_name = element_name
                self.canvas_display.change_selected_element(element_name)

    def btn_data_return_click(self, button):
        self.set_editor_mode(ScatterChartAnnotator.ModeNavigate)

    def update_points_list(self):
        self.lbx_scatter_points.clear_options()
        for idx, (p_x, p_y) in enumerate(self.tempo_scatter_values.points):
            display_value = "{0:d}: ({1:.1f}, {2:.1f})".format(idx + 1, p_x, p_y)

            self.lbx_scatter_points.add_option(str(idx), display_value)

    def btn_scatter_point_edit_click(self, button):
        # self.tempo_point_index = int(self.lbx_scatter_points.selected_option_value)
        self.canvas_display.locked = False
        self.set_editor_mode(ScatterChartAnnotator.ModePointEdit)

    def delete_tempo_scatter_point(self, del_idx):
        if self.tempo_scatter_values.remove_point(del_idx):
            # update GUI
            # ... canvas ...
            ps_points = self.scatter_points_to_canvas_points(self.tempo_scatter_values.points)
            self.canvas_display.update_point_set_element(self.tempo_canvas_name, ps_points, True)
            # ... list and view
            self.update_points_list()
            self.update_current_view()

    def btn_scatter_point_delete_click(self, button):
        if self.lbx_scatter_points.selected_option_value is None:
            print("Must select a data point from list")
            return

        # try delete
        del_idx = int(self.lbx_scatter_points.selected_option_value)
        self.delete_tempo_scatter_point(del_idx)

    def btn_scatter_point_add_click(self, button):
        self.set_editor_mode(ScatterChartAnnotator.ModePointAdd)

    def btn_scatter_return_accept_click(self, button):
        self.data.scatter_values[self.tempo_scatter_index] = ScatterValues.Copy(self.tempo_scatter_values)
        self.data_changed = True

        # all scatters must be displayed ... and nothing should be selected
        self.canvas_show_hide_scatters(-1)
        self.set_editor_mode(ScatterChartAnnotator.ModeSeriesSelect)
        self.update_current_view()

    def btn_scatter_return_cancel_click(self, button):
        # restore the scatter on the canvas to its previous  state
        ps_points = self.scatter_points_to_canvas_points(self.data.scatter_values[self.tempo_scatter_index].points)
        self.canvas_display.update_point_set_element(self.tempo_canvas_name, ps_points, True)
        # all scatters must be displayed ... and nothing should be selected on the canvas
        self.canvas_show_hide_scatters(-1)

        self.set_editor_mode(ScatterChartAnnotator.ModeSeriesSelect)
        self.update_current_view(False)

    def lbx_scatter_points_value_changed(self, new_value, old_value):
        pass
        # self.update_current_view(False)

    def img_main_mouse_double_click(self, img, position, button):
        if self.edition_mode == ScatterChartAnnotator.ModeSeriesEdit:
            # click relative position
            rel_x, rel_y = self.from_pos_to_rel_click(position)

            # find closest point ...
            distance, point_idx = self.tempo_scatter_values.closest_point(rel_x, rel_y)

            if button == 1:
                # left click
                if point_idx is not None and distance < ScatterChartAnnotator.DoubleClickMaxPointDistance:
                    # ... edit...
                    self.canvas_display.locked = False
                    self.set_editor_mode(ScatterChartAnnotator.ModePointEdit)
                else:
                    # ... add point ...
                    self.tempo_scatter_values.add_point(rel_x, rel_y)
                    # update GUI
                    # ... canvas ....
                    ps_points = self.scatter_points_to_canvas_points(self.tempo_scatter_values.points)
                    self.canvas_display.update_point_set_element(self.tempo_canvas_name, ps_points, True)
                    # ... list of points ...
                    self.update_points_list()

                self.update_current_view(False)
            else:
                # right click ... delete ...
                if distance < ScatterChartAnnotator.DoubleClickMaxPointDistance:
                    self.delete_tempo_scatter_point(point_idx)

    def img_main_mouse_motion(self, screen_img, pos, rel, buttons):
        if self.edition_mode in [ScatterChartAnnotator.ModeSeriesEdit, ScatterChartAnnotator.ModePointAdd]:
            mouse_x, mouse_y = pos
            img_x = int(mouse_x / self.view_scale)
            img_y = int(mouse_y / self.view_scale)

            angles = self.get_crosshair_angles(self.crosshairs_type)
            main_points = [(mouse_x + np.cos(angle) * self.mark_size,
                            mouse_y - np.sin(angle) * self.mark_size) for angle in angles]

            if self.crosshairs_type in [ScatterChartAnnotator.CrossHairs_30_150_270,
                                        ScatterChartAnnotator.CrossHairs_90_210_330]:
                # 3 lines: (Y) or inverted Y
                click_mark_points = np.array([main_points[0], [mouse_x, mouse_y],
                                              main_points[1], [mouse_x, mouse_y],
                                              main_points[2]])
            else:
                # default ... two lines with point in the center: (+) or (x)
                click_mark_points = np.array([main_points[0], main_points[2], [mouse_x, mouse_y],
                                              main_points[1], main_points[3]])

            self.canvas_select.update_polyline_element("click_mark", click_mark_points, True)

            if self.edition_mode == ScatterChartAnnotator.ModePointAdd:
                valid_cc = True
                if (img_y < 0 or img_y >= self.cc_labels.shape[0]) or (img_x < 0 or img_x >= self.cc_labels.shape[1]):
                    valid_cc = False
                else:
                    cc_idx = self.cc_labels[img_y, img_x]
                    cc_center_x, cc_center_y = self.cc_centroids[cc_idx]

                    # print((self.cc_stats[cc_idx, cv2.CC_STAT_AREA], np.power(self.cc_zoom_size * 4, 2)))
                    if self.cc_stats[cc_idx, cv2.CC_STAT_AREA] < np.power(self.cc_zoom_size * 4, 2):
                        cut_min_x = int(cc_center_x)
                        cut_max_x = int(cc_center_x + self.cc_zoom_size * 2 + 1)
                        cut_min_y = int(cc_center_y)
                        cut_max_y =int(cc_center_y + self.cc_zoom_size * 2 + 1)
                        zoom_cut = self.padded_base_rgb_image[cut_min_y:cut_max_y, cut_min_x:cut_max_x].copy()

                        zoom_cut[self.cc_zoom_size, :] = (255, 0, 0)
                        zoom_cut[:, self.cc_zoom_size] = (255, 0, 0)

                        self.cc_hover_idx = cc_idx
                    else:
                        valid_cc = False

                if not valid_cc:
                    zoom_cut = np.zeros((self.cc_zoom_size * 2 + 1, self.cc_zoom_size * 2 + 1, 3), dtype=np.uint8)
                    self.cc_hover_idx = None

                preview_size = (self.cc_zoom_size * 2 + 1) * 5
                self.img_preview.set_image(zoom_cut, preview_size, preview_size)

                # print("---")
                # self.img_preview
                # print(self.cc_labels[img_y, img_x])
                # print(self.cc_centroids[self.cc_labels[img_y, img_x]])
        else:
            self.canvas_select.elements["click_mark"].visible = False

    def img_scatter_cross_hairs_mouse_button_down(self, img_object, pos, button):
        if img_object.name == "img_scatter_cross_hairs_0_90_180_270":
            self.crosshairs_type = ScatterChartAnnotator.CrossHairs_0_90_180_270
        elif img_object.name == "img_scatter_cross_hairs_45_135_225_315":
            self.crosshairs_type = ScatterChartAnnotator.CrossHairs_45_135_225_315
        elif img_object.name == "img_scatter_cross_hairs_30_150_270":
            self.crosshairs_type = ScatterChartAnnotator.CrossHairs_30_150_270
        elif img_object.name == "img_scatter_cross_hairs_90_210_330":
            self.crosshairs_type = ScatterChartAnnotator.CrossHairs_90_210_330
