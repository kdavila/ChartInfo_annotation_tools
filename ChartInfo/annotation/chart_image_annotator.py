
import os
import time

import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.data.image_info import ImageInfo
from ChartInfo.data.chart_info import ChartInfo
from ChartInfo.data.panel_tree import PanelTree

from ChartInfo.annotation.chart_text_annotator import ChartTextAnnotator
from ChartInfo.annotation.chart_legend_annotator import ChartLegendAnnotator
from ChartInfo.annotation.chart_axes_annotator import ChartAxesAnnotator

from ChartInfo.annotation.bar_chart_annotator import BarChartAnnotator
from ChartInfo.annotation.box_chart_annotator import BoxChartAnnotator
from ChartInfo.annotation.line_chart_annotator import LineChartAnnotator
from ChartInfo.annotation.scatter_chart_annotator import ScatterChartAnnotator

from ChartInfo.util.time_stats import TimeStats


class ChartImageAnnotator(Screen):
    ModeNavigate = 0
    ModeEditPanels = 1
    ModeSelectPanelSplit = 2
    ModeConfirmOverwritePanels = 3
    ModeEditClass = 4
    ModeConfirmOverwriteClass = 5
    ModeConfirmExit = 6

    ViewModeRawData = 0
    ViewModeGrayData = 1
    ViewModeRawNoData = 2
    ViewModeGrayNoData = 3

    SplitOperationXSplit = 0
    SplitOperationYSplit = 1
    SplitOperationMerge = 2

    WaitModeNone = 0
    WaitModeText = 1
    WaitModeLegend = 2
    WaitModeAxes= 3
    WaitModeData = 4

    def __init__(self, size, chart_dir, annotation_dir, relative_path, parent_menu, admin_mode):
        Screen.__init__(self, "Chart Ground Truth Annotation Interface", size)

        self.general_background = (20, 85, 50)
        self.text_color = (255, 255, 255)

        self.parent = parent_menu
        self.chart_dir = chart_dir
        self.annotation_dir = annotation_dir
        self.relative_path = relative_path
        self.admin_mode = admin_mode

        self.time_stats = TimeStats()
        self.in_menu_time_start = time.time()
        self.wait_mode = ChartImageAnnotator.WaitModeNone

        # find output path ...
        relative_dir, img_filename = os.path.split(self.relative_path)
        img_base, ext = os.path.splitext(img_filename)
        # output dir
        self.output_dir = self.annotation_dir + relative_dir
        self.annotation_filename = self.output_dir + "/" + img_base + ".xml"

        # first ... load image ....
        self.current_image = cv2.imread(self.chart_dir + self.relative_path)
        self.current_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        # ... and cache the gray-scale version
        self.current_gray = np.zeros(self.current_image.shape, self.current_image.dtype)
        self.current_gray[:, :, 0] = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2GRAY)
        self.current_gray[:, :, 1] = self.current_gray[:, :, 0].copy()
        self.current_gray[:, :, 2] = self.current_gray[:, :, 0].copy()

        # load annotations for this image .... (if any)
        if os.path.exists(self.annotation_filename):
            # annotation found!
            self.image_info = ImageInfo.FromXML(self.annotation_filename, self.current_image)
        else:
            # create an empty annotation
            self.image_info = ImageInfo.CreateDefault(self.current_image)

        self.view_mode = ChartImageAnnotator.ViewModeRawData
        self.view_scale = 1.0
        self.split_panel_operation = None
        self.tempo_panel_tree = None
        self.selected_panel = 0
        self.unsaved_changes = False

        self.elements.back_color = self.general_background

        self.label_title = None
        self.container_confirm_buttons = None
        self.lbl_confirm_message = None
        self.btn_confirm_cancel = None
        self.btn_confirm_accept = None

        self.container_view_buttons = None
        self.lbl_zoom = None
        self.btn_zoom_reduce = None
        self.btn_zoom_increase = None
        self.btn_zoom_zero = None

        self.btn_view_raw_data = None
        self.btn_view_gray_data = None
        self.btn_view_raw_clear = None
        self.btn_view_gray_clear = None

        self.container_panels_buttons = None
        self.lbl_panels_title = None
        self.btn_label_panels = None
        self.btn_panels_verify = None
        self.lbl_panels_current = None
        self.btn_panels_prev = None
        self.btn_panels_next = None

        self.container_annotation_buttons = None
        self.lbl_edit_title = None
        self.btn_edit_class = None
        self.btn_edit_text = None
        self.btn_edit_legend = None
        self.btn_edit_axis = None
        self.btn_edit_data = None

        self.btn_verify_class = None
        self.btn_verify_text = None
        self.btn_verify_legend = None
        self.btn_verify_axis = None
        self.btn_verify_data = None

        self.container_split_panels = None
        self.lbl_split_panel_title = None
        self.btn_split_panel_horizontal = None
        self.btn_split_panel_vertical = None
        self.btn_merge_panel = None
        self.btn_split_return = None

        self.container_classify_panels = None
        self.lbl_class_panel_title = None
        self.lbx_class_panel_class = None
        self.btn_class_panel_continue = None

        self.btn_save = None
        self.btn_return = None

        self.container_images = None
        self.img_main = None

        # generate the interface!
        self.create_controllers()

        # get the view ...
        self.update_current_view(True)


    def create_controllers(self):
        # add elements....
        button_text_color = (35, 50, 20)
        button_back_color = (228, 228, 228)

        # Main Title
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - {0:s}".format(self.relative_path), 28)
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
        self.img_main.mouse_button_down_callback = self.img_main_mouse_button_down
        self.container_images.append(self.img_main)

        # panel for multi-panel figure options
        panel_buttons_bg = (10, 55, 25)
        self.container_panels_buttons = ScreenContainer("container_panels_buttons", (container_width, 160), back_color=panel_buttons_bg)
        self.container_panels_buttons.position = (self.container_view_buttons.get_left(), self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_panels_buttons)

        self.lbl_panels_title = ScreenLabel("lbl_panels_title", "Options for Multi-Panel Images", 21, 290, 1)
        self.lbl_panels_title.position = (5, 5)
        self.lbl_panels_title.set_background(panel_buttons_bg)
        self.lbl_panels_title.set_color(self.text_color)
        self.container_panels_buttons.append(self.lbl_panels_title)



        if self.admin_mode:
            self.btn_label_panels = ScreenButton("btn_label_panels", "Annotate", 21, button_2_width)
            self.btn_label_panels.position = (button_2_left, self.lbl_panels_title.get_bottom() + 10)

            self.btn_panels_verify = ScreenButton("btn_panels_verify", "Mark Verified", 21, button_2_width)
            self.btn_panels_verify.position = (button_2_right, self.lbl_panels_title.get_bottom() + 10)
            self.btn_panels_verify.set_colors(button_text_color, button_back_color)
            self.btn_panels_verify.click_callback = self.btn_panels_verify_click
            self.container_panels_buttons.append(self.btn_panels_verify)
        else:
            self.btn_label_panels = ScreenButton("btn_label_panels", "Annotate Panels", 21, button_width)
            self.btn_label_panels.position = (button_left, self.lbl_panels_title.get_bottom() + 10)

            self.btn_panels_verify = None

        self.btn_label_panels.set_colors(button_text_color, button_back_color)
        self.btn_label_panels.click_callback = self.btn_label_panels_click
        self.container_panels_buttons.append(self.btn_label_panels)

        self.lbl_panels_current = ScreenLabel("lbl_panels_title", "Current Panel: 1 / 1", 21, 290, 1)
        self.lbl_panels_current.position = (5, self.btn_label_panels.get_bottom() + 20)
        self.lbl_panels_current.set_background(panel_buttons_bg)
        self.lbl_panels_current.set_color(self.text_color)
        self.container_panels_buttons.append(self.lbl_panels_current)

        self.btn_panels_prev = ScreenButton("btn_panels_prev", "Previous", 21, 130)
        self.btn_panels_prev.set_colors(button_text_color, button_back_color)
        self.btn_panels_prev.position = (10, self.lbl_panels_current.get_bottom() + 10)
        self.btn_panels_prev.click_callback = self.btn_panels_prev_click
        self.container_panels_buttons.append(self.btn_panels_prev)

        self.btn_panels_next = ScreenButton("btn_panels_next", "Next", 21, 130)
        self.btn_panels_next.set_colors(button_text_color, button_back_color)
        self.btn_panels_next.position = (self.container_panels_buttons.width - self.btn_panels_next.width - 10,
                                            self.lbl_panels_current.get_bottom() + 10)
        self.btn_panels_next.click_callback = self.btn_panels_next_click
        self.container_panels_buttons.append(self.btn_panels_next)

        # =================================================

        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 380), back_color=panel_buttons_bg)
        self.container_annotation_buttons.position = (self.container_panels_buttons.get_left(), self.container_panels_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Options for Current Panel", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(panel_buttons_bg)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        if self.admin_mode:
            edit_button_left = button_2_left
            edit_button_width = 180
            verify_button_left = edit_button_left + edit_button_width + 10
            verify_button_width = 90
        else:
            edit_button_left = button_left
            edit_button_width = button_width
            verify_button_left = 0
            verify_button_width = 0

        self.btn_edit_class = ScreenButton("btn_edit_class", "Edit Classification", 21, edit_button_width)
        self.btn_edit_class.set_colors(button_text_color, button_back_color)
        self.btn_edit_class.position = (edit_button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_class.click_callback = self.btn_edit_class_click
        self.container_annotation_buttons.append(self.btn_edit_class)

        self.btn_edit_text = ScreenButton("btn_edit_text", "Edit Text", 21, edit_button_width)
        self.btn_edit_text.set_colors(button_text_color, button_back_color)
        self.btn_edit_text.position = (edit_button_left, self.btn_edit_class.get_bottom() + 10)
        self.btn_edit_text.click_callback = self.btn_edit_text_click
        self.container_annotation_buttons.append(self.btn_edit_text)

        self.btn_edit_legend = ScreenButton("btn_edit_legend", "Edit Legend", 21, edit_button_width)
        self.btn_edit_legend.set_colors(button_text_color, button_back_color)
        self.btn_edit_legend.position = (edit_button_left, self.btn_edit_text.get_bottom() + 10)
        self.btn_edit_legend.click_callback = self.btn_edit_legend_click
        self.container_annotation_buttons.append(self.btn_edit_legend)

        self.btn_edit_axis = ScreenButton("btn_edit_axis", "Edit Axis", 21, edit_button_width)
        self.btn_edit_axis.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis.position = (edit_button_left, self.btn_edit_legend.get_bottom() + 10)
        self.btn_edit_axis.click_callback = self.btn_edit_axis_click
        self.container_annotation_buttons.append(self.btn_edit_axis)

        self.btn_edit_data = ScreenButton("btn_edit_data", "Edit Data", 21, edit_button_width)
        self.btn_edit_data.set_colors(button_text_color, button_back_color)
        self.btn_edit_data.position = (edit_button_left, self.btn_edit_axis.get_bottom() + 10)
        self.btn_edit_data.click_callback = self.btn_edit_data_click
        self.container_annotation_buttons.append(self.btn_edit_data)

        self.btn_save = ScreenButton("btn_save", "Save", 21, button_width)
        self.btn_save.set_colors(button_text_color, button_back_color)
        self.btn_save.position = (button_left, self.btn_edit_data.get_bottom() + 30)
        self.btn_save.click_callback = self.btn_save_click
        self.container_annotation_buttons.append(self.btn_save)

        self.btn_return = ScreenButton("btn_return", "Return", 21, button_width)
        self.btn_return.set_colors(button_text_color, button_back_color)
        self.btn_return.position = (button_left, self.container_annotation_buttons.height - self.btn_return.height - 10)
        self.btn_return.click_callback = self.btn_return_click
        self.container_annotation_buttons.append(self.btn_return)

        if self.admin_mode:
            self.btn_verify_class = ScreenButton("btn_verify_class", "Verified", 21, verify_button_width)
            self.btn_verify_class.set_colors(button_text_color, button_back_color)
            self.btn_verify_class.position = (verify_button_left, self.btn_edit_class.get_top())
            self.btn_verify_class.click_callback = self.btn_verify_class_click
            self.container_annotation_buttons.append(self.btn_verify_class)

            self.btn_verify_text = ScreenButton("btn_verify_text", "Verified", 21, verify_button_width)
            self.btn_verify_text.set_colors(button_text_color, button_back_color)
            self.btn_verify_text.position = (verify_button_left, self.btn_edit_text.get_top())
            self.btn_verify_text.click_callback = self.btn_verify_text_click
            self.container_annotation_buttons.append(self.btn_verify_text)

            self.btn_verify_legend = ScreenButton("btn_verify_legend", "Verified", 21, verify_button_width)
            self.btn_verify_legend.set_colors(button_text_color, button_back_color)
            self.btn_verify_legend.position = (verify_button_left, self.btn_edit_legend.get_top())
            self.btn_verify_legend.click_callback = self.btn_verify_legend_click
            self.container_annotation_buttons.append(self.btn_verify_legend)

            self.btn_verify_axis = ScreenButton("btn_verify_axis", "Verified", 21, verify_button_width)
            self.btn_verify_axis.set_colors(button_text_color, button_back_color)
            self.btn_verify_axis.position = (verify_button_left, self.btn_edit_axis.get_top())
            self.btn_verify_axis.click_callback = self.btn_verify_axis_click
            self.container_annotation_buttons.append(self.btn_verify_axis)

            self.btn_verify_data = ScreenButton("btn_verify_data", "Verified", 21, verify_button_width)
            self.btn_verify_data.set_colors(button_text_color, button_back_color)
            self.btn_verify_data.position = (verify_button_left, self.btn_edit_data.get_top())
            self.btn_verify_data.click_callback = self.btn_verify_data_click
            self.container_annotation_buttons.append(self.btn_verify_data)

        # =======

        self.container_split_panels = ScreenContainer("container_split_panels", (container_width, 220), back_color=panel_buttons_bg)
        self.container_split_panels.position = (self.container_view_buttons.get_left(), self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_split_panels)

        self.lbl_split_panel_title = ScreenLabel("lbl_split_panel_title", "Edit Panels Options", 21, 290, 1)
        self.lbl_split_panel_title.position = (5, 5)
        self.lbl_split_panel_title.set_background(panel_buttons_bg)
        self.lbl_split_panel_title.set_color(self.text_color)
        self.container_split_panels.append(self.lbl_split_panel_title)

        self.btn_split_panel_horizontal = ScreenButton("btn_split_panel_horizontal", "Y - Split", 21, button_width)
        self.btn_split_panel_horizontal.set_colors(button_text_color, button_back_color)
        self.btn_split_panel_horizontal.position = (button_left, self.lbl_split_panel_title.get_bottom() + 10)
        self.btn_split_panel_horizontal.click_callback = self.btn_split_panel_horizontal_click
        self.container_split_panels.append(self.btn_split_panel_horizontal)

        self.btn_split_panel_vertical = ScreenButton("btn_split_panel_vertical", "X - Split", 21, button_width)
        self.btn_split_panel_vertical.set_colors(button_text_color, button_back_color)
        self.btn_split_panel_vertical.position = (button_left, self.btn_split_panel_horizontal.get_bottom() + 10)
        self.btn_split_panel_vertical.click_callback = self.btn_split_panel_vertical_click
        self.container_split_panels.append(self.btn_split_panel_vertical)

        self.btn_merge_panel = ScreenButton("btn_merge_panel", "Merge Panels", 21, button_width)
        self.btn_merge_panel.set_colors(button_text_color, button_back_color)
        self.btn_merge_panel.position = (button_left, self.btn_split_panel_vertical.get_bottom() + 10)
        self.btn_merge_panel.click_callback = self.btn_merge_panel_click
        self.container_split_panels.append(self.btn_merge_panel)

        self.btn_split_return = ScreenButton("btn_split_return", "Return", 21, button_width)
        self.btn_split_return.set_colors(button_text_color, button_back_color)
        self.btn_split_return.position = (button_left, self.btn_merge_panel.get_bottom() + 10)
        self.btn_split_return.click_callback = self.btn_split_return_click
        self.container_split_panels.append(self.btn_split_return)

        self.container_split_panels.visible = False

        # =====================================
        self.container_classify_panels = ScreenContainer("container_classify_panels", (container_width, 420), back_color=panel_buttons_bg)
        self.container_classify_panels.position = (self.container_view_buttons.get_left(), self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_classify_panels)

        self.lbl_class_panel_title = ScreenLabel("lbl_class_panel_title", "Classify Panel", 21, 290, 1)
        self.lbl_class_panel_title.position = (5, 5)
        self.lbl_class_panel_title.set_background(panel_buttons_bg)
        self.lbl_class_panel_title.set_color(self.text_color)
        self.container_classify_panels.append(self.lbl_class_panel_title)

        self.lbx_class_panel_class = ScreenTextlist("lbx_class_panel_class", (container_width - 20, 320), 22)
        self.lbx_class_panel_class.position = (10, self.lbl_class_panel_title.get_bottom() + 10)
        self.container_classify_panels.append(self.lbx_class_panel_class)
        self.add_chart_types()

        self.btn_class_panel_continue = ScreenButton("btn_class_panel_continue", "Continue", 21, button_width)
        self.btn_class_panel_continue.set_colors(button_text_color, button_back_color)
        self.btn_class_panel_continue.position = (button_left, self.container_classify_panels.height - self.btn_class_panel_continue.height - 10)
        self.btn_class_panel_continue.click_callback = self.btn_class_panel_continue_click
        self.container_classify_panels.append(self.btn_class_panel_continue)

        self.container_classify_panels.visible = False

        # =======================================

        self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
        self.update_panel_info()

    def add_chart_types(self):
        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeNonChart), "Non-Chart")
        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeLine), "Line Chart")
        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeScatter), "Scatter Chart")

        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeBar) + "-" + str(ChartInfo.OrientationHorizontal),
                                              "Bar Chart (Horizontal)")
        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeBar) + "-" + str(ChartInfo.OrientationVertical),
                                              "Bar Chart (Vertical)")

        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeBox) + "-" + str(ChartInfo.OrientationHorizontal),
                                              "Box Chart (Horizontal)")
        self.lbx_class_panel_class.add_option(str(ChartInfo.TypeBox) + "-" + str(ChartInfo.OrientationVertical),
                                              "Box Chart (Vertical)")

    def prepare_screen(self):
        if self.wait_mode != ChartImageAnnotator.WaitModeNone:
            # get delta of time on previous screen ... prepare to count towards this menu
            delta = self.get_reset_time_delta()
            # add delta on the corresponding process...
            if self.wait_mode == ChartImageAnnotator.WaitModeText:
                self.time_stats.time_text += delta
            elif self.wait_mode == ChartImageAnnotator.WaitModeLegend:
                self.time_stats.time_legend += delta
            elif self.wait_mode == ChartImageAnnotator.WaitModeAxes:
                self.time_stats.time_axes += delta
            elif self.wait_mode == ChartImageAnnotator.WaitModeData:
                self.time_stats.time_data += delta

            self.wait_mode = ChartImageAnnotator.WaitModeNone

        # call parent prepare screen ...
        Screen.prepare_screen(self)

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == ChartImageAnnotator.ModeConfirmOverwritePanels:
            # commit changes ....
            # ... create an empty annotation ...
            self.image_info = ImageInfo.CreateDefault(self.current_image)
            # copy the panel structure ...
            self.image_info.panel_tree = PanelTree.Copy(self.tempo_panel_tree)
            # ... get the empty annotation for each panel ...
            self.image_info.reset_panels_info()

            # go back to navigation mode ...
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
            self.update_current_view(False)
            self.selected_panel = 0
            self.update_panel_info()

            self.unsaved_changes = True

        elif self.edition_mode == ChartImageAnnotator.ModeConfirmOverwriteClass:
            # commit changes ....
            # ... get selected class ...
            if "-" in self.lbx_class_panel_class.selected_option_value:
                # Chart type with orientation
                type_str, orientation_str = self.lbx_class_panel_class.selected_option_value.split("-")
                type_value = int(type_str)
                orientation = int(orientation_str)
            else:
                # No orientation
                type_value = int(self.lbx_class_panel_class.selected_option_value)
                orientation = None

            if self.admin_mode:
                overwrite = input("Discard Chart Info (y/n)? ").lower() in ["y", "yes", "1", "true"]
            else:
                overwrite = True

            if overwrite:
                # ... create an empty panel annotation ...
                self.image_info.panels[self.selected_panel] = ChartInfo(type_value, orientation)
            else:
                # ... admin request simple overwrite of values which might lead to inconsistencies ...
                self.image_info.panels[self.selected_panel].type = type_value
                self.image_info.panels[self.selected_panel].orientation = orientation

            # go back to navigation mode ...
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
            self.update_current_view(False)

        elif self.edition_mode == ChartImageAnnotator.ModeConfirmExit:
            # return with unsaved changes lost
            print("Unsaved changes on " + self.relative_path + " were lost")

            delta = self.get_reset_time_delta()
            self.time_stats.time_main += delta
            self.parent.update_annotation_times(self.time_stats)

            self.parent.refresh_page()
            self.return_screen = self.parent



    def btn_confirm_cancel_click(self, button):
        if self.edition_mode == ChartImageAnnotator.ModeSelectPanelSplit:
            # simply go back ...
            self.set_editor_mode(ChartImageAnnotator.ModeEditPanels)
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmOverwritePanels:
            # go back to navigation mode ... no changes commited
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
            self.update_current_view(False)
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmOverwriteClass:
            # go back to navigation mode ... no changes commited
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
            self.update_current_view(False)
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmExit:
            # go back to navigation mode ... no changes commited
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
            self.update_current_view(False)

    def btn_zoom_reduce_click(self, button):
        self.update_view_scale(self.view_scale - 0.25)

    def btn_zoom_increase_click(self, button):
        self.update_view_scale(self.view_scale + 0.25)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = ChartImageAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = ChartImageAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = ChartImageAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = ChartImageAnnotator.ViewModeGrayNoData
        self.update_current_view()

    def get_reset_time_delta(self):
        new_time = time.time()
        delta = new_time - self.in_menu_time_start
        self.in_menu_time_start = new_time

        return delta

    def btn_label_panels_click(self, button):
        self.time_stats.time_main += self.get_reset_time_delta()
        self.tempo_panel_tree = PanelTree.Copy(self.image_info.panel_tree)
        self.set_editor_mode(ChartImageAnnotator.ModeEditPanels)

    def btn_panels_prev_click(self, button):
        if self.selected_panel > 0:
            self.selected_panel -= 1
            self.update_current_view(False)
            self.update_panel_info()


    def btn_panels_next_click(self, button):
        if self.selected_panel + 1 < len(self.image_info.panels):
            self.selected_panel += 1
            self.update_current_view(False)
            self.update_panel_info()

    def btn_return_click(self, button):
        if not self.unsaved_changes:
            print("Edition for " + self.relative_path + " completed")

            delta = self.get_reset_time_delta()
            self.time_stats.time_main += delta
            self.parent.update_annotation_times(self.time_stats)

            self.parent.refresh_page()
            self.return_screen = self.parent

        else:
            # go into confirmation mode
            self.set_editor_mode(ChartImageAnnotator.ModeConfirmExit)

    def btn_save_click(self, button):
        # create dirs (if they don't exist)
        os.makedirs(self.output_dir, exist_ok=True)

        xml_str = self.image_info.to_XML()
        with open(self.annotation_filename, 'w', encoding="utf-8") as out_file:
            out_file.write(xml_str)

        print("Data saved to: " + self.annotation_filename)
        self.unsaved_changes = False


    def btn_edit_class_click(self, button):
        prev_key = self.get_image_class_key()
        self.lbx_class_panel_class.change_option_selected(prev_key)

        delta = self.get_reset_time_delta()
        self.time_stats.time_main += delta
        self.set_editor_mode(ChartImageAnnotator.ModeEditClass)

    def btn_edit_text_click(self, button):
        # prepare time count for text ...
        delta = self.get_reset_time_delta()
        self.time_stats.time_main += delta
        self.wait_mode = ChartImageAnnotator.WaitModeText

        panel_image = self.image_info.get_panel_image(self.selected_panel)

        text_annotator = ChartTextAnnotator(self.size, panel_image, self.image_info.panels[self.selected_panel], self,
                                            self.admin_mode)
        text_annotator.prepare_screen()

        self.return_screen = text_annotator

    def btn_edit_legend_click(self, button):
        # prepare time count for legend ...
        delta = self.get_reset_time_delta()
        self.time_stats.time_main += delta
        self.wait_mode = ChartImageAnnotator.WaitModeLegend

        panel_image = self.image_info.get_panel_image(self.selected_panel)

        legend_annotator = ChartLegendAnnotator(self.size, panel_image, self.image_info.panels[self.selected_panel], self)
        legend_annotator.prepare_screen()

        self.return_screen = legend_annotator

    def btn_edit_axis_click(self, button):
        # prepare time count for axis ...
        delta = self.get_reset_time_delta()
        self.time_stats.time_main += delta
        self.wait_mode = ChartImageAnnotator.WaitModeAxes

        panel_image = self.image_info.get_panel_image(self.selected_panel)

        axes_annotator = ChartAxesAnnotator(self.size, panel_image, self.image_info.panels[self.selected_panel], self)
        axes_annotator.prepare_screen()

        self.return_screen = axes_annotator

    def btn_edit_data_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]

        if not current_panel.check_classes():
            print("Must select a valid chart type to annotate its data!")
            return

        if not current_panel.check_text():
            print("Text must be annotated first!")
            return

        if not current_panel.check_axes():
            print("Axes must be annotated first!")
            return

        panel_image = self.image_info.get_panel_image(self.selected_panel)

        if self.image_info.panels[self.selected_panel].type == ChartInfo.TypeBar:
            data_annotator = BarChartAnnotator(self.size, panel_image, current_panel, self)
        elif self.image_info.panels[self.selected_panel].type == ChartInfo.TypeBox:
            data_annotator = BoxChartAnnotator(self.size, panel_image, current_panel, self)
        elif self.image_info.panels[self.selected_panel].type == ChartInfo.TypeLine:
            data_annotator = LineChartAnnotator(self.size, panel_image, current_panel, self)
        elif self.image_info.panels[self.selected_panel].type == ChartInfo.TypeScatter:
            data_annotator = ScatterChartAnnotator(self.size, panel_image, current_panel, self)
        else:
            raise Exception("Not implemented!!")

        # prepare time count for data ...
        delta = self.get_reset_time_delta()
        self.time_stats.time_main += delta
        self.wait_mode = ChartImageAnnotator.WaitModeData

        data_annotator.prepare_screen()

        self.return_screen = data_annotator

    def update_current_view(self, resized=False):
        if self.view_mode in [ChartImageAnnotator.ViewModeGrayData, ChartImageAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.current_gray
        else:
            base_image = self.current_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [ChartImageAnnotator.ViewModeRawData, ChartImageAnnotator.ViewModeGrayData]:
            if self.edition_mode in [ChartImageAnnotator.ModeEditPanels, ChartImageAnnotator.ModeSelectPanelSplit,
                                     ChartImageAnnotator.ModeConfirmOverwritePanels]:
                # get panels from temporary tree
                panel_nodes = self.tempo_panel_tree.root.get_leaves()
                temporary_tree = True
            else:
                # get from current tree
                panel_nodes = self.image_info.panel_tree.root.get_leaves()
                temporary_tree = False

            for idx, panel_node in enumerate(panel_nodes):
                # mark the panel boundaries ...
                if idx == self.selected_panel and self.edition_mode == ChartImageAnnotator.ModeNavigate:
                    border_color = (0, 255, 0)
                else:
                    border_color = (255, 0, 0)

                if not temporary_tree:
                    # show the chart type (and orientation)
                    chart_type, chart_orientation = self.image_info.panels[idx].get_description()
                    chart_desc = "{0:s} ({1:s})".format(chart_type, chart_orientation)
                    font_scale = 2
                    font_face = cv2.FONT_HERSHEY_PLAIN
                    font_thickness = 1
                    font_padding = 2

                    text_size, font_baseline = cv2.getTextSize(chart_desc, font_face, font_scale, font_thickness)

                    modified_image[panel_node.y1:panel_node.y1 + text_size[1] + 10, panel_node.x1:panel_node.x1 + text_size[0] + 10] = 255

                    vertical_displacement = font_padding + text_size[1]
                    text_loc = (panel_node.x1 + font_padding, panel_node.y1 + vertical_displacement)
                    shadow_loc = (text_loc[0] + 2, text_loc[1] + 1)
                    cv2.putText(modified_image, chart_desc, shadow_loc, font_face, font_scale, (0, 0, 0),
                                thickness=font_thickness, lineType=cv2.LINE_AA)

                    cv2.putText(modified_image, chart_desc, text_loc, font_face, font_scale, border_color,
                                thickness=font_thickness, lineType=cv2.LINE_AA)

                cv2.rectangle(modified_image, (panel_node.x1, panel_node.y1), (panel_node.x2, panel_node.y2),
                              border_color, thickness=2)

            # TODO: show here any relevant annotations on the modified image ...



        # finally, resize ...
        modified_image = cv2.resize(modified_image, (int(w * self.view_scale), int(h * self.view_scale)),
                                    interpolation=cv2.INTER_NEAREST)

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

        # update scale text ...
        self.lbl_zoom.set_text("Zoom: " + str(int(round(self.view_scale * 100,0))) + "%")

    def btn_split_panel_horizontal_click(self, button):
        self.split_panel_operation = ChartImageAnnotator.SplitOperationYSplit
        self.set_editor_mode(ChartImageAnnotator.ModeSelectPanelSplit)

    def btn_split_panel_vertical_click(self, button):
        self.split_panel_operation = ChartImageAnnotator.SplitOperationXSplit
        self.set_editor_mode(ChartImageAnnotator.ModeSelectPanelSplit)

    def btn_merge_panel_click(self, button):
        self.split_panel_operation = ChartImageAnnotator.SplitOperationMerge
        self.set_editor_mode(ChartImageAnnotator.ModeSelectPanelSplit)

    def btn_split_return_click(self, button):
        # add time delta for panels ... from here, confirm or not will count towards main screen time
        delta = self.get_reset_time_delta()
        self.time_stats.time_panels += delta

        if self.tempo_panel_tree == self.image_info.panel_tree:
            # nothing changed ...
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)
        else:
            self.set_editor_mode(ChartImageAnnotator.ModeConfirmOverwritePanels)

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_panels_buttons.visible = (self.edition_mode == ChartImageAnnotator.ModeNavigate)
        self.container_annotation_buttons.visible = (self.edition_mode == ChartImageAnnotator.ModeNavigate)

        # Edit panels ...
        self.container_split_panels.visible = (self.edition_mode == ChartImageAnnotator.ModeEditPanels)
        self.container_classify_panels.visible = (self.edition_mode == ChartImageAnnotator.ModeEditClass)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ChartImageAnnotator.ModeSelectPanelSplit,
                                                                       ChartImageAnnotator.ModeConfirmOverwritePanels,
                                                                       ChartImageAnnotator.ModeConfirmOverwriteClass,
                                                                       ChartImageAnnotator.ModeConfirmExit]

        if self.edition_mode == ChartImageAnnotator.ModeSelectPanelSplit:
            if self.split_panel_operation == ChartImageAnnotator.SplitOperationYSplit:
                self.lbl_confirm_message.set_text("Select Point for Y - Split")
            elif self.split_panel_operation == ChartImageAnnotator.SplitOperationXSplit:
                self.lbl_confirm_message.set_text("Select Point for X - Split")
            elif self.split_panel_operation == ChartImageAnnotator.SplitOperationMerge:
                self.lbl_confirm_message.set_text("Select a panel to Merge")
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmOverwritePanels:
            self.lbl_confirm_message.set_text("Discard Previous Image Annotations?")
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmOverwriteClass:
            self.lbl_confirm_message.set_text("Discard Previous Panel Annotations?")
        elif self.edition_mode == ChartImageAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard unsaved changes?")

        self.btn_confirm_accept.visible = (self.container_confirm_buttons.visible and self.edition_mode != ChartImageAnnotator.ModeSelectPanelSplit)



    def img_main_mouse_button_down(self, img, pos, button):
        if self.edition_mode == ChartImageAnnotator.ModeSelectPanelSplit:
            scaled_x, scaled_y = pos
            click_x = int(scaled_x / self.view_scale)
            click_y = int(scaled_y / self.view_scale)

            selected_nodes = self.tempo_panel_tree.root.find_point_containers(click_x, click_y, False)
            if len(selected_nodes) == 1:
                current_node = selected_nodes[0]
                if self.split_panel_operation == ChartImageAnnotator.SplitOperationYSplit:
                    current_node.horizontal_split(click_y)
                elif self.split_panel_operation == ChartImageAnnotator.SplitOperationXSplit:
                    current_node.vertical_split(click_x)
                elif self.split_panel_operation == ChartImageAnnotator.SplitOperationMerge:
                    current_node.merge_with_parent()

                self.set_editor_mode(ChartImageAnnotator.ModeEditPanels)
                self.update_current_view(False)

    def update_panel_info(self):
        msg = "Current Panel: {0:d} / {1:d}".format(self.selected_panel + 1, len(self.image_info.panels))
        self.lbl_panels_current.set_text(msg)

    def btn_class_panel_continue_click(self, button):
        # finish time for classification ... from here, next time will count towards main menu ...
        delta = self.get_reset_time_delta()
        self.time_stats.time_classification += delta

        prev_key = self.get_image_class_key()
        if prev_key != self.lbx_class_panel_class.selected_option_value:
            self.set_editor_mode(ChartImageAnnotator.ModeConfirmOverwriteClass)
        else:
            # nothing was changed ...
            self.set_editor_mode(ChartImageAnnotator.ModeNavigate)

    def get_image_class_key(self):
        current_panel = self.image_info.panels[self.selected_panel]
        class_key = str(current_panel.type)
        if current_panel.type in [ChartInfo.TypeBar, ChartInfo.TypeBox]:
            class_key += "-" + str(current_panel.orientation)

        return class_key

    def subtool_completed(self, data_changed):
        if data_changed:
            self.unsaved_changes = True

    def btn_panels_verify_click(self, button):
        self.image_info.properties["VERIFIED_01_PANELS"] = time.time()
        self.unsaved_changes = True
        print("Image Panels have been marked as verified!!!")

    def btn_verify_class_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]
        current_panel.set_classes_verified(True)
        self.unsaved_changes = True

        print("Current Panels Classification has been marked as verified!!!")

    def btn_verify_text_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]
        current_panel.set_text_verified(True)
        self.unsaved_changes = True

        print("Current Panels Text has been marked as verified!!!")

    def btn_verify_legend_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]
        current_panel.set_legend_verified(True)
        self.unsaved_changes = True

        print("Current Panels Legend has been marked as verified!!!")

    def btn_verify_axis_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]
        current_panel.set_axes_verified(True)
        self.unsaved_changes = True

        print("Current Panels Axes have been marked as verified!!!")

    def btn_verify_data_click(self, button):
        current_panel = self.image_info.panels[self.selected_panel]
        current_panel.set_data_verified(True)
        self.unsaved_changes = True

        print("Current Panels Data has been marked as verified!!!")
