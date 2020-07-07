
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas

class BaseImageAnnotator(Screen):
    # four view modes for the image ...
    ViewModeRawData = 0
    ViewModeInvertedData = 1
    ViewModeGrayData = 2
    ViewModeRawNoData = 3
    ViewModeInvertedNoData = 4
    ViewModeGrayNoData = 5

    def __init__(self, title, size):
        Screen.__init__(self, title, size)

        self.base_rgb_image = None
        self.base_inv_image = None
        self.base_gray_image = None

        self.view_mode = BaseImageAnnotator.ViewModeRawData
        self.view_scale = 1.0

        self.container_view_buttons = None
        self.lbl_zoom = None
        self.btn_zoom_reduce = None
        self.btn_zoom_increase = None
        self.btn_zoom_zero = None

        self.lbl_view_data = None
        self.btn_view_raw_data = None
        self.btn_view_inv_data = None
        self.btn_view_gray_data = None

        self.lbl_view_clear = None
        self.btn_view_raw_clear = None
        self.btn_view_inv_clear = None
        self.btn_view_gray_clear = None

        self.container_images = None
        self.canvas_select = None
        self.canvas_display = None
        self.img_main = None

    def create_image_annotator_controls(self, container_top, container_width, general_background, text_color,
                                        button_text_color, button_back_color):
        # View panel with view control buttons
        self.container_view_buttons = ScreenContainer("container_view_buttons", (container_width, 160),
                                                      back_color=general_background)
        self.container_view_buttons.position = (self.width - self.container_view_buttons.width - 10, container_top)
        self.elements.append(self.container_view_buttons)

        button_2_width = 130
        button_2_left = int(container_width * 0.25) - button_2_width / 2
        button_2_right = int(container_width * 0.75) - button_2_width / 2

        # zoom ....
        self.lbl_zoom = ScreenLabel("lbl_zoom", "Zoom: 100%", 21, 290, 1)
        self.lbl_zoom.position = (5, 5)
        self.lbl_zoom.set_background(general_background)
        self.lbl_zoom.set_color(text_color)
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

        # ---
        # Data views

        button_4_width = 65
        button_4_gap = int((container_width - 20 - button_4_width * 4) / 3)
        button_4_left_1 = 10
        button_4_left_2 = 10 + (button_4_width + button_4_gap)
        button_4_left_3 = 10 + (button_4_width + button_4_gap) * 2
        button_4_left_4 = 10 + (button_4_width + button_4_gap) * 3

        self.lbl_view_data = ScreenLabel("lbl_view_data", "Data", 18, button_4_width)
        self.lbl_view_data.position = (button_4_left_1, self.btn_zoom_zero.get_bottom() + 10)
        self.lbl_view_data.set_background(general_background)
        self.lbl_view_data.set_color(text_color)
        self.container_view_buttons.append(self.lbl_view_data)

        self.btn_view_raw_data = ScreenButton("btn_view_raw_data", "RGB", 18, button_4_width)
        self.btn_view_raw_data.set_colors(button_text_color, button_back_color)
        self.btn_view_raw_data.position = (button_4_left_2, self.btn_zoom_zero.get_bottom() + 10)
        self.btn_view_raw_data.click_callback = self.btn_view_raw_data_click
        self.container_view_buttons.append(self.btn_view_raw_data)

        self.btn_view_inv_data = ScreenButton("btn_view_inv_data", "INV", 18, button_4_width)
        self.btn_view_inv_data.set_colors(button_text_color, button_back_color)
        self.btn_view_inv_data.position = (button_4_left_3, self.btn_zoom_zero.get_bottom() + 10)
        self.btn_view_inv_data.click_callback = self.btn_view_inv_data_click
        self.container_view_buttons.append(self.btn_view_inv_data)

        self.btn_view_gray_data = ScreenButton("btn_view_gray", "Gray", 18, button_4_width)
        self.btn_view_gray_data.set_colors(button_text_color, button_back_color)
        self.btn_view_gray_data.position = (button_4_left_4, self.btn_zoom_zero.get_bottom() + 10)
        self.btn_view_gray_data.click_callback = self.btn_view_gray_data_click
        self.container_view_buttons.append(self.btn_view_gray_data)

        # ------
        # clear views ...

        self.lbl_view_clear = ScreenLabel("lbl_view_clear", "Clear", 18, button_4_width)
        self.lbl_view_clear.position = (button_4_left_1, self.btn_view_raw_data.get_bottom() + 10)
        self.lbl_view_clear.set_background(general_background)
        self.lbl_view_clear.set_color(text_color)
        self.container_view_buttons.append(self.lbl_view_clear)

        self.btn_view_raw_clear = ScreenButton("btn_view_raw_clear", "RGB", 21, button_4_width)
        self.btn_view_raw_clear.set_colors(button_text_color, button_back_color)
        self.btn_view_raw_clear.position = (button_4_left_2, self.btn_view_raw_data.get_bottom() + 10)
        self.btn_view_raw_clear.click_callback = self.btn_view_raw_clear_click
        self.container_view_buttons.append(self.btn_view_raw_clear)

        self.btn_view_inv_clear = ScreenButton("btn_view_inv_clear", "INV", 21, button_4_width)
        self.btn_view_inv_clear.set_colors(button_text_color, button_back_color)
        self.btn_view_inv_clear.position = (button_4_left_3, self.btn_view_raw_data.get_bottom() + 10)
        self.btn_view_inv_clear.click_callback = self.btn_view_inv_clear_click
        self.container_view_buttons.append(self.btn_view_inv_clear)

        self.btn_view_gray_clear = ScreenButton("btn_view_gray_clear", "Gray", 21, button_4_width)
        self.btn_view_gray_clear.set_colors(button_text_color, button_back_color)
        self.btn_view_gray_clear.position = (button_4_left_4, self.btn_view_raw_data.get_bottom() + 10)
        self.btn_view_gray_clear.click_callback = self.btn_view_gray_clear_click
        self.container_view_buttons.append(self.btn_view_gray_clear)

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
        self.img_main.double_click_callback = self.img_main_mouse_double_click
        self.container_images.append(self.img_main)

        self.canvas_select = ScreenCanvas("canvas_select", 100, 100)
        self.canvas_select.position = (0, 0)
        self.canvas_select.locked = True
        self.canvas_select.object_edited_callback = self.canvas_select_object_edited
        # self.canvas_select.object_selected_callback = self.canvas_select_selection_changed
        self.container_images.append(self.canvas_select)

        # default selection objects
        # 1) A polygon ....
        base_points = np.array([[10, 10], [20, 10], [20, 20], [10, 20]], dtype=np.float64)
        self.canvas_select.add_polygon_element("selection_polygon", base_points)
        self.canvas_select.elements["selection_polygon"].visible = False
        # 2) A rectangle ....
        self.canvas_select.add_rectangle_element("selection_rectangle", 10, 10, 10, 10)
        self.canvas_select.elements["selection_rectangle"].visible = False

        self.canvas_display = ScreenCanvas("canvas_display", 100, 100)
        self.canvas_display.position = (0, 0)
        self.canvas_display.locked = True
        self.canvas_display.object_edited_callback = self.canvas_display_object_edited
        self.container_images.append(self.canvas_display)



    def btn_zoom_reduce_click(self, button):
        if self.view_scale <= 1.0:
            # reduce in quarters ...
            self.update_view_scale(self.view_scale - 0.25)
        else:
            # reduce in halves ....
            self.update_view_scale(self.view_scale - 0.50)

    def btn_zoom_increase_click(self, button):
        if self.view_scale < 1.0:
            # increase in quarters ...
            self.update_view_scale(self.view_scale + 0.25)
        else:
            # increase in halves ...
            self.update_view_scale(self.view_scale + 0.50)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_inv_data_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeInvertedData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_inv_clear_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeInvertedNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = BaseImageAnnotator.ViewModeGrayNoData
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
        # ... Canvas for Selection
        # ....... selection polygon  ...
        selection_polygon = self.canvas_select.elements["selection_polygon"]
        selection_polygon.points *= scale_factor
        # ....... selection rectangle ...
        selection_rectangle = self.canvas_select.elements["selection_rectangle"]
        selection_rectangle.x *= scale_factor
        selection_rectangle.y *= scale_factor
        selection_rectangle.w *= scale_factor
        selection_rectangle.h *= scale_factor
        # ... Canvas for display ...
        for polygon_name in self.canvas_display.elements:
            display_polygon = self.canvas_display.elements[polygon_name]
            display_polygon.points *= scale_factor

        # update scale text ...
        self.lbl_zoom.set_text("Zoom: " + str(int(round(self.view_scale * 100,0))) + "%")

    def update_current_view(self, resized=False):
        if self.view_mode in [BaseImageAnnotator.ViewModeGrayData, BaseImageAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.base_gray_image
        elif self.view_mode in [BaseImageAnnotator.ViewModeInvertedData, BaseImageAnnotator.ViewModeInvertedNoData]:
            if self.base_inv_image is None:
                self.base_inv_image = 255 - self.base_rgb_image
            base_image = self.base_inv_image
        else:
            base_image = self.base_rgb_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [BaseImageAnnotator.ViewModeRawData, BaseImageAnnotator.ViewModeInvertedData,
                              BaseImageAnnotator.ViewModeGrayData]:
            self.canvas_display.visible = True

            # This function must be implemented by the child class
            self.custom_view_update(modified_image)
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

    def img_main_mouse_button_down(self, img, pos, button):
        pass

    def img_main_mouse_double_click(self, element, pos, button):
        pass

    def canvas_select_object_edited(self, canvas, element_name):
        pass

    def canvas_display_object_edited(self, canvas, element_name):
        pass
