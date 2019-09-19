
import numpy as np

from .series_sorting import SeriesSorting
from .axes_info import AxesInfo

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
            if text_id.strip() == "":
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
        if chart_info.legend is None:
            # assume a single data series
            data_series = [None]
        else:
            legend_data_series = chart_info.legend.get_data_series()
            if len(legend_data_series) == 0:
                # assume a single data series
                data_series = [None]
            else:
                data_series = legend_data_series

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

        category_width = axis_length / len(categories)
        bar_width = int(category_width / (len(data_series) + 1))
        bar_offset = int(bar_width / 2)
        bar_outer_dist = bar_width

        # most common grouping ...
        grouping = BarData.GroupingByCategory

        data = BarData(data_series, categories, vertical,  grouping, bar_offset=bar_offset, bar_width=bar_width,
                       bar_outer_dist=bar_outer_dist, default_length=default_length)

        return data
