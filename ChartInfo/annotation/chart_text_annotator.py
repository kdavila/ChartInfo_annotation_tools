
import numpy as np
import cv2
from scipy.spatial import distance as dist

from shapely.geometry import Polygon

try:
    import pytesseract as OCR
except:
    print("WARNING: pytesseract not found! OCR will be disabled")
    OCR = None

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_canvas import ScreenCanvas
from AM_CommonTools.interface.controls.screen_textlist import ScreenTextlist
from AM_CommonTools.interface.controls.screen_textbox import ScreenTextbox

from ChartInfo.data.text_info import TextInfo

class ChartTextAnnotator(Screen):
    ModeNavigate = 0
    ModeAddingTextSelect = 1
    ModeAddingTextEdit = 2
    ModeEditingText = 3
    ModeConfirmDeleteText = 4
    ModeConfirmExit = 5
    ModeConfirmOverwrite = 6

    ViewModeRawData = 0
    ViewModeGrayData = 1
    ViewModeRawNoData = 2
    ViewModeGrayNoData = 3

    RotationAuto = 0
    Rotation0 = 1
    Rotation90 = 2
    Rotation180 = 3
    Rotation270 = 4

    def __init__(self, size, panel_image, panel_info, parent_screen, admin_mode):
        Screen.__init__(self, "Chart Text Ground Truth Annotation Interface", size)

        self.panel_image = panel_image
        self.panel_gray = np.zeros(self.panel_image.shape, self.panel_image.dtype)
        self.panel_gray[:, :, 0] = cv2.cvtColor(self.panel_image, cv2.COLOR_RGB2GRAY)
        self.panel_gray[:, :, 1] = self.panel_gray[:, :, 0].copy()
        self.panel_gray[:, :, 2] = self.panel_gray[:, :, 0].copy()

        self.panel_info = panel_info

        # working copy ...
        self.text_regions = [TextInfo.Copy(text_info) for text_info in self.panel_info.text]

        self.parent_screen = parent_screen
        self.admin_mode = admin_mode

        self.general_background = (150, 100, 60)
        self.text_color = (255, 255, 255)
        self.canvas_colors = {
            TextInfo.TypeChartTitle: (255, 0, 0),
            TextInfo.TypeAxisTitle: (0, 255, 0),
            TextInfo.TypeTickLabel: (0, 0, 255),
            TextInfo.TypeLegendTitle: (255, 255, 0),
            TextInfo.TypeLegendLabel: (255, 0, 255),
            TextInfo.TypeValueLabel: (0, 255, 255),
            TextInfo.TypeOther: (128, 0, 0),
        }
        self.canvas_sel_colors = {
            TextInfo.TypeChartTitle: (128, 0, 0),
            TextInfo.TypeAxisTitle: (0, 128, 0),
            TextInfo.TypeTickLabel: (0, 0, 128),
            TextInfo.TypeLegendTitle: (128, 128, 0),
            TextInfo.TypeLegendLabel: (128, 0, 128),
            TextInfo.TypeValueLabel: (0, 128, 128),
            TextInfo.TypeOther: (64, 0, 0),
        }

        self.elements.back_color = self.general_background

        self.edition_mode = None
        self.view_mode = ChartTextAnnotator.ViewModeRawData
        self.view_scale = 1.0

        self.data_changed = False
        self.tempo_edit_text = None

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

        self.container_text_options = None
        self.lbl_text_title = None
        self.lbx_text_list = None
        self.btn_text_add = None
        self.btn_text_edit = None
        self.btn_text_delete = None
        self.btn_return_accept = None
        self.btn_return_cancel = None

        self.container_edit_options = None
        self.lbl_edit_title = None
        self.lbx_edit_type = None
        self.lbl_edit_text = None
        self.btn_edit_OCR_0 = None
        self.btn_edit_OCR_180 = None
        self.btn_edit_OCR_any = None
        self.btn_edit_OCR_270 = None
        self.btn_edit_OCR_90 = None
        self.txt_edit_text = None
        self.btn_edit_cancel = None
        self.btn_edit_accept = None

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
        self.label_title = ScreenLabel("title", "Chart Image Annotation Tool - Panel Text Annotation", 28)
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
        # general edition options
        darker_background = (100, 66, 30)
        self.container_text_options = ScreenContainer("container_text_options", (container_width, 550),
                                                      back_color=darker_background)
        self.container_text_options.position = (self.container_view_buttons.get_left(), self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_text_options)

        self.lbl_text_title = ScreenLabel("lbl_text_title", "Options for Text Annotation", 21, 290, 1)
        self.lbl_text_title.position = (5, 5)
        self.lbl_text_title.set_background(darker_background)
        self.lbl_text_title.set_color(self.text_color)
        self.container_text_options.append(self.lbl_text_title)

        self.lbx_text_list = ScreenTextlist("lbx_text_list", (container_width - 20, 350), 18, back_color=(255,255,255),
                                            option_color=(0, 0, 0), selected_back=(120, 80, 50),
                                            selected_color=(255, 255, 255))
        self.lbx_text_list.position = (10, self.lbl_text_title.get_bottom() + 10)
        self.lbx_text_list.selected_value_change_callback = self.lbx_text_list_option_changed
        self.container_text_options.append(self.lbx_text_list)

        self.btn_text_add = ScreenButton("btn_text_add", "Add", 21, 90)
        self.btn_text_add.set_colors(button_text_color, button_back_color)
        self.btn_text_add.position = (10, self.lbx_text_list.get_bottom() + 10)
        self.btn_text_add.click_callback = self.btn_text_add_click
        self.container_text_options.append(self.btn_text_add)

        self.btn_text_edit = ScreenButton("btn_text_edit", "Edit", 21, 90)
        self.btn_text_edit.set_colors(button_text_color, button_back_color)
        self.btn_text_edit.position = ((self.container_text_options.width - self.btn_text_edit.width) / 2,
                                       self.lbx_text_list.get_bottom() + 10)
        self.btn_text_edit.click_callback = self.btn_text_edit_click
        self.container_text_options.append(self.btn_text_edit)

        self.btn_text_delete = ScreenButton("btn_text_delete", "Delete", 21, 90)
        self.btn_text_delete.set_colors(button_text_color, button_back_color)
        self.btn_text_delete.position = (self.container_text_options.width - self.btn_text_delete.width - 10,
                                           self.lbx_text_list.get_bottom() + 10)
        self.btn_text_delete.click_callback = self.btn_text_delete_click
        self.container_text_options.append(self.btn_text_delete)

        self.btn_return_accept = ScreenButton("btn_return_accept", "Accept", 21, button_2_width)
        self.btn_return_accept.set_colors(button_text_color, button_back_color)
        self.btn_return_accept.position = (button_2_left, self.container_text_options.height - self.btn_return_accept.height - 10)
        self.btn_return_accept.click_callback = self.btn_return_accept_click
        self.container_text_options.append(self.btn_return_accept)

        self.btn_return_cancel = ScreenButton("btn_return_cancel", "Cancel", 21, button_2_width)
        self.btn_return_cancel.set_colors(button_text_color, button_back_color)
        self.btn_return_cancel.position = (button_2_right, self.container_text_options.height - self.btn_return_cancel.height - 10)
        self.btn_return_cancel.click_callback = self.btn_return_cancel_click
        self.container_text_options.append(self.btn_return_cancel)

        # =============================================================
        # options for editing a given text

        self.container_edit_options = ScreenContainer("container_edit_options", (container_width, 550),
                                                      back_color=darker_background)
        self.container_edit_options.position = (self.container_view_buttons.get_left(), self.container_view_buttons.get_bottom() + 20)
        self.elements.append(self.container_edit_options)

        self.lbl_edit_title = ScreenLabel("lbl_edit_title", "Editing Text", 21, 290, 1)
        self.lbl_edit_title.position = (5, 5)
        self.lbl_edit_title.set_background(darker_background)
        self.lbl_edit_title.set_color(self.text_color)
        self.container_edit_options.append(self.lbl_edit_title)

        self.lbx_edit_type = ScreenTextlist("lbx_edit_type", (button_2_width, 280), 18, back_color=(255,255,255),
                                            option_color=(0, 0, 0), selected_back=(120, 80, 50),
                                            selected_color=(255, 255, 255))
        self.lbx_edit_type.position = (10, self.lbl_edit_title.get_bottom() + 10)
        self.container_edit_options.append(self.lbx_edit_type)
        self.add_text_types()

        self.btn_edit_force_box = ScreenButton("btn_edit_force_box", "Force Box", 21, button_2_width)
        self.btn_edit_force_box.set_colors(button_text_color, button_back_color)
        self.btn_edit_force_box.position = (button_2_right, self.lbl_edit_title.get_bottom() + 10)
        self.btn_edit_force_box.click_callback = self.btn_edit_force_box_click
        self.container_edit_options.append(self.btn_edit_force_box)

        self.btn_edit_force_quad = ScreenButton("btn_edit_force_quad", "Force Quad", 21, button_2_width)
        self.btn_edit_force_quad.set_colors(button_text_color, button_back_color)
        self.btn_edit_force_quad.position = (button_2_right, self.btn_edit_force_box.get_bottom() + 10)
        self.btn_edit_force_quad.click_callback = self.btn_edit_force_quad_click
        self.container_edit_options.append(self.btn_edit_force_quad)

        self.lbl_edit_text = ScreenLabel("lbl_edit_text", "Transcription", 21, button_width, 1)
        self.lbl_edit_text.position = (button_left, self.lbx_edit_type.get_bottom() + 20)
        self.lbl_edit_text.set_background(darker_background)
        self.lbl_edit_text.set_color(self.text_color)
        self.container_edit_options.append(self.lbl_edit_text)

        self.btn_edit_OCR_0 = ScreenButton("btn_edit_OCR_0", "OCR R+0", 21, button_2_width)
        self.btn_edit_OCR_0.set_colors(button_text_color, button_back_color)
        self.btn_edit_OCR_0.position = (button_2_left, self.lbl_edit_text.get_bottom() + 10)
        self.btn_edit_OCR_0.click_callback = self.btn_edit_OCR_0_click
        self.container_edit_options.append(self.btn_edit_OCR_0)

        self.btn_edit_OCR_any = ScreenButton("btn_edit_OCR_any", "OCR R+ANY", 21, button_2_width)
        self.btn_edit_OCR_any.set_colors(button_text_color, button_back_color)
        self.btn_edit_OCR_any.position = (button_2_right, self.lbl_edit_text.get_bottom() + 10)
        self.btn_edit_OCR_any.click_callback = self.btn_edit_OCR_any_click
        self.container_edit_options.append(self.btn_edit_OCR_any)

        """
        self.btn_edit_OCR_180 = ScreenButton("btn_edit_OCR_180", "OCR R+180", 21, button_2_width)
        self.btn_edit_OCR_180.set_colors(button_text_color, button_back_color)
        self.btn_edit_OCR_180.position = (button_2_right, self.lbl_edit_text.get_bottom() + 10)
        self.btn_edit_OCR_180.click_callback = self.btn_edit_OCR_180_click
        self.container_edit_options.append(self.btn_edit_OCR_180)
        """

        self.btn_edit_OCR_270 = ScreenButton("btn_edit_OCR_270", "OCR R-90", 21, button_2_width)
        self.btn_edit_OCR_270.set_colors(button_text_color, button_back_color)
        self.btn_edit_OCR_270.position = (button_2_left, self.btn_edit_OCR_0.get_bottom() + 10)
        self.btn_edit_OCR_270.click_callback = self.btn_edit_OCR_270_click
        self.container_edit_options.append(self.btn_edit_OCR_270)

        self.btn_edit_OCR_90 = ScreenButton("btn_edit_OCR_90", "OCR R+90", 21, button_2_width)
        self.btn_edit_OCR_90.set_colors(button_text_color, button_back_color)
        self.btn_edit_OCR_90.position = (button_2_right, self.btn_edit_OCR_0.get_bottom() + 10)
        self.btn_edit_OCR_90.click_callback = self.btn_edit_OCR_90_click
        self.container_edit_options.append(self.btn_edit_OCR_90)



        self.txt_edit_text = ScreenTextbox("txt_edit_text", "", 24, container_width - 20,
                                           text_color=(255, 255, 255), back_color=(0, 0, 0))
        self.txt_edit_text.position = (5, self.btn_edit_OCR_270.get_bottom() + 10)
        self.txt_edit_text.capture_EOL = True # allow multi-line elements
        self.container_edit_options.append(self.txt_edit_text)

        self.btn_edit_cancel = ScreenButton("btn_edit_cancel", "Cancel", 21, button_2_width)
        self.btn_edit_cancel.set_colors(button_text_color, button_back_color)
        self.btn_edit_cancel.position = (button_2_right, self.container_edit_options.height - self.btn_edit_cancel.height - 10)
        self.btn_edit_cancel.click_callback = self.btn_edit_cancel_click
        self.container_edit_options.append(self.btn_edit_cancel)

        self.btn_edit_accept = ScreenButton("btn_return_accept", "Accept", 21, button_2_width)
        self.btn_edit_accept.set_colors(button_text_color, button_back_color)
        self.btn_edit_accept.position = (button_2_left, self.container_edit_options.height - self.btn_edit_accept.height - 10)
        self.btn_edit_accept.click_callback = self.btn_edit_accept_click
        self.container_edit_options.append(self.btn_edit_accept)
        self.container_edit_options.visible = False

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
        self.img_main.double_click_callback = self.img_mouse_double_click
        self.img_main.mouse_button_down_callback = self.img_mouse_down
        self.container_images.append(self.img_main)

        self.canvas_select = ScreenCanvas("canvas_select", 100, 100)
        self.canvas_select.position = (0, 0)
        self.canvas_select.locked = True
        # self.canvas_select.object_edited_callback = self.canvas_object_edited
        # self.canvas_select.object_selected_callback = self.canvas_selection_changed
        self.container_images.append(self.canvas_select)

        base_points = np.array([[10, 10],[20, 10], [20, 20], [10, 20]], dtype=np.float64)
        self.canvas_select.add_polygon_element("selection_polygon", base_points)
        self.canvas_select.elements["selection_polygon"].visible = False

        self.canvas_display = ScreenCanvas("canvas_display", 100, 100)
        self.canvas_display.position = (0, 0)
        self.canvas_display.locked = True
        self.container_images.append(self.canvas_display)

        self.add_text_regions()

        self.set_editor_mode(ChartTextAnnotator.ModeNavigate)

    def add_text_types(self):
        self.lbx_edit_type.add_option(str(TextInfo.TypeChartTitle), "Chart Title")
        self.lbx_edit_type.add_option(str(TextInfo.TypeAxisTitle), "Axis Title")
        self.lbx_edit_type.add_option(str(TextInfo.TypeTickLabel), "Tick Label")
        self.lbx_edit_type.add_option(str(TextInfo.TypeLegendTitle), "Legend Title")
        self.lbx_edit_type.add_option(str(TextInfo.TypeLegendLabel), "Legend Label")
        self.lbx_edit_type.add_option(str(TextInfo.TypeValueLabel), "Value Label")
        self.lbx_edit_type.add_option(str(TextInfo.TypeOther), "Other")

    def get_text_display(self, text):
        return "{0:d} - {1:s}: {2:s}".format(text.id, text.get_type_description(), text.value)

    def add_text_regions(self):
        # populate the list-box using existing text regions (if any)
        for text in self.text_regions:
            self.lbx_text_list.add_option(str(text.id), self.get_text_display(text))

            self.canvas_display.add_polygon_element(str(text.id), text.position_polygon.copy(),
                                                    self.canvas_colors[text.type], self.canvas_sel_colors[text.type])


    def btn_zoom_reduce_click(self, button):
        self.update_view_scale(self.view_scale - 0.25)

    def btn_zoom_increase_click(self, button):
        self.update_view_scale(self.view_scale + 0.25)

    def btn_zoom_zero_click(self, button):
        self.update_view_scale(1.0)

    def btn_view_raw_data_click(self, button):
        self.view_mode = ChartTextAnnotator.ViewModeRawData
        self.update_current_view()

    def btn_view_gray_data_click(self, button):
        self.view_mode = ChartTextAnnotator.ViewModeGrayData
        self.update_current_view()

    def btn_view_raw_clear_click(self, button):
        self.view_mode = ChartTextAnnotator.ViewModeRawNoData
        self.update_current_view()

    def btn_view_gray_clear_click(self, button):
        self.view_mode = ChartTextAnnotator.ViewModeGrayNoData
        self.update_current_view()

    def update_current_view(self, resized=False):
        if self.view_mode in [ChartTextAnnotator.ViewModeGrayData, ChartTextAnnotator.ViewModeGrayNoData]:
            # gray scale mode
            base_image = self.panel_gray
        else:
            base_image = self.panel_image

        h, w, c = base_image.shape

        modified_image = base_image.copy()

        if self.view_mode in [ChartTextAnnotator.ViewModeRawData, ChartTextAnnotator.ViewModeGrayData]:
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
        self.container_text_options.visible = (self.edition_mode == ChartTextAnnotator.ModeNavigate)

        # Edit panels ...
        self.container_edit_options.visible = self.edition_mode in [ChartTextAnnotator.ModeAddingTextEdit,
                                                                    ChartTextAnnotator.ModeEditingText]

        # Confirm panel and buttons  ...
        self.container_confirm_buttons.visible = self.edition_mode in [ChartTextAnnotator.ModeAddingTextSelect,
                                                                       ChartTextAnnotator.ModeConfirmDeleteText,
                                                                       ChartTextAnnotator.ModeConfirmExit,
                                                                       ChartTextAnnotator.ModeConfirmOverwrite]

        if self.edition_mode == ChartTextAnnotator.ModeAddingTextSelect:
            self.lbl_confirm_message.set_text("Select Text Location")
        elif self.edition_mode == ChartTextAnnotator.ModeAddingTextEdit:
            self.lbl_confirm_message.set_text("Adding Text Region")
        elif self.edition_mode == ChartTextAnnotator.ModeConfirmDeleteText:
            self.lbl_confirm_message.set_text("Delete Text Region?")
        elif self.edition_mode == ChartTextAnnotator.ModeConfirmExit:
            self.lbl_confirm_message.set_text("Discard Changes to Text?")
        elif self.edition_mode == ChartTextAnnotator.ModeConfirmOverwrite:
            self.lbl_confirm_message.set_text("Discarding Legend/Axis data, Proceed?")

        # Do not show accept at these steps (they can be implicitly accepted, but need explicit cancel button only)
        self.btn_confirm_accept.visible = self.edition_mode != ChartTextAnnotator.ModeAddingTextSelect

        if new_mode in [ChartTextAnnotator.ModeAddingTextEdit, ChartTextAnnotator.ModeEditingText]:
            # show polygon
            self.canvas_select.locked = False
            self.canvas_select.elements["selection_polygon"].visible = True
        else:
            # for every other mode
            self.canvas_select.locked = True
            self.canvas_select.elements["selection_polygon"].visible = False

        if new_mode == ChartTextAnnotator.ModeAddingTextEdit:
            # prepare empty input ...
            self.lbx_text_list.change_option_selected(None)
            self.txt_edit_text.updateText("")

    def btn_confirm_accept_click(self, button):
        if self.edition_mode == ChartTextAnnotator.ModeConfirmExit:
            print("-> Changes made to Text Annotations were lost")
            self.return_screen = self.parent_screen
        elif self.edition_mode == ChartTextAnnotator.ModeConfirmDeleteText:
            # delete tempo region ...
            # remove from text regions
            self.text_regions.remove(self.tempo_edit_text)

            # remove from the GUI
            self.lbx_text_list.remove_option(str(self.tempo_edit_text.id))
            self.canvas_display.remove_element(str(self.tempo_edit_text.id))

            self.data_changed = True

            # return  ...
            self.set_editor_mode(ChartTextAnnotator.ModeNavigate)
        elif self.edition_mode == ChartTextAnnotator.ModeConfirmOverwrite:
            # overwrite text data ...
            if self.admin_mode:
                overwrite = input("Discard Axis and/or Legend Info (y/n)? ").lower() in ["y", "yes", "1", "true"]
            else:
                # for all other users, existing data will be discarded to ensure consistency
                overwrite = True

            self.panel_info.overwrite_text(self.text_regions, overwrite)
            self.parent_screen.subtool_completed(True)
            # return
            self.return_screen = self.parent_screen
        else:
            raise Exception("Not Implemented")

    def btn_confirm_cancel_click(self, button):
        if self.edition_mode in [ChartTextAnnotator.ModeAddingTextSelect,
                                 ChartTextAnnotator.ModeConfirmDeleteText,
                                 ChartTextAnnotator.ModeConfirmExit,
                                 ChartTextAnnotator.ModeConfirmOverwrite]:
            # return to navigation
            self.set_editor_mode(ChartTextAnnotator.ModeNavigate)
        else:
            print(self.edition_mode)
            raise Exception("Not Implemented")

    def get_next_polygon(self, click_x, click_y):

        if len(self.text_regions) > 0 and self.text_regions[-1].axis_aligned_rectangle_ratio() < 0.8:
            # simply copy as a polygon centered on the click point

            # copy and scale to current view ...
            points = self.text_regions[-1].position_polygon.copy() * self.view_scale

            # find scaled center ... compute and apply translation to get a polygon aligned with the click point
            old_cx = points[:, 0].mean()
            old_cy = points[:, 1].mean()

            delta_x = click_x - old_cx
            delta_y = click_y - old_cy

            points[:, 0] += delta_x
            points[:, 1] += delta_y
        else:
            if len(self.text_regions) == 0:
                # default small rectangle
                rect_w, rect_h = 40, 20
            else:
                # axis aligned container rectangle from last bbox
                min_x, min_y, max_x, max_y = self.text_regions[-1].get_axis_aligned_rectangle()

                rect_w = (max_x - min_x) * self.view_scale
                rect_h = (max_y - min_y) * self.view_scale

            points = np.array([[click_x, click_y], [click_x + rect_w, click_y],
                               [click_x + rect_w, click_y + rect_h], [click_x, click_y + rect_h]])

        return points

    def img_mouse_double_click(self, element, pos, button):
        if button == 1:
            # double left click ...
            if self.edition_mode == ChartTextAnnotator.ModeNavigate:
                click_x, click_y = pos
                points = self.get_next_polygon(click_x, click_y)
                self.canvas_select.elements["selection_polygon"].update(points)

                self.set_editor_mode(ChartTextAnnotator.ModeAddingTextEdit)
        elif button == 3:
            # double right click ....
            if self.edition_mode == ChartTextAnnotator.ModeNavigate:
                click_x, click_y = pos

                # scale the view ....
                click_x /= self.view_scale
                click_y /= self.view_scale

                # find if a given element was clicked ....
                for text_region in self.text_regions:
                    # check ...
                    if text_region.area_contains_point(click_x, click_y):
                        # clicked on a text region ...
                        self.lbx_text_list.change_option_selected(str(text_region.id))
                        # simulate click on edit button ....
                        self.btn_text_edit_click(None)
                        break


    def btn_text_add_click(self, button):
        self.set_editor_mode(ChartTextAnnotator.ModeAddingTextSelect)

    def btn_text_edit_click(self, button):
        if self.lbx_text_list.selected_option_value is None:
            print("Must select an option to edit")
            return

        for text in self.text_regions:
            if text.id == int(self.lbx_text_list.selected_option_value):
                # option found
                # copy
                self.tempo_edit_text = text

                # ... copy points to selection canvas ...
                polygon = self.tempo_edit_text.position_polygon.copy() * self.view_scale
                self.canvas_select.update_polygon_element("selection_polygon", polygon, True)
                # ... copy type to list of types
                self.lbx_edit_type.change_option_selected(str(self.tempo_edit_text.type))
                # ... copy transcript to textbox
                self.txt_edit_text.updateText(self.tempo_edit_text.value)

                self.canvas_display.elements[str(self.tempo_edit_text.id)].visible = False

                self.set_editor_mode(ChartTextAnnotator.ModeEditingText)
                break

    def btn_text_delete_click(self, button):
        if self.lbx_text_list.selected_option_value is None:
            print("Must select an option to edit")
            return

        for text in self.text_regions:
            if text.id == int(self.lbx_text_list.selected_option_value):
                # option found
                # copy
                self.tempo_edit_text = text

                self.set_editor_mode(ChartTextAnnotator.ModeConfirmDeleteText)
                break

    def btn_return_accept_click(self, button):
        if self.data_changed:
            if self.panel_info.legend is not None or self.panel_info.axes is not None:
                # confirm if return ... might overwrite existing data
                self.set_editor_mode(ChartTextAnnotator.ModeConfirmOverwrite)
            else:
                # overwrite text data ... both legend  and axes are None
                self.panel_info.overwrite_text(self.text_regions, False)
                # return
                self.return_screen = self.parent_screen
        else:
            # Nothing changed just return
            self.return_screen = self.parent_screen



    def btn_return_cancel_click(self, button):
        if self.data_changed:
            # confirm if return ...
            self.set_editor_mode(ChartTextAnnotator.ModeConfirmExit)
        else:
            # just return
            self.return_screen = self.parent_screen

    def find_next_id(self):
        if len(self.text_regions) == 0:
            return 0
        else:
            return max([text.id for text in self.text_regions]) + 1

    def btn_edit_accept_click(self, button):
        if self.lbx_edit_type.selected_option_value is None:
            print("-> Must Select text type")
            return

        if len(self.txt_edit_text.text.strip()) == 0:
            print("-> Must Provide Transcription")
            return

        text_polygon = self.canvas_select.elements["selection_polygon"].points / self.view_scale
        text_type = int(self.lbx_edit_type.selected_option_value)
        text_value = self.txt_edit_text.text.strip()

        if self.edition_mode == ChartTextAnnotator.ModeAddingTextEdit:
            # new text will be added
            next_id = self.find_next_id()
            text = TextInfo(next_id, text_polygon, text_type, text_value)
            self.text_regions.append(text)
            # add to the GUI
            display = self.get_text_display(text)
            self.lbx_text_list.add_option(str(next_id), display)
            self.canvas_display.add_polygon_element(str(text.id), text.position_polygon.copy() * self.view_scale,
                                                    self.canvas_colors[text.type], self.canvas_sel_colors[text.type])
            self.data_changed = True
            # return  ...
            self.set_editor_mode(ChartTextAnnotator.ModeNavigate)
        elif self.edition_mode == ChartTextAnnotator.ModeEditingText:
            # existing text should be over-written

            self.tempo_edit_text.position_polygon = text_polygon
            self.tempo_edit_text.type = text_type
            self.tempo_edit_text.value = text_value

            key_str = str(self.tempo_edit_text.id)
            display = self.get_text_display(self.tempo_edit_text)

            # update list
            self.lbx_text_list.update_option_display(key_str, display)
            # update and make canvas representation of the text region visible again ..
            canvas_points = self.tempo_edit_text.position_polygon.copy() * self.view_scale
            self.canvas_display.update_polygon_element(key_str, canvas_points, True)
            self.canvas_display.update_custom_colors(key_str, self.canvas_colors[self.tempo_edit_text.type],
                                                     self.canvas_sel_colors[self.tempo_edit_text.type])

            # remove temporal reference
            self.tempo_edit_text = None

            self.data_changed = True
            # return  ...
            self.set_editor_mode(ChartTextAnnotator.ModeNavigate)

    def btn_edit_cancel_click(self, button):
        if self.edition_mode == ChartTextAnnotator.ModeEditingText:
            # make the selected element visible again (no changes)
            self.canvas_display.elements[str(self.tempo_edit_text.id)].visible = True

        # return ....
        self.set_editor_mode(ChartTextAnnotator.ModeNavigate)

    def img_mouse_down(self, img_object, pos, button):
        if button == 1:
            if self.edition_mode == ChartTextAnnotator.ModeAddingTextSelect:
                click_x, click_y = pos
                points = self.get_next_polygon(click_x, click_y)
                self.canvas_select.elements["selection_polygon"].update(points)

                self.set_editor_mode(ChartTextAnnotator.ModeAddingTextEdit)

    def lbx_text_list_option_changed(self, new_value, old_value):
        self.canvas_display.change_selected_element(new_value)


    def btn_edit_OCR_0_click(self, button):
        self.apply_OCR(ChartTextAnnotator.Rotation0)
        # self.apply_OCR(ChartTextAnnotator.RotationAuto)

    def btn_edit_OCR_any_click(self, button):
        self.apply_OCR(ChartTextAnnotator.RotationAuto)

    def btn_edit_OCR_90_click(self, button):
        self.apply_OCR(ChartTextAnnotator.Rotation90)

    def btn_edit_OCR_270_click(self, button):
        self.apply_OCR(ChartTextAnnotator.Rotation270)

    def btn_edit_OCR_180_click(self, button):
        self.apply_OCR(ChartTextAnnotator.Rotation180)

    def order_points(self, pts):
        # sort the points based on their x-coordinates
        xSorted = pts[np.argsort(pts[:, 0]), :]

        # grab the left-most and right-most points from the sorted
        # x-roodinate points
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]

        # now, sort the left-most coordinates according to their
        # y-coordinates so we can grab the top-left and bottom-left
        # points, respectively
        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost

        # now that we have the top-left coordinate, use it as an
        # anchor to calculate the Euclidean distance between the
        # top-left and right-most points; by the Pythagorean
        # theorem, the point with the largest distance will be
        # our bottom-right point
        D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
        (br, tr) = rightMost[np.argsort(D)[::-1], :]

        # return the coordinates in top-left, top-right,
        # bottom-right, and bottom-left order
        return np.asarray([tl, tr, br, bl], dtype=pts.dtype)

    def crop_rotated_rectangle(self, img, coords):
        # find rotated rectangle
        rect = cv2.minAreaRect(coords.reshape(4, 1, 2).astype(np.float32))
        rbox = self.order_points(cv2.boxPoints(rect))
        # get width and height of the detected rectangle
        # output of minAreaRect is unreliable for already axis aligned rectangles!!
        width = np.linalg.norm([rbox[0, 0] - rbox[1, 0], rbox[0, 1] - rbox[1, 1]])
        height = np.linalg.norm([rbox[0, 0] - rbox[-1, 0], rbox[0, 1] - rbox[-1, 1]])
        src_pts = rbox.astype(np.float32)
        # coordinate of the points in box points after the rectangle has been straightened
        # this step needs order_points to be called on src
        dst_pts = np.array([[0, 0],
                            [width - 1, 0],
                            [width - 1, height - 1],
                            [0, height - 1]], dtype="float32")
        # the perspective transformation matrix
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        # directly warp the rotated rectangle to get the straightened rectangle
        warped = cv2.warpPerspective(img, M, (width, height), None, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT,
                                     (255, 255, 255))
        return warped

    def crop_axis_aligned_rectangle(self, img, text_polygon, rotation):
        panel_h, panel_w, _ = img.shape

        # get polygon bounding box ...
        x1 = max(0, int(text_polygon[:, 0].min()))
        y1 = max(0, int(text_polygon[:, 1].min()))

        x2 = min(panel_w, int(text_polygon[:, 0].max() + 1))
        y2 = min(panel_h, int(text_polygon[:, 1].max() + 1))

        # get image first ..
        text_img = img[y1:y2, x1:x2]
        h, w, _ = text_img.shape

        # apply rotation ... (if any)
        if rotation == ChartTextAnnotator.Rotation90:
            M = cv2.getRotationMatrix2D((0, 0), -90, 1)
            M[0, 2] += (h - 1)
            text_img = cv2.warpAffine(text_img, M, (h, w))

        elif rotation == ChartTextAnnotator.Rotation180:
            M = cv2.getRotationMatrix2D((0, 0), -180, 1)
            M[0, 2] += (w - 1)
            M[1, 2] += (h - 1)
            text_img = cv2.warpAffine(text_img, M, (w, h))

        elif rotation == ChartTextAnnotator.Rotation270:
            M = cv2.getRotationMatrix2D((0, 0), 90, 1)
            M[1, 2] += (w - 1)
            text_img = cv2.warpAffine(text_img, M, (h, w))

        return text_img

    def apply_OCR(self, rotation):
        if OCR is None:
            print("PyTesseract not found, please install to enable this function")
            return

        text_polygon = self.canvas_select.elements["selection_polygon"].points / self.view_scale
        print(text_polygon)

        if rotation == ChartTextAnnotator.RotationAuto:
            text_polygon = self.order_points(text_polygon)
            text_img = self.crop_rotated_rectangle(self.panel_image, text_polygon)
        else:
            text_img = self.crop_axis_aligned_rectangle(self.panel_image, text_polygon, rotation)

        result = OCR.image_to_string(text_img, config='--psm 6')
        self.txt_edit_text.updateText(result)

        #if result.strip() == "":
        cv2.imwrite("TEMPO_CHECK_OCR_2.png", text_img)

        print("-> Tesseract Result: " + result)


    def btn_edit_force_box_click(self, button):
        text_polygon = self.canvas_select.elements["selection_polygon"].points / self.view_scale

        poly = Polygon(text_polygon)
        minx, miny, maxx, maxy = poly.bounds

        text_polygon = np.array([[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy]])
        self.canvas_select.elements["selection_polygon"].update(text_polygon * self.view_scale)


    def btn_edit_force_quad_click(self, button):
        text_polygon = self.canvas_select.elements["selection_polygon"].points / self.view_scale

        rot_rect = cv2.minAreaRect(text_polygon.reshape(4, 1, 2).astype(np.float32))
        quad_points = self.order_points(cv2.boxPoints(rot_rect)).astype(text_polygon.dtype)

        self.canvas_select.elements["selection_polygon"].update(quad_points * self.view_scale)


