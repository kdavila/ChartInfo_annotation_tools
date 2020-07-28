
class BoxValues:
    def __init__(self, box_min, box_median, box_max, whisker_min, whisker_max):
        self.box_min = box_min
        self.box_median = box_median
        self.box_max = box_max
        self.whiskers_min = whisker_min
        self.whiskers_max = whisker_max

    def set_whisker_max(self, new_value):
        # constraint (not smaller than box maximum)
        if new_value < self.box_max:
            new_value = self.box_max

        self.whiskers_max = new_value

    def set_box_max(self, new_value):
        # constraints
        if new_value < self.box_median:
            # (not smaller than box median)
            new_value = self.box_median
        elif new_value > self.whiskers_max:
            # (not larger than whiskers max)
            new_value = self.whiskers_max

        self.box_max = new_value

    def set_box_median(self, new_value):
        # constraints
        if new_value < self.box_min:
            # (not smaller than box min)
            new_value = self.box_min
        elif new_value > self.box_max:
            # (not larger than box max)
            new_value = self.box_max

        self.box_median = new_value

    def set_box_min(self, new_value):
        # constraints
        if new_value < self.whiskers_min:
            # (not smaller than whisker min)
            new_value = self.whiskers_min
        elif new_value > self.box_median:
            # (not larger than box max)
            new_value = self.box_median

        self.box_min = new_value

    def set_whisker_min(self, new_value):
        # constraints
        if new_value > self.box_min:
            # (not larger than box min)
            new_value = self.box_min

        self.whiskers_min = new_value

    def get_box_lines(self, box_baseline, box_start, box_end, box_vertical):
        # a box can be drawn using 14 points
        # 4 define the main box (b_....)
        # 2 required for median (m_....)
        # 4 for bottom whisker  (wb_....)
        # 4 for top whisker     (wt_....)

        box_mid = (box_start + box_end) / 2

        if box_vertical:
            b_min = box_baseline - self.box_min
            b_med = box_baseline - self.box_median
            b_max = box_baseline - self.box_max
            w_min = box_baseline - self.whiskers_min
            w_max = box_baseline - self.whiskers_max

            b_min_start = (box_start, b_min)
            b_max_start = (box_start, b_max)
            b_max_end = (box_end, b_max)
            b_min_end = (box_end, b_min)

            b_med_start = (box_start, b_med)
            b_med_end = (box_end, b_med)

            wb_box_mid = (box_mid, b_min)
            wb_line_mid = (box_mid, w_min)
            wb_line_start = (box_start, w_min)
            wb_line_end = (box_end, w_min)

            wt_box_mid = (box_mid, b_max)
            wt_line_mid = (box_mid, w_max)
            wt_line_start = (box_start, w_max)
            wt_line_end = (box_end, w_max)
        else:
            b_min = box_baseline + self.box_min
            b_med = box_baseline + self.box_median
            b_max = box_baseline + self.box_max
            w_min = box_baseline + self.whiskers_min
            w_max = box_baseline + self.whiskers_max

            b_min_start = (b_min, box_start)
            b_max_start = (b_max, box_start)
            b_max_end = (b_max, box_end)
            b_min_end = (b_min, box_end)

            b_med_start = (b_med, box_start)
            b_med_end = (b_med, box_end)

            wb_box_mid = (b_min, box_mid)
            wb_line_mid = (w_min, box_mid)
            wb_line_start = (w_min, box_start)
            wb_line_end = (w_min, box_end)

            wt_box_mid = (b_max, box_mid)
            wt_line_mid = (w_max, box_mid)
            wt_line_start = (w_max, box_start)
            wt_line_end = (w_max, box_end)

        box_polygon = (b_min_start, b_max_start, b_max_end, b_min_end)
        box_median = (b_med_start, b_med_end)
        whisker_bottom = (wb_box_mid, wb_line_mid, wb_line_start, wb_line_end)
        whisker_top = (wt_box_mid, wt_line_mid, wt_line_start, wt_line_end)

        return box_polygon, box_median, whisker_bottom, whisker_top

    @staticmethod
    def Copy(other):
        assert isinstance(other, BoxValues)

        return BoxValues(other.box_min, other.box_median, other.box_max, other.whiskers_min, other.whiskers_max)

    def to_XML(self, indent=""):
        xml_str = indent + '<BoxValues>\n'
        xml_str += indent + "    <WhiskerMinimum>{0:s}</WhiskerMinimum>\n".format(str(self.whiskers_min))
        xml_str += indent + "    <BoxMinimum>{0:s}</BoxMinimum>\n".format(str(self.box_min))
        xml_str += indent + "    <BoxMedian>{0:s}</BoxMedian>\n".format(str(self.box_median))
        xml_str += indent + "    <BoxMaximum>{0:s}</BoxMaximum>\n".format(str(self.box_max))
        xml_str += indent + "    <WhiskerMaximum>{0:s}</WhiskerMaximum>\n".format(str(self.whiskers_max))
        xml_str += indent + '</BoxValues>\n'

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # Assume Root is <BoxValues>
        whisker_min = float(xml_root.find("WhiskerMinimum").text)
        box_min = float(xml_root.find("BoxMinimum").text)
        box_median = float(xml_root.find("BoxMedian").text)
        box_max = float(xml_root.find("BoxMaximum").text)
        whisker_max = float(xml_root.find("WhiskerMaximum").text)

        return BoxValues(box_min, box_median, box_max, whisker_min, whisker_max)
