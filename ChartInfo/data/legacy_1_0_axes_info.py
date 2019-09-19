

from .tick_info import TickInfo

class LegacyAxesInfo:
    def __init__(self, tick_labels, axes_titles):
        self.tick_labels = {text.id: text for text in tick_labels}
        self.axes_titles = {text.id: text for text in axes_titles}

        # handle all axis info (2 axis by default)

        # bounding box (x1, y1, x2, y2)
        self.bounding_box = None

        # lists of TickInfo sorted by their position value
        self.x_ticks = None
        self.y_ticks = None

        # divided tick labels ... (un-sorted lists of text ids)
        self.x_labels = None
        self.y_labels = None

        # the titles .. (text_id, int)
        self.x_title = None
        self.y_title = None

    def is_complete(self):
        if (self.bounding_box is None or
            self.x_ticks is None or self.y_ticks is None or
            self.x_labels is None or self.y_labels is None):
            return False

        return True

    def get_x_axis_labels(self):
        if self.x_labels is None:
            return []

        # get x_axis labels sorted from left to right ...
        tempo_sorted = []
        for text_id in self.x_labels:
            text_label = self.tick_labels[text_id]
            cx, cy = text_label.get_center()
            tempo_sorted.append((cx, text_label))

        tempo_sorted = sorted(tempo_sorted, key=lambda x:x[0])

        return [text_label for cx, text_label in tempo_sorted]

    def get_y_axis_labels(self):
        if self.y_labels is None:
            return []

        # get x_axis labels sorted from left to right ...
        tempo_sorted = []
        for text_id in self.y_labels:
            text_label = self.tick_labels[text_id]
            cx, cy = text_label.get_center()
            tempo_sorted.append((cy, text_label))

        tempo_sorted = sorted(tempo_sorted, key=lambda x: x[0])

        return [text_label for cy, text_label in tempo_sorted]

    def to_XML(self, indent=""):
        xml_str = indent + "<Axes>\n"

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

        # absolute points ... (sorted lists)
        if self.x_ticks is not None:
            xml_str += indent + "    <TicksX>\n"
            for tick_info in self.x_ticks:
                xml_str += tick_info.to_XML(indent + "        ")
            xml_str += indent + "    </TicksX>\n"

        if self.y_ticks is not None:
            xml_str += indent + "    <TicksY>\n"
            for tick_info in self.y_ticks:
                xml_str += tick_info.to_XML(indent + "        ")
            xml_str += indent + "    </TicksY>\n"

        if self.x_title is not None:
            xml_str += indent + "    <TitleX>{0:d}</TitleX>\n".format(self.x_title)
        if self.y_title is not None:
            xml_str += indent + "    <TitleY>{0:d}</TitleY>\n".format(self.y_title)

        # divided tick labels ... (un-sorted lists of text ids)
        if self.x_labels is not None:
            xml_str += indent + "    <LabelsX>\n"
            for text_id in self.x_labels:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(text_id)
            xml_str += indent + "    </LabelsX>\n"

        if self.y_labels is not None:
            xml_str += indent + "    <LabelsY>\n"
            for text_id in self.y_labels:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(text_id)
            xml_str += indent + "    </LabelsY>\n"

        xml_str += indent + "</Axes>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root, tick_labels, title_labels):
        # assume XML root = Axes
        info = LegacyAxesInfo(tick_labels, title_labels)

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

        # tick points (and labels)
        xml_ticks_x = xml_root.find("TicksX")
        if xml_ticks_x is not None:
            info.x_ticks = []
            for xml_tick in xml_ticks_x.findall("TickInfo"):
                tick = TickInfo.FromXML(xml_tick)
                info.x_ticks.append(tick)

        xml_ticks_y = xml_root.find("TicksY")
        if xml_ticks_y is not None:
            info.y_ticks = []
            for xml_tick in xml_ticks_y.findall("TickInfo"):
                tick = TickInfo.FromXML(xml_tick)
                info.y_ticks.append(tick)

        xml_x_title = xml_root.find("TitleX")
        if xml_x_title is not None:
            info.x_title = int(xml_x_title.text)

        xml_y_title = xml_root.find("TitleY")
        if xml_y_title is not None:
            info.y_title = int(xml_y_title.text)

        # divided tick labels ... (un-sorted lists of text ids)
        xml_labels_x = xml_root.find("LabelsX")
        if xml_labels_x is not None:
            info.x_labels = []
            for xml_text_id in xml_labels_x.findall("TextId"):
                text_id = int(xml_text_id.text)
                info.x_labels.append(text_id)

        xml_labels_y = xml_root.find("LabelsY")
        if xml_labels_y is not None:
            info.y_labels = []
            for xml_text_id in xml_labels_y.findall("TextId"):
                text_id = int(xml_text_id.text)
                info.y_labels.append(text_id)

        return info

    @staticmethod
    def Copy(other):
        assert isinstance(other, LegacyAxesInfo)

        copy_tick_labels = [other.tick_labels[text_id] for text_id in other.tick_labels]
        copy_titles_labels = [other.axes_titles[text_id] for text_id in other.axes_titles]
        info = LegacyAxesInfo(copy_tick_labels, copy_titles_labels)

        info.bounding_box = other.bounding_box
        info.x_title = other.x_title
        info.y_title = other.y_title

        # axis - ticks ....
        if other.x_ticks is not None:
            info.x_ticks = [TickInfo.Copy(tick) for tick in other.x_ticks]
        if other.y_ticks is not None:
            info.y_ticks = [TickInfo.Copy(tick) for tick in other.y_ticks]

        # axis - labels ....
        if other.x_labels is not None:
            info.x_labels = list(other.x_labels)
        if other.y_labels is not None:
            info.y_labels = list(other.y_labels)

        return info
