
import numpy as np
import cv2
from munkres import Munkres

from shapely.geometry import Polygon

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist

from ChartInfo.annotation.base_image_annotator import BaseImageAnnotator

from ChartInfo.data.text_info import TextInfo
from ChartInfo.data.legend_info import LegendInfo


class ChartLegendAnnotator(BaseImageAnnotator):
    ModeNavigate = 0
    ModeRectangleSelect = 1
    ModeRectangleEdit = 2
    ModeConfirmExit = 3

    def __init__(self, size, panel_image, panel_info, parent_screen):
        BaseImageAnnotator.__init__(self, "Chart Legend Ground Truth Annotation Interface", size)

        self.base_rgb_image = panel_image
        self.base_gray_image = np.zeros(self.base_rgb_image.shape, self.base_rgb_image.dtype)
        self.base_gray_image[:, :, 0] = cv2.cvtColor(self.base_rgb_image, cv2.COLOR_RGB2GRAY)
        self.base_gray_image[:, :, 1] = self.base_gray_image[:, :, 0].copy()
        self.base_gray_image[:, :, 2] = self.base_gray_image[:, :, 0].copy()

        self.panel_info = panel_info

        if self.panel_info.legend is None:
            # create a new legend info
            self.legend = LegendInfo(self.panel_info.get_all_text(TextInfo.TypeLegendLabel))
            # try to automatically find legend elements ...
            self.estimate_legend_boxes()
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

        self.label_title = None

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

        self.create_controllers()

        # get the view ...
        self.update_current_view(True)

    def get_best_assignments(self, cost_matrix, n_ccs, max_distance):
        # use the Munkres algorithm to find the optimal assignments
        m = Munkres()
        assignments = m.compute(cost_matrix.copy())

        # validate the assignments
        valid_assignments = []
        raw_cost = 0
        valid_cost = 0
        for text_idx, cc_idx in assignments:
            # check if the assignment is valid ...
            if (text_idx < len(self.legend.text_labels) and cc_idx < n_ccs and
                cost_matrix[text_idx, cc_idx] < max_distance):
                # valid ... add to list of assignments ....
                valid_assignments.append((text_idx, cc_idx))
                # add to valid cost ....
                valid_cost += cost_matrix[text_idx, cc_idx]

            # add to raw cost
            raw_cost += cost_matrix[text_idx, cc_idx]

        return raw_cost, valid_cost, valid_assignments

    def get_intervals_IOU(self, int_1_min, int_1_max, int_2_min, int_2_max):
        if int_1_min <= int_2_max and int_2_min <= int_1_max:
            # intersection ...
            int_min = max(int_1_min, int_2_min)
            int_max = min(int_1_max, int_2_max)
            int_size = int_max - int_min
            # union ...
            union_min = min(int_1_min, int_2_min)
            union_max = max(int_1_max, int_2_max)
            union_size = union_max - union_min

            # print((int_1_min, int_1_max, int_2_min, int_2_max, int_min, int_max, int_size, union_size))

            return int_size / union_size
        else:
            # no intersection ...
            return 0.0

    def estimate_legend_boxes(self):
        legend_orientation = self.legend.get_legend_orientation()
        if legend_orientation == LegendInfo.OrientationMixed:
            # hard to auto-validate, do not create an estimation
            return

        otsu_t, binarized = cv2.threshold(self.base_gray_image[:, :, 0], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binarized = 255 - binarized

        # subtract the all text  ...
        for txt_label in self.panel_info.get_all_text():
            min_x, min_y, max_x, max_y = txt_label.get_axis_aligned_rectangle()

            binarized[int(min_y):int(max_y), int(min_x):int(max_x)] = 0

        # get the CC ...
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binarized)
        # ... get CC stats ...
        cc_boxes = np.zeros((num_labels - 1, 4), dtype=np.int32)
        for cc_idx in range(1, num_labels):
            cc_min_x = stats[cc_idx, cv2.CC_STAT_LEFT]
            cc_max_x = cc_min_x + stats[cc_idx, cv2.CC_STAT_WIDTH]
            cc_min_y = stats[cc_idx, cv2.CC_STAT_TOP]
            cc_max_y = cc_min_y + stats[cc_idx, cv2.CC_STAT_HEIGHT]

            cc_boxes[cc_idx - 1] = cc_min_x, cc_max_x, cc_min_y, cc_max_y

        # find distances between each CC candidate and each legend text ...
        align_size = max(cc_boxes.shape[0], len(self.legend.text_labels))
        left_distances = np.zeros((align_size, align_size), dtype=np.int32)
        right_distances = np.zeros((align_size, align_size), dtype=np.int32)
        # max distance is the maximum width
        max_distance = labels.shape[1]

        left_distances[:, :] = max_distance
        right_distances[:, :] = max_distance
        # ... for each text label in the legend
        for text_idx, txt_label in enumerate(self.legend.text_labels):
            l_min_x, l_min_y, l_max_x, l_max_y = txt_label.get_axis_aligned_rectangle()

            # .... for each CC in the binarized image
            for cc_idx, (cc_min_x, cc_max_x, cc_min_y, cc_max_y) in enumerate(cc_boxes):
                # check area, confirm that this is not a large CC overlapping in range with the text region
                text_region = (l_max_x - l_min_x + 1) * (l_max_y - l_min_y + 1)
                cc_region = (cc_max_x - cc_min_x + 1) * (cc_max_y - cc_min_y + 1)
                if cc_region < text_region * 2:
                    # they should overlap vertically ...
                    if cc_min_y <= l_max_y and l_min_y <= cc_max_y:
                        # both legend text and the CC intersect vertically, check distance
                        if cc_min_x <= l_max_x and l_min_x <= cc_max_x:
                            # they also intersect horizontally
                            if cc_min_x < l_min_x:
                                # CC is the left-most
                                left_distances[text_idx, cc_idx] = 0
                            else:
                                # CC is the right-most
                                right_distances[text_idx, cc_idx] = 0
                        else:
                            # no horizontal intersection, find distance between edges
                            if cc_max_x < l_min_x:
                                # CC is on the left side of this legend element ...
                                left_distances[text_idx, cc_idx] = l_min_x - cc_max_x
                            else:
                                # CC is on the right side of this legend element ...
                                right_distances[text_idx, cc_idx] = cc_min_x - l_max_x
                    else:
                        # no vertical overlap, most legends should be connected to elements on the left or right
                        pass
                else:
                    # the CC is too big ... keep default of max distance
                    pass

        # running munkress on both sides ....
        n_ccs = cc_boxes.shape[0]
        l_raw_cost, l_valid_cost, l_assignments = self.get_best_assignments(left_distances, n_ccs, max_distance)
        r_raw_cost, r_valid_cost, r_assignments=  self.get_best_assignments(right_distances, n_ccs, max_distance)

        if l_raw_cost < r_raw_cost:
            # assume left alignment ...
            title = "try_left"
            assignments = l_assignments
        else:
            # use right alignment ..
            title = "try_right"
            assignments = r_assignments

        # cv2.imshow(title, binarized)

        # discard candidates if pairwise IOU is inconsistent ..
        min_overlap = 0.8
        for pair_idx, (text_idx_1, cc_idx_1) in enumerate(assignments[:-1]):
            cc_1_min_x, cc_1_max_x, cc_1_min_y, cc_1_max_y = cc_boxes[cc_idx_1]

            for text_idx_2, cc_idx_2 in assignments[pair_idx + 1:]:
                cc_2_min_x, cc_2_max_x, cc_2_min_y, cc_2_max_y = cc_boxes[cc_idx_2]

                if legend_orientation == LegendInfo.OrientationVertical:
                    # they should overlap on X ...
                    IOU = self.get_intervals_IOU(cc_1_min_x, cc_1_max_x, cc_2_min_x, cc_2_max_x)

                else:
                    # they should overlap on Y ...
                    IOU = self.get_intervals_IOU(cc_1_min_y, cc_1_max_y, cc_2_min_y, cc_2_max_y)

                # print((pair_idx, text_idx_1, text_idx_2, IOU))
                if IOU < min_overlap:
                    # do not create the default boxes
                    return

        # create the default bboxes for valid assignments ...
        for text_idx, cc_idx in assignments:
            text_id = self.legend.text_labels[text_idx].id

            # create default legend bbox using this element ...
            cc_min_x, cc_max_x, cc_min_y, cc_max_y = cc_boxes[cc_idx]
            points = np.array([[cc_min_x - 1, cc_min_y - 1],
                               [cc_max_x + 1, cc_min_y - 1],
                               [cc_max_x + 1, cc_max_y + 1],
                               [cc_min_x - 1, cc_max_y + 1]], dtype=np.float64)
            self.legend.marker_per_label[text_id] = points
            # print((text_idx, text_id, cc_idx, distances[text_idx, cc_idx]))

        # cv2.imshow("-", binarized)
        # cv2.waitKey()

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
        # legend entry edition options ....
        darker_background = (55, 45, 100)
        self.container_legend_edit  = ScreenContainer("container_legend_edit", (container_width, 150),
                                                        back_color=darker_background)
        self.container_legend_edit.position = (self.container_confirm_buttons.get_left(),
                                                  self.container_confirm_buttons.get_bottom() + 20)
        self.elements.append(self.container_legend_edit)
        self.container_legend_edit.visible = False

        self.btn_edit_force_box = ScreenButton("btn_edit_force_box", "Force Box", 21, button_width)
        self.btn_edit_force_box.set_colors(button_text_color, button_back_color)
        self.btn_edit_force_box.position = (button_left, 10)
        self.btn_edit_force_box.click_callback = self.btn_edit_force_box_click
        self.container_legend_edit.append(self.btn_edit_force_box)


        # ======================================
        # visuals
        # ===========================

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

    def custom_view_update(self, modified_image):
        pass

    def set_editor_mode(self, new_mode):
        self.edition_mode = new_mode

        # Navigation mode ...
        self.container_legend_options.visible = (self.edition_mode == ChartLegendAnnotator.ModeNavigate)

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ChartLegendAnnotator.ModeRectangleSelect,
                                                                       ChartLegendAnnotator.ModeRectangleEdit,
                                                                       ChartLegendAnnotator.ModeConfirmExit]

        self.container_legend_edit.visible = (self.edition_mode == ChartLegendAnnotator.ModeRectangleEdit)

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

    def img_main_mouse_button_down(self, img_object, pos, button):
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

    def btn_edit_force_box_click(self, button):
        legend_entry_polygon = self.canvas_select.elements["selection_polygon"].points / self.view_scale

        poly = Polygon(legend_entry_polygon)
        minx, miny, maxx, maxy = poly.bounds

        legend_entry_polygon = np.array([[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy]])
        self.canvas_select.elements["selection_polygon"].update(legend_entry_polygon * self.view_scale)

    def img_main_mouse_double_click(self, element, pos, button):
        if button == 1:
            # double left click ...
            if self.edition_mode == ChartLegendAnnotator.ModeNavigate:
                click_x, click_y = pos

                # scale the view ....
                click_x /= self.view_scale
                click_y /= self.view_scale

                # find if a given element was clicked ....
                for text_region in self.legend.text_labels:
                    # check ...
                    if text_region.area_contains_point(click_x, click_y):
                        # clicked on a text region ...
                        self.lbx_legend_list.change_option_selected(str(text_region.id))
                        # simulate click on edit button ....
                        self.btn_legend_edit_click(None)
                        break
