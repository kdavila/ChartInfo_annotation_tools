
from .series_sorting import SeriesSorting
from .axes_info import AxesInfo
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
