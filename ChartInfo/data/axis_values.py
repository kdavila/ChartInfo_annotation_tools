
import math

from .tick_info import TickInfo
from scipy import interpolate

class AxisValues:
    ValueTypeCategorical = 0
    ValueTypeNumerical = 1

    ScaleNone = 0
    ScaleLinear = 1
    ScaleLogarithmic = 2

    TicksTypeMarkers = 0
    TicksTypeSeparators = 1

    def __init__(self, value_type, ticks_type, scale_type):
        # general axis information ...
        self.values_type = value_type
        self.ticks_type = ticks_type
        self.scale_type = scale_type

        # ticks == None means ticks have not been annotated
        # ticks == [] means annotated but no ticks on given axis
        self.ticks = None

        # divided tick labels ... (un-sorted lists of text ids)
        self.labels = []

        # the title .. (text_id, int)
        self.title = None

        # TODO: handle points where axis is "interrupted" (scale-breaking points)
        self.interruptions = None

        self.cache_interp_x = None
        self.cache_interp_y = None
        self.cache_raw_abs_values = None

    def has_label(self, text_id):
        if self.labels is not None:
            return text_id in self.labels
        else:
            # the axis has no labels ...
            return False

    def has_rotated_labels(self, tick_labels, min_rectangle_ratio=0.8):
        for label_id in self.labels:
            if tick_labels[label_id].axis_aligned_rectangle_ratio() < min_rectangle_ratio:
                return True

        return False

    def has_unassigned_labels(self):
        # first, build an inverted index of label_ids associated with tick marks
        used_label_ids = {}
        for tick_info in self.ticks:
            if tick_info.label_id is not None:
                used_label_ids[tick_info.label_id] = True

        # now check if all label ids have been used ...
        for label_id in self.labels:
            if not label_id in used_label_ids:
                # Found a label id which is not associated with any tick so far ...
                return True

        # reaches this part if no unused label id was found
        return False

    def has_invalid_assignments(self):
        # find if there are ticks associated with labels that do not belong to this axis ..
        for tick_info in self.ticks:
            if tick_info.label_id is not None and tick_info.label_id not in self.labels:
                # found a tick associated with a label not from this axis!
                return True

        return False


    def ticks_with_labels(self):
        return [tick_info for tick_info in self.ticks if tick_info.label_id is not None]

    def get_description(self):
        if self.values_type == AxisValues.ValueTypeNumerical:
            value_type_str = "numerical"
        elif self.values_type == AxisValues.ValueTypeCategorical:
            value_type_str = "categorical"
        else:
            raise Exception("Axis Values Type Not Supported")

        if self.ticks_type == AxisValues.TicksTypeMarkers:
            ticks_type_str = "markers"
        elif self.ticks_type == AxisValues.TicksTypeSeparators:
            ticks_type_str = "separators"
        else:
            raise Exception("Axis Tick Type Not Supported")

        if self.scale_type == AxisValues.ScaleNone:
            scale_type_str = "none"
        elif self.scale_type == AxisValues.ScaleLinear:
            scale_type_str = "linear"
        elif self.scale_type == AxisValues.ScaleLogarithmic:
            scale_type_str = "logarithmic"
        else:
            raise Exception("Axis Scale Not Supported")

        return value_type_str, ticks_type_str, scale_type_str

    @staticmethod
    def TypesFromDescription(value_type_str, ticks_type_str, scale_type_str):
        value_type_str = value_type_str.strip().lower()
        ticks_type_str = ticks_type_str.strip().lower()
        scale_type_str = scale_type_str.strip().lower()

        if value_type_str == "numerical":
            value_type = AxisValues.ValueTypeNumerical
        elif value_type_str == "categorical":
            value_type = AxisValues.ValueTypeCategorical
        else:
            raise Exception("Axis Values Type Not Supported")

        if ticks_type_str == "markers":
            ticks_type =  AxisValues.TicksTypeMarkers
        elif ticks_type_str == "separators":
            ticks_type = AxisValues.TicksTypeSeparators
        else:
            raise Exception("Axis Tick Type Not Supported")

        if scale_type_str == "none":
            scale_type = AxisValues.ScaleNone
        elif scale_type_str == "linear":
            scale_type = AxisValues.ScaleLinear
        elif scale_type_str == "logarithmic":
            scale_type = AxisValues.ScaleLogarithmic
        else:
            raise Exception("Axis Scale Not Supported")

        return value_type, ticks_type, scale_type

    def is_complete(self):
        return self.ticks is not None and self.labels is not None

    def get_sorted_labels(self, tick_labels, sort_by_x, as_ticks=False):
        if self.labels is None:
            return []

        # get labels sorted ....
        tempo_sorted = []
        for text_id in self.labels:
            text_label = tick_labels[text_id]
            cx, cy = text_label.get_center()

            if sort_by_x:
                # from left to right ...
                tempo_sorted.append((cx, text_label))
            else:
                # top to bottom ...
                tempo_sorted.append((cy, text_label))

        tempo_sorted = sorted(tempo_sorted, key=lambda x:x[0])

        if as_ticks:
            # center position + text label object
            return [TickInfo(pos, text_label.id) for pos, text_label in tempo_sorted]
        else:
            # text label object only
            return [text_label for _, text_label in tempo_sorted]

    def get_tick_type_value_positions(self, is_vertical, text_labels):
        if self.cache_raw_abs_values is not None:
            return self.cache_raw_abs_values

        # this function considers the tick type and returns the sorted absolute positions (in pixel space)
        # of its labels (association of pixel coordinates with specific text labels)
        raw_values = []
        if self.ticks_type == AxisValues.TicksTypeMarkers:
            # use the exact positions of ticks with associated labels
            for tick_info in self.ticks:
                if tick_info.label_id is not None:
                    raw_values.append((tick_info.position, tick_info.label_id))
        else:
            # for separator ticks ... directly use the position of the labels
            for label_id in self.labels:
                # based on the center of the label ....
                lbl_cx, lbl_cy = text_labels[label_id].get_center()
                # ... and the orientation of the axis ...
                if is_vertical:
                    raw_values.append((lbl_cy, label_id))
                else:
                    raw_values.append((lbl_cx, label_id))

        # CACHE this operation
        self.cache_raw_abs_values = sorted(raw_values)

        return self.cache_raw_abs_values

    def get_interpolation_points(self, origin_value, is_vertical, text_labels):
        if self.cache_interp_x is not None:
            return self.cache_interp_x, self.cache_interp_y

        self.cache_interp_x = []
        self.cache_interp_y = []

        raw_values = self.get_tick_type_value_positions(is_vertical, text_labels)

        for raw_value, label_id in raw_values:
            if is_vertical:
                x = origin_value - raw_value
            else:
                x = raw_value - origin_value

            self.cache_interp_x.append(x)

            float_val = AxisValues.LabelNumericValue(text_labels[label_id].value)

            self.cache_interp_y.append(float_val)

        return self.cache_interp_x, self.cache_interp_y

    @staticmethod
    def IdentifyNumericPart(str_value):
        num_start = 0
        num_end = None
        commas = []
        dots = []
        while num_start < len(str_value) and not (
                "0" <= str_value[num_start] <= "9" or str_value[num_start] in [",", "."]):
            num_start += 1

        if num_start < len(str_value):
            num_end = num_start
            while num_end < len(str_value) and ("0" <= str_value[num_end] <= "9" or str_value[num_end] in [",", "."]):
                if str_value[num_end] == ".":
                    dots.append(num_end)
                if str_value[num_end] == ",":
                    commas.append(num_end)

                num_end += 1

        return num_start, num_end, dots, commas

    @staticmethod
    def RemoveThousandsSeparator(str_value):
        num_start, num_end, dots, commas = AxisValues.IdentifyNumericPart(str_value)

        if num_end is None:
            raise Exception("No numeric pattern was found on input string: " + str_value)

        if len(commas) > 1 and len(dots) > 1:
            # there can be multiple commas and at most one dot or multiple dots and at most one comma
            # there should not be both multiple commas and multiple dots
            raise Exception("Invalid combination of digit separators was found: " + str_value)

        # note that this function does not validate ... it only guesses format and tries to make sure that most strings
        # will be correctly parsed to float
        num_str = str_value[num_start:num_end]
        if len(commas) > 0:
            if len(dots) > 0:
                # need to figure out if using "1,234.56" or "1.234,56"
                if dots[-1] < commas[-1]:
                    # the comma appears last ... assume "1.234,56"
                    if len(commas) == 1:
                        # remove dots .... then replace comma with dot
                        num_str = num_str.replace(".", "")
                        num_str = num_str.replace(",", ".")
                    else:
                        # invalid ... there can be only one comma (fraction separator)
                        raise Exception("Invalid numeric string: " + str_value)
                else:
                    # the dot appears last ... assume "1,234.56"
                    if len(dots) == 1:
                        # remove commas
                        num_str = num_str.replace(",", "")
                    else:
                        # invalid ... there can be only one dot (fraction separator)
                        raise Exception("Invalid numeric string: " + str_value)
            else:
                # does not contain "dot", it could still be "1,234"="1234.00" or "1,23"="1.23"
                if len(commas) == 1 and num_end - commas[0] <= 3:
                    # assume comma is used as the separator for fractions ("." is for thousands but absent here)
                    # replace comma
                    num_str = num_str.replace(",", ".")
                else:
                    # assume commas are used as thousands separators, remove them
                    num_str = num_str.replace(",", "")

            result = str_value[:num_start] + num_str + str_value[num_end:]
        elif len(dots) > 1:
            # there is no comma on the string, but it contains more than one dot
            # assume that dots are used as the thousands separators and remove them
            num_str = num_str.replace(".", "")
            result = str_value[:num_start] + num_str + str_value[num_end:]
        else:
            # no conversion applied
            result = str_value

        return result

    @staticmethod
    def LabelNumericValue(str_val):
        multiplier = 1.0

        # TODO: Cases not yet handled:
        # TODO: - Fractions "1/2", "1/4" ...etc
        # TODO: - Dates (multiple formats)
        # TODO: - Times (multiple formats)
        # TODO: - Roman Numbers!
        # TODO: - Ordinals
        # TODO: - Some labels can be used by two axis (e.g. the zero)
        # TODO: - External multipliers (an Axis-level value multiplier, usually from a Scale Text Label)

        str_val = str_val.lower()

        # X,YYY,ZZZ.AA -> XYYYZZZ.AA
        # X.XXX.XXX,XX -> XYYYZZZ.AA
        str_val = AxisValues.RemoveThousandsSeparator(str_val)

        # TODO: This is a good place to capture potential units ....
        # keep this list sorted ... in decreasing order so "mm" will be handled before "m"
        known_units = ["usd","s", "ms", "m", "cm", "mm", "$", "x", "€", "£"]
        known_units = sorted([(len(unit), unit) for unit in known_units], reverse=True)
        for l, unit in known_units:
            if unit in "times" and "times" in str_val:
                # some units are substrings of "times"
                # but times is valid latex ... do not remove the unit candidate
                continue

            if unit in str_val:
                # TODO: should this rule be extended to all units ???
                # check if unit is "x"
                if unit == "x":
                    # only treat as unit and remove if it appears at the end of the string
                    if len(str_val[str_val.index(unit) + len(unit):].strip()) == 0:
                        str_val = str_val.replace(unit, "")
                else:
                    # by default, always remove the unit candidate
                    str_val = str_val.replace(unit, "")

        if "%" in str_val:
            str_val = str_val.replace("%", "")
            multiplier = 0.01

        if " " in str_val:
            str_val = str_val.replace(" ", "")

        # replace by space and strip to remove the space automatically only if they space is before or after the string
        # but still should trigger an error if the symbol is placed between other elements
        if "~" in str_val:
            str_val = str_val.replace("~", " ").strip()
        if "<" in str_val:
            str_val = str_val.replace("<", " ").strip()
        if ">" in str_val:
            str_val = str_val.replace("<", " ").strip()
        if "=" in str_val:
            str_val = str_val.replace("<", " ").strip()

        # Handle scientific notation (including LaTeX strings)
        if "x10" in str_val:
            str_val = str_val.replace("x10", "E")
        if "x 10" in str_val:
            str_val = str_val.replace("x 10", "E")
        if "*10" in str_val:
            str_val = str_val.replace("*10", "E")
        if "* 10" in str_val:
            str_val = str_val.replace("* 10", "E")
        if "\\times10^" in str_val:
            str_val = str_val.replace("\\times10", "E")
        if "\\times 10^" in str_val:
            str_val = str_val.replace("\\times 10", "E")
        if str_val[:3] == "10^":
            # directly starts with power of 10 and previous test would fail and next one would destroy value...
            # replace
            str_val = str_val.replace("10^", "1E")
        if "^" in str_val:
            str_val = str_val.replace("^", "")
        if "{" in str_val and "}" in str_val:
            str_val = str_val.replace("{", "")
            str_val = str_val.replace("}", "")

        return float(str_val.strip()) * multiplier

    @staticmethod
    def Project(axes, axis_values, vertical_axis, pixel_value):
        if axis_values.values_type == AxisValues.ValueTypeNumerical:
            # GET origin value
            # use X or Y origin based on axis being vertical or horizontal
            bb_x1, bb_y1, bb_x2, bb_y2 = axes.bounding_box

            """
                if is_vertical:
                    x = origin_value - tick_info.position
                else:
                    x = tick_info.position - origin_value
            """

            if vertical_axis:
                interp_x, interp_y = axis_values.get_interpolation_points(bb_y2, vertical_axis, axes.tick_labels)
                rel_pixel_value = bb_y2 - pixel_value
            else:
                interp_x, interp_y = axis_values.get_interpolation_points(bb_x1, vertical_axis, axes.tick_labels)
                rel_pixel_value = pixel_value - bb_x1

            # print((rel_pixel_value, interp_x, interp_y))

            # identify the closest
            if axis_values.scale_type == AxisValues.ScaleLinear:
                # check for tick values
                if len(interp_x) == 0:
                    # axis is marked as linear, but has no tick labels .... assume default range [0.0, 1.0]
                    if vertical_axis:
                        interp_x = [bb_y2 - bb_y1, 0.0]
                        interp_y = [1.0, 0.0]
                    else:
                        interp_x = [0.0, bb_x2 - bb_x1]
                        interp_y = [0.0, 1.0]

                # interpolate value ...
                f_int = interpolate.interp1d(interp_x, interp_y, 'linear', fill_value='extrapolate')
                return float(f_int(rel_pixel_value))
            elif axis_values.scale_type == AxisValues.ScaleLogarithmic:
                if 0.0 in interp_y:
                    pos = interp_y.index(0.0)
                    del interp_x[pos]
                    del interp_y[pos]

                if len(interp_x) == 0:
                    # axis is marked as linear, but has no tick labels .... assume default range [0.0, 1.0]
                    if vertical_axis:
                        interp_x = [bb_y2 - bb_y1, 0.0]
                        interp_y = [10.0, 1.0]
                    else:
                        interp_x = [0.0, bb_x2 - bb_x1]
                        interp_y = [1.0, 10.0]

                f_int = interpolate.interp1d(interp_x, [math.log(val) for val in interp_y], 'linear',
                                             fill_value='extrapolate')
                return float(math.exp(f_int(rel_pixel_value)))
            else:
                raise Exception("Cannot project on Numerical Axis without Scale")
        else:
            raise Exception("Cannot project on Categorical Axis")

    @staticmethod
    def FindClosestValue(axes, axis_values, vertical_axis, pixel_value):
        label_positions = axis_values.get_tick_type_value_positions(vertical_axis, axes.tick_labels)

        if len(label_positions) == 0:
            raise  Exception("Cannot find the closest value for given pixel coordinate on empty Axis")

        best_distance = None
        best_label_id = None
        for abs_pos, label_id in label_positions:
            dist = abs(pixel_value - abs_pos)

            if best_distance is None or dist < best_distance:
                best_distance = dist
                best_label_id = label_id

        closest_value = axes.tick_labels[best_label_id].value

        if axis_values.values_type == AxisValues.ValueTypeCategorical:
            # use raw tick label string as value
            return closest_value
        else:
            # numerical ... convert ...
            return AxisValues.LabelNumericValue(closest_value)

    def to_XML(self, indent=""):
        xml_str = indent + "<AxisValues>\n"

        # store types in human-readable format ...
        value_type_str, ticks_type_str, scale_type_str = self.get_description()

        xml_str += indent + '    <ValuesType>{0:s}</ValuesType>\n'.format(value_type_str)
        xml_str += indent + '    <TicksType>{0:s}</TicksType>\n'.format(ticks_type_str)
        xml_str += indent + '    <ScaleType>{0:s}</ScaleType>\n'.format(scale_type_str)

        # absolute points ... (sorted lists)
        if self.ticks is not None:
            xml_str += indent + "    <Ticks>\n"
            for tick_info in self.ticks:
                xml_str += tick_info.to_XML(indent + "        ")
            xml_str += indent + "    </Ticks>\n"

        if self.labels is not None:
            xml_str += indent + "    <Labels>\n"
            for text_id in self.labels:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(text_id)
            xml_str += indent + "    </Labels>\n"

        if self.title is not None:
            xml_str += indent + "    <Title>{0:d}</Title>\n".format(self.title)

        if self.interruptions is not None:
            raise Exception("Not Implemented")

        xml_str += indent + "</AxisValues>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assume XML_root is AxisValues node ....

        # general information ....
        value_type_str = xml_root.find("ValuesType").text
        ticks_type_str = xml_root.find("TicksType").text
        scale_type_str = xml_root.find("ScaleType").text

        value_type, ticks_type, scale_type = AxisValues.TypesFromDescription(value_type_str, ticks_type_str,
                                                                             scale_type_str)

        # create instance ...
        values = AxisValues(value_type, ticks_type, scale_type)

        # detailed information ...

        # tick points (and associated labels)
        xml_ticks = xml_root.find("Ticks")
        if xml_ticks is not None:
            values.ticks = []
            for xml_tick in xml_ticks.findall("TickInfo"):
                tick = TickInfo.FromXML(xml_tick)
                values.ticks.append(tick)

        # divided tick labels ... (un-sorted lists of text ids)
        xml_labels = xml_root.find("Labels")
        if xml_labels is not None:
            values.labels = []
            for xml_text_id in xml_labels.findall("TextId"):
                text_id = int(xml_text_id.text)
                values.labels.append(text_id)


        # the title .. (text_id, int)
        xml_title = xml_root.find("Title")
        if xml_title is not None:
            values.title = int(xml_title.text)

        # TODO: load interruptions ....
        values.interruptions = None

        return values

    @staticmethod
    def Copy(other):
        assert isinstance(other, AxisValues)

        values = AxisValues(other.values_type, other.ticks_type, other.scale_type)

        values.title = other.title

        # axis - ticks ....
        if other.ticks is not None:
            values.ticks = [TickInfo.Copy(tick) for tick in other.ticks]

        # axis - labels ....
        if other.labels is not None:
            values.labels = list(other.labels)

        if other.interruptions is not None:
            raise Exception("Not Implemented")

        return values

