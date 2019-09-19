
import time

from .text_info import TextInfo
from .legend_info import LegendInfo
from .axes_info import AxesInfo

from .bar_data import BarData
from .box_data import BoxData
from .line_data import LineData
from .scatter_data import ScatterData

class ChartInfo:
    TypeNonChart = 0
    TypeLine = 1
    TypeScatter = 2
    TypeBar = 3
    TypeBox = 4

    OrientationVertical = 0
    OrientationHorizontal = 1

    def __init__(self, type, orientation=None):
        self.type = type
        self.orientation = orientation
        self.text = []
        self.axes = None
        self.legend = None
        self.data = None
        self.properties = {}

    def is_vertical(self):
        return self.orientation == ChartInfo.OrientationVertical

    def set_verification(self, verification_name, verification_value):
        if verification_value:
            self.properties[verification_name] = time.time()
        else:
            if verification_name in self.properties:
                del self.properties[verification_name]

    def check_classes(self):
        if self.type != ChartInfo.TypeNonChart:
            return 2 if "VERIFIED_01_CLASS" in self.properties else 1
        else:
            return 0

    def set_classes_verified(self, verified):
        self.set_verification("VERIFIED_01_CLASS", verified)

    def check_text(self):
        if len(self.text) > 0:
            return 2 if "VERIFIED_02_TEXT" in self.properties else 1
        else:
            return 0

    def set_text_verified(self, verified):
        self.set_verification("VERIFIED_02_TEXT", verified)

    def check_legend(self):
        if self.legend is None or not self.legend.is_complete():
            # no legend or it is not completed ...
            return 0
        else:
            # there is legend and is complete
            return 2 if "VERIFIED_03_LEGEND" in self.properties else 1

    def set_legend_verified(self, verified):
        self.set_verification("VERIFIED_03_LEGEND", verified)

    def check_axes(self):
        if self.axes is None or not self.axes.is_complete():
            # no axes or it is not complete
            return 0
        else:
            return 2 if "VERIFIED_04_AXIS" in self.properties else 1

    def set_axes_verified(self, verified):
        self.set_verification("VERIFIED_04_AXIS", verified)

    def check_data(self):
        if self.data is None:
            # no data ...
            return 0
        else:
            return 2 if "VERIFIED_05_DATA" in self.properties else 1

    def set_data_verified(self, verified):
        self.set_verification("VERIFIED_05_DATA", verified)

    def get_all_text(self, text_type=None):
        result = []
        for text_info in self.text:
            if text_type is None or text_info.type == text_type:
                result.append(text_info)

        return result

    def get_text_index(self, text_type=None):
        result = {}
        for text_info in self.text:
            if text_type is None or text_info.type == text_type:
                result[text_info.id] =  text_info

        return result

    def overwrite_text(self, text_regions, discard_data):
        self.text = text_regions

        if discard_data:
            # discard any existing annotation here (to avoid inconsistencies)
            # TODO: maybe it could check for inconsistencies and avoid discarding everything ?
            self.axes = None
            self.legend = None
            self.data = None

    def get_description(self):

        if self.type == ChartInfo.TypeNonChart:
            type_str = "non-chart"
        elif self.type == ChartInfo.TypeLine:
            type_str = "line"
        elif self.type == ChartInfo.TypeScatter:
            type_str = "scatter"
        elif self.type == ChartInfo.TypeBar:
            type_str = "bar"
        elif self.type == ChartInfo.TypeBox:
            type_str = "box"
        else:
            raise Exception("Chart Type Not Supported")

        if self.orientation == ChartInfo.OrientationHorizontal:
            orientation_str = "horizontal"
        elif self.orientation == ChartInfo.OrientationVertical:
            orientation_str = "vertical"
        else:
            orientation_str = ""

        return type_str, orientation_str

    @staticmethod
    def TypesFromDescription(type_str, orientation_str):
        type_str = type_str.strip().lower()
        orientation_str = orientation_str.strip().lower()

        if type_str == "line":
            chart_type = ChartInfo.TypeLine
        elif type_str == "scatter":
            chart_type = ChartInfo.TypeScatter
        elif type_str == "bar":
            chart_type = ChartInfo.TypeBar
        elif type_str == "box":
            chart_type = ChartInfo.TypeBox
        elif type_str == "non-chart":
            chart_type = ChartInfo.TypeNonChart
        else:
            raise Exception("Chart Type Not Supported")

        if orientation_str == "horizontal":
            orientation_type = ChartInfo.OrientationHorizontal
        elif orientation_str == "vertical":
            orientation_type = ChartInfo.OrientationVertical
        else:
            orientation_type = None

        return chart_type, orientation_type

    def to_XML(self, indent=""):
        type_str, orientation_str = self.get_description()

        xml_str = indent + "<ChartInfo>\n"
        xml_str += indent + '    <Type orientation="{0:s}">{1:s}</Type>\n'.format(orientation_str, type_str)
        xml_str += indent + '    <Text>\n'
        for text_info in self.text:
            xml_str += text_info.to_XML(indent + "        ")
        xml_str += indent + '    </Text>\n'
        if self.legend is not None:
            xml_str += self.legend.to_XML(indent + "    ")
        if self.axes is not None:
            xml_str += self.axes.to_XML(indent + "    ")
        if self.data is not None:
            xml_str += self.data.to_XML(indent + "    ")

        if len(self.properties) > 0:
            xml_str += indent + '    <Properties>\n'
            for key in self.properties:
                xml_str += indent + '        <{0:s}>{1:s}</{0:s}>\n'.format(key, str(self.properties[key]))
            xml_str += indent + '    </Properties>\n'

        xml_str += indent + "</ChartInfo>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assumes that xml_root is ChartInfo node
        # get type description
        xml_type = xml_root.find("Type")
        type_str = xml_type.text
        orientation_str = xml_type.attrib["orientation"]
        chart_type, orientation_type = ChartInfo.TypesFromDescription(type_str, orientation_str)

        # create basic panel ...
        chart = ChartInfo(chart_type, orientation_type)

        # load text annotations (if any)
        xml_text_root = xml_root.find("Text")
        for xml_text in xml_text_root:
            text_region = TextInfo.FromXML(xml_text)
            chart.text.append(text_region)

        # load legend (if any)
        xml_legend_root = xml_root.find("Legend")
        if xml_legend_root is not None:
            # read existing legend!
            legend_labels = chart.get_all_text(TextInfo.TypeLegendLabel)
            legend = LegendInfo.FromXML(xml_legend_root, legend_labels)
            chart.legend = legend

        # load axes (if any)
        xml_axes_root = xml_root.find("Axes")
        if xml_axes_root is not None:
            axes_labels = chart.get_all_text(TextInfo.TypeTickLabel)
            title_labels = chart.get_all_text(TextInfo.TypeAxisTitle)
            axes, outdated_axes = AxesInfo.FromXML(xml_axes_root, axes_labels, title_labels)
            chart.axes = axes
        else:
            outdated_axes = False

        # load data (if any)
        xml_data_root = xml_root.find("Data")
        if xml_data_root is not None:
            chart_text_index = chart.get_text_index()

            data_class = xml_data_root.attrib["class"]
            if data_class == "BarData":
                chart.data = BarData.FromXML(xml_data_root, chart_text_index)
            elif data_class == "BoxData":
                chart.data = BoxData.FromXML(xml_data_root, chart_text_index)
            elif data_class == "LineData":
                chart.data = LineData.FromXML(xml_data_root, chart_text_index)
            elif data_class == "ScatterData":
                chart.data = ScatterData.FromXML(xml_data_root, chart_text_index)
            else:
                raise Exception("Support to read data annotations from this chart type not implemented!")

        # load properties (if any)
        xml_properties_root = xml_root.find("Properties")
        if xml_properties_root is not None:
            for xml_property in xml_properties_root:
                chart.properties[xml_property.tag] = xml_property.text

        # remove out-dated verifications ...
        if outdated_axes and "VERIFIED_04_AXIS" in chart.properties:
            print("-> WARNING: File contains Axis information in old format!")
            del chart.properties["VERIFIED_04_AXIS"]

        return chart




