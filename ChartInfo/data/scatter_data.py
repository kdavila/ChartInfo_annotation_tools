
from .scatter_values import ScatterValues

class ScatterData:
    DataVersion = 1.0

    def __init__(self, data_series):
        self.data_series = data_series

        # Note: all coordinate values are relative to the axes origin
        self.scatter_values = [ScatterValues() for series in self.data_series]

    def total_series(self):
        return len(self.scatter_values)

    def add_data_series(self, text_label=None, default_points=None):
        # add to data series ...
        self.data_series.append(text_label)

        # prepare scattered values
        new_values = ScatterValues()
        if default_points is not None:
            new_values.points = default_points

        # add to sets of values ....
        self.scatter_values.append(new_values)

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from set of scattered values ...
            del self.scatter_values[index]

            # remove from data series ...
            del self.data_series[index]

            return True
        else:
            return False

    @staticmethod
    def Copy(other):
        assert isinstance(other, ScatterData)

        # copy object ....
        data = ScatterData(list(other.data_series))

        # create copy of the individual lines ...
        for idx, scatter_values in enumerate(other.scatter_values):
            data.scatter_values[idx] = ScatterValues.Copy(scatter_values)

        return data

    @staticmethod
    def CreateDefault(chart_info):
        # first, determine data series ...
        data_series = chart_info.get_data_series_candidates()

        data = ScatterData(data_series)

        # There is no such thing as a good default set of points for scatter plots ....
        # ... only if these were taken from image analysis ...

        return data

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="ScatterData">\n'
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
        for scatter_values in self.scatter_values:
            xml_str += scatter_values.to_XML(indent + "        ")
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

        data = ScatterData(data_series)
        for idx, xml_scatter_values in enumerate(xml_root.find("ChartValues").findall("ScatterValues")):
            data.scatter_values[idx] = ScatterValues.FromXML(xml_scatter_values)

        return data

