
import os

import xml.etree.ElementTree as ET

from .panel_tree import PanelTree
from .chart_info import ChartInfo

class ImageInfo:
    def __init__(self, image):
        self.image = image
        self.panel_tree = None
        # a list of Chart Info objects
        self.panels = []

        self.properties = {}

    def reset_panels_info(self):
        current_panels = self.panel_tree.root.get_leaves()
        self.panels = [ChartInfo(ChartInfo.TypeNonChart) for panel in current_panels]

    def get_panel_image(self, panel_idx):
        # panel boundaries ...
        panel_nodes = self.panel_tree.root.get_leaves()
        panel_node = panel_nodes[panel_idx]

        return self.image[panel_node.y1:panel_node.y2 + 1, panel_node.x1:panel_node.x2 + 1].copy()


    def check_classes(self):
        # check if all panels have been labeled ...
        all_scores = []
        for chart_info in self.panels:
            all_scores.append(chart_info.check_classes())

        return min(all_scores)

    def check_text(self):
        # check if all panels have been labeled ...
        all_scores = []
        for chart_info in self.panels:
            all_scores.append(chart_info.check_text())

        return min(all_scores)

    def check_legend(self):
        # check if all panels have been labeled ...
        all_scores = []
        for chart_info in self.panels:
            all_scores.append(chart_info.check_legend())

        return min(all_scores)

    def check_axes(self):
        # check if all panels have been labeled ...
        all_scores = []
        for chart_info in self.panels:
            all_scores.append(chart_info.check_axes())

        return min(all_scores)

    def check_data(self):
        # check if all panels have been labeled ...
        all_scores = []
        for chart_info in self.panels:
            all_scores.append(chart_info.check_data())

        return min(all_scores)

    def to_XML(self):
        xml_str = "<ImageInfo>\n"

        xml_str += self.panel_tree.to_XML()
        xml_str += "    <Panels>\n"
        for panel in self.panels:
            xml_str += panel.to_XML("        ")
        xml_str += "    </Panels>\n"

        if len(self.properties) > 0:
            xml_str += '    <Properties>\n'
            for key in self.properties:
                xml_str += '        <{0:s}>{1:s}</{0:s}>\n'.format(key, str(self.properties[key]))
            xml_str += '    </Properties>\n'

        xml_str += "</ImageInfo>\n"
        return xml_str

    @staticmethod
    def FromXML(filename, image):
        try:
            tree = ET.parse(filename)
        except:
            raise Exception("Could not parse the file: " + filename)

        root = tree.getroot()  # ProjectionAnnotations

        info = ImageInfo(image)

        # load panel tree ....
        xml_panel_tree = root.find("PanelTree")
        info.panel_tree = PanelTree.FromXML(xml_panel_tree)

        # load panels ....
        xml_panels_root = root.find("Panels")
        for xml_panel in xml_panels_root:
            chart_info = ChartInfo.FromXML(xml_panel)
            info.panels.append(chart_info)

        # load properties (if any)
        xml_properties_root = root.find("Properties")
        if xml_properties_root is not None:
            for xml_property in xml_properties_root:
                info.properties[xml_property.tag] = xml_property.text

        return info

    @staticmethod
    def CreateDefault(image):
        info = ImageInfo(image)
        info.panel_tree = PanelTree.FromImage(image)

        panel_info = ChartInfo(ChartInfo.TypeNonChart)
        info.panels.append(panel_info)

        return info

    @staticmethod
    def ListChartDirectory(main_input_dir, rel_path):
        elements = os.listdir(main_input_dir + rel_path)

        results = []
        for element in elements:
            element_path = main_input_dir + rel_path + "/" + element

            if os.path.isdir(element_path):
                # call recursively
                results += ImageInfo.ListChartDirectory(main_input_dir, rel_path + "/" + element)
            else:
                # is a file ... check ...
                base, ext = os.path.splitext(element_path)
                if ext.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:
                    results.append(rel_path + "/" + element)

        return results

    @staticmethod
    def GetAllStatuses(image_info):
        status_ints = ImageInfo.GetNullStatuses()

        if image_info is None:
            return status_ints
        else:
            assert isinstance(image_info, ImageInfo)

        status_ints[0] = 2 if "VERIFIED_01_PANELS" in image_info.properties else 1
        status_ints[1] = image_info.check_classes()
        status_ints[2] = image_info.check_text()
        status_ints[3] = image_info.check_legend()
        status_ints[4] = image_info.check_axes()
        status_ints[5] = image_info.check_data()

        return status_ints

    @staticmethod
    def GetNullStatuses():
        return [0] * 6

    @staticmethod
    def CheckNewerStatus(original_status, other_status):
        newer = True
        for idx in range(len(original_status)):
            if original_status[idx] > other_status[idx]:
                newer = False
                break

        return newer