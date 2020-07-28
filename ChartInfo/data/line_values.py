
import numpy as np
from scipy import interpolate

from shapely.geometry import LineString, Point

class LineValues:
    # Insert Modes
    InsertByXValue = 0
    InsertByYValue = 1
    InsertByCloseLine = 2

    PointDistanceSame = 0.95

    # TODO: consider these maybe?
    LinearInterpolation = 0
    QuadraticInterpolation = 1
    CubicInterpolation = 2

    def __init__(self):
        self.points = []

        self.cache_line_interp = None

    def get_all_x_values(self):
        # get all unique x values (sorted)
        # note that set is required for older annotations produced before adding constrains forcing points to be unique
        tempo_array = np.array(self.points)
        raw_x_values = list(set(tempo_array[:, 0].tolist()))
        return sorted(raw_x_values)

    def get_y_value(self, x_Value):
        if self.cache_line_interp is None:
            tempo_sorted = sorted(self.points)

            last_val_x = None
            valid_unique_x = []
            valid_unique_y = []
            for x, y in tempo_sorted:
                if x != last_val_x:
                    last_val_x = x
                    valid_unique_x.append(x)
                    valid_unique_y.append(y)

            self.cache_line_interp = interpolate.interp1d(valid_unique_x, valid_unique_y, 'linear',
                                                          fill_value='extrapolate')

        return self.cache_line_interp(x_Value)

    def get_line_relative_bbox(self):
        point_array = np.array(self.points)
        min_x = point_array[:, 0].min()
        max_x = point_array[:, 0].max()
        min_y = point_array[:, 1].min()
        max_y = point_array[:, 1].max()

        return min_x, min_y, max_x, max_y

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

    def add_point_by_close_line(self, x, y):
        if len(self.points) < 2:
            # simply add at the end ...
            self.points.append((x, y))
        else:
            # find the pair of points with the smaller distance ...
            point = Point(x, y)
            all_distances = []
            for idx in range(len(self.points) - 1):
                segment = LineString([self.points[idx], self.points[idx + 1]])
                distance = segment.distance(point)
                all_distances.append((distance, idx))

            all_distances = sorted(all_distances)

            closest_dist, closest_idx = all_distances[0]
            self.points.insert(closest_idx + 1, (x, y))

    def add_point_by_axis_value(self, x, y, axis):
        if len(self.points) == 0:
            # simply add ....
            self.points.append((x, y))
        else:
            insert_at = len(self.points)
            new_point = (x, y)
            for idx, line_point in enumerate(self.points):
                if new_point[axis] < line_point[axis]:
                    # point for insertion found ... stop ...
                    insert_at = idx
                    break

            self.points.insert(insert_at, new_point)

    def contains_point(self, x, y):
        if len(self.points) == 0:
            return False

        raw_diff = np.array(self.points) - np.array([[x, y]])
        all_distances = np.linalg.norm(raw_diff, axis=1)

        return all_distances.min() <= LineValues.PointDistanceSame

    def add_point(self, x, y, mode):
        if self.contains_point(x, y):
            # will not add repeated point
            return False

        if mode == LineValues.InsertByCloseLine:
            self.add_point_by_close_line(x, y)
        elif mode == LineValues.InsertByXValue:
            self.add_point_by_axis_value(x, y, 0)
        elif mode == LineValues.InsertByYValue:
            self.add_point_by_axis_value(x, y, 1)
        else:
            raise Exception("Invalid Point Insertion Mode")

        return True

    def remove_point(self, idx):
        if 0 <= idx <= len(self.points):
            del self.points[idx]
            return True
        else:
            return False

    def to_XML(self, indent=""):
        xml_str = indent + '<LineValues>\n'
        for x, y in self.points:
            xml_str += indent + '    <Point>\n'
            xml_str += indent + '        <X>{0:s}</X>\n'.format(str(x))
            xml_str += indent + '        <Y>{0:s}</Y>\n'.format(str(y))
            xml_str += indent + '    </Point>\n'
        xml_str += indent + '</LineValues>\n'

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assume xml_root is LineValues
        values = LineValues()
        for xml_point in xml_root.findall("Point"):
            x = float(xml_point.find("X").text)
            y = float(xml_point.find("Y").text)

            values.points.append((x, y))

        return values

    @staticmethod
    def Copy(other):
        assert isinstance(other, LineValues)

        values = LineValues()
        values.points = [point for point in other.points]

        return values
