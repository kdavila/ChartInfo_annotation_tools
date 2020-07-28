
from .line_values import LineValues
from .axis_values import AxisValues

class LineData:
    DataVersion = 1.0

    Parsing_TickInRangeThreshold = 5

    def __init__(self, data_series):
        self.data_series = data_series

        # Note: all coordinate values are relative to the axes origin 
        self.lines = [LineValues() for series in self.data_series]

    def total_lines(self):
        return len(self.lines)

    def add_data_series(self, text_label=None, default_points=None):
        # add to data series ...
        self.data_series.append(text_label)

        # prepare line
        new_line = LineValues()
        if default_points is not None:
            new_line.points = default_points

        # add to lines ....
        self.lines.append(new_line)

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from lines ...
            del self.lines[index]

            # remove from data series ...
            del self.data_series[index]

            return True
        else:
            return False

    def parse_data(self, chart_info):
        # now infer data quantities based on line data ...
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if chart_info.axes.x1_axis is not None and chart_info.axes.x2_axis is not None:
            raise Exception("There are two Horizontal Axes, cannot determine the independent variable")

        if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is None:
            raise Exception("There is no Horizontal Axis!")

        if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is not None:
            # use upper axis as independent variable axis (very rare)
            x_axis = chart_info.axes.x2_axis
        else:
            # use lower axis as independent variable axis (common)
            x_axis = chart_info.axes.x1_axis

        if ((x_axis.values_type == AxisValues.ValueTypeNumerical and x_axis.scale_type == AxisValues.ScaleNone) or
            (x_axis.values_type == AxisValues.ValueTypeCategorical)):
            # only sample at known points (label values on the axis)
            axis_ticks = x_axis.ticks_with_labels()

            var_x_pixel_points = []
            var_x_chart_values = []
            for tick_info in axis_ticks:
                tick_label = chart_info.axes.tick_labels[tick_info.label_id]

                if x_axis.ticks_type == AxisValues.TicksTypeMarkers:
                    # for marker ticks .. use position as annotated ..
                    var_x_pixel_points.append(tick_info.position)
                else:
                    # for separator ticks ... use center of label ...
                    pos_x, pos_y = tick_label.get_center()
                    var_x_pixel_points.append(pos_x)

                var_x_chart_values.append(tick_label.value)
        else:
            # sample based on line data ....
            var_x_pixel_points = None
            var_x_chart_values = None

        # for each data series ...
        data_series = []
        all_line_points = []
        for series_idx, series_text in enumerate(self.data_series):
            # data series = list of lists of (X, Y) coordinates in logical coordinates (chart-space)
            # all_line_points = List of lists of (X, Y) coordinates in image coordinates (pixel-space)
            line_values = self.lines[series_idx]

            # sample X coordinates ... then find corresponding Y coordinates
            # for now, we assume that X-1 (or X-2) represent the independent variables
            # TODO: future versions should include a label for dependent/independent variable (similar to orientation)

            current_data_series = []
            current_line_points = []

            if var_x_chart_values is None:
                # Line-based sampling of x coordinates is required
                # A numerical X axis with a valid scale is expected
                # will be using the coordinates provided by the user ...
                all_rel_x_values = line_values.get_all_x_values()
                line_x_pixel_points = [x_val + x1 for x_val in all_rel_x_values]

                line_x_chart_values = []
                for x_val in line_x_pixel_points:
                    proj_x_val = AxisValues.Project(chart_info.axes, x_axis, False, x_val)
                    line_x_chart_values.append(proj_x_val)
            else:
                # use the common x values sampled for all lines ...
                line_x_pixel_points = var_x_pixel_points
                line_x_chart_values = var_x_chart_values

            # get line container box in coordinates relative to the data region
            lr_min_x, lr_min_y, lr_max_x, lr_max_y = line_values.get_line_relative_bbox()

            for x_val_idx in range(len(line_x_chart_values)):
                if var_x_chart_values is not None:
                    # we need to differentiate and avoid sampling lines at unknown points needing extrapolation
                    # if they are too far away from the range of known points
                    if ((line_x_pixel_points[x_val_idx] < x1 + lr_min_x - LineData.Parsing_TickInRangeThreshold) or
                        (x1 + lr_max_x + LineData.Parsing_TickInRangeThreshold < line_x_pixel_points[x_val_idx])):
                        # point is out of range for interpolation, and too far to extrapolate with confidence ...
                        # skip!!!
                        continue

                # get point in relative coordinate space (with respect to the data region)
                rel_x_value = line_x_pixel_points[x_val_idx] - x1
                rel_y_value = line_values.get_y_value(rel_x_value)

                line_y_pixel = y2 - rel_y_value

                line_data_point = {
                    "x": line_x_pixel_points[x_val_idx],
                    "y": line_y_pixel,
                }
                current_line_points.append(line_data_point)

                data_series_point = {
                    "x": line_x_chart_values[x_val_idx],
                }

                # get Y value on chart space ...
                # Y-1 axis (Common)
                if chart_info.axes.y1_axis is not None:
                    proj_y_val = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, line_y_pixel)
                    data_series_point["y"] = proj_y_val
                # Y-2 axis (Rare)
                if chart_info.axes.y2_axis is not None:
                    proj_y_val = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, line_y_pixel)
                    data_series_point["y2"] = proj_y_val

                current_data_series.append(data_series_point)

            data_series.append(current_data_series)
            all_line_points.append(current_line_points)

        # print(data_series)
        # print(all_line_points)

        return all_line_points, data_series

    @staticmethod
    def Copy(other):
        assert isinstance(other, LineData)

        # copy object ....
        data = LineData(list(other.data_series))

        # create copy of the individual lines ...
        for idx, line_values in enumerate(other.lines):
            data.lines[idx] = LineValues.Copy(line_values)

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

        data = LineData(data_series)

        # create default lines with 2 points each, equally spaced ...
        axis_range = a_y2 - a_y1
        axis_domain = a_x2 - a_x1

        for idx, line in enumerate(data.lines):
            line_y = ((idx + 1) / (len(data_series) + 1)) * axis_range
            data.lines[idx].points = [(0, line_y), (axis_domain, line_y)]

        return data

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="LineData">\n'
        # data series ...
        xml_str += indent + "    <DataSeries>\n"
        for series in self.data_series:
            if series is None:
                xml_str += indent + "        <TextId></TextId>\n"
            else:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(series.id)
        xml_str += indent + "    </DataSeries>\n"

        # data values ...
        xml_str += indent + "    <LinesValues>\n"
        for line_values in self.lines:
            xml_str += line_values.to_XML(indent + "        ")
        xml_str += indent + "    </LinesValues>\n"
        xml_str += indent + '</Data>\n'

        return xml_str

    @staticmethod
    def FromXML(xml_root, text_index):
        # assume xml_root is Data
        data_series = []
        for xml_text_id in xml_root.find("DataSeries").findall("TextId"):
            text_id = xml_text_id.text
            if text_id is None or text_id.strip() == "":
                # an empty data series
                data_series.append(None)
            else:
                data_series.append(text_index[int(text_id)])

        data = LineData(data_series)
        for idx, xml_line_values in enumerate(xml_root.find("LinesValues").findall("LineValues")):
            data.lines[idx] = LineValues.FromXML(xml_line_values)

        return data

