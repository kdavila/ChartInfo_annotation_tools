
import numpy as np

from xml.sax.saxutils import escape, unescape

from shapely.geometry import Polygon, Point

class TextInfo:
    TypeChartTitle = 0
    TypeAxisTitle = 1
    TypeTickLabel = 2
    TypeLegendTitle = 3
    TypeLegendLabel = 4
    TypeValueLabel = 5
    TypeOther = 6
    TypeTickGrouping = 7
    TypeDataMarkLabel = 8

    def __init__(self, id, position_polygon, text_type, text_value):
        # must be a numpy array with a row for each x-y coord
        self.id = int(id)
        self.position_polygon = position_polygon
        self.type = text_type
        self.value = text_value

    def __repr__(self):
        return "<TextInfo: ({0:d}) [{1:s}] \"{2:s}\" >".format(self.id, self.get_type_description(), self.value)

    def get_center(self):
        c_x = self.position_polygon[:, 0].mean()
        c_y = self.position_polygon[:, 1].mean()

        return c_x, c_y

    def get_axis_aligned_rectangle(self):
        min_x = self.position_polygon[:, 0].min()
        max_x = self.position_polygon[:, 0].max()
        min_y = self.position_polygon[:, 1].min()
        max_y = self.position_polygon[:, 1].max()

        # XYXY format
        return min_x, min_y, max_x, max_y

    def axis_aligned_rectangle_ratio(self):
        min_x, min_y, max_x, max_y = self.get_axis_aligned_rectangle()

        rectangular_area = (max_x - min_x) * (max_y - min_y)
        polygon_area = Polygon(self.position_polygon).area

        return polygon_area / rectangular_area

    def area_contains_point(self, point_x, point_y):
        poly = Polygon(self.position_polygon)
        point = Point(point_x, point_y)

        return poly.contains(point)

    def get_type_description(self):
        if self.type == TextInfo.TypeChartTitle:
            return "chart-title"
        elif self.type == TextInfo.TypeAxisTitle:
            return "axis-title"
        elif self.type == TextInfo.TypeTickLabel:
            return "tick-label"
        elif self.type == TextInfo.TypeTickGrouping:
            return "tick-grouping"
        elif self.type == TextInfo.TypeLegendTitle:
            return "legend-title"
        elif self.type == TextInfo.TypeLegendLabel:
            return "legend-label"
        elif self.type == TextInfo.TypeValueLabel:
            return "value-label"
        elif self.type == TextInfo.TypeDataMarkLabel:
            return "mark-label"
        elif self.type == TextInfo.TypeOther:
            return "other"
        else:
            raise Exception("Invalid Text Type")

    @staticmethod
    def TypeFromDescription(type_str):
        type_str = type_str.strip().lower()

        if type_str == "chart-title":
            return TextInfo.TypeChartTitle
        elif type_str == "axis-title":
            return TextInfo.TypeAxisTitle
        elif type_str == "tick-label":
            return TextInfo.TypeTickLabel
        elif type_str == "tick-grouping":
            return TextInfo.TypeTickGrouping
        elif type_str == "legend-title":
            return TextInfo.TypeLegendTitle
        elif type_str == "legend-label":
            return TextInfo.TypeLegendLabel
        elif type_str == "value-label":
            return TextInfo.TypeValueLabel
        elif type_str == "mark-label":
            return TextInfo.TypeDataMarkLabel
        elif type_str == "other":
            return TextInfo.TypeOther
        else:
            raise Exception("Invalid Text Type")

    @staticmethod
    def Copy(other):
        assert isinstance(other, TextInfo)

        return TextInfo(other.id, other.position_polygon.copy(), other.type, other.value)

    def to_XML(self, indent=""):
        type_desc = self.get_type_description()

        xml_str = indent + "<TextInfo>\n"
        xml_str += indent + "    <Id>{0:s}</Id>\n".format(str(self.id))
        xml_str += indent + "    <Polygon>\n"
        for x, y in self.position_polygon:
            xml_str += indent + "        <Point>\n"
            xml_str += indent + "            <X>{0:s}</X>\n".format(str(x))
            xml_str += indent + "            <Y>{0:s}</Y>\n".format(str(y))
            xml_str += indent + "        </Point>\n"

        xml_str += indent + "    </Polygon>\n"
        xml_str += indent + "    <Type>{0:s}</Type>\n".format(type_desc)
        xml_str += indent + "    <Value>{0:s}</Value>\n".format(escape(self.value))
        xml_str += indent + "</TextInfo>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assume xml_root is TextInfo
        text_id = int(xml_root.find("Id").text)

        polygon_points = []
        xml_polygon = xml_root.find("Polygon")
        for xml_point in xml_polygon:
            point_x = float(xml_point.find("X").text)
            point_y = float(xml_point.find("Y").text)

            polygon_points.append([point_x, point_y])

        polygon_points = np.array(polygon_points)
        text_type = TextInfo.TypeFromDescription(xml_root.find("Type").text)
        text_value = unescape(xml_root.find("Value").text.strip())

        return TextInfo(text_id, polygon_points, text_type, text_value)
