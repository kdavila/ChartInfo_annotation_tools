
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.data.text_info import TextInfo
from ChartInfo.data.legend_info import LegendInfo

class ChartLegendAnnotator(Screen):
    ModeNavigate = 0
    ModeRectangleSelect = 1
    ModeRectangleEdit = 2
    ModeConfirmExit = 3

    ViewModeRawData = 0
    ViewModeGrayData = 1
    ViewModeRawNoData = 2
    ViewModeGrayNoData = 3

    def __init__(self, size, panel_image, panel_info, parent_screen):
        Screen.__init__(self, "Chart Legend Ground Truth Annotation Interface", size)

        self.panel_image = panel_image
        self.panel_gray = np.zeros(self.panel_image.shape, self.panel_image.dtype)
        self.panel_gray[:, :, 0] = cv2.cvtColor(self.panel_image, cv2.COLOR_RGB2GRAY)
        self.panel_gray[:, :, 1] = self.panel_gray[:, :, 0].copy()
        self.panel_gray[:, :, 2] = self.panel_gray[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.legend is None:
            # create a new legend info
            self.legend = LegendInfo(self.panel_info.get_all_text(TextInfo.TypeLegendLabel))
            self.data_changed = True
        else:
            # make a copy
            self.legend = LegendInfo.Copy(self.panel_info.legend)
            self.data_changed = False

        self.parent_screen = parent_screen

        self.general_background = (80, 70, 150)
        self.text_color = (255, 255, 255)

        self.elements.back_color = self.general_background

        self.edition_mode = None
        self.tempo_text_id = None
        self.view_mode = ChartLegendAnnotator.ViewModeRawData
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

        self.container_legend_options = None
        self.lbl_legend_title = None
        self.lbx_legend_list = None
        self.btn_legend_edit = None
        self.btn_legend_delete = None
        self.btn_return_accept = None
        self.btn_return_cancel = None

        self.container_images = None
        self.canvas_select = None
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
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Legend Markers Annotation", 28)
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

        # ======================================
        # legend options
        darker_background = (55, 45, 100)
        self.container_legend_options = ScreenContainer("container_legend_options", (container_width, 550),
                                                        back_color=darker_background)
        self.container_legend_options.position = (self.container_view_buttons.get_left(),
                                                  self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_legend_options)

        self.lbl_legend_title = ScreenLabel("lbl_legend_title", "Legend Marker Annotation", 21, 290, 1)
        self.lbl_legend_title.position = (5, 5)
        self.lbl_legend_title.set_background(darker_background)
        self.lbl_legend_title.set_color(self.text_color)
        self.container_legend_options.append(self.lbl_legend_title)

        self.lbx_legend_list = ScreenTextlist("lbx_legend_list", (container_width - 20, 350), 18,
                                              back_color=(255,255,255), option_color=(0, 0, 0),
                                              selected_back=(120, 80, 50), selected_color=(255, 255, 255))
        self.lbx_legend_list.position = (10, self.lbl_legend_title.get_bottom() + 10)
        self.lbx_legend_list.selected_value_change_callback = self.lbx_legend_list_changed
        self.container_legend_options.append(self.lbx_legend_list)

        self.btn_legend_edit = ScreenButton("btn_legend_edit", "Edit", 21, button_2_width)
        self.btn_legend_edit.set_colors(button_text_color, button_back_color)
        self.btn_legend_edit.position = (button_2_left, self.lbx_legend_list.get_bottom() + 10)
        self.btn_legend_edit.click_callback = self.btn_legend_edit_click
        self.container_legend_options.append(self.btn_legend_edit)

        self.btn_legend_delete = ScreenButton("btn_legend_delete", "Delete", 21, button_2_width)
        self.btn_legend_delete.set_colors(button_text_color, button_back_color)
        self.btn_legend_delete.position = (button_2_right, self.lbx_legend_list.get_bottom() + 10)
        self.btn_legend_delete.click_callback = self.btn_legend_delete_click
        self.container_legend_options.append(self.btn_legend_delete)

        self.btn_return_accept = ScreenButton("btn_return_accept", "Accept", 21, button_2_width)
        return_top = self.container_legend_options.height - self.btn_return_accept.height - 10
        self.btn_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_return_accept.position = (button_2_left, return_top)
        self.btn_return_accept.click_callback = self.btn_return_accept_click
        self.container_legend_options.append(self.btn_return_accept)

        self.btn_return_cancel = ScreenButton("btn_return_cancel", "Cancel", 21, button_2_width)
        self.btn_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_return_cancel.position = (button_2_right, return_top)
        self.btn_return_cancel.click_callback = self.btn_return_cancel_click
        self.container_legend_options.append(self.btn_return_cancel)

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

        self.canvas_select = ScreenCanvas("canvas_select", 100, 100)
        self.canvas_select.position = (0, 0)
        self.canvas_select.locked = True
        # self.canvas_select.object_edited_callback = self.canvas_object_edited
        # self.canvas_select.object_selected_callback = self.canvas_selection_changed
        self.container_images.append(self.canvas_select)

        base_points = np.array([[10, 10], [20, 10], [20, 20], [10, 20]], dtype=np.float64)
        self.canvas_select.add_polygon_element("selection_polygon", base_points)
        self.canvas_select.elements["selection_polygon"].visible = False

        self.canvas_display = ScreenCanvas("canvas_display", 100, 100)
        self.canvas_display.position = (0, 0)
        self.canvas_display.locked = True
        self.container_images.append(self.canvas_display)

        self.add_text_regions()

        self.set_editor_mode(ChartLegendAnnotator.ModeNavigate)

    def get_color_display_info(self, text_id):
        main_color = self.canvas_display.colors[text_id % len(self.canvas_display.colors)]
        sel_color = self.canvas_display.sel_colors[text_id % len(self.canvas_display.sel_colors)]

        return main_color, sel_color

    def get_text_display_info(self, text):
        return "{0:d} - {1:s}".format(text.id, text.value)

    def add_text_regions(self):
        # populate the list-box using existing text regions (if any)
        for text in self.legend.text_labels:
            text_desc = self.get_text_display_info(text)
            main_color, sel_color = self.get_color_display_info(text.id)

            self.lbx_legend_list.add_option(str(text.id), text_desc)

            self.canvas_display.add_polygon_element(str(text.id), text.position_polygon.copy(), main_color, sel_color)

            if self.legend.marker_per_label[text.id] is not None:
                marker_pos = self.legend.marker_per_label[text.id].copy()
                self.canvas_display.add_polygon_element(str(text.id) + "-mark", marker_pos, main_color, sel_color)

    def btn_zoom_reduce_click(self, button):
        self.update_view_scale(self.view_scale - 0.25)

    def btn_zoom_increase_click(self, button):
        self.update_view_scale(self.view_scale + 0.25)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = ChartLegendAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = ChartLegendAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = ChartLegendAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = ChartLegendAnnotator.ViewModeGrayNoData
        self.update_current_view()

    def update_current_view(self, resized=False):
        if self.view_mode in [ChartLegendAnnotator.ViewModeGrayData, ChartLegendAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.panel_gray
        else:
            base_image = self.panel_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [ChartLegendAnnotator.ViewModeRawData, ChartLegendAnnotator.ViewModeGrayData]:
            # TODO: show here any relevant annotations on the modified image ...
            # (for example, draw the polygons)
            self.canvas_display.visible = True
        else:
            self.canvas_display.visible = False

        # finally, resize ...
        modified_image = cv2.resize(modified_image, (int(w * self.view_scale), int(h * self.view_scale)),
                                    interpolation=cv2.INTER_NEAREST)

        # update canvas size ....
        self.canvas_select.height, self.canvas_select.width, _ = modified_image.shape
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
        # ... selection ...
        selection_polygon = self.canvas_select.elements["selection_polygon"]
        selection_polygon.points *= scale_factor
        # ... display ...
        for polygon_name in self.canvas_display.elements:
            display_polygon = self.canvas_display.elements[polygon_name]
            display_polygon.points *= scale_factor

        # update scale text ...
        self.lbl_zoom.set_text("Zoom: " + str(int(round(self.view_scale * 100,0))) + "%")

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_legend_options.visible = (self.edition_mode == ChartLegendAnnotator.ModeNavigate)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ChartLegendAnnotator.ModeRectangleSelect,
                                                                       ChartLegendAnnotator.ModeRectangleEdit,
                                                                       ChartLegendAnnotator.ModeConfirmExit]

        if self.edition_mode == ChartLegendAnnotator.ModeRectangleSelect:
            self.lbl_confirm_message.set_text("Select Legend Mark Location")
        elif self.edition_mode == ChartLegendAnnotator.ModeRectangleEdit:
            self.lbl_confirm_message.set_text("Editing Legend Mark Location")
        elif self.edition_mode == ChartLegendAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Legend?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode != ChartLegendAnnotator.ModeRectangleSelect

        if new_mode in [ChartLegendAnnotator.ModeRectangleEdit]:
            # show polygon
            self.canvas_select.locked = False
            self.canvas_select.elements["selection_polygon"].visible = True
        else:
            # for every other mode
            self.canvas_select.locked = True
            self.canvas_select.elements["selection_polygon"].visible = False

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [ChartLegendAnnotator.ModeRectangleEdit,
                                 ChartLegendAnnotator.ModeRectangleSelect,
                                 ChartLegendAnnotator.ModeConfirmExit]:

            if self.edition_mode == ChartLegendAnnotator.ModeRectangleEdit:
                polygon_name = str(self.tempo_text_id) + "-mark"

                if polygon_name in self.canvas_display.elements:
                    self.canvas_display.elements[polygon_name].visible = True

            # return to navigation
            self.set_editor_mode(ChartLegendAnnotator.ModeNavigate)
        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == ChartLegendAnnotator.ModeConfirmExit:
            print("-> Changes made to Legend Annotations were lost")
            self.return_screen = self.parent_screen
        elif self.edition_mode == ChartLegendAnnotator.ModeRectangleEdit:
            # get polygon from GUI
            raw_polygon = self.canvas_select.elements["selection_polygon"].points.copy()
            mark_polygon = raw_polygon / self.view_scale
            # update on GUI ...
            polygon_name = str(self.tempo_text_id) + "-mark"
            if self.legend.marker_per_label[self.tempo_text_id] is None:
                # add to the display canvas ...
                main_color, sel_color = self.get_color_display_info(self.tempo_text_id)
                self.canvas_display.add_polygon_element(polygon_name, raw_polygon, main_color, sel_color)
            else:
                # update the display canvas ...
                self.canvas_display.update_polygon_element(polygon_name, raw_polygon, True)

            # update on DATA
            self.legend.marker_per_label[self.tempo_text_id] = mark_polygon.copy()
            self.data_changed = True

            # return ...
            self.set_editor_mode(ChartLegendAnnotator.ModeNavigate)
        else:
            raise Exception("Not Implemented")

    def get_next_axis_aligned_box(self, click_x, click_y):

        last_known_polygon = None
        for text_id in self.legend.marker_per_label:
            if self.legend.marker_per_label[text_id] is not None:
                last_known_polygon = self.legend.marker_per_label[text_id]
                break

        if last_known_polygon is None:
            # default small rectangle
            rect_w, rect_h = 40, 20
        else:
            # axis aligned container rectangle from last bbox
            min_x = last_known_polygon[:, 0].min()
            max_x = last_known_polygon[:, 0].max()
            min_y = last_known_polygon[:, 1].min()
            max_y = last_known_polygon[:, 1].max()

            rect_w = (max_x - min_x) * self.view_scale
            rect_h = (max_y - min_y) * self.view_scale

        points = np.array([[click_x, click_y], [click_x + rect_w, click_y],
                           [click_x + rect_w, click_y + rect_h], [click_x, click_y + rect_h]])

        return points

    def img_mouse_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode == ChartLegendAnnotator.ModeRectangleSelect:
                click_x, click_y = pos
                points = self.get_next_axis_aligned_box(click_x, click_y)
                self.canvas_select.elements["selection_polygon"].update(points)

                self.set_editor_mode(ChartLegendAnnotator.ModeRectangleEdit)

    def lbx_legend_list_changed(self, new_value, old_value):
        self.canvas_display.change_selected_element(new_value)

    def btn_legend_edit_click(self, button):
        if self.lbx_legend_list.selected_option_value is None:
            print("Must select a legend label from the list")
            return

        # check if new or edit
        self.tempo_text_id = int(self.lbx_legend_list.selected_option_value)
        if self.legend.marker_per_label[self.tempo_text_id] is None:
            # new ...
            self.set_editor_mode(ChartLegendAnnotator.ModeRectangleSelect)
        else:
            # edit existing ...
            # ... copy points to selection canvas ...
            polygon = self.legend.marker_per_label[self.tempo_text_id].copy() * self.view_scale
            self.canvas_select.update_polygon_element("selection_polygon", polygon, True)

            self.canvas_display.elements[str(self.tempo_text_id) + "-mark"].visible = False

            self.set_editor_mode(ChartLegendAnnotator.ModeRectangleEdit)

    def btn_legend_delete_click(self, button):
        if self.lbx_legend_list.selected_option_value is None:
            print("Must select a legend label from the list")
            return

        self.tempo_text_id = int(self.lbx_legend_list.selected_option_value)

        # delete from GUI ...
        if self.legend.marker_per_label[self.tempo_text_id] is not None:
            polygon_name = str(self.tempo_text_id) + "-mark"
            self.canvas_display.remove_element(polygon_name)

        # delete from Data ...
        self.legend.marker_per_label[self.tempo_text_id] = None

        self.data_changed = True


    def btn_return_accept_click(self, button):
        if self.data_changed:
            # overwrite existing legend data ...
            self.panel_info.legend = LegendInfo.Copy(self.legend)
            self.parent_screen.subtool_completed(True)

        # return
        self.return_screen = self.parent_screen

    def btn_return_cancel_click(self, button):
        if self.data_changed:
            self.set_editor_mode(ChartLegendAnnotator.ModeConfirmExit)
        else:
            # simply return
            self.return_screen = self.parent_screen


