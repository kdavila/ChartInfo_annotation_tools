
from AM_CommonTools.util.line_segment_2D import LineSegment2D

class Polygon2D:
    def __init__(self, points):
        # assume [(x, y), ....]
        self.points = points

        # pre-compute lines ...
        self.lines = []
        for i in range(len(points)):
            line = LineSegment2D(self.points[i], self.points[(i + 1) % len(self.points)])
            self.lines.append(line)

    def lineIntersects(self, line):
        # test intersection between the given line and each side of the polygon
        for side in self.lines:
            if side.intersection(line) is not None:
                return True

        return False