
import os
import numpy as np
import cv2

from AM_CommonTools.interface.controls.screen import Screen
from AM_CommonTools.interface.controls.screen_container import ScreenContainer
from AM_CommonTools.interface.controls.screen_label import ScreenLabel
from AM_CommonTools.interface.controls.screen_image import ScreenImage
from AM_CommonTools.interface.controls.screen_button import ScreenButton
from AM_CommonTools.interface.controls.screen_paginator import ScreenPaginator

from .chart_image_annotator import ChartImageAnnotator
from ChartInfo.data.image_info import ImageInfo
from ChartInfo.util.time_stats import TimeStats

class ChartMainAnnotator(Screen):

    def __init__(self, size, chart_dir, annotation_dir, admin_mode):
        Screen.__init__(self, "Chart Ground Truth Annotation Interface", size)

        # load the chart directory info ...
        self.chart_image_list = ImageInfo.ListChartDirectory(chart_dir, "")
        print("A total of {0:d} chart images were found".format(len(self.chart_image_list)))

        self.annotation_times = TimeStats()

        self.general_background = (20, 50, 85)
        self.text_color = (255, 255, 255)
        self.admin_mode = admin_mode
        self.small_mode = size[0] < 1500

        # about the grid ....
        self.tb_grid_cols = 5 if self.small_mode else 6
        self.tb_grid_rows = 3 if self.small_mode else 4
        self.tb_width = 160
        self.tb_height = 120
        self.tb_outer_margin = 16
        self.tb_inner_margin = 4
        self.tb_label_height = 14  # this is approx
        self.tb_progress_h = 16
        self.tb_progress_border = 4

        self.tb_col_width = (self.tb_outer_margin + self.tb_width)
        self.tb_row_height = (self.tb_outer_margin + self.tb_inner_margin * 2 + self.tb_progress_h +
                              self.tb_label_height + self.tb_height)

        self.elements.back_color = self.general_background

        self.chart_dir = chart_dir
        self.annotation_dir = annotation_dir

        # define here all graphic object references ....
        # ...for thumbnails ....
        self.container_thumbnails = None
        self.thumbnails_images = None
        self.thumbnails_status = None
        self.thumbnails_labels = None
        self.cache_raw_status = None
        self.paginator = None
        # ... right side image options ...
        self.lbl_page_descriptor = None
        self.container_image_info = None
        self.img_status_panels = None
        self.img_status_classes = None
        self.img_status_text = None
        self.img_status_legend = None
        self.img_status_axis = None
        self.img_status_data = None
        self.img_display = None
        self.img_title = None
        self.btn_label_image = None
        self.btn_next_image = None
        self.btn_prev_image = None
        # ... general ...
        self.btn_exit = None

        # ... create them!!! .....
        self.create_controllers()

        # ... load current page data ....
        self.current_page = None
        self.selected_element = 0
        self.load_page(None, 0)

    def create_controllers(self):
        button_text_color = (35, 50, 20)
        button_back_color = (228, 228, 228)

        # thumbnail grid parameters
        tb_empty = np.zeros((3, 4, 3), dtype=np.uint8)
        default_status = self.gen_status_image([0] * 6, self.tb_width, self.tb_progress_h, self.tb_progress_border)

        # create the thumbnail container ....
        tb_contained_width = self.tb_col_width * self.tb_grid_cols + self.tb_outer_margin
        tb_contained_height = self.tb_row_height * self.tb_grid_rows + self.tb_outer_margin
        self.container_thumbnails = ScreenContainer("container_nav_buttons", (tb_contained_width, tb_contained_height),
                                                    back_color=(15, 30, 50))
        self.container_thumbnails.position = (10, 10)
        self.elements.append(self.container_thumbnails)

        # generate the default grid ....
        self.thumbnails_images = []
        self.thumbnails_status = []
        self.thumbnails_labels = []
        self.cache_raw_status = []
        for row in range(self.tb_grid_rows):
            for col in range(self.tb_grid_cols):
                corner_x = self.tb_outer_margin + self.tb_col_width * col
                corner_y = self.tb_outer_margin + self.tb_row_height * row

                tb_image = ScreenImage("tb_image_{0:d}_{1:d}".format(row, col), tb_empty, self.tb_width, self.tb_height, True)
                tb_image.position = (corner_x, corner_y)
                tb_image.tag = (row, col)
                tb_image.click_callback = self.thumbnail_image_click
                self.container_thumbnails.append(tb_image)
                self.thumbnails_images.append(tb_image)

                tb_status = ScreenImage("tb_status_{0:d}_{1:d}".format(row, col), default_status, self.tb_width, self.tb_progress_h)
                tb_status.position = (corner_x, tb_image.get_bottom() + self.tb_inner_margin)
                self.container_thumbnails.append(tb_status)
                self.thumbnails_status.append(tb_status)
                self.cache_raw_status.append(None)

                tb_label = ScreenLabel("tb_label_{0:d}_{1:d}".format(row, col), "<IMAGE FILE NAME>" , 12, self.tb_width, centered=1)
                tb_label.position = (corner_x, tb_status.get_bottom() + self.tb_inner_margin)
                tb_label.background = self.container_thumbnails.back_color
                tb_label.set_color(self.text_color)
                self.container_thumbnails.append(tb_label)
                self.thumbnails_labels.append(tb_label)

        # the paginator ...
        self.paginator = ScreenPaginator("tb_paginator", 16, self.tb_grid_cols * self.tb_grid_rows, len(self.chart_image_list),
                                         self.container_thumbnails.width, text_color=button_text_color, back_color=button_back_color)
        self.paginator.position = (self.container_thumbnails.get_left(), self.container_thumbnails.get_bottom() + 20)
        self.paginator.page_selected_callback = self.load_page
        self.elements.append(self.paginator)

        img_container_width = self.width - 45 - self.container_thumbnails.width

        self.lbl_page_descriptor = ScreenLabel("lbl_page_descriptor", "Page XXX of YYY (ZZZZZ elements)", 16,
                                               img_container_width)
        self.lbl_page_descriptor.position = (self.container_thumbnails.get_right() + 15, self.container_thumbnails.get_top())
        self.lbl_page_descriptor.background = self.general_background
        self.lbl_page_descriptor.set_color(self.text_color)
        self.elements.append(self.lbl_page_descriptor)

        img_container_height = int(img_container_width) + 140
        self.container_image_info = ScreenContainer("container_image_info", (img_container_width, img_container_height),
                                                    back_color=(15,30, 50))
        self.container_image_info.position = (self.lbl_page_descriptor.get_left(), self.lbl_page_descriptor.get_bottom() + 10)
        self.elements.append(self.container_image_info)

        base_img = np.zeros((2, 2, 3), np.uint8)
        self.img_display = ScreenImage("img_display", base_img, self.container_image_info.width - 20,
                                       self.container_image_info.width - 20, True)
        self.img_display.position = (10, 20)
        self.container_image_info.append(self.img_display)

        stats_part_w = int((self.container_image_info.width - 20) / 6)
        text = "Pns" if self.small_mode else "Panels"
        self.img_status_panels = ScreenLabel("img_status_panels", text, 21, stats_part_w)
        self.img_status_panels.position = (int(20 + stats_part_w * 0), self.img_display.get_bottom() + 10)
        self.img_status_panels.background = (255, 0, 0)
        self.img_status_panels.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_panels)

        text = "Cls" if self.small_mode else "Classes"
        self.img_status_classes = ScreenLabel("img_status_classes", text, 21, stats_part_w)
        self.img_status_classes.position = (int(20 + stats_part_w * 1), self.img_status_panels.get_top())
        self.img_status_classes.background = (255, 0, 0)
        self.img_status_classes.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_classes)

        text = "Txt" if self.small_mode else "Text"
        self.img_status_text = ScreenLabel("img_status_text", text, 21, stats_part_w)
        self.img_status_text.position = (int(20 + stats_part_w * 2), self.img_status_panels.get_top())
        self.img_status_text.background = (255, 0, 0)
        self.img_status_text.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_text)

        text = "Lgn" if self.small_mode else "Legend"
        self.img_status_legend = ScreenLabel("img_status_text", text, 21, stats_part_w)
        self.img_status_legend.position = (int(20 + stats_part_w * 3), self.img_status_panels.get_top())
        self.img_status_legend.background = (255, 0, 0)
        self.img_status_legend.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_legend)

        text = "Axs" if self.small_mode else "Axis"
        self.img_status_axis = ScreenLabel("img_status_axis", text, 21, stats_part_w)
        self.img_status_axis.position = (int(20 + stats_part_w * 4), self.img_status_panels.get_top())
        self.img_status_axis.background = (255, 0, 0)
        self.img_status_axis.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_axis)

        text = "Dta" if self.small_mode else "Data"
        self.img_status_data = ScreenLabel("img_status_data", text, 21, stats_part_w)
        self.img_status_data.position = (int(20 + stats_part_w * 5), self.img_status_panels.get_top())
        self.img_status_data.background = (255, 0, 0)
        self.img_status_data.set_color((255, 255, 255))
        self.container_image_info.append(self.img_status_data)

        self.img_title = ScreenLabel("img_title", "<Image File Name>" * 10, 16, self.img_display.width)
        self.img_title.position = (10, self.img_status_panels.get_bottom() + 10)
        self.img_title.background = self.container_image_info.back_color
        self.img_title.set_color(self.text_color)
        self.container_image_info.append(self.img_title)

        btn_width = 90 if self.small_mode else 100
        btn_padding = 10 if self.small_mode else 20
        self.btn_label_image = ScreenButton("btn_label_image", "Annotate", 18, btn_width,
                                            text_color=button_text_color, back_color=button_back_color)
        self.btn_label_image.position = (int((self.container_image_info.width - self.btn_label_image.width) / 2),
                                         self.img_title.get_bottom() + 10)
        self.btn_label_image.click_callback = self.btn_annotate_click
        self.container_image_info.append(self.btn_label_image)

        self.btn_prev_image = ScreenButton("btn_prev_image", "Previous", 18, btn_width, text_color=button_text_color,
                                           back_color=button_back_color)
        self.btn_prev_image.position = (self.btn_label_image.get_left() - self.btn_prev_image.width - btn_padding,
                                         self.img_title.get_bottom() + 10)
        self.btn_prev_image.click_callback = self.btn_prev_image_click
        self.container_image_info.append(self.btn_prev_image)

        self.btn_next_image = ScreenButton("btn_next_image", "Next", 18, btn_width, text_color=button_text_color,
                                           back_color=button_back_color)
        self.btn_next_image.position = (self.btn_label_image.get_right() + btn_padding,
                                        self.img_title.get_bottom() + 10)
        self.btn_next_image.click_callback = self.btn_next_image_click
        self.container_image_info.append(self.btn_next_image)

        self.img_title.set_text("[Select Image]")

        # ... general ...
        self.btn_exit = ScreenButton("btn_exit", "Exit", 18, 100, text_color=button_text_color, back_color=button_back_color)
        self.btn_exit.position = (self.width - 15 - self.btn_exit.width, self.height - 15 - self.btn_exit.height)
        self.btn_exit.click_callback = self.btn_exit_click
        self.elements.append(self.btn_exit)

    def get_status_colors(self, all_status):
        status_colors = []
        for idx, value in enumerate(all_status):
            if value == 2:
                # labeled and verified
                color = (128, 255, 128)
            elif value == 1:
                # labeled but unverified
                color = (192, 192, 64)
            else:
                # not labeled or verified
                color = (192, 64, 64)

            status_colors.append(color)

        return status_colors

    def gen_status_image(self, all_status, width, height, border):
        result = np.zeros((height, width, 3), np.uint8)

        approx_width = (width - (len(all_status) + 1) * border) / len(all_status)
        status_colors = self.get_status_colors(all_status)
        last_x = 0
        for idx, color in enumerate(status_colors):
            left = last_x + border
            right = left + approx_width

            result[border:-border, int(left):int(right), :] = color
            last_x = right

        return result

    def btn_exit_click(self, button):
        # Just exit
        self.return_screen = None
        print("APPLICATION FINISHED")

    def update_annotation_times(self, chart_annotation_times):
        print("HERE!!")
        self.annotation_times.update_stats(chart_annotation_times)

    def refresh_page(self):
        self.load_page(None, self.current_page, True)
        self.update_selected_image_info()
        if self.admin_mode:
            print(str(self.annotation_times))

    def load_page(self, paginator, new_page, refresh=False):
        if new_page == self.current_page and not refresh:
            # page not changed ...
            return

        self.current_page = new_page

        page_size = len(self.thumbnails_images)

        current_elements = self.chart_image_list[self.current_page * page_size:(self.current_page + 1) * page_size]

        for idx in range(page_size):
            row = int(idx / self.tb_grid_cols)
            col = idx % self.tb_grid_cols

            if idx < len(current_elements):
                # update image ...
                chart_path = current_elements[idx]
                current_img = cv2.imread(self.chart_dir + chart_path)
                current_img = cv2.cvtColor(current_img, cv2.COLOR_BGR2RGB)
                self.thumbnails_images[idx].set_image(current_img, self.tb_width, self.tb_height, keep_aspect=True)

                # center new image
                corner_x = self.tb_outer_margin + self.tb_col_width * col
                corner_y = self.tb_outer_margin + self.tb_row_height * row
                self.center_image_in_box(self.thumbnails_images[idx], corner_x, corner_y, self.tb_width, self.tb_height)

                # find annotation path ...
                relative_dir, img_filename = os.path.split(chart_path)
                img_base, ext = os.path.splitext(img_filename)
                # output dir
                output_dir = self.annotation_dir + relative_dir
                annotation_filename = output_dir + "/" + img_base + ".xml"

                # default : No annotations ...
                if os.path.exists(annotation_filename):
                    # read the annotation ...
                    print(annotation_filename)
                    image_info = ImageInfo.FromXML(annotation_filename, current_img)

                    status_ints = ImageInfo.GetAllStatuses(image_info)
                else:
                    status_ints = ImageInfo.GetAllStatuses(None)

                self.cache_raw_status[idx] = status_ints

                status = self.gen_status_image(status_ints, self.tb_width, self.tb_progress_h, self.tb_progress_border)
                self.thumbnails_status[idx].set_image(status, self.tb_width, self.tb_progress_h)
                self.thumbnails_labels[idx].set_text(chart_path[1:])

                self.thumbnails_images[idx].visible = True
                self.thumbnails_status[idx].visible = True
                self.thumbnails_labels[idx].visible = True
            else:
                # special case for the last page ...
                self.cache_raw_status[idx] = None
                self.thumbnails_images[idx].visible = False
                self.thumbnails_status[idx].visible = False
                self.thumbnails_labels[idx].visible = False

        msg = "Page {0:d} of {1:d} ({2:d} elements)".format(self.current_page + 1, self.paginator.total_pages,
                                                            len(self.chart_image_list))
        self.lbl_page_descriptor.set_text(msg)

        if not refresh:
            self.selected_element = None
            self.update_selected_image(0)

    def update_selected_image(self, new_index):
        if new_index == self.selected_element:
            # no change in selection ...
            return

        self.selected_element = new_index

        page_size = len(self.thumbnails_images)
        for idx in range(page_size):
            if idx == self.selected_element:
                self.thumbnails_images[idx].border_width = 2
                self.thumbnails_images[idx].border_color = (255, 0, 0)

                self.thumbnails_labels[idx].set_color((255, 0, 0))
            else:
                self.thumbnails_images[idx].border_width = 0
                self.thumbnails_images[idx].border_color = (0, 0, 0)

                self.thumbnails_labels[idx].set_color(self.text_color)

        # update the panel on the right side
        self.update_selected_image_info()

    def update_selected_image_info(self):
        # This simply updates the GUI of the selected image
        # using self.selected_element

        # update image ....
        self.img_display.set_image(self.thumbnails_images[self.selected_element].original_image,
                                   self.container_image_info.width - 20, self.container_image_info.width - 20,
                                   True)
        self.center_image_in_box(self.img_display, 10, 10, self.container_image_info.width - 20,
                                 self.container_image_info.width - 20)

        # update image name ...
        self.img_title.set_text(self.thumbnails_labels[self.selected_element].text)

        # update image status ...
        raw_status = self.cache_raw_status[self.selected_element]
        status_colors = self.get_status_colors(raw_status)

        self.img_status_panels.background = status_colors[0]
        self.img_status_panels.set_color(self.invert_color(status_colors[0]))
        self.img_status_classes.background = status_colors[1]
        self.img_status_classes.set_color(self.invert_color(status_colors[1]))
        self.img_status_text.background = status_colors[2]
        self.img_status_text.set_color(self.invert_color(status_colors[2]))
        self.img_status_legend.background = status_colors[3]
        self.img_status_legend.set_color(self.invert_color(status_colors[3]))
        self.img_status_axis.background = status_colors[4]
        self.img_status_axis.set_color(self.invert_color(status_colors[4]))
        self.img_status_data.background = status_colors[5]
        self.img_status_data.set_color(self.invert_color(status_colors[5]))

    def invert_color(self, color):
        return 255 - color[0], 255 - color[1], 255 - color[2]

    def center_image_in_box(self, screen_image, x, y, width, height):
        assert isinstance(screen_image, ScreenImage)

        delta_x = int((width - screen_image.width) / 2)
        delta_y = int((height - screen_image.height) / 2)
        screen_image.position = (x + delta_x, y + delta_y)

    def thumbnail_image_click(self, thumbnail_image):
        # print((thumbnail_image.name, thumbnail_image.tag))
        row, col = thumbnail_image.tag
        idx = row * self.tb_grid_cols + col

        self.update_selected_image(idx)

    def btn_annotate_click(self, button):
        # find image name based on current page
        page_size = len(self.thumbnails_images)
        current_elements = self.chart_image_list[self.current_page * page_size:(self.current_page + 1) * page_size]
        chart_path = current_elements[self.selected_element]

        # create the child sub-menu ....
        image_annotator = ChartImageAnnotator(self.size, self.chart_dir, self.annotation_dir, chart_path, self,
                                              self.admin_mode)
        image_annotator.prepare_screen()

        self.return_screen = image_annotator

    def btn_next_image_click(self, button):
        page_size = len(self.thumbnails_images)
        current_elements = self.chart_image_list[self.current_page * page_size:(self.current_page + 1) * page_size]

        if self.selected_element + 1 < len(current_elements):
            # move to next within same page ...
            self.update_selected_image(self.selected_element + 1)
        else:
            if self.current_page + 1 < self.paginator.total_pages:
                self.paginator.set_current_page(self.current_page + 1)
                self.load_page(self.paginator, self.current_page + 1, True)
                self.update_selected_image(0)
            else:
                print("Current element is the last on the list of images")

    def btn_prev_image_click(self, button):
        page_size = len(self.thumbnails_images)

        if self.selected_element > 0:
            # move to the previous within the same page ...
            self.update_selected_image(self.selected_element - 1)
        else:
            if self.current_page > 0:
                self.paginator.set_current_page(self.current_page - 1)
                self.load_page(self.paginator, self.current_page - 1, True)
                self.update_selected_image(page_size - 1)
            else:
                print("Current element is the first on the list of images")

