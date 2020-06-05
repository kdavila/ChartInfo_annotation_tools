
from .line_values import LineValues

class LineData:
    DataVersion = 1.0

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

