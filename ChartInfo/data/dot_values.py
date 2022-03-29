
import numpy as np

from shapely.geometry import LineString, Point

class DotValues:
    PointDistanceSame = 0.95

    def __init__(self):
        self.points = []

    def closest_point(self, in_x, in_y):
        if len(self.points) == 0:
            return None, None

        distances = []
        point_in = Point(in_x, in_y)
        for idx, (x, y) in enumerate(self.points):
            distances.append((point_in.distance(Point(x, y)), idx))

        distances = sorted(distances)

        return distances[0]

    def set_point(self, idx, x, y):
        if 0 <= idx <= len(self.points):
            self.points[idx] = x, y

    def contains_point(self, x, y):
        if len(self.points) == 0:
            return False

        raw_diff = np.array(self.points) - np.array([[x, y]])
        all_distances = np.linalg.norm(raw_diff, axis=1)

        return all_distances.min() <= DotValues.PointDistanceSame

    def add_point(self, x, y):
        # check that there is not point in this position already ...
        if not self.contains_point(x, y):
            # add ....
            self.points.append((x, y))

    def remove_point(self, idx):
        if 0 <= idx <= len(self.points):
            del self.points[idx]
            return True
        else:
            return False

    def to_XML(self, indent=""):
        xml_str = indent + '<DotValues>\n'
        for x, y in self.points:
            xml_str += indent + '    <Point>\n'
            xml_str += indent + '        <X>{0:s}</X>\n'.format(str(x))
            xml_str += indent + '        <Y>{0:s}</Y>\n'.format(str(y))
            xml_str += indent + '    </Point>\n'
        xml_str += indent + '</DotValues>\n'

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assume xml_root is DotValues
        values = DotValues()
        for xml_point in xml_root.findall("Point"):
            x = float(xml_point.find("X").text)
            y = float(xml_point.find("Y").text)

            values.points.append((x, y))

        return values

    @staticmethod
    def Copy(other):
        assert isinstance(other, DotValues)

        values = DotValues()
        values.points = [point for point in other.points]

        return values
