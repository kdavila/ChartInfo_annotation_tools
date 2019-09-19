
from .tick_info import TickInfo

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

    def has_label(self, text_id):
        if self.labels is not None:
            return text_id in self.labels
        else:
            # the axis has no labels ...
            return False

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

