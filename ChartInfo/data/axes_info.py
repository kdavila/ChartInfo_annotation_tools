
from .tick_info import TickInfo
from .axis_values import AxisValues

from .legacy_1_0_axes_info import LegacyAxesInfo

class AxesInfo:
    DataVersion = 1.1

    AxisX1 = 0
    AxisY1 = 1
    AxisX2 = 2
    AxisY2 = 3

    def __init__(self, tick_labels, axes_titles):
        # text indices ...
        self.tick_labels = {text.id: text for text in tick_labels}
        self.axes_titles = {text.id: text for text in axes_titles}

        # bounding box (x1, y1, x2, y2)
        self.bounding_box = None

        # handle all axes info (2 axis by default = x1, y1)
        self.x1_axis = None
        self.y1_axis = None
        # ... un-common axes ...
        self.x2_axis = None
        self.y2_axis = None

    def axis_has_rotated_labels(self, axis, min_rectangle_ratio=0.8):
        if axis == AxesInfo.AxisX1:
            if self.x1_axis is not None:
                return self.x1_axis.has_rotated_labels(self.tick_labels, min_rectangle_ratio)
            else:
                return False
        elif axis == AxesInfo.AxisX2:
            if self.x2_axis is not None:
                return self.x2_axis.has_rotated_labels(self.tick_labels, min_rectangle_ratio)
            else:
                return False
        elif axis == AxesInfo.AxisY1:
            if self.y1_axis is not None:
                return self.y1_axis.has_rotated_labels(self.tick_labels, min_rectangle_ratio)
            else:
                return False
        elif axis == AxesInfo.AxisY2:
            if self.y2_axis is not None:
                return self.y2_axis.has_rotated_labels(self.tick_labels, min_rectangle_ratio)
            else:
                return False

        else:
            raise Exception("Unknown Axis")

    def axis_get_projected_value(self, axis, pixel_value):
        if axis == AxesInfo.AxisX1:
            if self.x1_axis is not None:
                pass
            else:
                raise Exception("Cannot Project to X-1, Axis is not defined on this chart")
        elif axis == AxesInfo.AxisX2:
            if self.x2_axis is not None:
                pass
            else:
                raise Exception("Cannot Project to X-1, Axis is not defined on this chart")
        elif axis == AxesInfo.AxisY1:
            if self.y1_axis is not None:
                pass
            else:
                raise Exception("Cannot Project to Y-1, Axis is not defined on this chart")
        elif axis == AxesInfo.AxisY2:
            if self.y2_axis is not None:
                pass
            else:
                raise Exception("Cannot Project to Y-2, Axis is not defined on this chart")
        else:
            raise Exception("Unknown Axis")

    def is_complete(self):
        return not (self.bounding_box is None or
                    ((self.x1_axis is None or not self.x1_axis.is_complete()) and
                     (self.x2_axis is None or not self.x2_axis.is_complete()) and
                     (self.y1_axis is None or not self.y1_axis.is_complete()) and
                     (self.y2_axis is None or not self.y2_axis.is_complete())))

    def projected_label_ticks(self):
        projections = {}

        # Add X-1
        if self.x1_axis is not None:
            projections[AxesInfo.AxisX1] = self.x1_axis.get_sorted_labels(self.tick_labels, True, True)

        # Add X-2
        if self.x2_axis is not None:
            projections[AxesInfo.AxisX2] = self.x2_axis.get_sorted_labels(self.tick_labels, True, True)

        # Add Y-1
        if self.y1_axis is not None:
            projections[AxesInfo.AxisY1] = self.y1_axis.get_sorted_labels(self.tick_labels, False, True)

        # Add Y-2
        if self.y2_axis is not None:
            projections[AxesInfo.AxisY2] = self.y2_axis.get_sorted_labels(self.tick_labels, False, True)

        return projections

    def empty_axes(self):
        return self.x1_axis is None and self.x2_axis is None and self.y1_axis is None and self.y2_axis is None

    def find_label_axis(self, text_id):
        if not text_id in self.tick_labels:
            # not a tick label ...
            return None

        # check per axis ...
        if self.x1_axis is not None and self.x1_axis.has_label(text_id):
            return AxesInfo.AxisX1
        elif self.x2_axis is not None and self.x2_axis.has_label(text_id):
            return AxesInfo.AxisX2
        elif self.y1_axis is not None and self.y1_axis.has_label(text_id):
            return AxesInfo.AxisY1
        elif self.y2_axis is not None and self.y2_axis.has_label(text_id):
            return AxesInfo.AxisY2
        else:
            return None

    def get_axis_labels(self, axis):
        if axis == AxesInfo.AxisX1:
            if self.x1_axis is None:
                return []
            else:
                return self.x1_axis.get_sorted_labels(self.tick_labels, True)

        elif axis == AxesInfo.AxisX2:
            if self.x2_axis is None:
                return []
            else:
                return self.x2_axis.get_sorted_labels(self.tick_labels, True)

        elif axis == AxesInfo.AxisY1:
            if self.y1_axis is None:
                return []
            else:
                return self.y1_axis.get_sorted_labels(self.tick_labels, False)

        elif axis == AxesInfo.AxisY2:
            if self.y2_axis is None:
                return []
            else:
                return self.y2_axis.get_sorted_labels(self.tick_labels, False)

        else:
            raise Exception("Unknown Axis")

    def to_XML(self, indent=""):
        xml_str = indent + "<Axes>\n"

        # add Axis Version Stamp ...
        xml_str += indent + "    <Version>{0:s}</Version>\n".format(str(AxesInfo.DataVersion))

        # tick labels ....
        xml_str += indent + "    <TickLabels>\n"
        for text_id in self.tick_labels:
            xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(text_id)
        xml_str += indent + "    </TickLabels>\n"

        # bounding box (x1, y1, x2, y2)
        if self.bounding_box is not None:
            x1, y1, x2, y2 = self.bounding_box
            xml_str += indent + "    <BoundingBox>\n"
            xml_str += indent + "        <X1>{0:s}</X1>\n".format(str(x1))
            xml_str += indent + "        <Y1>{0:s}</Y1>\n".format(str(y1))
            xml_str += indent + "        <X2>{0:s}</X2>\n".format(str(x2))
            xml_str += indent + "        <Y2>{0:s}</Y2>\n".format(str(y2))
            xml_str += indent + "    </BoundingBox>\n"

        # all axis ...
        if self.x1_axis is not None:
            xml_str += indent + "    <AxisX1>\n"
            xml_str += self.x1_axis.to_XML(indent + "        ")
            xml_str += indent + "    </AxisX1>\n"

        if self.x2_axis is not None:
            xml_str += indent + "    <AxisX2>\n"
            xml_str += self.x2_axis.to_XML(indent + "        ")
            xml_str += indent + "    </AxisX2>\n"

        if self.y1_axis is not None:
            xml_str += indent + "    <AxisY1>\n"
            xml_str += self.y1_axis.to_XML(indent + "        ")
            xml_str += indent + "    </AxisY1>\n"

        if self.y2_axis is not None:
            xml_str += indent + "    <AxisY2>\n"
            xml_str += self.y2_axis.to_XML(indent + "        ")
            xml_str += indent + "    </AxisY2>\n"

        xml_str += indent + "</Axes>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root, tick_labels, title_labels):
        # check for XML version ...
        xml_version = xml_root.find("Version")
        if xml_version is None:
            # very first version of axis annotations ...
            return AxesInfo.FromLegacy_1_0_XML(xml_root, tick_labels, title_labels), True
        else:
            if float(xml_version.text) < AxesInfo.DataVersion:
                # newer format, but not the most current format ...
                out_dated_format = True
            else:
                out_dated_format = False

        # assume XML root = Axes
        info = AxesInfo(tick_labels, title_labels)

        # validate input tick labels
        validation_ids = []
        xml_tick_labels = xml_root.find("TickLabels")
        for xml_text_id in xml_tick_labels.findall("TextId"):
            validation_ids.append(int(xml_text_id.text))

        if not set(validation_ids) == set(info.tick_labels.keys()):
            raise Exception("Invalid Axes Info on XML file")

        # get boundaries (if defined)
        xml_bounding_box = xml_root.find("BoundingBox")
        if xml_bounding_box is not None:
            x1 = float(xml_bounding_box.find("X1").text)
            y1 = float(xml_bounding_box.find("Y1").text)
            x2 = float(xml_bounding_box.find("X2").text)
            y2 = float(xml_bounding_box.find("Y2").text)

            info.bounding_box = (x1, y1, x2, y2)

        # read each axis ...
        xml_axis_x1 = xml_root.find("AxisX1")
        if xml_axis_x1 is not None:
            info.x1_axis = AxisValues.FromXML(xml_axis_x1.find("AxisValues"))

        xml_axis_x2 = xml_root.find("AxisX2")
        if xml_axis_x2 is not None:
            info.x2_axis = AxisValues.FromXML(xml_axis_x2.find("AxisValues"))

        xml_axis_y1 = xml_root.find("AxisY1")
        if xml_axis_y1 is not None:
            info.y1_axis = AxisValues.FromXML(xml_axis_y1.find("AxisValues"))

        xml_axis_y2 = xml_root.find("AxisY2")
        if xml_axis_y2 is not None:
            info.y2_axis = AxisValues.FromXML(xml_axis_y2.find("AxisValues"))

        return info, out_dated_format

    @staticmethod
    def Copy(other):
        assert isinstance(other, AxesInfo)

        # general info ..
        copy_tick_labels = [other.tick_labels[text_id] for text_id in other.tick_labels]
        copy_titles_labels = [other.axes_titles[text_id] for text_id in other.axes_titles]

        info = AxesInfo(copy_tick_labels, copy_titles_labels)

        info.bounding_box = other.bounding_box

        # copy the axes ...
        if other.x1_axis is not None:
            info.x1_axis = AxisValues.Copy(other.x1_axis)
        if other.x2_axis is not None:
            info.x2_axis = AxisValues.Copy(other.x2_axis)

        if other.y1_axis is not None:
            info.y1_axis = AxisValues.Copy(other.y1_axis)
        if other.y2_axis is not None:
            info.y2_axis = AxisValues.Copy(other.y2_axis)

        return info

    @staticmethod
    def FromLegacy_1_0_XML(xml_root, tick_labels, title_labels):
        old_axes = LegacyAxesInfo.FromXML(xml_root, tick_labels, title_labels)

        # create new version ...
        copy_tick_labels = [old_axes.tick_labels[text_id] for text_id in old_axes.tick_labels]
        copy_titles_labels = [old_axes.axes_titles[text_id] for text_id in old_axes.axes_titles]

        info = AxesInfo(copy_tick_labels, copy_titles_labels)
        info.bounding_box = old_axes.bounding_box

        # set two axes by default ....
        info.x1_axis = AxisValues(AxisValues.ValueTypeCategorical, AxisValues.TicksTypeMarkers, AxisValues.ScaleNone)
        info.y1_axis = AxisValues(AxisValues.ValueTypeNumerical, AxisValues.TicksTypeMarkers, AxisValues.ScaleLinear)

        # copy titles ...
        info.x1_axis.title = old_axes.x_title
        info.y1_axis.title = old_axes.y_title

        # copy ticks ...
        if old_axes.x_ticks is not None:
            info.x1_axis.ticks = [TickInfo.Copy(tick) for tick in old_axes.x_ticks]
        if old_axes.y_ticks is not None:
            info.y1_axis.ticks = [TickInfo.Copy(tick) for tick in old_axes.y_ticks]

        # copy labels ....
        if old_axes.x_labels is not None:
            info.x1_axis.labels = list(old_axes.x_labels)
        if old_axes.y_labels is not None:
            info.y1_axis.labels = list(old_axes.y_labels)

        return info
