
import pygame
import numpy as np
from pygame import Surface, Rect
from shapely.geometry import Polygon, Point, LineString

from .screen_element import ScreenElement

# TODO: these classes are growing ... and should go to a file of their own ...
class ScreenCanvasElement:
    def __init__(self, visible):
        self.visible = visible

    def compute_dashes_per_side(self, polygon_points, closed, total_dashes):
        # base case ... no dashes ....
        if total_dashes is None or total_dashes <= 1:
            return None

        n_sides = polygon_points.shape[0]
        if not closed:
            n_sides -= 1

        # for each side of the polygon ...
        length_per_side = np.zeros(n_sides)
        for idx in range(n_sides):
            side_length = np.linalg.norm(polygon_points[idx, :] - polygon_points[(idx + 1) % polygon_points.shape[0], :])
            length_per_side[idx] = side_length

        # normalize length
        total_sum = length_per_side.sum()
        if total_sum > 0:
            length_per_side /= total_sum

        dashes_per_side = []
        for idx in range(n_sides):
            dashes_per_side.append(max(1, int(round(length_per_side[idx] * total_dashes))))

        return dashes_per_side

    def int_point(self, point):
        return int(round(point[0])), int(round(point[1]))

    # children classes should implement methods
    # check_drag_type
    # drag
    # render
    # update


class ScreenCanvasRectangle(ScreenCanvasElement):
    def __init__(self, x, y, w, h, visible=True, total_dashes=1):
        ScreenCanvasElement.__init__(self, visible)

        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.total_dashes = total_dashes

    def update(self, x, y, w, h, visible=True, total_dashes=1):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        self.total_dashes = total_dashes

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        x = round(self.x + off_x)
        y = round(self.y + off_y)
        w = round(self.w)
        h = round(self.h)

        if self.total_dashes is None or self.total_dashes <= 1:
            # simple rectangle ....
            pygame.draw.rect(background, main_color, (x, y, w, h), stroke_width)
        else:
            # dashed rectangle ....
            ratio_x = w / (w + h)
            hor_dashes = max(1, int(round(ratio_x * self.total_dashes / 2.0)))
            ver_dashes = max(1, int(round((1.0 - ratio_x) * self.total_dashes / 2.0)))

            # draw horizontal dashed lines ...
            t_pieces = 2 * hor_dashes - 1
            fraction = 1.0 / t_pieces
            for idx in range(hor_dashes):
                start_prc = (idx * 2) * fraction
                end_prc = start_prc + fraction
                # top
                pygame.draw.line(background, main_color, (int(x + start_prc * w), int(y)),
                                 (int(x + end_prc * w), int(y)), stroke_width)
                # bottom
                pygame.draw.line(background, main_color, (int(x + start_prc * w), int(y + h)), (int(x + end_prc * w),
                                                                                                int(y + h)),
                                 stroke_width)

            # draw vertical dashed lines ...
            t_pieces = 2 * ver_dashes - 1
            fraction = 1.0 / t_pieces
            for idx in range(ver_dashes):
                start_prc = (idx * 2) * fraction
                end_prc = start_prc + fraction

                # left
                pygame.draw.line(background, main_color, (int(x), int(y + start_prc * h)),
                                 (int(x), int(y + end_prc * h)), stroke_width)
                # right
                pygame.draw.line(background, main_color, (int(x + w), int(y + start_prc * h)),
                                 (int(x + w), int(y + end_prc * h)),
                                 stroke_width)

        if hl_color is not None:
            # selected
            half_hl = hl_size / 2
            pygame.draw.rect(background, hl_color, (x - half_hl, y - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x + w - half_hl, y - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x - half_hl, y + h - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x + w - half_hl, y + h - half_hl, hl_size, hl_size))

            """
            # use circles instead?
            pygame.draw.circle(background, hl_color, (int(x), int(y)), int(half_hl))
            pygame.draw.circle(background, hl_color, (int(x + w), int(y)), int(half_hl))
            pygame.draw.circle(background, hl_color, (int(x), int(y + h)), int(half_hl))
            pygame.draw.circle(background, hl_color, (int(x + w), int(y + h)), int(half_hl))
            """

    def check_drag_type(self, off_x, off_y, hl_size, px, py):
        if not self.visible:
            return -1

        rel_x = self.x + off_x
        rel_y = self.y + off_y

        half = hl_size / 2

        # against any highlighted point
        if (rel_x - half <= px <= rel_x + half) and (rel_y - half <= py <= rel_y + half):
            return 1

        if (rel_x + self.w - half <= px <= rel_x + self.w + half) and (rel_y - half <= py <= rel_y + half):
            return 2

        if (rel_x - half <= px <= rel_x + half) and (rel_y + self.h - half <= py <= rel_y + self.h + half):
            return 3

        if (rel_x + self.w - half <= px <= rel_x + self.w + half) and (rel_y + self.h - half <= py <= rel_y + self.h + half):
            return 4

        # intersection
        if (rel_x <= px <= rel_x + self.w) and (rel_y <= py <= rel_y + self.h):
            return 0

        # reaches here if it doesn't intersect the polygon at all.
        return -1

    def drag(self, drag_type, dx, dy, min_width, min_height):
        prev_x = self.x
        prev_y = self.y
        prev_w = self.w
        prev_h = self.h

        if drag_type == 0:
            # translation, scale not affected
            self.x += dx
            self.y += dy

        if drag_type == 1:
            # Top-left corner
            self.x += dx
            self.y += dy
            self.w -= dx
            self.h -= dy

        if drag_type == 2:
            # Top-right
            self.y += dy
            self.w += dx
            self.h -= dy

        if drag_type == 3:
            # Bottom-left
            self.x += dx
            self.w -= dx
            self.h += dy

        if drag_type == 4:
            # Bottom-right corner
            self.w += dx
            self.h += dy

        if self.w < min_width:
            self.w = min_width
        if self.h < min_height:
            self.h = min_height

        # return True if anything was changed at all ...
        return prev_x != self.x or prev_y != self.y or prev_w != self.w or prev_h != self.h


class ScreenCanvasPolygon(ScreenCanvasElement):
    def __init__(self, points, visible=True, total_dashes=1):
        ScreenCanvasElement.__init__(self, visible)

        self.points = np.array(points)
        self.polygon = Polygon(self.points)
        self.total_dashes = total_dashes
        # polygon_points, closed, total_dashes
        self.dashes_per_side = self.compute_dashes_per_side(self.points, True, total_dashes)

    def update(self, points, visible=True, total_dashes=1):
        if points is None:
            # empty state
            self.points[:, :] = 0.0
        else:
            # copy new state
            self.points[:,:] = points
        self.visible = visible
        self.total_dashes = total_dashes
        self.dashes_per_side = self.compute_dashes_per_side(self.points, True, total_dashes)

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        offset_points = (self.points + np.array([[off_x, off_y]]))

        if self.total_dashes is None or self.total_dashes <= 1:
            offset_points = offset_points.round().tolist()
            pygame.draw.polygon(background, main_color, offset_points, stroke_width)
        else:
            # for each of the polygon
            for side_idx in range(self.points.shape[0]):
                # draw the dashed line ....
                t_pieces = 2 * self.dashes_per_side[side_idx] - 1
                fraction = 1.0 / t_pieces

                p1 = offset_points[side_idx, :]
                p2 = offset_points[(side_idx + 1) % offset_points.shape[0], :]

                for dash_idx in range(self.dashes_per_side[side_idx]):
                    start_prc = (dash_idx * 2) * fraction
                    end_prc = start_prc + fraction

                    dash_p1 = p1 * (1.0 - start_prc) + p2 * start_prc
                    dash_p2 = p1 * (1.0 - end_prc) + p2 * end_prc

                    pygame.draw.line(background, main_color, self.int_point(dash_p1), self.int_point(dash_p2),
                                     stroke_width)

        if hl_color is not None:
            # selected
            half_hl = hl_size / 2

            for x, y in offset_points:
                pygame.draw.rect(background, hl_color, (x - half_hl, y - half_hl, hl_size, hl_size))

    def check_drag_type(self, off_x, off_y, hl_size, px, py):
        if not self.visible:
            return -1

        offset_points = (self.points + np.array([[off_x, off_y]])).tolist()

        half = hl_size / 2

        # against any highlighted point
        for idx, (x, y) in enumerate(offset_points):
            if (x - half <= px <= x + half) and (y - half <= py <= y + half):
                # the index of the point being dragged + 1
                return 1 + idx

        # against a side of the polygon ...
        point = Point(px, py)
        for idx in range(len(offset_points)):
            p1 = offset_points[idx]
            p2 = offset_points[(idx + 1) % len(offset_points)]
            side = LineString([p1, p2])

            if side.distance(point) < half:
                return 1 + idx + len(offset_points)

        # intersection
        offset_polygon = Polygon(offset_points)
        if offset_polygon.contains(point):
            return 0

        # reaches here if it doesn't intersect the polygon (or its points) at all.
        return -1

    def drag(self, drag_type, dx, dy, min_width, min_height):
        # create a copy of the points ...
        new_points = self.points.copy()
        if drag_type == 0:
            # simple translation, shape not affected
            new_points += np.array([[dx, dy]])

        if drag_type > 0:
            drag_type -= 1
            if drag_type < new_points.shape[0]:
                # one point is dragged ....
                new_points[drag_type, 0] += dx
                new_points[drag_type, 1] += dy
            else:
                # one edge is dragged ...
                drag_type -= new_points.shape[0]
                new_points[drag_type, 0] += dx
                new_points[drag_type, 1] += dy
                new_points[(drag_type + 1) % new_points.shape[0], 0] += dx
                new_points[(drag_type + 1) % new_points.shape[0], 1] += dy

        test_polygon = Polygon(new_points)
        valid_polygon = test_polygon.is_valid
        min_x, min_y, max_x, max_y = test_polygon.bounds

        if (max_x - min_x) < min_width:
            valid_polygon = False
        if (max_y - min_y) < min_height:
            valid_polygon = False

        values_changed = np.sum(np.abs(new_points - self.points)) > 0.001
        if valid_polygon and values_changed:
            # update ...
            self.points[:,:] = new_points
            return True
        else:
            return False


class ScreenCanvasPolyLine(ScreenCanvasElement):
    def __init__(self, points, visible=True, total_dashes=1):
        ScreenCanvasElement.__init__(self, visible)

        self.points = np.array(points, np.float64)
        self.total_dashes = total_dashes
        self.dashes_per_side = self.compute_dashes_per_side(self.points, False, total_dashes)

    def update(self, points, visible=True, total_dashes=1):
        if points is None:
            # empty state
            self.points[:, :] = 0.0
        else:
            # copy new state
            self.points = np.array(points, np.float64)

        self.visible = visible
        self.total_dashes = total_dashes
        self.dashes_per_side = self.compute_dashes_per_side(self.points, False, total_dashes)

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        offset_points = (self.points + np.array([[off_x, off_y]]))

        # for each side of the polyline ...
        for side_idx in range(self.points.shape[0] - 1):
            p1 = offset_points[side_idx, :]
            p2 = offset_points[side_idx + 1, :]

            # draw the dashed line ....
            if self.total_dashes is None or self.total_dashes <= 1:
                # draw connection using a single solid line ...
                pygame.draw.line(background, main_color, self.int_point(p1), self.int_point(p2), stroke_width)
            else:
                # draw connection using a dashed line ...
                t_pieces = 2 * self.dashes_per_side[side_idx] - 1
                fraction = 1.0 / t_pieces

                for dash_idx in range(self.dashes_per_side[side_idx]):
                    start_prc = (dash_idx * 2) * fraction
                    end_prc = start_prc + fraction

                    dash_p1 = p1 * (1.0 - start_prc) + p2 * start_prc
                    dash_p2 = p1 * (1.0 - end_prc) + p2 * end_prc

                    pygame.draw.line(background, main_color, self.int_point(dash_p1), self.int_point(dash_p2),
                                     stroke_width)

        if hl_color is not None:
            # selected
            half_hl = hl_size / 2

            for x, y in offset_points:
                pygame.draw.rect(background, hl_color, (x - half_hl, y - half_hl, hl_size, hl_size))

    def check_drag_type(self, off_x, off_y, hl_size, px, py):
        if not self.visible:
            return -1

        offset_points = (self.points + np.array([[off_x, off_y]])).tolist()

        half = hl_size / 2

        # against any highlighted point
        for idx, (x, y) in enumerate(offset_points):
            if (x - half <= px <= x + half) and (y - half <= py <= y + half):
                # the index of the point being dragged + 1
                return 1 + idx

        # against a side of the polygon ...
        point = Point(px, py)
        for idx in range(len(offset_points) - 1):
            p1 = offset_points[idx]
            p2 = offset_points[idx + 1]
            side = LineString([p1, p2])

            if side.distance(point) < half:
                return 1 + idx + len(offset_points)

        # there is no intersection dragging for polyline ...
        # so, at the moment there is no way to define drag type 0 (move everything)

        # so, it reaches here if it doesn't intersect the polyline points or edges at all.
        return -1

    def drag(self, drag_type, dx, dy, min_width, min_height):
        # create a copy of the points ...
        new_points = self.points.copy()
        if drag_type == 0:
            # simple translation, shape not affected
            new_points += np.array([[dx, dy]])

        if drag_type > 0:
            drag_type -= 1
            if drag_type < new_points.shape[0]:
                # one point is dragged ....
                new_points[drag_type, 0] += dx
                new_points[drag_type, 1] += dy
            else:
                # one edge is dragged ...
                drag_type -= new_points.shape[0]
                new_points[drag_type, 0] += dx
                new_points[drag_type, 1] += dy
                new_points[drag_type + 1, 0] += dx
                new_points[drag_type + 1, 1] += dy

        valid_polyline = True
        min_x, max_x = new_points[:, 0].min(), new_points[:, 0].max()
        min_y, max_y = new_points[:, 1].min(), new_points[:, 1].max()

        if (max_x - min_x) < min_width and (max_y - min_y) < min_height:
            valid_polyline = False

        values_changed = np.sum(np.abs(new_points - self.points)) > 0.001
        if valid_polyline and values_changed:
            # update ...
            self.points[:,:] = new_points
            return True
        else:
            return False


class ScreenCanvasPointSet(ScreenCanvasElement):
    StyleRectangles = 0

    def __init__(self, points, visible=True, style=0):
        ScreenCanvasElement.__init__(self, visible)

        self.points = np.array(points, np.float64)
        self.style = style

    def update(self, points, visible=True, style=0):
        if points is None:
            # empty state
            self.points[:, :] = 0.0
        else:
            # copy new state
            self.points = np.array(points, np.float64)

        self.visible = visible
        self.style = style

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible or self.points.shape[0] == 0:
            return

        offset_points = (self.points + np.array([[off_x, off_y]]))

        # selected
        half_hl = hl_size / 2

        color = hl_color if hl_color is not None else main_color

        for x, y in offset_points:
            if self.style == ScreenCanvasPointSet.StyleRectangles:
                pygame.draw.rect(background, color, (x - half_hl, y - half_hl, hl_size, hl_size))

    def check_drag_type(self, off_x, off_y, hl_size, px, py):
        if not self.visible:
            return -1

        offset_points = (self.points + np.array([[off_x, off_y]])).tolist()

        half = hl_size / 2

        # against any highlighted point
        for idx, (x, y) in enumerate(offset_points):
            if (x - half <= px <= x + half) and (y - half <= py <= y + half):
                # the index of the point being dragged + 1
                return 1 + idx

        # there is no intersection or edge dragging for point set  ...
        # so, at the moment there is no way to define drag type 0 (move everything)

        # it reaches here if it doesn't intersect any points at all.
        return -1

    def drag(self, drag_type, dx, dy, min_width, min_height):
        # create a copy of the points ...
        new_points = self.points.copy()
        if drag_type == 0:
            # simple translation, shape not affected
            new_points += np.array([[dx, dy]])

        if drag_type > 0:
            drag_type -= 1
            if drag_type < new_points.shape[0]:
                # one point is dragged ....
                new_points[drag_type, 0] += dx
                new_points[drag_type, 1] += dy

        valid_point_set = True

        values_changed = np.sum(np.abs(new_points - self.points)) > 0.001
        if valid_point_set and values_changed:
            # update ...
            self.points[:,:] = new_points
            return True
        else:
            return False


class ScreenCanvasSlide(ScreenCanvasElement):
    def __init__(self, position, is_vertical, base_length, slider_length, slider_positions, visible=True):
        ScreenCanvasElement.__init__(self, visible)

        self.original_position = position
        self.original_length = base_length
        self.original_slider_positions = slider_positions

        self.is_vertical = is_vertical
        self.slider_length = slider_length
        self.strict_boundaries = True

        self.points = np.zeros((2 + len(slider_positions), 2), np.float64)
        self.__set_points()

    def get_slider_positions(self):
        if self.is_vertical:
            # use y coordinates ...
            return self.points[2:, 1].tolist()
        else:
            # use x coordinates ...
            return self.points[2:, 0].tolist()

    def __set_points(self):
        self.points[0, :] = self.original_position

        if self.is_vertical:
            # fixed x value...
            self.points[1:, 0] = self.original_position[0]
            # moving alongside the y axis
            # ... last point of the base bar
            self.points[1, 1] = self.original_position[1] + self.original_length
            # ... now the sliders centers ...
            self.points[2:, 1] = self.original_slider_positions
        else:
            # fixed y value...
            self.points[1:, 1] = self.original_position[1]
            # moving alongside the x axis
            # ... last point of the base bar
            self.points[1, 0] = self.original_position[0] + self.original_length
            # ... now the sliders centers ...
            self.points[2:, 0] = self.original_slider_positions

    def update(self, position, is_vertical, base_length, slider_length, slider_positions, visible=True):
        self.original_position = position
        self.original_length = base_length
        self.original_slider_positions = slider_positions

        self.is_vertical = is_vertical
        self.slider_length = slider_length
        self.visible = visible

        self.points = np.zeros((2 + len(slider_positions), 2), np.float64)
        self.__set_points()

    def __get_sliders_points(self, offset_points):
        n_sliders = len(self.original_slider_positions)

        # now each of the sliders ...
        hl_slider_l = self.slider_length / 2
        sliders_points = []
        scaling_points = []
        for slider_idx in range(n_sliders):
            base_inter_point = offset_points[2 + slider_idx]
            if n_sliders > 1:
                w_p2 = slider_idx / (n_sliders - 1)
            else:
                w_p2 = 0.5

            # three points are needed: beginning, ending and intermediate
            if self.is_vertical:
                # fixed x, y changing .. the slider is shown as a horizontal line at the given y position
                p1 = (base_inter_point[0] - hl_slider_l, base_inter_point[1])
                p2 = (base_inter_point[0] + hl_slider_l, base_inter_point[1])
                p_int = (p1[0] * (1.0 - w_p2) + p2[0] * w_p2, base_inter_point[1])

                # check for scaling points ...
                if slider_idx == 0:
                    # top point (only visible if not higher than fist point
                    scale_top = (base_inter_point[0], base_inter_point[1] - hl_slider_l)
                    draw_top = scale_top[1] >= offset_points[0, 1]
                    scaling_points.append((scale_top, draw_top))
                elif slider_idx + 1 == n_sliders:
                    # bottom point (only visible if not lower than last point
                    scale_bottom = (base_inter_point[0], base_inter_point[1] + hl_slider_l)
                    draw_bottom = scale_bottom[1] <= offset_points[1, 1]
                    scaling_points.append((scale_bottom, draw_bottom))
            else:
                # fixed y, x changing ... the slider is shown as a vertical line at the given xposition
                p1 = (base_inter_point[0], base_inter_point[1] - hl_slider_l)
                p2 = (base_inter_point[0], base_inter_point[1] + hl_slider_l)
                p_int = (base_inter_point[0], p1[1] * (1.0 - w_p2) + p2[1] * w_p2)

                # check for scaling points ...
                if slider_idx == 0:
                    # left point (only visible if not lower than fist point
                    scale_left = (base_inter_point[0] - hl_slider_l, base_inter_point[1])
                    draw_left = scale_left[0] >= offset_points[0, 0]
                    scaling_points.append((scale_left, draw_left))
                elif slider_idx + 1 == n_sliders:
                    # right point (only visible if not greater than last point
                    scale_right = (base_inter_point[0] + hl_slider_l, base_inter_point[1])
                    draw_right = scale_right[0] <= offset_points[1, 0]
                    scaling_points.append((scale_right, draw_right))

            sliders_points.append((p1, p2, p_int))

        return sliders_points, scaling_points

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        offset_points = (self.points + np.array([[off_x, off_y]]))

        # ... other drawing parameters
        darker_main = tuple([int(val / 2) for val in main_color])
        if hl_color is not None:
            # selected
            half_hl = hl_size / 2
            rect_s = hl_size
            middle_color = hl_color
        else:
            half_hl = stroke_width
            middle_color = main_color
            rect_s = stroke_width * 3

        # draw the base of the sliders ...
        # use darker color before/after first slider ...
        p1 = self.int_point(offset_points[0, :])
        p2 = self.int_point(offset_points[2, :])
        p3 = self.int_point(offset_points[-1, :])
        p4 = self.int_point(offset_points[1, :])

        pygame.draw.line(background, darker_main, p1, p2, stroke_width)
        pygame.draw.line(background, main_color, p2, p3, stroke_width)
        pygame.draw.line(background, darker_main, p3, p4, stroke_width)
        # pygame.draw.line(background, main_color, self.int_point(p1), self.int_point(p2), stroke_width)

        # get current slider and scaling points ...
        sliders_points, scaling_points = self.__get_sliders_points(offset_points)

        # draw scale points ...
        for s_p, draw_point in scaling_points:
            if draw_point:
                # draw the draggable scaling point
                pygame.draw.rect(background, middle_color, (s_p[0] - half_hl, s_p[1] - half_hl, rect_s, rect_s))

        # draw sliders!!!
        for p1, p2, p_int in sliders_points:
            # draw slider line ...
            pygame.draw.line(background, main_color, self.int_point(p1), self.int_point(p2), stroke_width)

            # draw the dragging point
            pygame.draw.rect(background, middle_color, (p_int[0] - half_hl, p_int[1] - half_hl, rect_s, rect_s))


    def check_drag_type(self, off_x, off_y, hl_size, px, py):
        if not self.visible:
            return -1

        offset_points = (self.points + np.array([[off_x, off_y]]))

        # get current slider and scaling points ...
        sliders_points, scaling_points = self.__get_sliders_points(offset_points)
        half = hl_size / 2

        # first, check click on the scaling points ...
        (sp_1_pos, sp_1_draw), (sp_2_pos, sp_2_draw) = scaling_points
        if (sp_1_draw and (sp_1_pos[0] - half <= px <= sp_1_pos[0] + half) and
            (sp_1_pos[1] - half <= py <= sp_1_pos[1] + half)):
            return 1
        if (sp_2_draw and (sp_2_pos[0] - half <= px <= sp_2_pos[0] + half) and
            (sp_2_pos[1] - half <= py <= sp_2_pos[1] + half)):
            return 2

        # second, check click against the rectangles on each slider ....
        for idx, (p1, p2, p_int) in enumerate(sliders_points):
            if (p_int[0] - half <= px <= p_int[0] + half) and (p_int[1] - half <= py <= p_int[1] + half):
                # the index of the slider being dragged + 1
                return 3 + idx

        # third, check click against the lines of the sliders ...
        for idx, (p1, p2, p_int) in enumerate(sliders_points):
            slider_line = LineString([p1, p2])
            point = Point(px, py)

            if slider_line.distance(point) < half:
                return 3 + idx

        # reaches here is nothing is can be dragged
        return -1

    def drag(self, drag_type, dx, dy, min_width, min_height):
        # create a copy of the points ...
        new_points = self.points.copy()

        valid_slider = True
        n_sliders = len(self.original_slider_positions)

        if drag_type == 0:
            # simple translation, shape not affected
            new_points += np.array([[dx, dy]])
        elif drag_type == 1 or drag_type == 2:
            # dragging from first point or last point ...
            if drag_type == 1:
                # drag all sliders except the last one
                # this is, re-scale the object from the left/top
                delta_sign = -1     # invert displacement
                t_point = 2         # from first point
            else:
                # drag all sliders except the first one
                # this is, re-scale the object from the right/bottom
                delta_sign = 1      # direct displacement
                t_point = -1        # from last point

            # vertical or horizontal ...?
            if self.is_vertical:
                # y-dist
                t_axis = 1
                delta = dy
            else:
                # x-dist
                t_axis = 0
                delta = dx

            # resizing of the object ...
            original_size = new_points[-1, t_axis] - new_points[2, t_axis]
            new_size = original_size + delta * delta_sign
            # used to resize the object ..
            scale_factor = new_size / original_size

            # subtract the first slider point
            new_points[2:, t_axis] -= self.points[t_point, t_axis]
            # ... scaling ...
            new_points[2:, t_axis] *= scale_factor
            # translate to original position plus delta
            new_points[2:, t_axis] += self.points[t_point, t_axis] + delta

        if drag_type >= 3:
            # drag a specific slider ...
            dragged = drag_type - 3

            # move the corresponding slider ...
            if self.is_vertical:
                # move on y
                new_points[2 + dragged, 1] += dy

                # validate ...
                if dy < 0:
                    # moving up .... check previous ...
                    if dragged > 0:
                        if new_points[1 + dragged, 1] > new_points[2 + dragged, 1]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 1] = new_points[1 + dragged, 1]
                    else:
                        if self.strict_boundaries and new_points[0, 1] > new_points[2 + dragged, 1]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 1] = new_points[0, 1]
                else:
                    # moving down ... check next ...
                    if dragged + 1 < n_sliders:
                        if new_points[2 + dragged, 1] > new_points[3 + dragged, 1]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 1] = new_points[3 + dragged, 1]
                    else:
                        if self.strict_boundaries and new_points[2 + dragged, 1] > new_points[1, 1]:
                            new_points[2 + dragged, 1] = new_points[1, 1]
            else:
                # move on x
                new_points[2 + dragged, 0] += dx

                # validate
                if dx < 0:
                    # moving left .... check previous ...
                    if dragged > 0:
                        if new_points[1 + dragged, 0] > new_points[2 + dragged, 0]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 0] = new_points[1 + dragged, 0]
                    else:
                        if self.strict_boundaries and new_points[0, 0] > new_points[2 + dragged, 0]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 0] = new_points[0, 0]
                else:
                    # moving right ... check next ...
                    if dragged + 1 < n_sliders:
                        if new_points[2 + dragged, 0] > new_points[3 + dragged, 0]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 0] = new_points[3 + dragged, 0]
                    else:
                        if self.strict_boundaries and new_points[2 + dragged, 0] > new_points[1, 0]:
                            # force equal (boundary reached!)
                            new_points[2 + dragged, 0] = new_points[1, 0]

        values_changed = np.sum(np.abs(new_points - self.points)) > 0.001
        if valid_slider and values_changed:
            # update ...
            self.points[:,:] = new_points
            return True
        else:
            return False


class ScreenCanvas(ScreenElement):
    def __init__(self, name, width, height):
        ScreenElement.__init__(self, name)

        self.width = width
        self.height = height

        self.elements = {}
        self.custom_colors = {}
        self.custom_sel_colors = {}
        self.draw_order = []
        self.name_order = {}
        self.selected_element = None

        self.colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        self.min_width = 10
        self.min_height = 10
        self.sel_size = 10
        self.sel_colors = [(128,0,0), (0,128,0), (0,0, 128), (128,128,0), (128,0,128), (0,128,128)]

        self.locked = False
        self.drag_type = -1 # No dragging

        self.object_edited_callback = None
        self.object_selected_callback = None

    def clear(self):
        # delete all elements
        self.elements = {}
        self.custom_colors = {}
        self.custom_sel_colors = {}
        self.draw_order = []
        self.name_order = {}
        self.selected_element = None
        # no active dragging
        self.drag_type = -1

    def get_selected(self):
        if self.selected_element is None:
            return None
        else:
            return self.elements[self.selected_element]

    def update_names_order(self):
        tempo_names = sorted(self.draw_order)
        self.name_order = {name: idx for idx, name in enumerate(tempo_names)}

    def __add_canvas_element(self, name, canvas_element, custom_color=None, custom_sel_color=None):
        if name not in self.elements:
            self.elements[name] = canvas_element
            self.custom_colors[name] = custom_color
            self.custom_sel_colors[name] = custom_sel_color
            self.draw_order.insert(0, name)
            self.update_names_order()

    def add_rectangle_element(self, name, x, y, w, h, custom_color=None, custom_sel_color=None):
        canvas_rectangle = ScreenCanvasRectangle(x, y, w, h)
        self.__add_canvas_element(name, canvas_rectangle, custom_color, custom_sel_color)

    def add_polygon_element(self, name, polygon_points, custom_color=None, custom_sel_color=None):
        canvas_polygon = ScreenCanvasPolygon(polygon_points)
        self.__add_canvas_element(name, canvas_polygon, custom_color, custom_sel_color)

    def add_polyline_element(self, name, polyline_points, custom_color=None, custom_sel_color=None):
        canvas_polyline = ScreenCanvasPolyLine(polyline_points)
        self.__add_canvas_element(name, canvas_polyline, custom_color, custom_sel_color)

    def add_point_set_element(self, name, point_set, custom_color=None, custom_sel_color=None):
        canvas_point_set = ScreenCanvasPointSet(point_set)
        self.__add_canvas_element(name, canvas_point_set, custom_color, custom_sel_color)

    def add_slider_element(self, name, position, is_vertical, base_length, slider_length, slider_positions,
                           custom_color=None, custom_sel_color=None):
        canvas_slide = ScreenCanvasSlide(position, is_vertical, base_length, slider_length, slider_positions)
        self.__add_canvas_element(name, canvas_slide, custom_color, custom_sel_color)

    def update_rectangle_element(self, name, x, y, w, h, visible, dashes=1):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasRectangle)

        element.update(x, y, w, h, visible, dashes)

    def update_polygon_element(self, name, polygon_points, visible, dashes=1):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasPolygon)

        element.update(polygon_points, visible, dashes)

    def update_polyline_element(self, name, polyline_points, visible, dashes=1):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasPolyLine)

        element.update(polyline_points, visible, dashes)

    def update_point_set_element(self, name, point_set, visible, style=0):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasPointSet)

        element.update(point_set, visible, style)

    def update_slider_element(self, name, position, is_vertical, base_length, slider_length, slider_positions, visible):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasSlide)

        element.update(position, is_vertical, base_length, slider_length, slider_positions, visible)

    def update_custom_colors(self, name, custom_color, custom_sel_color):
        if name in self.elements:
            self.custom_colors[name] = custom_color
            self.custom_sel_colors[name] = custom_sel_color

    def rename_element(self, old_name, new_name):
        if old_name in self.elements and old_name != new_name and new_name not in self.elements:
            # old name exists, new name is different and is not in use
            # copy with new name
            self.elements[new_name] = self.elements[old_name]
            self.custom_colors[new_name] = self.custom_colors[old_name]
            self.custom_sel_colors[new_name] = self.custom_colors[old_name]
            # delete old name reference
            del self.elements[old_name]
            del self.custom_colors[old_name]
            del self.custom_sel_colors[old_name]

            # check if selected ....
            if self.selected_element == old_name:
                # update selected name
                self.selected_element = new_name

            pos = self.draw_order.index(old_name)
            self.draw_order.remove(old_name)
            self.draw_order.insert(pos, new_name)

            self.update_names_order()

    def remove_element(self, element_name):
        if element_name in self.elements:
            # delete name reference
            del self.elements[element_name]
            del self.custom_colors[element_name]
            del self.custom_sel_colors[element_name]

            # check if selected ....
            if self.selected_element == element_name:
                # update selected name
                self.selected_element = None

            # no longer drawing
            self.draw_order.remove(element_name)

            self.update_names_order()

    def render(self, background, off_x=0, off_y=0):
        background.set_clip(Rect(self.position[0], self.position[1], self.width, self.height))

        for idx, element in enumerate(self.draw_order):
            # render....
            render_element = self.elements[element]
            name_order_idx = self.name_order[element]

            if self.custom_colors[element] is None:
                # use default sequence of colors
                main_color = self.colors[name_order_idx % len(self.colors)]
            else:
                # use given color
                main_color = self.custom_colors[element]

            if self.selected_element == element:
                # selected
                if self.custom_sel_colors[element] is None:
                    # default highlighting color
                    highlight_color = self.sel_colors[name_order_idx % len(self.sel_colors)]
                else:
                    highlight_color = self.custom_sel_colors[element]
            else:
                highlight_color = None

            render_element.render(background, off_x + self.position[0], off_y + self.position[1],
                                  main_color, highlight_color, self.sel_size)

        pygame.draw.rect(background, (0, 0, 0), (self.position[0], self.position[1], self.width, self.height), 2)
        background.set_clip(None)

    def on_mouse_button_down(self, pos, button):
        if self.locked:
            return

        if button == 1:
            pre_selected_element = self.selected_element
            self.selected_element = None

            # Left-click
            px, py = pos

            # for every object in reversed draw order ...
            # (things drawn last are visible on top)
            for idx, element in enumerate(reversed(self.draw_order)):
                # check if the current element is being dragged ...
                current_element = self.elements[element]
                dragging = current_element.check_drag_type(self.position[0], self.position[1], self.sel_size, px, py)

                # if dragging status is positive (or zero)
                if dragging != -1:
                    # keep dragging status ... and mark current element as selected ...
                    self.drag_type = dragging
                    self.selected_element = element
                    break

            # if is not top of draw order, move to first ...
            if self.selected_element is not None and self.draw_order[-1] != self.selected_element:
                self.draw_order.remove(self.selected_element)
                #self.draw_order.insert(0, self.selected_element)
                self.draw_order.append(self.selected_element)

            if self.selected_element != pre_selected_element:
                if self.object_selected_callback is not None:
                    self.object_selected_callback(self.selected_element)

    def change_selected_element(self, new_selected_element):
        # only if it is a real change
        if new_selected_element == self.selected_element:
            return

        # copy selected
        self.selected_element = new_selected_element

        # move to last (if needed)
        if self.selected_element is not None and self.draw_order[-1] != self.selected_element:
            self.draw_order.remove(self.selected_element)
            #self.draw_order.insert(0, self.selected_element)
            self.draw_order.append(self.selected_element)

    def on_mouse_button_up(self, pos, button):
        if self.locked:
            return

        self.drag_type = -1

    def on_mouse_enter(self, pos, rel, buttons):
        if self.locked:
            return

        self.drag_type = -1
        #print(pos)

    def on_mouse_leave(self, pos, rel, buttons):
        if self.locked:
            return

        self.drag_type = -1
        #print(pos)

    def on_mouse_motion(self, pos, rel, buttons):
        if self.locked:
            return

        if self.selected_element is None:
            return

        if self.drag_type == -1:
            # not actually dragging/editing anything
            return

        curr_elem = self.elements[self.selected_element]
        dx, dy = rel

        modified = curr_elem.drag(self.drag_type, dx, dy, self.min_width, self.min_height)

        if modified and self.object_edited_callback is not None:
            self.object_edited_callback(self, self.selected_element)

        #print(str((pos, rel, buttons)))
        #print(pos)
