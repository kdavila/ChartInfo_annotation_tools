
class TickInfo:
    def __init__(self, position, label_id=None):
        self.position = position
        self.label_id = label_id

    def to_XML(self, indent=""):
        xml_str = indent + "<TickInfo>\n"
        xml_str += indent + "    <Position>{0:s}</Position>\n".format(str(self.position))
        if self.label_id is not None:
            xml_str += indent + "    <LabelId>{0:d}</LabelId>\n".format(self.label_id)
        xml_str += indent + "</TickInfo>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assume xml_root = TickInfo
        position = float(xml_root.find("Position").text)

        xml_label_id = xml_root.find("LabelId")
        if xml_label_id is None:
            label_id = None
        else:
            label_id = int(xml_root.find("LabelId").text)

        return TickInfo(position, label_id)

    @staticmethod
    def Copy(other):
        assert isinstance(other, TickInfo)

        return TickInfo(other.position, other.label_id)
