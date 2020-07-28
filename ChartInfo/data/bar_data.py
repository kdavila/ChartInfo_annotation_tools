
import numpy as np
from shapely.geometry import Polygon
from munkres import Munkres

from .series_sorting import SeriesSorting
from .axes_info import AxesInfo
from .axis_values import AxisValues
from .text_info import TextInfo

class BarData:
    DataVersion = 1.0

    GroupingByCategory = 0
    GroupingByDataSeries = 1

    def __init__(self, data_series, categories, vertical, grouping, bar_offset=0.0, bar_width=1.0, bar_inner_dist=0.0,
                 bar_outer_dist=1.0, default_length=0):
        # Arrays of text_info sorted by location (left to right or top to down)
        # these might contain None values...
        self.data_series = data_series
        self.categories = categories

        # Group by Category or By Data Series
        self.bar_grouping = grouping

        # a list of list representing the organization (of bars) ...
        # for both ordering and stacking ...
        self.bar_sorting = SeriesSorting(len(self.data_series))

        # bar generation patterns
        self.bar_vertical = vertical
        self.bar_offset = bar_offset
        self.bar_width = bar_width
        self.bar_inner_dist = bar_inner_dist
        self.bar_outer_dist = bar_outer_dist

        # actual lengths (in pixels) from the axis line...
        # note these values might be negative in some cases
        self.bar_lengths = [[default_length for cat_idx in range(len(self.categories))]
                            for s_idx in range(len(self.data_series))]

    def total_bars(self):
        return len(self.data_series) * len(self.categories)

    def total_layers(self):
        return self.bar_sorting.stacking_layers()

    def get_lengths(self):
        return [list(lengths) for lengths in self.bar_lengths]

    def get_layer_elements(self, layer_idx):
        return [self.data_series[series_idx] for series_idx in self.bar_sorting.get_layer_elements(layer_idx)]

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from bar lengths ...
            del self.bar_lengths[index]

            # remove from data series ...
            del self.data_series[index]

            # remove from sorting ...
            self.bar_sorting.remove_series(index)

            return True
        else:
            return False

    def remove_category(self, index):
        if 0 <= index <= len(self.categories):
            # remove from lengths ...
            for series_idx in range(len(self.data_series)):
                del self.bar_lengths[series_idx][index]

            # remove from categories ...
            del self.categories[index]

            return True
        else:
            return False

    def add_data_series(self, text_label=None, default_length=0):
        # add to data series ...
        self.data_series.append(text_label)
        # add to bar lengths ....
        self.bar_lengths.append([default_length for cat_idx in range(len(self.categories))])

        self.bar_sorting.add_series()

    def add_category(self, text_label=None, default_length=0):
        # add to categories ...
        self.categories.append(text_label)

        # add lengths ...
        for series_idx in range(len(self.data_series)):
            self.bar_lengths[series_idx].append(default_length)

    def mean_length(self):
        return np.mean(self.bar_lengths)

    @staticmethod
    def get_bar_lines(bar_vertical, bar_baseline, bar_start, bar_end, bar_length):
        if bar_vertical:
            bar_max = bar_baseline - bar_length

            left_axis = (bar_start, bar_baseline)
            left_top = (bar_start, bar_max)
            right_top = (bar_end, bar_max)
            right_axis = (bar_end, bar_baseline)

            return (left_axis, left_top, right_top, right_axis), bar_max
        else:
            bar_max = bar_baseline + bar_length

            top_axis = (bar_baseline, bar_start)
            top_right = (bar_max, bar_start)
            bottom_right = (bar_max, bar_end)
            bottom_axis = (bar_baseline, bar_end)

            return (top_axis, top_right, bottom_right, bottom_axis), bar_max

    @staticmethod
    def get_stacked_bar_lines(bar_vertical, cat_idx, group, bar_lengths, bar_baseline, bar_start, bar_end):
        polygons = []
        polygon_index = []
        current_baseline = bar_baseline
        for stack_idx, series_idx in enumerate(group):
            # ...retrieve corresponding bar length ...
            bar_length = bar_lengths[series_idx][cat_idx]

            bar_lines, bar_max = BarData.get_bar_lines(bar_vertical, current_baseline, bar_start, bar_end, bar_length)

            polygons.append(bar_lines)
            polygon_index.append((series_idx, cat_idx, stack_idx, current_baseline))

            current_baseline = bar_max

        return polygons, polygon_index

    def computer_bar_polygons(self, chart_info):
        # note that this function overlaps on functionality the one used by the corresponding bar chart annotator
        # but this one does not consider temporary data structures or special highlighting, just the actual positions
        # of the bars

        # this depends on the parent ....
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if self.bar_vertical:
            # assume left to right
            bar_start = x1 + self.bar_offset
            # assume they start at the bottom
            bar_baseline = y2
        else:
            # assume top to bottom
            bar_start = y1 + self.bar_offset
            # assume they start at the left
            bar_baseline = x1

        current_lines = []
        bar_polygon_index = []

        if self.bar_grouping == BarData.GroupingByCategory:
            # bar are grouped by categorical value ...
            for cat_idx, category in enumerate(self.categories):
                for group_idx, group in enumerate(self.bar_sorting.order):
                    bar_end = bar_start + self.bar_width

                    # add stacked bars ...
                    polygons, polygon_index = BarData.get_stacked_bar_lines(self.bar_vertical, cat_idx, group,
                                                                            self.bar_lengths, bar_baseline, bar_start,
                                                                            bar_end)

                    current_lines += polygons
                    bar_polygon_index += polygon_index

                    # move to end of the bar ... (+ width)
                    bar_start += self.bar_width
                    # check if move to the next stack of bars on same grouping
                    if group_idx + 1 < len(self.bar_sorting.order):
                        # + distance between contiguous bars
                        bar_start += self.bar_inner_dist

                # next group of bars ...
                bar_start += self.bar_outer_dist
        else:
            # bar are grouped by data series
            for group_idx, group in enumerate(self.bar_sorting.order):
                for cat_idx, category in enumerate(self.categories):
                    bar_end = bar_start + self.bar_width

                    # draw stacked bars ...
                    polygons, polygon_index = BarData.get_stacked_bar_lines(self.bar_vertical, cat_idx, group,
                                                                            self.bar_lengths, bar_baseline, bar_start,
                                                                            bar_end)

                    # for click processing ...
                    current_lines += polygons
                    bar_polygon_index += polygon_index

                    # move to the end of the bar
                    bar_start += self.bar_width
                    # check if move to the next stack of bars on same grouping
                    if cat_idx + 1 < len(self.categories):
                        bar_start += self.bar_inner_dist

                # next group of bars ...
                bar_start += self.bar_outer_dist

        current_lines = np.array(current_lines).round().astype(np.int32)
        bar_polygons = current_lines

        return bar_polygons, bar_polygon_index

    def assign_value_labels_to_bars(self, bar_polygons, value_labels):
        # use the hungarian method ... but first compute all pairwise distances
        cost_matrix = np.zeros((len(bar_polygons), len(bar_polygons)))
        # ... fill the cost matrix ...
        for bar_idx, bar_polygon in enumerate(bar_polygons):
            bar_as_poly = Polygon(bar_polygon)
            for lbl_idx, val_label in enumerate(value_labels):
                lbl_as_poly = Polygon(val_label.position_polygon)
                cost_matrix[bar_idx, lbl_idx] = bar_as_poly.distance(lbl_as_poly)

        m = Munkres()
        assignments = m.compute(cost_matrix)

        bar_idx_to_value_label = {}
        for bar_idx, lbl_idx in assignments:
            try:
                bar_idx_to_value_label[bar_idx] = AxisValues.LabelNumericValue(value_labels[lbl_idx].value)
            except:
                # found a value label that cannot be interpreted ...
                # this will allow to fall back to projection-based bar value inference
                return None

        return bar_idx_to_value_label

    def get_data_series_JSON(self, chart_info, bar_polygons, bar_polygon_index):
        bar_baselines = {}
        for bar_idx, (series_idx, cat_idx, stack_idx, baseline) in enumerate(bar_polygon_index):
            if not series_idx in bar_baselines:
                bar_baselines[series_idx] = {}

            bar_baselines[series_idx][cat_idx] = baseline, bar_idx

        # check if stacked bar chart ....
        is_stacked = self.total_layers() > 1

        # check if bars have value labels ...
        all_value_labels = chart_info.get_all_text(TextInfo.TypeValueLabel)
        if len(all_value_labels) == len(bar_polygon_index):
            # there is one value label for each bar in the image... find the best assignments
            bar_idx_to_value_label = self.assign_value_labels_to_bars(bar_polygons, all_value_labels)
        else:
            # no value label assignments
            bar_idx_to_value_label = None

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

                baseline, bar_idx = bar_baselines[series_idx][cat_idx]

                if bar_idx_to_value_label is not None:
                    # use existing value label values ...
                    data_point["y"] = bar_idx_to_value_label[bar_idx]
                else:
                    # to get the value of the bar, we need to get the numerical value of the base of the bar
                    # and subtract it from the value of the top of the bar.... this is scale dependent
                    bar_length = self.bar_lengths[series_idx][cat_idx]
                    if self.bar_vertical:
                        bar_max = baseline - bar_length

                        # project min and max bar heights
                        if chart_info.axes.y1_axis is not None:
                            # most common case, project against y axis on left side ...
                            proj_height = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, bar_max)
                            data_point["y"] = proj_height
                            if is_stacked:
                                proj_base = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, baseline)
                                data_point["y"] -= proj_base

                        if chart_info.axes.y2_axis is not None:
                            # less common case, project against y axes on right side ...
                            proj_height = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, bar_max)
                            data_point["y2"] = proj_height
                            if is_stacked:
                                proj_base = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, baseline)
                                data_point["y2"] -= proj_base

                        # print(((baseline), (bar_max, proj_height)))

                        if chart_info.axes.y1_axis is None and chart_info.axes.y2_axis is None:
                            raise Exception("No Dependent Axis found")

                    else:
                        bar_max = baseline + bar_length

                        # project min and max bar heights
                        if chart_info.axes.x1_axis is not None:
                            # most common case, project against y axis on left side ...
                            proj_height = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, False, bar_max)
                            data_point["y"] = proj_height
                            if is_stacked:
                                proj_base = AxisValues.Project(chart_info.axes, chart_info.axes.x1_axis, False,
                                                               baseline)
                                data_point["y"] -= proj_base

                        if chart_info.axes.x2_axis is not None:
                            # less common case, project against y axes on right side ...
                            proj_height = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, False, bar_max)
                            data_point["y2"] = proj_height
                            if is_stacked:
                                proj_base = AxisValues.Project(chart_info.axes, chart_info.axes.x2_axis, False,
                                                               baseline)
                                data_point["y2"] -= proj_base

                        if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is None:
                            raise Exception("No Dependent Axis found")

                # TODO: can I project against categorical axes?
                # TODO: what happens if there is no dependent axes? (and no labels)
                # TODO:    ----- should I fall back to use percentage of bounding box ???
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

    @staticmethod
    def get_bar_polygons_JSON(bar_polygons):
        # finally convert the polygon data to JSON
        bars = []
        for bar_polygon in bar_polygons:
            x0 = bar_polygon[:, 0].min()
            x1 = bar_polygon[:, 0].max()
            y0 = bar_polygon[:, 1].min()
            y1 = bar_polygon[:, 1].max()

            bar_info = {
                "x0": int(round(x0)),
                "y0": int(round(y0)),
                "width": int(round(x1 - x0)),
                "height": int(round(y1 - y0)),
            }
            # print((bar_info, bar_polygon))
            bars.append(bar_info)

        return bars

    def parse_data(self, chart_info):
        # re-construct the bars from annotations ...
        bar_polygons, bar_polygon_index = self.computer_bar_polygons(chart_info)

        # Task 6.a
        bars = BarData.get_bar_polygons_JSON(bar_polygons)
        # Task 6.b
        data_series = self.get_data_series_JSON(chart_info, bar_polygons, bar_polygon_index)

        return bars, data_series

    @staticmethod
    def Copy(other):
        assert isinstance(other, BarData)

        copy_series = list(other.data_series)
        copy_categories = list(other.categories)

        data = BarData(copy_series, copy_categories, other.bar_vertical, other.bar_grouping,
                       other.bar_offset, other.bar_width, other.bar_inner_dist, other.bar_outer_dist)

        data.bar_sorting = SeriesSorting.Copy(other.bar_sorting)

        for series_idx in range(len(other.bar_lengths)):
            data.bar_lengths[series_idx] = list(other.bar_lengths[series_idx])

        return data

    def get_grouping_desc(self):
        if self.bar_grouping == BarData.GroupingByCategory:
            return "by-category"
        elif self.bar_grouping == BarData.GroupingByDataSeries:
            return "by-data-series"
        else:
            raise Exception("Unexpected Bar Data Grouping found")

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="BarData">\n'

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

        xml_str += self.bar_sorting.to_XML(indent + "   ")

        xml_str += indent + "   <Vertical>{0:s}</Vertical>\n".format("1" if self.bar_vertical else "0")

        xml_str += indent + "   <BarOffset>{0:s}</BarOffset>\n".format(str(self.bar_offset))
        xml_str += indent + "   <BarWidth>{0:s}</BarWidth>\n".format(str(self.bar_width))
        xml_str += indent + "   <BarInnerDist>{0:s}</BarInnerDist>\n".format(str(self.bar_inner_dist))
        xml_str += indent + "   <BarOuterDist>{0:s}</BarOuterDist>\n".format(str(self.bar_outer_dist))

        xml_str += indent + "   <BarLengths>\n"
        xml_value = indent + '           <Length category="{0:d}">{1:s}</Length>\n'
        for s_idx in range(len(self.data_series)):
            xml_str += indent + '       <Series index="{0:d}">\n'.format(s_idx)
            for cat_idx in range(len(self.categories)):
                xml_str += xml_value.format(cat_idx, str(self.bar_lengths[s_idx][cat_idx]))
            xml_str += indent + "       </Series>\n"
        xml_str += indent + "   </BarLengths>\n"

        xml_str += indent + '</Data>\n'

        return xml_str

    @staticmethod
    def GroupingFromDesc(desc_string):
        desc_string = desc_string.strip().lower()

        if desc_string == "by-category":
            return BarData.GroupingByCategory
        elif desc_string == "by-data-series":
            return BarData.GroupingByDataSeries
        else:
            raise Exception("Unexpected Bar Data Grouping Description found!")

    @staticmethod
    def FromXML(xml_root, text_index):
        # assume xml_root is BarData
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
        grouping = BarData.GroupingFromDesc(xml_root.find("Grouping").text)

        offset = float(xml_root.find("BarOffset").text)
        width = float(xml_root.find("BarWidth").text)
        inner_dist = float(xml_root.find("BarInnerDist").text)
        outer_dist = float(xml_root.find("BarOuterDist").text)

        data = BarData(data_series, categories, vertical, grouping, offset, width, inner_dist, outer_dist)
        data.bar_sorting = SeriesSorting.FromXML(xml_root.find("SeriesSorting"))

        xml_all_lengths = xml_root.find("BarLengths")
        for s_idx, xml_series in enumerate(xml_all_lengths):
            for cat_idx, xml_length in enumerate(xml_series):
                data.bar_lengths[s_idx][cat_idx] = float(xml_length.text)

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

        # then, determine the categories and orientation based defaults ...
        if chart_info.is_vertical():
            # vertical bars ... X axis has the categories ...
            vertical = True
            categories = chart_info.axes.get_axis_labels(AxesInfo.AxisX1)

            default_length = int((a_y2 - a_y1) * 0.5)
            axis_length = a_x2 - a_x1
        else:
            # horizontal bars ... Y axis has the categories ...
            vertical = False
            categories = chart_info.axes.get_axis_labels(AxesInfo.AxisY1)

            default_length = int((a_x2 - a_x1) * 0.5)
            axis_length = a_y2 - a_y1

        if len(categories) == 0:
            # create an empty category by default
            categories = [None]

        category_width = axis_length / len(categories)
        bar_width = int(category_width / (len(data_series) + 1))
        bar_offset = int(bar_width / 2)
        bar_outer_dist = bar_width

        # most common grouping ...
        grouping = BarData.GroupingByCategory

        data = BarData(data_series, categories, vertical,  grouping, bar_offset=bar_offset, bar_width=bar_width,
                       bar_outer_dist=bar_outer_dist, default_length=default_length)

        return data
