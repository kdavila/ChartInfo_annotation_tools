
class LineSegment2D:
    def __init__(self, p1, p2):
        self.x1, self.y1 = p1
        self.x2, self.y2 = p2

        # pre-compute line boundaries ...
        self.x_min = min(self.x1, self.x2)
        self.x_max = max(self.x1, self.x2)
        self.y_min = min(self.y1, self.y2)
        self.y_max = max(self.y1, self.y2)

        # precompute line slope and intersect
        if self.x1 == self.x2:
            self.vertical = True
            self.m = None
            self.b = None
        else:
            self.vertical = False
            self.m = (self.y2 - self.y1) / (self.x2 - self.x1)
            self.b = self.y1 - self.m * self.x1

    def intersection(self, line_s):
        if not self.vertical:
            # first line is not vertical....
            # slope and intersect....
            if line_s.vertical:
                # second line is vertical line....
                if self.x_min <= line_s.x1 <= self.x_max:
                    # the vertical line s is inside the x-range of the line l...
                    y_int = line_s.x1 * self.m + self.b
                    # check if y_int in range of vertical line...
                    if line_s.y_min <= y_int <= line_s.y_max:
                        # intersection point with the vertical line ...
                        return line_s.x1, y_int
                    else:
                        # no intersection between segments ...
                        return None
                else:
                    # vertical line s is out of x-range of the line l ..
                    return None
            else:
                # second is not a vertical line ...
                # check if parallel
                if self.m == line_s.m:
                    # parallel lines, can only intersect if l_b == s_b
                    # (meaning they are the same line), and have intersecting ranges
                    if self.b == line_s.b:
                        if self.x_min <= line_s.x_max and line_s.x_min <= self.x_max:
                            mid_x = (max(self.x_min, line_s.x_min) + min(self.x_max, line_s.x_max)) / 2.0
                            mid_y = self.m * mid_x + self.b

                            return mid_x, mid_y
                        else:
                            return None
                    else:
                        return None
                else:
                    # not parallel, they must have an intersection point
                    x_int = (line_s.b - self.b) / (self.m - line_s.m)
                    # y_int = x_int * l_m + l_b

                    # the intersection point must be in both lines...
                    if (self.x_min <= x_int <= self.x_max) and (line_s.x_min <= x_int <= line_s.x_max):
                        y_int = x_int * self.m + self.b
                        return x_int, y_int
                    else:
                        return None
        else:
            # l is vertical line
            if line_s.vertical:
                # the segment s is a vertical line (too)...
                # only if they are on the same x position, and their range intersects
                if line_s.x1 == self.x1 and line_s.y_min < self.y_max and self.y_min <= line_s.y_max:
                    mid_y = (max(self.y_min, line_s.y_min) + min(self.y_max, line_s.y_max)) / 2.0

                    return self.x1, mid_y
                else:
                    return None
            else:
                # calculate intersection point
                if line_s.x_min <= self.x1 <= line_s.x_max:
                    # the vertical line l is inside the x-range of the segment s...
                    y_int = self.x1 * line_s.m + line_s.b
                    # check if y_int in y-range of vertical line...
                    if self.y_min <= y_int <= self.y_max:
                        return self.x1, y_int
                    else:
                        return None
                else:
                    # the vertical line l is out of the x-range of line s
                    return None