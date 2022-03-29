
from .dot_values import DotValues
from .axis_values import AxisValues

class DotData:
    DataVersion = 1.0

    def __init__(self, data_series):
        self.data_series = data_series

        # Note: all coordinate values are relative to the axes origin
        self.dot_values = [DotValues() for series in self.data_series]

    def total_series(self):
        return len(self.dot_values)

    def add_data_series(self, text_label=None, default_points=None):
        # add to data series ...
        self.data_series.append(text_label)

        # prepare doted values
        new_values = DotValues()
        if default_points is not None:
            new_values.points = default_points

        # add to sets of values ....
        self.dot_values.append(new_values)

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from set of doted values ...
            del self.dot_values[index]

            # remove from data series ...
            del self.data_series[index]

            return True
        else:
            return False

    def parse_data(self, chart_info):
        print('-----------------')
        print('PARSE_DATA IS GETTING CALLED HERE')
        print('-----------------')        
        # now infer data quantities based on dot data ...
        # this is very similar to line charts ....
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # <Start: Identical to Line Charts .. Refactor???>
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

        """
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
        """
        # <End: Identical to Line Charts .... Refactor??>

        # for each data series ...
        data_series = []
        all_dot_points = []
        for series_idx, series_text in enumerate(self.data_series):
            # data series = list of lists of (X, Y) coordinates in logical coordinates (chart-space)
            # all_dot_points = List of lists of (X, Y) coordinates in image coordinates (pixel-space)
            dot = self.dot_values[series_idx]

            current_data_series = []
            current_dot_points = []

            # For each point in the dot
            for p_idx, (p_x, p_y) in enumerate(dot.points):
                # first convert the X coordinate to a value ...
                # assume (p_x, p_y) are coordinates relative to the data series)
                # convert to pixel space
                line_x_pixel = p_x + x1
                line_y_pixel = y2 - p_y

                line_data_point = {
                    "x": line_x_pixel,
                    "y": line_y_pixel,
                }
                current_dot_points.append(line_data_point)

                if x_axis.values_type == AxisValues.ValueTypeNumerical:
                    proj_x_val = AxisValues.Project(chart_info.axes, x_axis, False, line_x_pixel)
                else:
                    # categorical x axis ... find closest category
                    proj_x_val = AxisValues.FindClosestValue(chart_info.axes, x_axis, False, line_x_pixel)

                data_series_point = {
                    "x": proj_x_val,
                }
                # get Y value on chart space ...
                # Y-1 axis (Common)
                if chart_info.axes.y1_axis is not None:
                    if chart_info.axes.y1_axis.values_type == AxisValues.ValueTypeNumerical:
                        proj_y_val = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, line_y_pixel)
                    else:
                        # categorical x axis ... find closest category
                        proj_y_val = AxisValues.FindClosestValue(chart_info.axes, chart_info.axes.y1_axis, True, line_y_pixel)
                    print('projected y val:',proj_y_val) 
                    data_series_point["y"] = proj_y_val
                # Y-2 axis (Rare)
                # if chart_info.axes.y2_axis is not None:
                #     proj_y_val = AxisValues.Project(chart_info.axes, chart_info.axes.y2_axis, True, line_y_pixel)
                #     data_series_point["y2"] = proj_y_val
                else: 
                    print("Transfer to .json not yet implemented for single-axis dot graphs.")

                current_data_series.append(data_series_point)

            if series_text is None:
                series_name = "[unnamed data series #{0:d}]".format(series_idx)
            else:
                series_name = series_text.value

            final_data_series = {
                "data": current_data_series,
                "name": series_name,
            }

            data_series.append(final_data_series)
            all_dot_points.append(current_dot_points)

        return all_dot_points, data_series

    @staticmethod
    def Copy(other):
        assert isinstance(other, DotData)

        # copy object ....
        data = DotData(list(other.data_series))

        # create copy of the individual lines ...
        for idx, dot_values in enumerate(other.dot_values):
            data.dot_values[idx] = DotValues.Copy(dot_values)

        return data

    @staticmethod
    def CreateDefault(chart_info):
        # first, determine data series ...
        data_series = chart_info.get_data_series_candidates()

        data = DotData(data_series)

        # There is no such thing as a good default set of points for dot plots ....
        # ... only if these were taken from image analysis ...

        return data

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="DotData">\n'
        # data series ...
        xml_str += indent + "    <DataSeries>\n"
        for series in self.data_series:
            if series is None:
                xml_str += indent + "        <TextId></TextId>\n"
            else:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(series.id)
        xml_str += indent + "    </DataSeries>\n"

        # data values ...
        xml_str += indent + "    <ChartValues>\n"
        for dot_values in self.dot_values:
            xml_str += dot_values.to_XML(indent + "        ")
        xml_str += indent + "    </ChartValues>\n"
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

        data = DotData(data_series)
        for idx, xml_dot_values in enumerate(xml_root.find("ChartValues").findall("DotValues")):
            data.dot_values[idx] = DotValues.FromXML(xml_dot_values)

        return data

