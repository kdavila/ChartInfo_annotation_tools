
import numpy as np

from .series_sorting import SeriesSorting
from .axes_info import AxesInfo
from .axes_info import AxisValues
from .box_values import BoxValues

class BoxData:
    DataVersion = 1.0

    GroupingByCategory = 0
    GroupingByDataSeries = 1

    def __init__(self, data_series, categories, vertical, grouping, box_offset=0.0, box_width=1.0, box_inner_dis=1.0,
                 box_outer_dist=1.0, default_box_min=0, default_box_median=0, default_box_max=0,
                 default_whisker_min=0, default_whisker_max=0):
        # Arrays of text_info sorted by location (left to right or top to down)
        self.data_series = data_series
        self.categories = categories

        # Group by Category or By Data Series
        self.box_grouping = grouping

        # a list of list representing the organization (of boxes) ...
        # for ordering ... stacking disabled for Box Plots...
        self.box_sorting = SeriesSorting(len(self.data_series))

        self.box_vertical = vertical

        self.box_offset = box_offset
        self.box_width = box_width
        self.box_inner_dist = box_inner_dis
        self.box_outer_dist = box_outer_dist

        self.boxes = [
            [
                BoxValues(default_box_min, default_box_median, default_box_max,
                          default_whisker_min, default_whisker_max)
            for cat in self.categories] for s in self.data_series
        ]

    def add_data_series(self, text_label=None, default_box_min=0, default_box_median=0, default_box_max=0,
                        default_whisker_min=0, default_whisker_max=0):
        # add to data series ...
        self.data_series.append(text_label)

        # add to boxes .... (outer list)
        self.boxes.append([
            BoxValues(default_box_min, default_box_median, default_box_max, default_whisker_min, default_whisker_max)
            for cat in self.categories])

        self.box_sorting.add_series()

    def add_category(self, text_label=None, default_box_min=0, default_box_median=0, default_box_max=0,
                     default_whisker_min=0, default_whisker_max=0):
        # add to categories ...
        self.categories.append(text_label)

        # add to boxes ... (inner lists)
        for series_idx in range(len(self.data_series)):
            self.boxes[series_idx].append(BoxValues(default_box_min, default_box_median, default_box_max,
                                                    default_whisker_min, default_whisker_max))

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from boxes (outer list) ...
            del self.boxes[index]

            # remove from data series ...
            del self.data_series[index]

            # remove from sorting ...
            self.box_sorting.remove_series(index)

            return True
        else:
            return False

    def remove_category(self, index):
        if 0 <= index <= len(self.categories):
            # remove from boxes (inner lists) ...
            for series_idx in range(len(self.data_series)):
                del self.boxes[series_idx][index]

            # remove from categories ...
            del self.categories[index]

            return True
        else:
            return False

    def total_boxes(self):
        return len(self.categories) * len(self.data_series)

    def get_boxes(self):
        return [[BoxValues.Copy(box) for box in inner_boxes] for inner_boxes in self.boxes]

    @staticmethod
    def Copy(other):
        assert isinstance(other, BoxData)

        copy_series = list(other.data_series)
        copy_categories = list(other.categories)

        data = BoxData(copy_series, copy_categories, other.box_vertical, other.box_grouping,
                       other.box_offset, other.box_width, other.box_inner_dist, other.box_outer_dist)

        data.box_sorting = SeriesSorting.Copy(other.box_sorting)
        data.boxes = other.get_boxes()

        return data

    def get_grouping_desc(self):
        if self.box_grouping == BoxData.GroupingByCategory:
            return "by-category"
        elif self.box_grouping == BoxData.GroupingByDataSeries:
            return "by-data-series"
        else:
            raise Exception("Unexpected Box Data Grouping found")

    def compute_box_polygons(self, chart_info):
        # Parallel to the version of the function in Box Chart Annotator, but without drawing structures and temporals
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if self.box_vertical:
            # assume left to right
            box_start = x1 + self.box_offset
            # assume they start at the bottom
            box_baseline = y2
        else:
            # assume top to bottom
            box_start = y1 + self.box_offset
            # assume they start at the left
            box_baseline = x1

        boxes_lines = []
        medians_lines = []
        top_whiskers = []
        bottom_whiskers = []

        box_polygon_index = []

        if self.box_grouping == BoxData.GroupingByCategory:
            # boxes are grouped by categorical value ...
            for cat_idx, category in enumerate(self.categories):
                for group_idx, group in enumerate(self.box_sorting.order):
                    box_end = box_start + self.box_width

                    # No stacking for box plots ... the group should contain only one data series ...
                    series_idx = group[0]

                    # ...retrieve corresponding box values ...
                    box = self.boxes[series_idx][cat_idx]

                    # ... get drawing info ...
                    all_box_lines = box.get_box_lines(box_baseline, box_start, box_end, self.box_vertical)
                    box_polygon, box_median, whisker_bottom, whisker_top = all_box_lines

                    #  ... add drawing info ....
                    boxes_lines.append(box_polygon)
                    medians_lines.append(box_median)
                    bottom_whiskers.append(whisker_bottom)
                    top_whiskers.append(whisker_top)

                    # ... index for quicker mapping between boxes to click positions ....
                    box_polygon_index.append((series_idx, cat_idx))

                    # move to end of the box ... (+ width)
                    box_start += self.box_width
                    # check if move to the next box on same grouping
                    if group_idx + 1 < len(self.box_sorting.order):
                        # + distance between contiguous bars
                        box_start += self.box_inner_dist

                # next group of boxes ...
                box_start += self.box_outer_dist

        else:
            # boxes are grouped by data series
            for group_idx, group in enumerate(self.box_sorting.order):
                for cat_idx, category in enumerate(self.categories):
                    box_end = box_start + self.box_width

                    # No stacking for box plots ... the group should contain only one data series ...
                    series_idx = group[0]

                    # ...retrieve corresponding box values ...
                    box = self.boxes[series_idx][cat_idx]

                    # ... get drawing info ...
                    all_box_lines = box.get_box_lines(box_baseline, box_start, box_end, self.box_vertical)
                    box_polygon, box_median, whisker_bottom, whisker_top = all_box_lines

                    #  ... add drawing info ....
                    boxes_lines.append(box_polygon)
                    medians_lines.append(box_median)
                    bottom_whiskers.append(whisker_bottom)
                    top_whiskers.append(whisker_top)

                    # ... index for quicker mapping between boxes to click positions ....
                    box_polygon_index.append((series_idx, cat_idx))

                    # move to the end of the box
                    box_start += self.box_width
                    # check if move to the next box on same grouping
                    if cat_idx + 1 < len(self.categories):
                        box_start += self.box_inner_dist

                # next group of boxes ...
                box_start += self.box_outer_dist

        boxes_lines = np.array(boxes_lines).round().astype(np.int32)
        medians_lines = np.array(medians_lines).round().astype(np.int32)
        bottom_whiskers = np.array(bottom_whiskers).round().astype(np.int32)
        top_whiskers = np.array(top_whiskers).round().astype(np.int32)

        all_lines = boxes_lines, medians_lines, bottom_whiskers, top_whiskers

        return all_lines, box_polygon_index

    @staticmethod
    def get_box_line_JSON(p1, p2):
        p1_x, p1_y = p1
        p2_x, p2_y = p2

        cx = (p1_x + p2_x) / 2.0
        cy = (p1_y + p2_y) / 2.0

        x0 = min(p1_x, p2_x)
        y0 = min(p1_y, p2_y)

        w = max(p1_x, p2_x) - x0
        h = max(p1_y, p2_y) - y0

        info = {
            "_bb": {
                "height": float(h),
                "width": float(w),
                "x0": float(x0),
                "y0": float(y0)
            },
            "x": float(cx),
            "y": float(cy)
        }

        return info

    @staticmethod
    def get_box_polygons_JSON(all_lines):
        # construct the box visual output
        boxes = []
        all_boxes_l, all_medians_l, all_bottom_w, all_top_w = all_lines
        # for each box ....
        for box_l, median_l, bottom_w, top_w in zip(all_boxes_l, all_medians_l, all_bottom_w, all_top_w):
            wb_box_mid, wb_line_mid, wb_line_start, wb_line_end = bottom_w
            wt_box_mid, wt_line_mid, wt_line_start, wt_line_end = top_w
            b_min_start, b_max_start, b_max_end, b_min_end = box_l
            b_med_start, b_med_end = median_l

            box_info = {
                "min": BoxData.get_box_line_JSON(wb_line_start, wb_line_end),
                "first_quartile": BoxData.get_box_line_JSON(b_min_start, b_min_end),
                "median": BoxData.get_box_line_JSON(b_med_start, b_med_end),
                "third_quartile": BoxData.get_box_line_JSON(b_max_start, b_max_end),
                "max": BoxData.get_box_line_JSON(wt_line_start, wt_line_end),
            }
            boxes.append(box_info)

        return boxes

    def get_data_series_JSON(self, chart_info):
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if self.box_vertical:
            # assume they start at the bottom
            box_baseline = y2
        else:
            # assume they start at the left
            box_baseline = x1

        # now infer data quantities based on polygons ...
        # for each data series ...
        data_series = []
        for series_idx, series_text in enumerate(self.data_series):
            series_data = []
            for cat_idx, category_text in enumerate(self.categories):
                if category_text is None:
                    category_name = "[unnamed category #{0:d}]".format(cat_idx)
                else:
                    category_name = category_text.value

                data_point = {"x": category_name}

                # to get the value of the boxes, we need to get the numerical value of each point of interest....
                # this is scale dependent
                box = self.boxes[series_idx][cat_idx]

                if self.box_vertical:
                    b_min = box_baseline - box.box_min
                    b_med = box_baseline - box.box_median
                    b_max = box_baseline - box.box_max
                    w_min = box_baseline - box.whiskers_min
                    w_max = box_baseline - box.whiskers_max

                    if chart_info.axes.y1_axis is not None:
                        # most common case, project against y axis on left side ...
                        proj_w_min = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, w_min)
                        proj_b_min = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, b_min)
                        proj_b_med = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, b_med)
                        proj_b_max = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, b_max)
                        proj_w_max = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, w_max)

                        data_point["min"] = proj_w_min
                        data_point["first_quartile"] = proj_b_min
                        data_point["median"] = proj_b_med
                        data_point["third_quartile"] = proj_b_max
                        data_point["max"] = proj_w_max

                    if chart_info.axes.y2_axis is not None:
                        # less common case, project against y axis on right side ...
                        proj_w_min = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, w_min)
                        proj_b_min = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, b_min)
                        proj_b_med = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, b_med)
                        proj_b_max = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, b_max)
                        proj_w_max = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, w_max)

                        data_point["y2-min"] = proj_w_min
                        data_point["y2-first_quartile"] = proj_b_min
                        data_point["y2-median"] = proj_b_med
                        data_point["y2-third_quartile"] = proj_b_max
                        data_point["y2-max"] = proj_w_max

                    if chart_info.axes.y1_axis is None and chart_info.axes.y2_axis is None:
                        raise Exception("No Dependent Axis found")
                else:
                    b_min = box_baseline + box.box_min
                    b_med = box_baseline + box.box_median
                    b_max = box_baseline + box.box_max
                    w_min = box_baseline + box.whiskers_min
                    w_max = box_baseline + box.whiskers_max

                    if chart_info.axes.x1_axis is not None:
                        # most common case, project against x axis on bottom  ...
                        proj_w_min = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, True, w_min)
                        proj_b_min = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, True, b_min)
                        proj_b_med = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, True, b_med)
                        proj_b_max = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, True, b_max)
                        proj_w_max = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, True, w_max)

                        data_point["min"] = proj_w_min
                        data_point["first_quartile"] = proj_b_min
                        data_point["median"] = proj_b_med
                        data_point["third_quartile"] = proj_b_max
                        data_point["max"] = proj_w_max

                    if chart_info.axes.x2_axis is not None:
                        # less common case, project against x axis on top  ...
                        proj_w_min = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, True, w_min)
                        proj_b_min = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, True, b_min)
                        proj_b_med = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, True, b_med)
                        proj_b_max = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, True, b_max)
                        proj_w_max = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, True, w_max)

                        data_point["y2-min"] = proj_w_min
                        data_point["y2-first_quartile"] = proj_b_min
                        data_point["y2-median"] = proj_b_med
                        data_point["y2-third_quartile"] = proj_b_max
                        data_point["y2-max"] = proj_w_max

                    if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is None:
                        raise Exception("No Dependent Axis found")

                # print((data_point))
                series_data.append(data_point)

            if series_text is None:
                series_name = "[unnamed data series #{0:d}]".format(series_idx)
            else:
                series_name = series_text.value

            data_series_info = {
                "name": series_name,
                "data": series_data,
            }
            # print((series_idx, series_text))
            data_series.append(data_series_info)

        return data_series

    def parse_data(self, chart_info):
        all_lines, box_polygon_index = self.compute_box_polygons(chart_info)

        # task 6.a
        boxes = BoxData.get_box_polygons_JSON(all_lines)
        # task 6.b
        data_series = self.get_data_series_JSON(chart_info)

        # print(data_series)
        return boxes, data_series

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="BoxData">\n'

        # data series ...
        xml_str += indent + "   <DataSeries>\n"
        for series in self.data_series:
            if series is None:
                xml_str += indent + "       <TextId></TextId>\n"
            else:
                xml_str += indent + "       <TextId>{0:d}</TextId>\n".format(series.id)
        xml_str += indent + "   </DataSeries>\n"

        # categories ...
        xml_str += indent + "   <Categories>\n"
        for category in self.categories:
            if category is None:
                xml_str += indent + "       <TextId></TextId>\n"
            else:
                xml_str += indent + "       <TextId>{0:d}</TextId>\n".format(category.id)
        xml_str += indent + "   </Categories>\n"

        grouping_desc = self.get_grouping_desc()
        xml_str += indent + "   <Grouping>{0:s}</Grouping>\n".format(grouping_desc)

        xml_str += self.box_sorting.to_XML(indent + "   ")

        xml_str += indent + "   <Vertical>{0:s}</Vertical>\n".format("1" if self.box_vertical else "0")

        xml_str += indent + "   <BoxOffset>{0:s}</BoxOffset>\n".format(str(self.box_offset))
        xml_str += indent + "   <BoxWidth>{0:s}</BoxWidth>\n".format(str(self.box_width))
        xml_str += indent + "   <BoxInnerDist>{0:s}</BoxInnerDist>\n".format(str(self.box_inner_dist))
        xml_str += indent + "   <BoxOuterDist>{0:s}</BoxOuterDist>\n".format(str(self.box_outer_dist))

        xml_str += indent + "   <BoxValues>\n"
        for s_idx in range(len(self.data_series)):
            xml_str += indent + '       <Series index="{0:d}">\n'.format(s_idx)
            for cat_idx in range(len(self.categories)):
                xml_str += self.boxes[s_idx][cat_idx].to_XML(indent + "           ")
            xml_str += indent + "       </Series>\n"
        xml_str += indent + "   </BoxValues>\n"

        xml_str += indent + '</Data>\n'

        return xml_str

    @staticmethod
    def GroupingFromDesc(desc_string):
        desc_string = desc_string.strip().lower()

        if desc_string == "by-category":
            return BoxData.GroupingByCategory
        elif desc_string == "by-data-series":
            return BoxData.GroupingByDataSeries
        else:
            raise Exception("Unexpected Bar Data Grouping Description found!")

    @staticmethod
    def FromXML(xml_root, text_index):
        # assume xml_root is BoxData
        data_series = []
        for xml_text_id in xml_root.find("DataSeries").findall("TextId"):
            text_id = xml_text_id.text
            if text_id is None or text_id.strip() == "":
                # an empty data series
                data_series.append(None)
            else:
                data_series.append(text_index[int(text_id)])

        categories = []
        for xml_text_id in xml_root.find("Categories").findall("TextId"):
            text_id = xml_text_id.text
            if text_id is None or text_id.strip() == "":
                # an empty data series
                categories.append(None)
            else:
                categories.append(text_index[int(text_id)])

        vertical = xml_root.find("Vertical").text == "1"
        grouping = BoxData.GroupingFromDesc(xml_root.find("Grouping").text)

        offset = float(xml_root.find("BoxOffset").text)
        width = float(xml_root.find("BoxWidth").text)
        inner_dist = float(xml_root.find("BoxInnerDist").text)
        outer_dist = float(xml_root.find("BoxOuterDist").text)

        data = BoxData(data_series, categories, vertical, grouping, offset, width, inner_dist, outer_dist)
        data.box_sorting = SeriesSorting.FromXML(xml_root.find("SeriesSorting"))

        xml_all_box_values = xml_root.find("BoxValues")
        for s_idx, xml_series in enumerate(xml_all_box_values):
            for cat_idx, xml_box_values in enumerate(xml_series):
                data.boxes[s_idx][cat_idx] = BoxValues.FromXML(xml_box_values)

        return data

    @staticmethod
    def CreateDefault(chart_info):
        # get chart bounding box ...
        a_x1, a_y1, a_x2, a_y2 = chart_info.axes.bounding_box
        a_x1 = int(a_x1)
        a_y1 = int(a_y1)
        a_x2 = int(a_x2)
        a_y2 = int(a_y2)

        # first, determine data series ...
        data_series = chart_info.get_data_series_candidates()

        if chart_info.is_vertical():
            # vertical boxes... X axis has the data series ...
            vertical = True
            categories = chart_info.axes.get_axis_labels(AxesInfo.AxisX1)

            axis_range = a_y2 - a_y1
        else:
            # horizontal boxes ... Y axis has the data series ...
            vertical = False
            categories = chart_info.axes.get_axis_labels(AxesInfo.AxisY1)

            axis_range = a_x2 - a_x1

        # most common grouping ...
        grouping = BoxData.GroupingByCategory

        if len(categories) == 0:
            # create an empty category by default
            categories = [None]

        category_width = axis_range / len(categories)
        box_width = round(category_width / (len(data_series) + 1), 1)
        box_offset = round(box_width / 2, 1)
        box_inner_dist = 0.0
        box_outer_dist = box_width

        default_whiskers_min = int(axis_range * (1 / 6))
        default_box_min = int(axis_range * (2 / 6))
        default_box_median = int(axis_range * (3 / 6))
        default_box_max = int(axis_range * (4 / 6))
        default_whiskers_max = int(axis_range * (5 / 6))

        data = BoxData(data_series, categories, vertical, grouping, box_offset, box_width,
                       box_inner_dist, box_outer_dist, default_box_min, default_box_median, default_box_max,
                       default_whiskers_min, default_whiskers_max)

        return data
