
import numpy as np
import cv2

from shapely.geometry import Point, Polygon, LineString

from munkres import Munkres

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.annotation.base_image_annotator import BaseImageAnnotator

from ChartInfo.data.chart_info import ChartInfo
from ChartInfo.data.text_info import TextInfo
from ChartInfo.data.axes_info import AxesInfo
from ChartInfo.data.axis_values import AxisValues
from ChartInfo.data.tick_info import TickInfo

class ChartAxesAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeBBoxSelect = 1
    ModeBBoxEdit = 2
    ModeAxisEdit = 3
    ModeAxisInfoEdit = 4
    ModeTitleSelect = 5
    ModeTicksEdit = 6
    ModeTicksSelect = 7
    ModeLabelsEdit = 8
    ModeLabelPerTickEdit = 9
    ModeLabelPerTickSelect = 10
    ModeConfirmExit = 11
    ModeConfirmAxisDelete = 12

    AxisX1 = 0
    AxisY1 = 1
    AxisX2 = 2
    AxisY2 = 3

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Chart Axes Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.axes is None:
            # create a new axes info
            tick_labels = self.panel_info.get_all_text(TextInfo.TypeTickLabel)
            title_labels = self.panel_info.get_all_text(TextInfo.TypeAxisTitle)
            self.axes = AxesInfo(tick_labels, title_labels)
            self.data_changed = True
        else:
            # make a copy
            self.axes = AxesInfo.Copy(self.panel_info.axes)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (112, 146, 190)
        self.text_color = (255, 255, 255)

        self.elements.back_color = self.general_background

        # temporary
        self.edition_mode = None
        self.edit_axis = None
        self.tempo_axis_values = None
        self.tempo_ticks = None
        self.tempo_tick_idx = None
        self.tempo_labels_unassigned = None
        self.tempo_labels_axis = None

        # GUI ...
        self.label_title = None

        self.container_confirm_buttons = None
        self.lbl_confirm_message = None
        self.btn_confirm_cancel = None
        self.btn_confirm_accept = None

        self.container_annotation_buttons = None
        self.lbl_edit_title = None
        self.btn_edit_bbox = None
        self.lbl_edit_current_axes = None
        self.lbl_edit_axis_x1 = None
        self.btn_edit_axis_x1_add = None
        self.btn_edit_axis_x1_edit = None
        self.lbl_edit_axis_y1 = None
        self.btn_edit_axis_y1_add = None
        self.btn_edit_axis_y1_edit = None
        self.lbl_edit_axis_x2 = None
        self.btn_edit_axis_x2_add = None
        self.btn_edit_axis_x2_edit = None
        self.lbl_edit_axis_y2 = None
        self.btn_edit_axis_y2_add = None
        self.btn_edit_axis_y2_edit = None
        self.lbl_edit_axes_summary = None
        self.btn_return_accept = None
        self.btn_return_cancel = None

        self.container_axis_buttons = None
        self.lbl_axis_title = None
        self.btn_axis_edit_info = None
        self.btn_axis_edit_ticks = None
        self.btn_axis_edit_labels = None
        self.btn_axis_edit_labels_per_tick = None
        self.btn_axis_delete = None
        self.btn_axis_return_accept = None
        self.btn_axis_return_cancel = None

        self.container_info_buttons = None
        self.lbl_info_title = None
        self.lbl_info_axis_title = None
        self.lbl_info_axis_title_value = None
        self.btn_info_title_set = None
        self.btn_info_title_delete = None
        self.lbl_info_axis_type_title = None
        self.lbx_info_axis_type = None
        self.lbl_info_ticks_type_title = None
        self.lbx_info_ticks_type = None
        self.lbl_info_scale_type_title = None
        self.lbx_info_scale_type = None
        self.btn_info_return = None

        self.container_ticks_buttons = None
        self.lbl_ticks_title = None
        self.lbl_ticks_count = None
        self.btn_ticks_decrease = None
        self.btn_ticks_increase = None
        self.btn_ticks_redistribute = None
        self.btn_ticks_auto = None
        self.lbx_ticks_list = None
        self.btn_ticks_set = None
        self.btn_ticks_return = None

        self.container_labels_buttons = None
        self.lbl_labels_title = None
        self.lbl_labels_unassigned = None
        self.lbx_labels_unassigned = None
        self.btn_labels_add = None
        self.lbl_labels_axis = None
        self.lbx_labels_axis = None
        self.btn_labels_remove = None
        self.btn_labels_return = None

        self.container_labels_per_tick_buttons = None
        self.lbl_lpt_title = None
        self.lbl_lpt_ticks = None
        self.lbx_lpt_assignments = None
        self.btn_lpt_assign = None
        self.btn_lpt_remove = None
        self.btn_lpt_auto = None
        self.btn_lpt_return = None

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
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Chart Axes Annotation", 28)
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
        darker_background = (94, 96, 125)
        self.container_annotation_buttons = ScreenContainer("container_annotation_buttons", (container_width, 430),
                                                            back_color=darker_background)
        self.container_annotation_buttons.position = (self.container_view_buttons.get_left(),
                                                      self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_annotation_buttons)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Axes Annotation Options", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_title)

        self.btn_edit_bbox = ScreenButton("btn_edit_bbox", "Edit Bounding Box", 21, button_width)
        self.btn_edit_bbox.set_colors(button_text_color, button_back_color)
        self.btn_edit_bbox.position = (button_left, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_bbox.click_callback = self.btn_edit_bbox_click
        self.container_annotation_buttons.append(self.btn_edit_bbox)

        self.lbl_edit_axis_x1 = ScreenLabel("lbl_edit_axis_x1", "X-1 (Bottom)", 21, button_2_width, 1)
        self.lbl_edit_axis_x1.position = (button_2_left, self.btn_edit_bbox.get_bottom() + 30)
        self.lbl_edit_axis_x1.set_background(darker_background)
        self.lbl_edit_axis_x1.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_axis_x1)

        self.btn_edit_axis_x1_add = ScreenButton("btn_edit_axis_x1_add", "Add", 21, button_2_width)
        self.btn_edit_axis_x1_add.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_x1_add.position = (button_2_right, self.lbl_edit_axis_x1.get_top() - 10)
        self.btn_edit_axis_x1_add.click_callback = self.btn_edit_axis_x1_add_click
        self.container_annotation_buttons.append(self.btn_edit_axis_x1_add)

        self.btn_edit_axis_x1_edit = ScreenButton("btn_edit_axis_x1_edit", "Edit", 21, button_2_width)
        self.btn_edit_axis_x1_edit.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_x1_edit.position = (button_2_right, self.lbl_edit_axis_x1.get_top() - 10)
        self.btn_edit_axis_x1_edit.click_callback = self.btn_edit_axis_x1_edit_click
        self.container_annotation_buttons.append(self.btn_edit_axis_x1_edit)

        self.lbl_edit_axis_y1 = ScreenLabel("lbl_edit_axis_y1", "Y-1 (Left)", 21, button_2_width, 1)
        self.lbl_edit_axis_y1.position = (button_2_left, self.lbl_edit_axis_x1.get_bottom() + 30)
        self.lbl_edit_axis_y1.set_background(darker_background)
        self.lbl_edit_axis_y1.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_axis_y1)

        self.btn_edit_axis_y1_add = ScreenButton("btn_edit_axis_y1_add", "Add", 21, button_2_width)
        self.btn_edit_axis_y1_add.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_y1_add.position = (button_2_right, self.lbl_edit_axis_y1.get_top() - 10)
        self.btn_edit_axis_y1_add.click_callback = self.btn_edit_axis_y1_add_click
        self.container_annotation_buttons.append(self.btn_edit_axis_y1_add)

        self.btn_edit_axis_y1_edit = ScreenButton("btn_edit_axis_y1_edit", "Edit", 21, button_2_width)
        self.btn_edit_axis_y1_edit.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_y1_edit.position = (button_2_right, self.lbl_edit_axis_y1.get_top() - 10)
        self.btn_edit_axis_y1_edit.click_callback = self.btn_edit_axis_y1_edit_click
        self.container_annotation_buttons.append(self.btn_edit_axis_y1_edit)

        self.lbl_edit_axis_x2 = ScreenLabel("lbl_edit_axis_x2", "X-2 (Top)", 21, button_2_width, 1)
        self.lbl_edit_axis_x2.position = (button_2_left, self.lbl_edit_axis_y1.get_bottom() + 30)
        self.lbl_edit_axis_x2.set_background(darker_background)
        self.lbl_edit_axis_x2.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_axis_x2)

        self.btn_edit_axis_x2_add = ScreenButton("btn_edit_axis_x2_add", "Add", 21, button_2_width)
        self.btn_edit_axis_x2_add.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_x2_add.position = (button_2_right, self.lbl_edit_axis_x2.get_top() - 10)
        self.btn_edit_axis_x2_add.click_callback = self.btn_edit_axis_x2_add_click
        self.container_annotation_buttons.append(self.btn_edit_axis_x2_add)

        self.btn_edit_axis_x2_edit = ScreenButton("btn_edit_axis_x2_edit", "Edit", 21, button_2_width)
        self.btn_edit_axis_x2_edit.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_x2_edit.position = (button_2_right, self.lbl_edit_axis_x2.get_top() - 10)
        self.btn_edit_axis_x2_edit.click_callback = self.btn_edit_axis_x2_edit_click
        self.container_annotation_buttons.append(self.btn_edit_axis_x2_edit)

        self.lbl_edit_axis_y2 = ScreenLabel("lbl_edit_axis_y2", "Y-2 (Right)", 21, button_2_width, 1)
        self.lbl_edit_axis_y2.position = (button_2_left, self.lbl_edit_axis_x2.get_bottom() + 30)
        self.lbl_edit_axis_y2.set_background(darker_background)
        self.lbl_edit_axis_y2.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_axis_y2)

        self.btn_edit_axis_y2_add = ScreenButton("btn_edit_axis_y2_add", "Add", 21, button_2_width)
        self.btn_edit_axis_y2_add.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_y2_add.position = (button_2_right, self.lbl_edit_axis_y2.get_top() - 10)
        self.btn_edit_axis_y2_add.click_callback = self.btn_edit_axis_y2_add_click
        self.container_annotation_buttons.append(self.btn_edit_axis_y2_add)

        self.btn_edit_axis_y2_edit = ScreenButton("btn_edit_axis_y2_edit", "Edit", 21, button_2_width)
        self.btn_edit_axis_y2_edit.set_colors(button_text_color, button_back_color)
        self.btn_edit_axis_y2_edit.position = (button_2_right, self.lbl_edit_axis_y2.get_top() - 10)
        self.btn_edit_axis_y2_edit.click_callback = self.btn_edit_axis_y2_edit_click
        self.container_annotation_buttons.append(self.btn_edit_axis_y2_edit)

        self.lbl_edit_axes_summary = ScreenLabel("lbl_edit_axes_summary", "[Here Axis Info]\n" * 4, 21,
                                                 self.container_annotation_buttons.width - 40, 0)
        self.lbl_edit_axes_summary.position = (20, self.btn_edit_axis_y2_edit.get_bottom() + 30)
        self.lbl_edit_axes_summary.set_background(darker_background)
        self.lbl_edit_axes_summary.set_color(self.text_color)
        self.container_annotation_buttons.append(self.lbl_edit_axes_summary)

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

        # =====================================================================
        # container with axis edition options

        self.container_axis_buttons = ScreenContainer("container_axis_buttons", (container_width, 380),
                                                      back_color=darker_background)
        self.container_axis_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_axis_buttons)

        self.lbl_axis_title = ScreenLabel("lbl_axis_title", "[HERE] - Axis Edition Options", 21, 290, 1)
        self.lbl_axis_title.position = (5, 5)
        self.lbl_axis_title.set_background(darker_background)
        self.lbl_axis_title.set_color(self.text_color)
        self.container_axis_buttons.append(self.lbl_axis_title)

        self.btn_axis_edit_info = ScreenButton("btn_axis_edit_info", "Edit Axis Information", 21, button_width)
        self.btn_axis_edit_info.set_colors(button_text_color, button_back_color)
        self.btn_axis_edit_info.position = (button_left, self.lbl_edit_title.get_bottom() + 20)
        self.btn_axis_edit_info.click_callback = self.btn_axis_edit_info_click
        self.container_axis_buttons.append(self.btn_axis_edit_info)

        self.btn_axis_edit_ticks = ScreenButton("btn_axis_edit_ticks", "Edit Ticks", 21, button_width)
        self.btn_axis_edit_ticks.set_colors(button_text_color, button_back_color)
        self.btn_axis_edit_ticks.position = (button_left, self.btn_axis_edit_info.get_bottom() + 10)
        self.btn_axis_edit_ticks.click_callback = self.btn_axis_edit_ticks_click
        self.container_axis_buttons.append(self.btn_axis_edit_ticks)

        self.btn_axis_edit_labels = ScreenButton("btn_axis_edit_labels", "Edit Labels", 21, button_width)
        self.btn_axis_edit_labels.set_colors(button_text_color, button_back_color)
        self.btn_axis_edit_labels.position = (button_left, self.btn_axis_edit_ticks.get_bottom() + 10)
        self.btn_axis_edit_labels.click_callback = self.btn_axis_edit_labels_click
        self.container_axis_buttons.append(self.btn_axis_edit_labels)

        self.btn_axis_edit_labels_per_tick = ScreenButton("btn_axis_edit_labels_per_tick", "Edit Label Per Tick", 21,
                                                          button_width)
        self.btn_axis_edit_labels_per_tick.set_colors(button_text_color, button_back_color)
        self.btn_axis_edit_labels_per_tick.position = (button_left, self.btn_axis_edit_labels.get_bottom() + 10)
        self.btn_axis_edit_labels_per_tick.click_callback = self.btn_axis_edit_labels_per_tick_click
        self.container_axis_buttons.append(self.btn_axis_edit_labels_per_tick)

        self.btn_axis_delete = ScreenButton("btn_axis_delete", "Delete Axis", 21, button_width)
        self.btn_axis_delete.set_colors(button_text_color, button_back_color)
        self.btn_axis_delete.position = (button_left, self.btn_axis_edit_labels_per_tick.get_bottom() + 20)
        self.btn_axis_delete.click_callback = self.btn_axis_delete_click
        self.container_axis_buttons.append(self.btn_axis_delete)

        self.btn_axis_return_accept = ScreenButton("btn_axis_return_accept", "Accept", 21, button_2_width)
        return_top = self.container_axis_buttons.height - self.btn_axis_return_accept.height - 10
        self.btn_axis_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_axis_return_accept.position = (button_2_left, return_top)
        self.btn_axis_return_accept.click_callback = self.btn_axis_return_accept_click
        self.container_axis_buttons.append(self.btn_axis_return_accept)

        self.btn_axis_return_cancel = ScreenButton("btn_axis_return_cancel", "Cancel", 21, button_2_width)
        self.btn_axis_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_axis_return_cancel.position = (button_2_right, return_top)
        self.btn_axis_return_cancel.click_callback = self.btn_axis_return_cancel_click
        self.container_axis_buttons.append(self.btn_axis_return_cancel)

        # ============================================================================
        #  Container with options to edit general axis information ...

        self.container_info_buttons = ScreenContainer("container_info_buttons", (container_width, 490),
                                                      back_color=darker_background)
        self.container_info_buttons.position = (self.container_view_buttons.get_left(),
                                                self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_info_buttons)

        self.lbl_info_title = ScreenLabel("lbl_info_title", "General Axis Information", 21, 290, 1)
        self.lbl_info_title.position = (5, 5)
        self.lbl_info_title.set_background(darker_background)
        self.lbl_info_title.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_title)

        self.lbl_info_axis_title = ScreenLabel("lbl_info_axis_title", "Title for Current Axis", 21, 290, 1)
        self.lbl_info_axis_title.position = (5, self.lbl_info_title.get_bottom() + 20)
        self.lbl_info_axis_title.set_background(darker_background)
        self.lbl_info_axis_title.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_axis_title)

        self.lbl_info_axis_title_value = ScreenLabel("lbl_info_axis_title_value", "[ No Title ]", 21, 290, 1)
        self.lbl_info_axis_title_value.position = (5, self.lbl_info_axis_title.get_bottom() + 10)
        self.lbl_info_axis_title_value.set_background(darker_background)
        self.lbl_info_axis_title_value.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_axis_title_value)

        self.btn_info_title_set = ScreenButton("btn_info_title_set", "Set", 21, button_2_width)
        self.btn_info_title_set.set_colors(button_text_color, button_back_color)
        self.btn_info_title_set.position = (button_2_left, self.lbl_info_axis_title_value.get_bottom() + 10)
        self.btn_info_title_set.click_callback = self.btn_info_title_set_click
        self.container_info_buttons.append(self.btn_info_title_set)

        self.btn_info_title_delete = ScreenButton("btn_info_title_delete", "Remove", 21, button_2_width)
        self.btn_info_title_delete.set_colors(button_text_color, button_back_color)
        self.btn_info_title_delete.position = (button_2_right, self.lbl_info_axis_title_value.get_bottom() + 10)
        self.btn_info_title_delete.click_callback = self.btn_info_title_delete_click
        self.container_info_buttons.append(self.btn_info_title_delete)

        # ----

        self.lbl_info_ticks_type_title = ScreenLabel("lbl_info_ticks_type_title", "Type of Ticks", 21, 290, 1)
        self.lbl_info_ticks_type_title.position = (5, self.btn_info_title_set.get_bottom() + 10)
        self.lbl_info_ticks_type_title.set_background(darker_background)
        self.lbl_info_ticks_type_title.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_ticks_type_title)

        self.lbx_info_ticks_type = ScreenTextlist("lbx_info_ticks_type", (container_width - 20, 90), 18,
                                                  back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                  selected_back=(50, 80, 120), selected_color=(255, 255, 255))
        self.lbx_info_ticks_type.position = (10, self.lbl_info_ticks_type_title.get_bottom() + 10)
        self.container_info_buttons.append(self.lbx_info_ticks_type)

        # ----

        self.lbl_info_axis_type_title = ScreenLabel("lbl_info_axis_type_title", "Type of Values", 21, button_2_width, 1)
        self.lbl_info_axis_type_title.position = (button_2_left, self.lbx_info_ticks_type.get_bottom() + 10)
        self.lbl_info_axis_type_title.set_background(darker_background)
        self.lbl_info_axis_type_title.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_axis_type_title)


        self.lbx_info_axis_type = ScreenTextlist("lbx_info_axis_type", (button_2_width, 90), 18,
                                                 back_color=(255, 255, 255), option_color=(0, 0, 0),
                                                 selected_back=(50, 80, 120), selected_color=(255, 255, 255))
        self.lbx_info_axis_type.position = (button_2_left, self.lbl_info_axis_type_title.get_bottom() + 10)
        self.container_info_buttons.append(self.lbx_info_axis_type)

        # ----

        self.lbl_info_scale_type_title = ScreenLabel("lbl_info_scale_type_title", "Scale of Values", 21, button_2_width, 1)
        self.lbl_info_scale_type_title.position = (button_2_right, self.lbx_info_ticks_type.get_bottom() + 10)
        self.lbl_info_scale_type_title.set_background(darker_background)
        self.lbl_info_scale_type_title.set_color(self.text_color)
        self.container_info_buttons.append(self.lbl_info_scale_type_title)

        self.lbx_info_scale_type = ScreenTextlist("lbx_info_scale_type", (button_2_width, 135), 18,
                                                  back_color=(255,255,255), option_color=(0, 0, 0),
                                                  selected_back=(50, 80, 120), selected_color=(255, 255, 255))
        self.lbx_info_scale_type.position = (button_2_right, self.lbl_info_scale_type_title.get_bottom() + 10)
        self.container_info_buttons.append(self.lbx_info_scale_type)

        self.btn_info_return = ScreenButton("btn_info_return", "Return", 21, button_width)
        self.btn_info_return.set_colors(button_text_color, button_back_color)
        self.btn_info_return.position = (button_left, self.lbx_info_scale_type.get_bottom() + 20)
        self.btn_info_return.click_callback = self.btn_info_return_click
        self.container_info_buttons.append(self.btn_info_return)

        # ==============================
        # tick edition options
        self.container_ticks_buttons = ScreenContainer("container_ticks_buttons", (container_width, 480),
                                                            back_color=darker_background)
        self.container_ticks_buttons.position = (self.container_view_buttons.get_left(),
                                                 self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_ticks_buttons)

        self.lbl_ticks_title = ScreenLabel("lbl_edit_title", "Tick Annotation Options", 21, 290, 1)
        self.lbl_ticks_title.position = (5, 5)
        self.lbl_ticks_title.set_background(darker_background)
        self.lbl_ticks_title.set_color(self.text_color)
        self.container_ticks_buttons.append(self.lbl_ticks_title)

        self.lbl_ticks_count = ScreenLabel("lbl_ticks_count", "? Axis: ?? Ticks", 21, 290, 1)
        self.lbl_ticks_count.position = (5, self.lbl_ticks_title.get_bottom() + 20)
        self.lbl_ticks_count.set_background(darker_background)
        self.lbl_ticks_count.set_color(self.text_color)
        self.container_ticks_buttons.append(self.lbl_ticks_count)

        self.btn_ticks_decrease = ScreenButton("btn_ticks_decrease", "[ - ]", 21, button_2_width)
        self.btn_ticks_decrease.set_colors(button_text_color, button_back_color)
        self.btn_ticks_decrease.position = (button_2_left, self.lbl_ticks_count.get_bottom() + 10)
        self.btn_ticks_decrease.click_callback = self.btn_ticks_decrease_click
        self.container_ticks_buttons.append(self.btn_ticks_decrease)

        self.btn_ticks_increase = ScreenButton("btn_ticks_increase", "[ + ]", 21, button_2_width)
        self.btn_ticks_increase.set_colors(button_text_color, button_back_color)
        self.btn_ticks_increase.position = (button_2_right, self.lbl_ticks_count.get_bottom() + 10)
        self.btn_ticks_increase.click_callback = self.btn_ticks_increase_click
        self.container_ticks_buttons.append(self.btn_ticks_increase)

        self.btn_ticks_redistribute = ScreenButton("btn_ticks_redistribute", "Redistribute", 21, button_2_width)
        self.btn_ticks_redistribute.set_colors(button_text_color, button_back_color)
        self.btn_ticks_redistribute.position = (button_2_left, self.btn_ticks_decrease.get_bottom() + 10)
        self.btn_ticks_redistribute.click_callback = self.btn_ticks_redistribute_click
        self.container_ticks_buttons.append(self.btn_ticks_redistribute)


        self.btn_ticks_auto = ScreenButton("btn_ticks_auto", "Auto Add", 21, button_2_width)
        self.btn_ticks_auto.set_colors(button_text_color, button_back_color)
        self.btn_ticks_auto.position = (button_2_right, self.btn_ticks_decrease.get_bottom() + 10)
        self.btn_ticks_auto.click_callback = self.btn_ticks_auto_click
        self.container_ticks_buttons.append(self.btn_ticks_auto)

        self.lbx_ticks_list = ScreenTextlist("lbx_ticks_list", (container_width - 20, 200), 18,
                                             back_color=(255,255,255), option_color=(0, 0, 0),
                                             selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_ticks_list.position = (10, self.btn_ticks_redistribute.get_bottom() + 20)
        self.lbx_ticks_list.selected_value_change_callback = self.lbx_ticks_list_changed
        self.container_ticks_buttons.append(self.lbx_ticks_list)

        self.btn_ticks_set = ScreenButton("btn_ticks_set", "Set Tick Position", 21, button_width)
        self.btn_ticks_set.set_colors(button_text_color, button_back_color)
        self.btn_ticks_set.position = (button_left, self.lbx_ticks_list.get_bottom() + 10)
        self.btn_ticks_set.click_callback = self.btn_ticks_set_click
        self.container_ticks_buttons.append(self.btn_ticks_set)

        self.btn_ticks_return = ScreenButton("btn_ticks_return", "Return", 21, button_width)
        self.btn_ticks_return.set_colors(button_text_color, button_back_color)
        self.btn_ticks_return.position = (button_left, self.btn_ticks_set.get_bottom() + 20)
        self.btn_ticks_return.click_callback = self.btn_ticks_return_click
        self.container_ticks_buttons.append(self.btn_ticks_return)
        self.container_ticks_buttons.visible = False

        # ==============================
        # label assignment options
        self.container_labels_buttons = ScreenContainer("container_labels_buttons", (container_width, 550),
                                                        back_color=darker_background)
        self.container_labels_buttons.position = (self.container_view_buttons.get_left(),
                                                 self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_labels_buttons)

        self.lbl_labels_title = ScreenLabel("lbl_labels_title", "Axis Labels Options", 21, 290, 1)
        self.lbl_labels_title.position = (5, 5)
        self.lbl_labels_title.set_background(darker_background)
        self.lbl_labels_title.set_color(self.text_color)
        self.container_labels_buttons.append(self.lbl_labels_title)

        self.lbl_labels_unassigned = ScreenLabel("lbl_labels_unassigned", "Unassigned Labels", 21, 290, 1)
        self.lbl_labels_unassigned.position = (5, self.lbl_labels_title.get_bottom() + 20)
        self.lbl_labels_unassigned.set_background(darker_background)
        self.lbl_labels_unassigned.set_color(self.text_color)
        self.container_labels_buttons.append(self.lbl_labels_unassigned)

        self.lbx_labels_unassigned = ScreenTextlist("lbx_labels_unassigned", (container_width - 20, 140), 18,
                                                    back_color=(255,255,255), option_color=(0, 0, 0),
                                                    selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_labels_unassigned.position = (10, self.lbl_labels_unassigned.get_bottom() + 10)
        self.lbx_labels_unassigned.selected_value_change_callback = self.lbx_labels_unassigned_changed
        self.container_labels_buttons.append(self.lbx_labels_unassigned)

        self.btn_labels_add = ScreenButton("btn_labels_add", "Add Label", 21, button_width)
        self.btn_labels_add.set_colors(button_text_color, button_back_color)
        self.btn_labels_add.position = (button_left, self.lbx_labels_unassigned.get_bottom() + 10)
        self.btn_labels_add.click_callback = self.btn_labels_add_click
        self.container_labels_buttons.append(self.btn_labels_add)

        self.lbl_labels_axis = ScreenLabel("lbl_labels_axis", "Current Axis Labels", 21, 290, 1)
        self.lbl_labels_axis.position = (5, self.btn_labels_add.get_bottom() + 20)
        self.lbl_labels_axis.set_background(darker_background)
        self.lbl_labels_axis.set_color(self.text_color)
        self.container_labels_buttons.append(self.lbl_labels_axis)

        self.lbx_labels_axis = ScreenTextlist("lbx_labels_axis", (container_width - 20, 140), 18,
                                              back_color=(255,255,255), option_color=(0, 0, 0),
                                              selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_labels_axis.position = (10, self.lbl_labels_axis.get_bottom() + 10)
        self.lbx_labels_axis.selected_value_change_callback = self.lbx_labels_axis_changed
        self.container_labels_buttons.append(self.lbx_labels_axis)

        self.btn_labels_remove = ScreenButton("btn_labels_remove", "Remove Label", 21, button_width)
        self.btn_labels_remove.set_colors(button_text_color, button_back_color)
        self.btn_labels_remove.position = (button_left, self.lbx_labels_axis.get_bottom() + 10)
        self.btn_labels_remove.click_callback = self.btn_labels_remove_click
        self.container_labels_buttons.append(self.btn_labels_remove)

        self.btn_labels_return = ScreenButton("btn_labels_return", "Return", 21, button_width)
        self.btn_labels_return.set_colors(button_text_color, button_back_color)
        self.btn_labels_return.position = (button_left, self.btn_labels_remove.get_bottom() + 20)
        self.btn_labels_return.click_callback = self.btn_labels_return_click
        self.container_labels_buttons.append(self.btn_labels_return)
        self.container_labels_buttons.visible = False

        # ==============================
        # labels per tick assignment options
        self.container_labels_per_tick_buttons = ScreenContainer("container_labels_per_tick_buttons",
                                                                 (container_width, 530), back_color=darker_background)
        self.container_labels_per_tick_buttons.position = (self.container_view_buttons.get_left(),
                                                           self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_labels_per_tick_buttons)

        self.lbl_lpt_title = ScreenLabel("lbl_lpt_title", "Axis Label Per Tick Options", 21, 290, 1)
        self.lbl_lpt_title.position = (5, 5)
        self.lbl_lpt_title.set_background(darker_background)
        self.lbl_lpt_title.set_color(self.text_color)
        self.container_labels_per_tick_buttons.append(self.lbl_lpt_title)

        self.lbl_lpt_ticks = ScreenLabel("lbl_lpt_ticks", "Axis Ticks", 21, 290, 1)
        self.lbl_lpt_ticks.position = (5, self.lbl_lpt_title.get_bottom() + 20)
        self.lbl_lpt_ticks.set_background(darker_background)
        self.lbl_lpt_ticks.set_color(self.text_color)
        self.container_labels_per_tick_buttons.append(self.lbl_lpt_ticks)

        self.lbx_lpt_assignments = ScreenTextlist("lbx_lpt_assignments", (container_width - 20, 300), 18,
                                                    back_color=(255,255,255), option_color=(0, 0, 0),
                                                    selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_lpt_assignments.position = (10, self.lbl_lpt_ticks.get_bottom() + 10)
        self.lbx_lpt_assignments.selected_value_change_callback = self.lbx_lpt_assignments_changed
        self.container_labels_per_tick_buttons.append(self.lbx_lpt_assignments)

        self.btn_lpt_assign = ScreenButton("btn_lpt_assign", "Set Label", 21, button_2_width)
        self.btn_lpt_assign.set_colors(button_text_color, button_back_color)
        self.btn_lpt_assign.position = (button_2_left, self.lbx_lpt_assignments.get_bottom() + 10)
        self.btn_lpt_assign.click_callback = self.btn_lpt_assign_click
        self.container_labels_per_tick_buttons.append(self.btn_lpt_assign)

        self.btn_lpt_remove = ScreenButton("btn_lpt_remove", "Remove Label", 21, button_2_width)
        self.btn_lpt_remove.set_colors(button_text_color, button_back_color)
        self.btn_lpt_remove.position = (button_2_right, self.lbx_lpt_assignments.get_bottom() + 10)
        self.btn_lpt_remove.click_callback = self.btn_lpt_remove_click
        self.container_labels_per_tick_buttons.append(self.btn_lpt_remove)

        self.btn_lpt_auto = ScreenButton("btn_lpt_auto", "Auto Assign Labels", 21, button_width)
        self.btn_lpt_auto.set_colors(button_text_color, button_back_color)
        self.btn_lpt_auto.position = (button_left, self.btn_lpt_assign.get_bottom() + 10)
        self.btn_lpt_auto.click_callback = self.btn_lpt_auto_click
        self.container_labels_per_tick_buttons.append(self.btn_lpt_auto)

        self.btn_lpt_return = ScreenButton("btn_lpt_return", "Return", 21, button_width)
        self.btn_lpt_return.set_colors(button_text_color, button_back_color)
        self.btn_lpt_return.position = (button_left, self.btn_lpt_auto.get_bottom() + 30)
        self.btn_lpt_return.click_callback = self.btn_lpt_return_click
        self.container_labels_per_tick_buttons.append(self.btn_lpt_return)
        self.container_labels_per_tick_buttons.visible = False

        # =====================
        # Zoom-in on current position

        self.container_preview_buttons = ScreenContainer("container_preview_buttons", (container_width, 280),
                                                         back_color=darker_background)
        self.container_preview_buttons.position = (self.container_confirm_buttons.get_left(),
                                                   self.container_confirm_buttons.get_bottom() + 20)
        self.elements.append(self.container_preview_buttons)

        self.lbl_preview_title = ScreenLabel("lbl_preview_title", "Zoom: 500%", 25, 290, 1)
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

        self.update_axes_buttons()
        self.update_axis_list_boxes()
        self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)

    def update_axis_list_boxes(self):
        self.lbx_info_axis_type.clear_options()
        self.lbx_info_axis_type.add_option(str(AxisValues.ValueTypeNumerical), "Numerical")
        self.lbx_info_axis_type.add_option(str(AxisValues.ValueTypeCategorical), "Categorical")

        self.lbx_info_ticks_type.clear_options()
        self.lbx_info_ticks_type.add_option(str(AxisValues.TicksTypeMarkers), "Markers")
        self.lbx_info_ticks_type.add_option(str(AxisValues.TicksTypeSeparators), "Separators")

        self.lbx_info_scale_type.clear_options()
        self.lbx_info_scale_type.add_option(str(AxisValues.ScaleNone), "None")
        self.lbx_info_scale_type.add_option(str(AxisValues.ScaleLinear), "Linear")
        self.lbx_info_scale_type.add_option(str(AxisValues.ScaleLogarithmic), "Logarithmic")

    def draw_axes_lines(self, modified_image):
        x1, y1, x2, y2 = self.axes.bounding_box
        x1, y1 = int(x1), int(y1)
        x2, y2 = int(x2), int(y2)

        # TODO: draw axis to reflect types
        # Axis Type: Numerical or Categorical
        # Tick Type: Marker or Separator
        # Scale Type: None, Linear, Logarithmic

        # X-1
        if self.edit_axis == ChartAxesAnnotator.AxisX1:
            cv2.line(modified_image, (x1, y2), (x2, y2), (128, 0, 0), thickness=2)  # x = Thick, Dark Red
        elif self.axes.x1_axis is not None:
            cv2.line(modified_image, (x1, y2), (x2, y2), (0, 0, 255), thickness=2)  # x = Thick, blue
        else:
            cv2.line(modified_image, (x1, y2), (x2, y2), (0, 0, 255), thickness=1)  # x = Thin, blue

        # X-2
        if self.edit_axis == ChartAxesAnnotator.AxisX2:
            cv2.line(modified_image, (x1, y1), (x2, y1), (128, 0, 0), thickness=2)  # x = Thick, Dark Red
        elif self.axes.x2_axis is not None:
            cv2.line(modified_image, (x1, y1), (x2, y1), (0, 0, 255), thickness=2)  # x = Thick, blue
        else:
            cv2.line(modified_image, (x1, y1), (x2, y1), (0, 0, 255), thickness=1)  # x = Thin, blue

        # Y-1
        if self.edit_axis == ChartAxesAnnotator.AxisY1:
            cv2.line(modified_image, (x1, y1), (x1, y2), (128, 0, 0), thickness=2)  # y = Thick, Dark red
        elif self.axes.y1_axis is not None:
            cv2.line(modified_image, (x1, y1), (x1, y2), (0, 255, 0), thickness=2)  # y = Thick, green
        else:
            cv2.line(modified_image, (x1, y1), (x1, y2), (0, 255, 0), thickness=1)  # y = Thin, green

        # Y-2
        if self.edit_axis == ChartAxesAnnotator.AxisY2:
            cv2.line(modified_image, (x2, y1), (x2, y2), (128, 0, 0), thickness=2)  # y = Thick, Dark red
        elif self.axes.y2_axis is not None:
            cv2.line(modified_image, (x2, y1), (x2, y2), (0, 255, 0), thickness=2)  # y = Thick, green
        else:
            cv2.line(modified_image, (x2, y1), (x2, y2), (0, 255, 0), thickness=1)  # y = Thin, green

    def axis_ticks_lines(self, axis_values, is_horizontal, axis_position, tick_length):
        if axis_values is None or axis_values.ticks is None:
            return []

        tempo_lines = []
        for tick_info in axis_values.ticks:
            if is_horizontal:
                # draw axis ticks on x...
                p1 = (int(tick_info.position), int(axis_position - tick_length))
                p2 = (int(tick_info.position), int(axis_position + tick_length))
            else:
                # draw axis ticks on y...
                p1 = (int(axis_position - tick_length), int(tick_info.position))
                p2 = (int(axis_position + tick_length), int(tick_info.position))

            tempo_lines.append((p1, p2, tick_info.label_id))

        return tempo_lines

    def draw_axis_ticks(self, modified_image):
        x1, y1, x2, y2 = self.axes.bounding_box
        x1, y1 = int(x1), int(y1)
        x2, y2 = int(x2), int(y2)

        h, w, c = modified_image.shape

        # draw ticks ...
        tempo_lines = []
        tempo_shadow_rects = []
        if self.edition_mode in [ChartAxesAnnotator.ModeTicksEdit, ChartAxesAnnotator.ModeTicksSelect]:
            # when in edit mode, only the axes being edited will be shown ...
            tick_length = 10

            # use tempo ticks ...
            if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                y_tick = y2 if self.edit_axis == ChartAxesAnnotator.AxisX1 else y1

                # tempo ticks for X axis ...
                for idx, tick_info in enumerate(self.tempo_ticks):
                    p1 = (int(tick_info.position), int(y_tick - tick_length))
                    p2 = (int(tick_info.position), int(y_tick + tick_length))

                    tempo_lines.append((p1, p2, tick_info.label_id))

                    # check if adding shadows ...
                    if self.edition_mode == ChartAxesAnnotator.ModeTicksSelect and self.tempo_tick_idx == idx:
                        # highlight
                        if idx > 0:
                            # left shadow
                            tempo_shadow_rects.append(((0, 0), (int(self.tempo_ticks[idx - 1].position), h)))
                        if idx + 1 < len(self.tempo_ticks):
                            # right shadow ...
                            tempo_shadow_rects.append(((int(self.tempo_ticks[idx + 1].position), 0), (w, h)))

            elif self.edit_axis in [ChartAxesAnnotator.AxisY1, ChartAxesAnnotator.AxisY2]:
                x_ticks = x1 if self.edit_axis == ChartAxesAnnotator.AxisY1 else x2
                # tempo ticks for Y axis ...
                for idx, tick_info in enumerate(self.tempo_ticks):
                    p1 = (int(x_ticks - tick_length), int(tick_info.position))
                    p2 = (int(x_ticks + tick_length), int(tick_info.position))
                    tempo_lines.append((p1, p2, tick_info.label_id))

                    # check if adding shadows ...
                    if self.edition_mode == ChartAxesAnnotator.ModeTicksSelect and self.tempo_tick_idx == idx:
                        # highlight
                        if idx > 0:
                            # top shadow
                            tempo_shadow_rects.append(((0, 0), (w, int(self.tempo_ticks[idx - 1].position))))
                        if idx + 1 < len(self.tempo_ticks):
                            # bottom shadow ...
                            tempo_shadow_rects.append(((0, int(self.tempo_ticks[idx + 1].position)), (w, h)))
        else:
            # when not in edit mode, multiple axis might be rendered ...
            tick_length = 5

            if self.edition_mode not in [ChartAxesAnnotator.ModeLabelPerTickEdit,
                                         ChartAxesAnnotator.ModeLabelPerTickSelect]:
                # is not on label tick edition/selection mode ... render all
                # note that this could be either temporal or absolute per each axis ...
                render_x1 = True
                render_y1 = True
                render_x2 = True
                render_y2 = True
            else:
                # only render the axis that is being edited (Label x Tick Edit/Select)
                render_x1 = (self.edit_axis == ChartAxesAnnotator.AxisX1)
                render_y1 = (self.edit_axis == ChartAxesAnnotator.AxisY1)
                render_x2 = (self.edit_axis == ChartAxesAnnotator.AxisX2)
                render_y2 = (self.edit_axis == ChartAxesAnnotator.AxisY2)

            if render_x1:
                if self.edit_axis == ChartAxesAnnotator.AxisX1:
                    tempo_axis = self.tempo_axis_values
                else:
                    tempo_axis = self.axes.x1_axis

                tempo_lines += self.axis_ticks_lines(tempo_axis, True, y2, tick_length)

            if render_x2:
                if self.edit_axis == ChartAxesAnnotator.AxisX2:
                    tempo_axis = self.tempo_axis_values
                else:
                    tempo_axis = self.axes.x2_axis

                tempo_lines += self.axis_ticks_lines(tempo_axis, True, y1, tick_length)

            if render_y1:
                if self.edit_axis == ChartAxesAnnotator.AxisY1:
                    tempo_axis = self.tempo_axis_values
                else:
                    tempo_axis = self.axes.y1_axis

                tempo_lines += self.axis_ticks_lines(tempo_axis, False, x1, tick_length)

            if render_y2:
                if self.edit_axis == ChartAxesAnnotator.AxisY2:
                    tempo_axis = self.tempo_axis_values
                else:
                    tempo_axis = self.axes.y2_axis

                tempo_lines += self.axis_ticks_lines(tempo_axis, False, x2, tick_length)

        # draw all tick lines ...
        for idx, (p1, p2, label_id) in enumerate(tempo_lines):
            if self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickSelect:
                if idx == self.tempo_tick_idx:
                    # red for selected tick
                    tick_color = (255, 0, 0)
                else:
                    # all other ticks in black
                    tick_color = (0, 0, 0)
            elif self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickEdit:
                # add ticks on changing colors ...
                tick_color = self.canvas_select.colors[idx % len(self.canvas_select.colors)]
            else:
                # check if tick has label ...
                if label_id is None:
                    # add ticks in red
                    tick_color = (255, 0, 0)
                else:
                    # tick has label, add in orange ..
                    tick_color = (255, 128, 64)

            cv2.line(modified_image, p1, p2, tick_color, thickness=2)

        return tempo_shadow_rects

    def draw_labels_and_titles(self, modified_image):
        # Labels ....
        labels_to_draw = []
        if self.edition_mode == ChartAxesAnnotator.ModeLabelsEdit:
            # use the temporary lists of labels ...
            if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                current_color = (0, 0, 255)
                other_color = (0, 255, 0)
            else:
                current_color = (0, 255, 0)
                other_color = (0, 0, 255)

            for text_id in self.axes.tick_labels:
                current_text = self.axes.tick_labels[text_id]

                if text_id in self.tempo_labels_axis:
                    # current axis
                    labels_to_draw.append((current_text.position_polygon, current_color))
                elif text_id in self.tempo_labels_unassigned:
                    # not assigned ...
                    labels_to_draw.append((current_text.position_polygon, (255, 0, 0)))
                else:
                    # assigned ... to another axis ...
                    labels_to_draw.append((current_text.position_polygon, other_color))

        elif self.edition_mode in [ChartAxesAnnotator.ModeAxisEdit, ChartAxesAnnotator.ModeAxisInfoEdit,
                                   ChartAxesAnnotator.ModeTitleSelect, ChartAxesAnnotator.ModeTicksEdit,
                                   ChartAxesAnnotator.ModeTicksSelect, ChartAxesAnnotator.ModeConfirmAxisDelete,
                                   ChartAxesAnnotator.ModeLabelPerTickEdit, ChartAxesAnnotator.ModeLabelPerTickSelect]:

            # Based on the temporary axis values structure

            # index of labels associated to ticks ...
            inv_label_index = {}
            if self.tempo_axis_values.ticks is not None:
                for idx, tick in enumerate(self.tempo_axis_values.ticks):
                    if tick.label_id is not None:
                        inv_label_index[tick.label_id] = idx

            # for all tick labels in the axis being edited ...
            for text_id in self.tempo_axis_values.labels:
                current_text = self.axes.tick_labels[text_id]

                # based on the status
                if self.edition_mode in [ChartAxesAnnotator.ModeLabelPerTickEdit,
                                         ChartAxesAnnotator.ModeLabelPerTickSelect]:
                    # used multiple colors ...
                    if text_id in inv_label_index:
                        # has assignment ...
                        color_idx = inv_label_index[text_id]
                        color = self.canvas_select.colors[color_idx % len(self.canvas_select.colors)]
                    else:
                        # unassigned label
                        color = (64, 64, 64)
                else:
                    # use axis color ...
                    if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                        color = (0, 0, 255)
                    else:
                        color = (0, 255, 0)

                labels_to_draw.append((current_text.position_polygon, color))

            # Axes Titles
            for text_id in self.axes.axes_titles:
                current_text = self.axes.axes_titles[text_id]

                # check assignments considering that one axis is being edited and the assignment on the temporal
                # should be considered ....
                if ((self.edit_axis == ChartAxesAnnotator.AxisX1 and self.tempo_axis_values.title == text_id) or
                    (self.edit_axis != ChartAxesAnnotator.AxisX1 and self.axes.x1_axis is not None and self.axes.x1_axis.title == text_id)):
                    labels_to_draw.append((current_text.position_polygon, (0, 0, 255)))
                elif ((self.edit_axis == ChartAxesAnnotator.AxisX2 and self.tempo_axis_values.title == text_id) or
                      (self.edit_axis != ChartAxesAnnotator.AxisX2 and self.axes.x2_axis is not None and self.axes.x2_axis.title == text_id)):
                    labels_to_draw.append((current_text.position_polygon, (0, 0, 255)))
                elif ((self.edit_axis == ChartAxesAnnotator.AxisY1 and self.tempo_axis_values.title == text_id) or
                      (self.edit_axis != ChartAxesAnnotator.AxisY1 and self.axes.y1_axis is not None and self.axes.y1_axis.title == text_id)):
                    labels_to_draw.append((current_text.position_polygon, (0, 255, 0)))
                elif ((self.edit_axis == ChartAxesAnnotator.AxisY2 and self.tempo_axis_values.title == text_id) or
                      (self.edit_axis != ChartAxesAnnotator.AxisY2 and self.axes.y2_axis is not None and self.axes.y2_axis.title == text_id)):
                    labels_to_draw.append((current_text.position_polygon, (0, 255, 0)))
                else:
                    # not assigned ...
                    labels_to_draw.append((current_text.position_polygon, (255, 0, 0)))
        else:
            # in general ... no temporals being used ....

            # Tick Labels
            for text_id in self.axes.tick_labels:
                current_text = self.axes.tick_labels[text_id]

                label_axis = self.axes.find_label_axis(text_id)
                if label_axis in [AxesInfo.AxisX1, AxesInfo.AxisX2]:
                    # assigned to either X1 or X2
                    labels_to_draw.append((current_text.position_polygon, (0, 0, 255)))
                elif label_axis in [AxesInfo.AxisY1, AxesInfo.AxisY2]:
                    # assigned to either Y1 or Y2
                    labels_to_draw.append((current_text.position_polygon, (0, 255, 0)))
                else:
                    # not assigned ...
                    labels_to_draw.append((current_text.position_polygon, (255, 0, 0)))

            # Axes Titles
            for text_id in self.axes.axes_titles:
                current_text = self.axes.axes_titles[text_id]

                if ((self.axes.x1_axis is not None and self.axes.x1_axis.title == text_id) or
                        (self.axes.x2_axis is not None and self.axes.x2_axis.title == text_id)):
                    # assigned to either X-1 or X-2 axis
                    labels_to_draw.append((current_text.position_polygon, (0, 0, 255)))
                elif ((self.axes.y1_axis is not None and self.axes.y1_axis.title == text_id) or
                      (self.axes.y2_axis is not None and self.axes.y2_axis.title == text_id)):
                    # assigned to either Y-1 or Y-2 axis
                    labels_to_draw.append((current_text.position_polygon, (0, 255, 0)))
                else:
                    # not assigned ...
                    labels_to_draw.append((current_text.position_polygon, (255, 0, 0)))

        for polygon, color in labels_to_draw:
            modified_image = cv2.polylines(modified_image, [polygon.astype(np.int32)], True, color, thickness=1)

        return modified_image

    def custom_view_update(self, modified_image):
        if self.axes.bounding_box is not None:
            self.draw_axes_lines(modified_image)
            tempo_shadow_rects = self.draw_axis_ticks(modified_image)
            modified_image = self.draw_labels_and_titles(modified_image)

            # shadow rectangles ???
            for (c1, r1), (c2, r2) in tempo_shadow_rects:
                modified_image[r1:r2, c1:c2] = (modified_image[r1:r2, c1:c2] / 2).astype(np.uint8)

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        if self.edition_mode == ChartAxesAnnotator.ModeNavigate:
            self.container_annotation_buttons.visible = True

            axes_description = ""
            axis_desc = "{0:s}: {1:s} ({2:s}) - {3:s}\n"
            if self.axes.x1_axis is not None:
                value_type_str, ticks_type_str, scale_type_str = self.axes.x1_axis.get_description()
                axes_description += axis_desc.format("X-1", value_type_str, scale_type_str, ticks_type_str)

            if self.axes.y1_axis is not None:
                value_type_str, ticks_type_str, scale_type_str = self.axes.y1_axis.get_description()
                axes_description += axis_desc.format("Y-1", value_type_str, scale_type_str, ticks_type_str)

            if self.axes.x2_axis is not None:
                value_type_str, ticks_type_str, scale_type_str = self.axes.x2_axis.get_description()
                axes_description += axis_desc.format("X-2", value_type_str, scale_type_str, ticks_type_str)

            if self.axes.y2_axis is not None:
                value_type_str, ticks_type_str, scale_type_str = self.axes.y2_axis.get_description()
                axes_description += axis_desc.format("Y-2", value_type_str, scale_type_str, ticks_type_str)

            if axes_description == "":
                axes_description = "No Axes Annotations"

            self.lbl_edit_axes_summary.set_text(axes_description)
        else:
            self.container_annotation_buttons.visible = False

        # edit modes ...
        self.container_axis_buttons.visible = (self.edition_mode == ChartAxesAnnotator.ModeAxisEdit)
        self.container_info_buttons.visible = (self.edition_mode == ChartAxesAnnotator.ModeAxisInfoEdit)
        self.container_ticks_buttons.visible = (self.edition_mode == ChartAxesAnnotator.ModeTicksEdit)
        self.container_labels_buttons.visible = (self.edition_mode == ChartAxesAnnotator.ModeLabelsEdit)
        self.container_labels_per_tick_buttons.visible = (self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickEdit)
        self.container_preview_buttons.visible = self.edition_mode in [ChartAxesAnnotator.ModeBBoxSelect,
                                                                       ChartAxesAnnotator.ModeBBoxEdit,
                                                                       ChartAxesAnnotator.ModeTicksSelect]

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ChartAxesAnnotator.ModeBBoxSelect,
                                                                       ChartAxesAnnotator.ModeBBoxEdit,
                                                                       ChartAxesAnnotator.ModeTitleSelect,
                                                                       ChartAxesAnnotator.ModeTicksSelect,
                                                                       ChartAxesAnnotator.ModeLabelPerTickSelect,
                                                                       ChartAxesAnnotator.ModeConfirmExit,
                                                                       ChartAxesAnnotator.ModeConfirmAxisDelete]

        if self.edition_mode == ChartAxesAnnotator.ModeBBoxSelect:
            self.lbl_confirm_message.set_text("Select Axes Location")
        elif self.edition_mode == ChartAxesAnnotator.ModeBBoxEdit:
            self.lbl_confirm_message.set_text("Editing Axes Location")
        elif self.edition_mode == ChartAxesAnnotator.ModeTitleSelect:
            if self.edit_axis == ChartAxesAnnotator.AxisX1:
                self.lbl_confirm_message.set_text("Select X-1 Axis Title")
            elif self.edit_axis == ChartAxesAnnotator.AxisX2:
                self.lbl_confirm_message.set_text("Select X-2 Axis Title")
            elif self.edit_axis == ChartAxesAnnotator.AxisY1:
                self.lbl_confirm_message.set_text("Select Y-1 Axis Title")
            elif self.edit_axis == ChartAxesAnnotator.AxisY2:
                self.lbl_confirm_message.set_text("Select Y-2 Axis Title")
            else:
                raise Exception("Invalid Axis")

        elif self.edition_mode == ChartAxesAnnotator.ModeTicksSelect:
            self.lbl_confirm_message.set_text("Select Tick Location")
        elif self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickSelect:
            self.lbl_confirm_message.set_text("Select Label for Tick")
        elif self.edition_mode == ChartAxesAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Axes?")
        elif self.edition_mode == ChartAxesAnnotator.ModeConfirmAxisDelete:
            self.lbl_confirm_message.set_text("Discard Axis Annotations?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode not in [ChartAxesAnnotator.ModeBBoxSelect,
                                                                    ChartAxesAnnotator.ModeTitleSelect,
                                                                    ChartAxesAnnotator.ModeTicksSelect,
                                                                    ChartAxesAnnotator.ModeLabelPerTickSelect]

        if new_mode in [ChartAxesAnnotator.ModeBBoxEdit]:
            # show polygon
            self.canvas_select.locked = False
            self.canvas_select.elements["selection_rectangle"].visible = True
        else:
            # for every other mode
            self.canvas_select.locked = True
            self.canvas_select.elements["selection_rectangle"].visible = False

        if new_mode == ChartAxesAnnotator.ModeAxisEdit:
            self.update_current_view(False)

            if self.edit_axis == ChartAxesAnnotator.AxisX1:
                self.lbl_axis_title.set_text("X-1 - Axis Edition Options")
                self.btn_axis_delete.visible = self.axes.x1_axis is not None
            elif self.edit_axis == ChartAxesAnnotator.AxisX2:
                self.lbl_axis_title.set_text("X-2 - Axis Edition Options")
                self.btn_axis_delete.visible = self.axes.x2_axis is not None
            elif self.edit_axis == ChartAxesAnnotator.AxisY1:
                self.lbl_axis_title.set_text("Y-1 - Axis Edition Options")
                self.btn_axis_delete.visible = self.axes.y1_axis is not None
            elif self.edit_axis == ChartAxesAnnotator.AxisY2:
                self.lbl_axis_title.set_text("Y-2 - Axis Edition Options")
                self.btn_axis_delete.visible = self.axes.y2_axis is not None
            else:
                raise Exception("Invalid Axis")

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [ChartAxesAnnotator.ModeBBoxEdit, ChartAxesAnnotator.ModeBBoxSelect,
                                 ChartAxesAnnotator.ModeConfirmExit]:
            # return to navigation
            self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)

        elif self.edition_mode == ChartAxesAnnotator.ModeTitleSelect:
            # return to title edition
            self.set_editor_mode(ChartAxesAnnotator.ModeAxisInfoEdit)
            self.update_current_view(False)

        elif self.edition_mode == ChartAxesAnnotator.ModeTicksSelect:
            # return to tick edition
            self.set_editor_mode(ChartAxesAnnotator.ModeTicksEdit)
            self.update_current_view(False)

        elif self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickSelect:
            # return to label per tick edition
            self.set_editor_mode(ChartAxesAnnotator.ModeLabelPerTickEdit)
            self.update_current_view(False)

        elif self.edition_mode == ChartAxesAnnotator.ModeConfirmAxisDelete:
            # return to axis edit ...
            self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)
            self.update_current_view(False)

        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == ChartAxesAnnotator.ModeConfirmExit:
            print("-> Changes made to Axes Annotations were lost")
            self.return_screen = self.parent_screen
        elif self.edition_mode == ChartAxesAnnotator.ModeBBoxEdit:
            # get rectangle ...
            sel_rectangle = self.canvas_select.elements["selection_rectangle"]
            x1 = sel_rectangle.x / self.view_scale
            y1 = sel_rectangle.y / self.view_scale
            x2 = x1 + (sel_rectangle.w / self.view_scale)
            y2 = y1 + (sel_rectangle.h / self.view_scale)

            self.axes.bounding_box = (x1, y1, x2, y2)

            # use heuristics to associate labels with axis ....
            if self.axes.empty_axes():
                self.auto_infer_axes_using_tick_centers_distances_to_axes()

            self.data_changed = True
            self.update_axes_buttons()
            self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)
            self.update_current_view(False)

        elif self.edition_mode == ChartAxesAnnotator.ModeConfirmAxisDelete:
            # remove info ...
            if self.edit_axis == ChartAxesAnnotator.AxisX1:
                self.axes.x1_axis = None
            elif self.edit_axis == ChartAxesAnnotator.AxisX2:
                self.axes.x2_axis = None
            elif self.edit_axis == ChartAxesAnnotator.AxisY1:
                self.axes.y1_axis = None
            elif self.edit_axis == ChartAxesAnnotator.AxisY2:
                self.axes.y2_axis = None
            else:
                raise Exception("Invalid Axis Selected for deletion")

            self.edit_axis = None
            self.data_changed = True

            self.update_axes_buttons()
            self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)
            self.update_current_view(False)
        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def get_axes_default_types(self):
        # some general assumptions per chart type ... (should change later)
        if self.panel_info.type in [ChartInfo.TypeBar, ChartInfo.TypeBox]:
            independent_value_type = AxisValues.ValueTypeCategorical
            independent_ticks_type = AxisValues.TicksTypeSeparators
            independent_value_scale = AxisValues.ScaleNone
        else:
            independent_value_type = AxisValues.ValueTypeNumerical
            independent_ticks_type = AxisValues.TicksTypeMarkers
            independent_value_scale = AxisValues.ScaleLinear

        # by default ...
        dependent_value_type = AxisValues.ValueTypeNumerical
        dependent_ticks_type = AxisValues.TicksTypeMarkers
        dependent_value_scale = AxisValues.ScaleLinear

        if self.panel_info.orientation == ChartInfo.OrientationHorizontal:
            # X are dependent
            x_value_type = dependent_value_type
            x_ticks_type = dependent_ticks_type
            x_value_scale = dependent_value_scale

            # Y is independent ...
            y_value_type = independent_value_type
            y_ticks_type = independent_ticks_type
            y_value_scale = independent_value_scale
        else:
            # X is independent
            x_value_type = independent_value_type
            x_ticks_type = independent_ticks_type
            x_value_scale = independent_value_scale

            # Y are dependent
            y_value_type = dependent_value_type
            y_ticks_type = dependent_ticks_type
            y_value_scale = dependent_value_scale

        return (x_value_type, x_ticks_type, x_value_scale), (y_value_type, y_ticks_type, y_value_scale)

    def boxes_centers_to_lines_distances(self, text_boxes_dict, lines):
        # get all distances from each label ....
        all_distances = np.zeros((len(text_boxes_dict), len(lines)), dtype=np.float64)
        for idx, text_id in enumerate(text_boxes_dict):
            # use centroid of polygon coordinates ...
            p = Point(text_boxes_dict[text_id].position_polygon.mean(axis=0))

            for line_idx, line in enumerate(lines):
                all_distances[idx, line_idx] = line.distance(p)

        return all_distances

    def auto_infer_axes_using_tick_centers_distances_to_axes(self):
        # A naive basic method to infer axes using tick labels and axis bounding

        # define the default axes types ...
        x_default_types, y_default_types = self.get_axes_default_types()
        x_value_type, x_ticks_type, x_value_scale = x_default_types
        y_value_type, y_ticks_type, y_value_scale = y_default_types

        # Axes lines ...
        x1, y1, x2, y2 = self.axes.bounding_box
        line_x1 = LineString([(x1, y2), (x2, y2)])
        line_x2 = LineString([(x1, y1), (x2, y1)])
        line_y1 = LineString([(x1, y1), (x1, y2)])
        line_y2 = LineString([(x2, y1), (x2, y2)])

        # get all distances from each label ....
        current_lines = [line_x1, line_y1, line_x2, line_y2]
        all_distances = self.boxes_centers_to_lines_distances(self.axes.tick_labels, current_lines)

        closest = np.argmin(all_distances, axis=1)

        # Naive heuristic to decide which axes seem to be visible ...
        if (closest == 0).sum() > 0:
            self.axes.x1_axis = AxisValues(x_value_type, x_ticks_type, x_value_scale)

        if (closest == 1).sum() > 0:
            self.axes.y1_axis = AxisValues(y_value_type, y_ticks_type, y_value_scale)

        if (closest == 2).sum() > 0:
            self.axes.x2_axis = AxisValues(x_value_type, x_ticks_type, x_value_scale)

        if (closest == 3).sum() > 0:
            self.axes.y2_axis = AxisValues(y_value_type, y_ticks_type, y_value_scale)

        # Assign each tick label to the closest existing axis ...
        for idx, text_id in enumerate(self.axes.tick_labels):
            # iterate through the axes ... based on distance ...
            # this is needed in case that the closest axis has not been added ...
            # then the tick will be added to the next closest existing axis ...
            for axis_index in np.argsort(all_distances[idx]):
                if axis_index == 0 and self.axes.x1_axis is not None:
                    # Closer to X1
                    self.axes.x1_axis.labels.append(text_id)
                    break
                if axis_index == 1 and self.axes.y1_axis is not None:
                    # Closer to Y1
                    self.axes.y1_axis.labels.append(text_id)
                    break
                if axis_index == 2 and self.axes.x2_axis is not None:
                    # Closer to X2
                    self.axes.x2_axis.labels.append(text_id)
                    break
                if axis_index == 3 and self.axes.y2_axis is not None:
                    # Closer to Y2
                    self.axes.y2_axis.labels.append(text_id)
                    break

        # Axes Titles
        title_distances = self.boxes_centers_to_lines_distances(self.axes.axes_titles, current_lines)

        for idx, text_id in enumerate(self.axes.axes_titles):
            # iterate through the axes ... based on distance ...
            # same as done with tick labels ...
            for axis_index in np.argsort(title_distances[idx]):
                if axis_index == 0 and self.axes.x1_axis is not None:
                    # Closer to X1
                    self.axes.x1_axis.title = text_id
                    break
                if axis_index == 1 and self.axes.y1_axis is not None:
                    # Closer to Y1
                    self.axes.y1_axis.title = text_id
                    break
                if axis_index == 2 and self.axes.x2_axis is not None:
                    # Closer to X2
                    self.axes.x2_axis.title = text_id
                    break
                if axis_index == 3 and self.axes.y2_axis is not None:
                    # Closer to Y2
                    self.axes.y2_axis.title = text_id
                    break

        if self.axes.x1_axis is None:
            print("No X1")
        else:
            print("X1 has {0:d} labels and {1:s} title".format(len(self.axes.x1_axis.labels),
                                                               "NO" if self.axes.x1_axis.title is None else "A"))

        if self.axes.y1_axis is None:
            print("No Y1")
        else:
            print("Y1 has {0:d} labels and {1:s} title".format(len(self.axes.y1_axis.labels),
                                                               "NO" if self.axes.y1_axis.title is None else "A"))

        if self.axes.x2_axis is None:
            print("No X2")
        else:
            print("X2 has {0:d} labels and {1:s} title".format(len(self.axes.x2_axis.labels),
                                                               "NO" if self.axes.x2_axis.title is None else "A"))

        if self.axes.y2_axis is None:
            print("No Y2")
        else:
            print("Y2 has {0:d} labels and {1:s} title".format(len(self.axes.y2_axis.labels),
                                                               "NO" if self.axes.y2_axis.title is None else "A"))

    def img_main_mouse_button_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode == ChartAxesAnnotator.ModeBBoxSelect:
                rect_x, rect_y = pos

                # default size .... based on estimations from text ....
                tick_labels = self.panel_info.get_all_text(TextInfo.TypeTickLabel)
                if len(tick_labels) > 0:
                    all_tick_centers = np.array([label.get_center() for label in tick_labels])
                    min_x, max_x = all_tick_centers[:, 0].min(), all_tick_centers[:, 0].max()
                    min_y, max_y = all_tick_centers[:, 1].min(), all_tick_centers[:, 1].max()

                    rect_w = (max_x - min_x) * 0.90 * self.view_scale
                    rect_h = (max_y - min_y) * 0.90 * self.view_scale
                else:
                    # default arbitrary size ...
                    rect_w, rect_h = 30, 30

                self.canvas_select.elements["selection_rectangle"].update(rect_x, rect_y, rect_w, rect_h)

                self.set_editor_mode(ChartAxesAnnotator.ModeBBoxEdit)

            elif self.edition_mode == ChartAxesAnnotator.ModeTicksSelect:
                click_x, click_y = pos

                if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                    position = click_x / self.view_scale
                elif self.edit_axis in [ChartAxesAnnotator.AxisY1, ChartAxesAnnotator.AxisY2]:
                    position = click_y / self.view_scale
                else:
                    raise Exception("Invalid Axis")

                # validate position ...
                if (self.tempo_tick_idx > 0 and
                        self.tempo_ticks[self.tempo_tick_idx - 1].position > position):
                    print("Cannot move the tick before the position of its previous neighbor")
                    return

                if (self.tempo_tick_idx + 1 < len(self.tempo_ticks) and
                    self.tempo_ticks[self.tempo_tick_idx + 1].position < position):
                    print("Cannot move the tick after the position of its next neighbor")
                    return

                self.tempo_ticks[self.tempo_tick_idx].position = position

                self.set_editor_mode(ChartAxesAnnotator.ModeTicksEdit)
                self.update_current_view(False)

            elif self.edition_mode == ChartAxesAnnotator.ModeLabelPerTickSelect:
                # click pos ...
                click_x, click_y = pos
                click_x /= self.view_scale
                click_y /= self.view_scale

                point = Point((click_x, click_y))

                # check for labels on current axis ...
                inv_label_index = {}
                for idx, tick in enumerate(self.tempo_axis_values.ticks):
                    if tick.label_id is not None:
                        inv_label_index[tick.label_id] = idx

                for text_id in self.tempo_axis_values.labels:
                    current_text = self.axes.tick_labels[text_id]

                    # check if click point intersects polygon
                    current_polygon = Polygon(current_text.position_polygon)

                    if current_polygon.contains(point):
                        # click on a given text object!
                        if text_id in inv_label_index:
                            # this text label is already associated with a tick, ignore if same ....
                            if inv_label_index[text_id] == self.tempo_tick_idx:
                                # same ... just go back ....
                                self.set_editor_mode(ChartAxesAnnotator.ModeLabelPerTickEdit)
                                self.update_current_view()
                            else:
                                # different, show error message ...
                                print("This Label is already associated with another tick")
                                print("remove existing association first")
                        else:
                            # the selected label is not associated with any tick yet, link!
                            # ... logically ...
                            self.tempo_axis_values.ticks[self.tempo_tick_idx].label_id = text_id
                            # ... update GUI ....
                            assign_desc = self.get_text_description(current_text)
                            full_display = "{0:d} - [{1:s}]".format(self.tempo_tick_idx + 1, assign_desc)
                            self.lbx_lpt_assignments.update_option_display(str(self.tempo_tick_idx), full_display)

                            # go back ....
                            self.set_editor_mode(ChartAxesAnnotator.ModeLabelPerTickEdit)
                            self.update_current_view()

                        break

            elif self.edition_mode == ChartAxesAnnotator.ModeTitleSelect:
                # click pos ...
                click_x, click_y = pos
                click_x /= self.view_scale
                click_y /= self.view_scale

                point = Point((click_x, click_y))

                current_title_id = self.tempo_axis_values.title

                # get all other titles (not including the title selected for the current axis in the original structure)
                other_titles = []
                if (self.edit_axis != ChartAxesAnnotator.AxisX1 and
                    self.axes.x1_axis is not None and self.axes.x1_axis.title is not None):
                    other_titles.append(self.axes.x1_axis.title)
                if (self.edit_axis != ChartAxesAnnotator.AxisX2 and
                    self.axes.x2_axis is not None and self.axes.x2_axis.title is not None):
                    other_titles.append(self.axes.x2_axis.title)
                if (self.edit_axis != ChartAxesAnnotator.AxisY1 and
                    self.axes.y1_axis is not None and self.axes.y1_axis.title is not None):
                    other_titles.append(self.axes.y1_axis.title)
                if (self.edit_axis != ChartAxesAnnotator.AxisY2 and
                    self.axes.y2_axis is not None and self.axes.y2_axis.title is not None):
                    other_titles.append(self.axes.y2_axis.title)

                for text_id in self.axes.axes_titles:
                    current_text = self.axes.axes_titles[text_id]

                    # check if click point intersects polygon
                    current_polygon = Polygon(current_text.position_polygon)

                    if current_polygon.contains(point):
                        # click on a given text object!
                        if text_id in other_titles:
                            # this text label is already associate with an axis
                            # show error message ...
                            print("This Label is already associated with another Axis")
                            print("remove existing association first")
                            return
                        else:
                            if text_id != current_title_id:
                                # link!
                                self.tempo_axis_values.title = text_id
                                # ... update GUI ....
                                self.update_axis_title()

                            # go back ....
                            self.set_editor_mode(ChartAxesAnnotator.ModeAxisInfoEdit)
                            self.update_current_view()

                        break

    def btn_edit_bbox_click(self, button):
        if self.axes.bounding_box is None:
            self.set_editor_mode(ChartAxesAnnotator.ModeBBoxSelect)
        else:
            x1, y1, x2, y2 = self.axes.bounding_box
            rect_x = x1 * self.view_scale
            rect_y = y1 * self.view_scale
            rect_w = (x2 - x1) * self.view_scale
            rect_h = (y2 - y1) * self.view_scale

            self.canvas_select.elements["selection_rectangle"].update(rect_x, rect_y, rect_w, rect_h)
            self.set_editor_mode(ChartAxesAnnotator.ModeBBoxEdit)

    def prepare_ticks_edition(self):
        x1, y1, x2, y2 = self.axes.bounding_box

        if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
            # Horizontal axis ... use x boundaries by default
            if self.tempo_axis_values.ticks is None:
                self.tempo_ticks = [TickInfo(x1), TickInfo(x2)]
            else:
                self.tempo_ticks = list(self.tempo_axis_values.ticks)

        elif self.edit_axis in [ChartAxesAnnotator.AxisY1, ChartAxesAnnotator.AxisY2]:
            # Vertical axis ... use y boundaries by default
            if self.tempo_axis_values.ticks is None:
                self.tempo_ticks = [TickInfo(y1), TickInfo(y2)]
            else:
                self.tempo_ticks = list(self.tempo_axis_values.ticks)

        else:
            print(self.edit_axis)
            raise Exception("Invalid axis selection")

        # ... GUI ....
        self.update_tick_GUI()

    def update_tick_GUI(self):
        if self.edit_axis == ChartAxesAnnotator.AxisX1:
            axis_str = "X-1"
        elif self.edit_axis == ChartAxesAnnotator.AxisY1:
            axis_str = "Y-1"
        elif self.edit_axis == ChartAxesAnnotator.AxisX2:
            axis_str = "X-2"
        elif self.edit_axis == ChartAxesAnnotator.AxisY2:
            axis_str = "Y-2"
        else:
            raise Exception("Invalid axis selection")

        self.lbl_ticks_count.set_text("{0:s} Axis: {1:d} Ticks".format(axis_str, len(self.tempo_ticks)))

        self.lbx_ticks_list.clear_options()
        for idx, tick_info in enumerate(self.tempo_ticks):
            self.lbx_ticks_list.add_option(str(idx), str(idx + 1))

    def get_text_description(self, text):
        return "{0:d} - {1:s}".format(text.id, text.value)

    def prepare_labels_edition(self):
        if self.tempo_axis_values.labels is None:
            self.tempo_labels_axis = []
        else:
            self.tempo_labels_axis = list(self.tempo_axis_values.labels)

        # get list of unassigned!!
        # ... start from the entire set ...
        pending_unassigned = set(self.axes.tick_labels.keys())
        # ... subtract each axis ... (that is not being edited)
        if self.edit_axis != AxesInfo.AxisX1 and self.axes.x1_axis is not None and self.axes.x1_axis.labels is not None:
            pending_unassigned -= set(self.axes.x1_axis.labels)
        if self.edit_axis != AxesInfo.AxisX2 and self.axes.x2_axis is not None and self.axes.x2_axis.labels is not None:
            pending_unassigned -= set(self.axes.x2_axis.labels)
        if self.edit_axis != AxesInfo.AxisY1 and self.axes.y1_axis is not None and self.axes.y1_axis.labels is not None:
            pending_unassigned -= set(self.axes.y1_axis.labels)
        if self.edit_axis != AxesInfo.AxisY2 and self.axes.y2_axis is not None and self.axes.y2_axis.labels is not None:
            pending_unassigned -= set(self.axes.y2_axis.labels)
        # ... finally, substract the axis being edited ...
        if self.tempo_axis_values.labels is not None:
            pending_unassigned -= set(self.tempo_axis_values.labels)

        self.tempo_labels_unassigned = list(pending_unassigned)

        # add to the lists of options
        self.lbx_labels_axis.clear_options()
        for text_id in self.tempo_labels_axis:
            self.lbx_labels_axis.add_option(str(text_id), self.get_text_description(self.axes.tick_labels[text_id]))

        self.lbx_labels_unassigned.clear_options()
        for text_id in self.tempo_labels_unassigned:
            self.lbx_labels_unassigned.add_option(str(text_id), self.get_text_description(self.axes.tick_labels[text_id]))

    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing axes data ...
            self.panel_info.axes = AxesInfo.Copy(self.axes)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(ChartAxesAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen

    def btn_ticks_decrease_click(self, button):
        if len(self.tempo_ticks) == 0:
            print("Cannot reduce the number of ticks for this axis")
            return

        if len(self.tempo_ticks) >= 2:
            # delete the second tick ...
            del self.tempo_ticks[1]
        else:
            # delete the only tick
            del self.tempo_ticks[0]

        self.redistribute_ticks()
        self.update_current_view(False)

    def btn_ticks_increase_click(self, button):
        if len(self.tempo_ticks) >= 2:
            # insert a tick anywhere between first and last
            self.tempo_ticks.insert(1, TickInfo(None, None))
        else:
            # harder cases ....
            x1, y1, x2, y2 = self.axes.bounding_box

            if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                # Horizontal axis ... use x boundaries by default
                x_c = int((x1 + x2) / 2)
                if len(self.tempo_ticks) == 0:
                    # use center ...
                    self.tempo_ticks = [TickInfo(x_c, None)]
                else:
                    if self.tempo_ticks[0].position < x_c:
                        # use right end
                        self.tempo_ticks.insert(1, TickInfo(x2, None))
                    else:
                        # use left end
                        self.tempo_ticks.insert(0, TickInfo(x1, None))

            elif self.edit_axis in [ChartAxesAnnotator.AxisY1, ChartAxesAnnotator.AxisY2]:
                # Vertical axis ... use y boundaries by default
                y_c = int((y1 + y2) / 2)
                if len(self.tempo_ticks) == 0:
                    # use center ...
                    self.tempo_ticks = [TickInfo(y_c, None)]
                else:
                    if self.tempo_ticks[0].position < y_c:
                        # use bottom end
                        self.tempo_ticks.insert(1, TickInfo(y2, None))
                    else:
                        # use top end
                        self.tempo_ticks.insert(0, TickInfo(y1, None))

        self.redistribute_ticks()
        self.update_current_view(False)

    def btn_ticks_redistribute_click(self, button):
        self.redistribute_ticks()
        self.update_current_view(False)

    def redistribute_ticks(self):
        if len(self.tempo_ticks) >= 2:
            min_pos = self.tempo_ticks[0].position
            max_pos = self.tempo_ticks[-1].position
            step = (max_pos - min_pos) / (len(self.tempo_ticks) - 1)

            for idx in range(1, len(self.tempo_ticks) - 1):
                self.tempo_ticks[idx].position = min_pos + idx * step

        self.update_tick_GUI()

    def lbx_ticks_list_changed(self, new_value, old_value):
        pass

    def btn_ticks_set_click(self, button):
        if self.lbx_ticks_list.selected_option_value is None:
            print("Must select a Tick ")
            return

        self.tempo_tick_idx = int(self.lbx_ticks_list.selected_option_value)
        self.set_editor_mode(ChartAxesAnnotator.ModeTicksSelect)
        self.update_current_view(False)

    def btn_ticks_return_click(self, button):
        # set the ticks on the temporal axis values ...
        self.tempo_axis_values.ticks = self.tempo_ticks

        # return ....
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)
        self.update_current_view(False)

    def lbx_labels_unassigned_changed(self, new_value, old_value):
        pass

    def lbx_labels_axis_changed(self, new_value, old_value):
        pass

    def btn_labels_add_click(self, button):
        if self.lbx_labels_unassigned.selected_option_value is None:
            print("Must select an unassigned label")
            return

        add_text_id = int(self.lbx_labels_unassigned.selected_option_value)
        add_text_display = self.lbx_labels_unassigned.option_display[self.lbx_labels_unassigned.selected_option_value]

        # (add to one list, remove from the other)
        self.tempo_labels_axis.append(add_text_id)
        self.tempo_labels_unassigned.remove(add_text_id)

        # update GUI ...
        # (add to one list, remove from the other, update visualization)
        self.lbx_labels_axis.add_option(str(add_text_id), add_text_display)
        self.lbx_labels_unassigned.remove_option(str(add_text_id))
        self.update_current_view(True)

    def btn_labels_remove_click(self, button):
        if self.lbx_labels_axis.selected_option_value is None:
            print("Must select an axis label")
            return

        remove_text_id = int(self.lbx_labels_axis.selected_option_value)
        remove_text_display = self.lbx_labels_axis.option_display[self.lbx_labels_axis.selected_option_value]

        # (add to one list, remove from the other)
        self.tempo_labels_unassigned.append(remove_text_id)
        self.tempo_labels_axis.remove(remove_text_id)

        # update GUI ...
        # (add to one list, remove from the other, update visualization)
        self.lbx_labels_unassigned.add_option(str(remove_text_id), remove_text_display)
        self.lbx_labels_axis.remove_option(str(remove_text_id))
        self.update_current_view(True)

    def btn_labels_return_click(self, button):
        self.tempo_axis_values.labels = list(self.tempo_labels_axis)

        # return ....
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)
        self.update_current_view(False)

    def prepare_labels_per_tick(self):
        self.lbx_lpt_assignments.clear_options()

        for idx, tick_info in enumerate(self.tempo_axis_values.ticks):
            if tick_info.label_id is None:
                assign_desc = ""
            else:
                assign_desc = self.get_text_description(self.axes.tick_labels[tick_info.label_id])

            full_display = "{0:d} - [{1:s}]".format(idx + 1, assign_desc)
            self.lbx_lpt_assignments.add_option(str(idx), full_display)

    def lbx_lpt_assignments_changed(self, new_value, old_value):
        pass

    def btn_lpt_assign_click(self, button):
        if self.lbx_lpt_assignments.selected_option_value is None:
            print("Must select a tick from the list!")
            return

        self.tempo_tick_idx = int(self.lbx_lpt_assignments.selected_option_value)
        self.set_editor_mode(ChartAxesAnnotator.ModeLabelPerTickSelect)
        self.update_current_view()

    def btn_lpt_remove_click(self, button):
        if self.lbx_lpt_assignments.selected_option_value is None:
            print("Must select a tick from the list!")
            return

        # remove link!
        self.tempo_tick_idx = int(self.lbx_lpt_assignments.selected_option_value)
        self.tempo_axis_values.ticks[self.tempo_tick_idx].label_id = None

        # update GUI
        full_display = "{0:d} - [{1:s}]".format(self.tempo_tick_idx + 1, "")
        self.lbx_lpt_assignments.update_option_display(str(self.tempo_tick_idx), full_display)
        self.update_current_view()

    def btn_lpt_auto_click(self, button):
        # do the auto assignment ....
        x1, y1, x2, y2 = self.axes.bounding_box

        # ... get all point representations for each tick ...
        all_tick_points = []
        for tick_idx, tick_info in enumerate(self.tempo_axis_values.ticks):
            # point depends on axis
            if self.edit_axis == ChartAxesAnnotator.AxisX1:
                all_tick_points.append(Point((tick_info.position, y2)))
            elif self.edit_axis == ChartAxesAnnotator.AxisX2:
                all_tick_points.append(Point((tick_info.position, y1)))
            elif self.edit_axis == ChartAxesAnnotator.AxisY1:
                all_tick_points.append(Point((x1, tick_info.position)))
            elif self.edit_axis == ChartAxesAnnotator.AxisY2:
                all_tick_points.append(Point((x2, tick_info.position)))

            # remove any existing link
            tick_info.label_id = None

        # ... get the polygon representations for each label ...
        all_label_polygons = []
        for text_id in self.tempo_axis_values.labels:
            current_text = self.axes.tick_labels[text_id]

            # check if click point intersects polygon
            current_polygon = Polygon(current_text.position_polygon)

            all_label_polygons.append((text_id, current_polygon))

        # ... get all pairwise distances ...
        # ... prepare squared cost matrix with dummy entries ...
        n_max = max(len(all_tick_points), len(all_label_polygons))
        cost_matrix = np.zeros((n_max, n_max), dtype=np.float64)
        for tick_idx, tick_point in enumerate(all_tick_points):
            for text_offset, (text_id, label_polygon) in enumerate(all_label_polygons):
                cost_matrix[tick_idx, text_offset] = label_polygon.distance(tick_point)

        # dummy values ....
        max_cost = cost_matrix.max()
        if len(all_tick_points) < len(all_label_polygons):
            # dummy rows ...
            cost_matrix[len(all_tick_points):, :] = max_cost + 1
        else:
            # dummy columns ...
            cost_matrix[:, len(all_label_polygons):] = max_cost + 1

        # run munkres ...
        m = Munkres()
        assignments = m.compute(cost_matrix)

        for tick_idx, text_offset in assignments:
            if tick_idx < len(all_tick_points) and text_offset < len(all_label_polygons):
                # valid assignment ... execute ...
                text_id, label_polygon = all_label_polygons[text_offset]
                self.tempo_axis_values.ticks[tick_idx].label_id = text_id

        # update GUI
        self.prepare_labels_per_tick()
        self.update_current_view()

    def btn_lpt_return_click(self, button):
        # return ....
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)
        self.update_current_view(False)

    def btn_edit_axis_x1_add_click(self, button):
        if self.axes.x1_axis is not None:
            print("The Chart already has this Axis")
            return

        self.prepare_axis_add(ChartAxesAnnotator.AxisX1)

    def btn_edit_axis_x1_edit_click(self, button):
        if self.axes.x1_axis is None:
            print("The Chart does not have this Axis")
            return

        self.edit_axis = ChartAxesAnnotator.AxisX1
        self.tempo_axis_values = AxisValues.Copy(self.axes.x1_axis)
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)


    def btn_edit_axis_y1_add_click(self, button):
        if self.axes.y1_axis is not None:
            print("The Chart already has this Axis")
            return

        self.prepare_axis_add(ChartAxesAnnotator.AxisY1)

    def btn_edit_axis_y1_edit_click(self, button):
        if self.axes.y1_axis is None:
            print("The Chart does not have this Axis")
            return

        self.edit_axis = ChartAxesAnnotator.AxisY1
        self.tempo_axis_values = AxisValues.Copy(self.axes.y1_axis)
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)

    def btn_edit_axis_x2_add_click(self, button):
        if self.axes.x2_axis is not None:
            print("The Chart already has this Axis")
            return

        self.prepare_axis_add(ChartAxesAnnotator.AxisX2)

    def btn_edit_axis_x2_edit_click(self, button):
        if self.axes.x2_axis is None:
            print("The Chart does not have this Axis")
            return

        self.edit_axis = ChartAxesAnnotator.AxisX2
        self.tempo_axis_values = AxisValues.Copy(self.axes.x2_axis)
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)

    def btn_edit_axis_y2_add_click(self, button):
        if self.axes.y2_axis is not None:
            print("The Chart already has this Axis")
            return

        self.prepare_axis_add(ChartAxesAnnotator.AxisY2)

    def btn_edit_axis_y2_edit_click(self, button):
        if self.axes.y2_axis is None:
            print("The Chart does not have this Axis")
            return

        self.edit_axis = ChartAxesAnnotator.AxisY2
        self.tempo_axis_values = AxisValues.Copy(self.axes.y2_axis)
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)

    def prepare_axis_add(self, new_axis):
        if new_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
            (value_type, ticks_type, value_scale), _ = self.get_axes_default_types()
        else:
            _, (value_type, ticks_type, value_scale) = self.get_axes_default_types()

        self.edit_axis = new_axis
        self.tempo_axis_values = AxisValues(value_type, ticks_type, value_scale)
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)

    def update_axes_buttons(self):
        showing_buttons = self.axes.bounding_box is not None

        self.lbl_edit_axis_x1.visible = showing_buttons
        self.lbl_edit_axis_y1.visible = showing_buttons
        self.lbl_edit_axis_x2.visible = showing_buttons
        self.lbl_edit_axis_y2.visible = showing_buttons

        # X1
        if self.axes.x1_axis is not None:
            self.btn_edit_axis_x1_add.visible = False
            self.btn_edit_axis_x1_edit.visible = showing_buttons
        else:
            self.btn_edit_axis_x1_add.visible = showing_buttons
            self.btn_edit_axis_x1_edit.visible = False

        # Y1
        if self.axes.y1_axis is not None:
            self.btn_edit_axis_y1_add.visible = False
            self.btn_edit_axis_y1_edit.visible = showing_buttons
        else:
            self.btn_edit_axis_y1_add.visible = showing_buttons
            self.btn_edit_axis_y1_edit.visible = False

        # X2
        if self.axes.x2_axis is not None:
            self.btn_edit_axis_x2_add.visible = False
            self.btn_edit_axis_x2_edit.visible = showing_buttons
        else:
            self.btn_edit_axis_x2_add.visible = showing_buttons
            self.btn_edit_axis_x2_edit.visible = False

        # Y2
        if self.axes.y2_axis is not None:
            self.btn_edit_axis_y2_add.visible = False
            self.btn_edit_axis_y2_edit.visible = showing_buttons
        else:
            self.btn_edit_axis_y2_add.visible = showing_buttons
            self.btn_edit_axis_y2_edit.visible = False

    def update_axis_title(self):
        if self.tempo_axis_values.title is None:
            self.lbl_info_axis_title_value.set_text("[ No Title ]")
        else:
            self.lbl_info_axis_title_value.set_text(self.axes.axes_titles[self.tempo_axis_values.title].value)

    def update_axis_info(self):
        self.lbx_info_axis_type.change_option_selected(str(self.tempo_axis_values.values_type))
        self.lbx_info_ticks_type.change_option_selected(str(self.tempo_axis_values.ticks_type))
        self.lbx_info_scale_type.change_option_selected(str(self.tempo_axis_values.scale_type))

    def btn_axis_edit_info_click(self, button):
        self.update_axis_title()
        self.update_axis_info()
        self.set_editor_mode(ChartAxesAnnotator.ModeAxisInfoEdit)

    def btn_axis_edit_ticks_click(self, button):
        self.prepare_ticks_edition()
        self.set_editor_mode(ChartAxesAnnotator.ModeTicksEdit)
        self.update_current_view()

    def btn_axis_edit_labels_click(self, button):
        self.prepare_labels_edition()
        self.set_editor_mode(ChartAxesAnnotator.ModeLabelsEdit)
        self.update_current_view()

    def btn_axis_edit_labels_per_tick_click(self, button):
        if self.tempo_axis_values.ticks is None:
            print("Axis ticks must be defined first!")
            return

        self.prepare_labels_per_tick()
        self.set_editor_mode(ChartAxesAnnotator.ModeLabelPerTickEdit)
        self.update_current_view()

    def btn_axis_delete_click(self, button):
        self.set_editor_mode(ChartAxesAnnotator.ModeConfirmAxisDelete)

    def btn_axis_return_accept_click(self, button):
        # update info ...
        if self.edit_axis == ChartAxesAnnotator.AxisX1:
            self.axes.x1_axis = AxisValues.Copy(self.tempo_axis_values)
        elif self.edit_axis == ChartAxesAnnotator.AxisX2:
            self.axes.x2_axis = AxisValues.Copy(self.tempo_axis_values)
        elif self.edit_axis == ChartAxesAnnotator.AxisY1:
            self.axes.y1_axis = AxisValues.Copy(self.tempo_axis_values)
        elif self.edit_axis == ChartAxesAnnotator.AxisY2:
            self.axes.y2_axis = AxisValues.Copy(self.tempo_axis_values)
        else:
            raise Exception("Invalid Axis Selected for deletion")

        self.data_changed = True
        self.edit_axis = None
        self.tempo_axis_values = None

        self.update_axes_buttons()
        self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)
        self.update_current_view(False)

    def btn_axis_return_cancel_click(self, button):
        # simply return to navigation ...
        self.edit_axis = None
        self.set_editor_mode(ChartAxesAnnotator.ModeNavigate)
        self.update_current_view(False)

    def btn_info_title_set_click(self, button):
        self.set_editor_mode(ChartAxesAnnotator.ModeTitleSelect)

    def btn_info_title_delete_click(self, button):
        if self.tempo_axis_values.title is not None:
            self.tempo_axis_values.title = None
            self.update_axis_title()
            self.update_current_view()

    def btn_info_return_click(self, button):
        # Copy new types info ...
        self.tempo_axis_values.values_type = int(self.lbx_info_axis_type.selected_option_value)
        self.tempo_axis_values.ticks_type = int(self.lbx_info_ticks_type.selected_option_value)
        self.tempo_axis_values.scale_type = int(self.lbx_info_scale_type.selected_option_value)

        self.set_editor_mode(ChartAxesAnnotator.ModeAxisEdit)

    def img_main_mouse_motion(self, screen_img, pos, rel, buttons):
        if self.edition_mode in [ChartAxesAnnotator.ModeBBoxSelect, ChartAxesAnnotator.ModeBBoxEdit,
                                 ChartAxesAnnotator.ModeTicksSelect]:
            mouse_x, mouse_y = pos

            # TODO: abstract the whole ZOOM window into the main class
            img_pixel_x = int(round(mouse_x / self.view_scale))
            img_pixel_y = int(round(mouse_y / self.view_scale))

            sel_rect = self.canvas_select.elements["selection_rectangle"]
            if self.canvas_select.drag_type == 1:
                # dragging top-left corner of the selection rectangle ...
                ref_pixel_x = int(round(sel_rect.x / self.view_scale))
                ref_pixel_y = int(round(sel_rect.y / self.view_scale))
            elif self.canvas_select.drag_type == 2:
                # dragging top-right corner of the selection rectangle ...
                ref_pixel_x = int(round((sel_rect.x + sel_rect.w) / self.view_scale))
                ref_pixel_y = int(round(sel_rect.y / self.view_scale))
            elif self.canvas_select.drag_type == 3:
                # dragging bottom-left corner of the selection rectangle...
                ref_pixel_x = int(round(sel_rect.x / self.view_scale))
                ref_pixel_y = int(round((sel_rect.y + sel_rect.h) / self.view_scale))
            elif self.canvas_select.drag_type == 4:
                # dragging bottom-right corner of the selection rectangle...
                ref_pixel_x = int(round((sel_rect.x + sel_rect.w) / self.view_scale))
                ref_pixel_y = int(round((sel_rect.y + sel_rect.h) / self.view_scale))
            else:
                # use current mouse position as the default reference point
                ref_pixel_x = img_pixel_x
                ref_pixel_y = img_pixel_y

            zoom_pixels = 20
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

            # decrease color contrast
            zoom_cut = zoom_cut.astype(np.float64)
            zoom_cut /= 2
            zoom_cut += 63
            zoom_cut = zoom_cut.astype(np.uint8)

            # highlight the center pixel by default ...
            if ref_pixel_y - cut_min_y < zoom_cut.shape[0]:
                zoom_cut[ref_pixel_y - cut_min_y, :] = (255, 0, 0)
            if ref_pixel_x - cut_min_x < zoom_cut.shape[1]:
                zoom_cut[:, ref_pixel_x - cut_min_x] = (255, 0, 0)

            self.img_preview.set_image(zoom_cut, 200, 200)

    def btn_ticks_auto_click(self, button):
        self.tempo_ticks = []

        for text_id in self.axes.tick_labels:
            current_text = self.axes.tick_labels[text_id]

            # self.tempo_axis_values
            if text_id in self.tempo_axis_values.labels:
                c_x, c_y = current_text.get_center()

                if self.edit_axis in [ChartAxesAnnotator.AxisX1, ChartAxesAnnotator.AxisX2]:
                    # Horizontal axis ... use x
                    self.tempo_ticks.append(TickInfo(c_x, text_id))

                elif self.edit_axis in [ChartAxesAnnotator.AxisY1, ChartAxesAnnotator.AxisY2]:
                    # Vertical axis ... use y
                    self.tempo_ticks.append(TickInfo(c_y, text_id))

        self.update_tick_GUI()
        self.update_current_view(False)

