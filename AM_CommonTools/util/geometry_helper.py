
class GeometryHelper:
    @staticmethod
    def lineIntersectPolygon(line, polygon):
        # assuming the given polygon is not closed
        n_sides = len(polygon)

        # test intersection between the given line and each side of the polygon
        for k in range(n_sides):
            p1 = polygon[k]
            p2 = polygon[(k + 1) % n_sides]

            if GeometryHelper.linesIntersect((p1, p2), line):
                return True
            
        return False

    @staticmethod
    def boxesBoudingBox(boxes):
        # asume boxes is a list of boxes in the format
        # [((min_x, max_x), (min_y, max_y)), ... ]
        all_min_x, all_max_x, all_min_y, all_max_y = [], [], [], []
        for (min_x, max_x), (min_y, max_y) in boxes:
            all_min_x.append(min_x)
            all_max_x.append(max_x)
            all_min_y.append(min_y)
            all_max_y.append(max_y)

        return (min(all_min_x), max(all_max_x)), (min(all_min_y), max(all_max_y))

    @staticmethod
    def boxesIntercept(box1, box2):
        # assume box format ...
        # ((min_x, max_x), (min_y, max_y))
        (b1_min_x, b1_max_x), (b1_min_y, b1_max_y) = box1
        (b2_min_x, b2_max_x), (b2_min_y, b2_max_y) = box2

        return ((b1_min_x <= b2_max_x) and (b2_min_x <= b1_max_x) and
                (b1_min_y <= b2_max_y) and (b2_min_y <= b2_max_y))

    @staticmethod
    def getLineBoundaries(p1, p2):
        # check minimum
        # ....x....
        x1, y1 = p1
        x2, y2 = p2
        if x1 < x2:
            l_x_min = x1
            l_x_max = x2
        else:
            l_x_min = x2
            l_x_max = x1

        # ....Y....
        if y1 < y2:
            l_y_min = y1
            l_y_max = y2
        else:
            l_y_min = y2
            l_y_max = y1

        return l_x_min, l_x_max, l_y_min, l_y_max

    @staticmethod
    def linesIntersect(line_l, line_s):
        # assumes that each line is a tuple or list with a pair of points (x, y)
        # line = ( (x1, y1), (x2, y2) )
        ((l_x1, l_y1), (l_x2, l_y2)) = line_l
        ((s_x1, s_y1), (s_x2, s_y2)) = line_s

        # check limits
        l_xmin, l_xmax, l_ymin, l_ymax = GeometryHelper.getLineBoundaries((l_x1, l_y1), (l_x2, l_y2))
        s_xmin, s_xmax, s_ymin, s_ymax = GeometryHelper.getLineBoundaries((s_x1, s_y1), (s_x2, s_y2))

        if l_x2 != l_x1:
            # first line is not vertical....
            # slope and intersect....
            l_m = (l_y2 - l_y1) / float(l_x2 - l_x1)
            l_b = l_y1 - l_m * l_x1

            if s_x1 == s_x2:
                # second line is vertical line....
                if l_xmin <= s_x1 <= l_xmax:
                    # the vertical line s is inside the x-range of the line l...
                    y_int = s_x1 * l_m + l_b
                    # check if y_int in range of vertical line...
                    return s_ymin <= y_int <= s_ymax
                else:
                    # vertical line s is out of x-range of the line l ..
                    return False
            else:
                # second is not a vertical line ..., compute slope and intersect ...
                s_m = (s_y2 - s_y1) / (s_x2 - s_x1)
                s_b = s_y1 - s_m * s_x1

                # check if parallel
                if s_m == l_m:
                    # parallel lines, can only intersect if l_b == s_b
                    # (meaning they are the same line), and have intersecting ranges
                    if l_b == s_b:
                        return l_xmin <= s_xmax and s_xmin <= l_xmax
                    else:
                        return False
                else:
                    # not parallel, they must have an intersection point
                    x_int = (s_b - l_b) / (l_m - s_m)
                    # y_int = x_int * l_m + l_b

                    # the intersection point must be in both lines...
                    return l_xmin <= x_int <= l_xmax and s_xmin <= x_int <= s_xmax
        else:
            # l is vertical line
            if s_x1 == s_x2:
                # the segment s is a vertical line (too)...
                # only if they are on the same x position, and their range intersects
                return s_x1 == l_x1 and s_ymin < l_ymax and l_ymin < s_ymax
            else:
                # calculate intersection point
                if s_xmin <= l_x1 <= s_xmax:
                    # the vertical line l is inside the x-range of the segment s...
                    s_m = (s_y2 - s_y1) / (s_x2 - s_x1)
                    s_b = s_y1 - s_m * s_x1

                    y_int = l_x1 * s_m + s_b
                    # check if y_int in y-range of vertical line...
                    return l_ymin <= y_int <= l_ymax
                else:
                    # the vertical line l is out of the x-range of line s
                    return False
