
import pygame
import numpy as np
from pygame import Surface, Rect
from shapely.geometry import asPolygon, Polygon, Point, LineString

from .screen_element import ScreenElement

# TODO: these classes are growing ... and should go to a file of their own ...
class ScreenCanvasRectangle:
    def __init__(self, x, y, w, h, visible=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible

    def update(self, x, y, w, h, visible=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        x = round(self.x + off_x)
        y = round(self.y + off_y)
        w = round(self.w)
        h = round(self.h)

        pygame.draw.rect(background, main_color, (x, y, w, h), stroke_width)

        if hl_color is not None:
            # selected
            half_hl = hl_size / 2
            pygame.draw.rect(background, hl_color, (x - half_hl, y - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x + w - half_hl, y - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x - half_hl, y + h - half_hl, hl_size, hl_size))
            pygame.draw.rect(background, hl_color, (x + w - half_hl, y + h - half_hl, hl_size, hl_size))

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


class ScreenCanvasPolygon:
    def __init__(self, points, visible=True):
        self.points = np.array(points)
        self.polygon = asPolygon(self.points)
        self.visible = visible

    def update(self, points, visible=True):
        if points is None:
            # empty state
            self.points[:, :] = 0.0
        else:
            # copy new state
            self.points[:,:] = points
        self.visible = visible

    def render(self, background, off_x, off_y, main_color, hl_color, hl_size, stroke_width=2):
        if not self.visible:
            return

        offset_points = (self.points + np.array([[off_x, off_y]])).round().tolist()

        pygame.draw.polygon(background, main_color, offset_points, stroke_width)

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

        test_polygon = asPolygon(new_points)
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

    def update_rectangle_element(self, name, x, y, w, h, visible):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasRectangle)

        element.update(x, y, w, h, visible)

    def update_polygon_element(self, name, polygon_points, visible):
        element = self.elements[name]
        assert isinstance(element, ScreenCanvasPolygon)

        element.update(polygon_points, visible)

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
