
import numpy as np

# from shapely.geometry import Point

from .text_info import TextInfo

class LegendInfo:
    OrientationMixed = 0
    OrientationHorizontal = 1
    OrientationVertical = 2

    def __init__(self, text_labels):
        # of class TextInfo
        self.text_labels = text_labels
        # Numpy representing the four corners of the data marker for each textInfo key (id)
        self.marker_per_label = {text_info.id: None for text_info in text_labels}

    def is_complete(self):
        # check if all markers have been labeled
        for text_id in self.marker_per_label:
            if self.marker_per_label[text_id] is None:
                # an un-labeled marker is found
                return False

        # no un-labeled markers found, assume it is complete
        return True

    def get_marker_median_color(self, panel_img, entry_id):
        if entry_id is None or not entry_id in self.marker_per_label:
            return None

        marker = self.marker_per_label[entry_id]
        marker_min_x, marker_max_x = int(marker[:, 0].min()), int(marker[:, 0].max())
        marker_min_y, marker_max_y = int(marker[:, 1].min()), int(marker[:, 1].max())

        marker_img = panel_img[marker_min_y:marker_max_y, marker_min_x:marker_max_x]
        marker_median_r = np.median(marker_img[:, :, 0])
        marker_median_g = np.median(marker_img[:, :, 1])
        marker_median_b = np.median(marker_img[:, :, 2])

        return marker_median_r, marker_median_g, marker_median_b

    def get_legend_orientation(self):
        if len(self.text_labels) <= 1:
            # by default ...
            return LegendInfo.OrientationVertical

        # afterwards the following test only one of these can remain true
        all_overlap_on_x = True
        all_overlap_on_y = True
        # do all pai-rwaise range comparisons
        for idx_1, text_1 in enumerate(self.text_labels[:-1]):
            txt_1_min_x, txt_1_min_y, txt_1_max_x, txt_1_max_y = text_1.get_axis_aligned_rectangle()

            for text_2 in self.text_labels[idx_1 + 1:]:
                txt_2_min_x, txt_2_min_y, txt_2_max_x, txt_2_max_y = text_2.get_axis_aligned_rectangle()

                # do the overlap test ...
                # ... on x ...
                if not (txt_1_min_x < txt_2_max_x and txt_2_min_x < txt_1_max_x):
                    all_overlap_on_x = False
                # ... on y ...
                if not (txt_1_min_y < txt_2_max_y and txt_2_min_y < txt_1_max_y):
                    all_overlap_on_y = False

                # it only takes one counter example to conclude the test ...
                if not (all_overlap_on_x or all_overlap_on_y):
                    break

        if all_overlap_on_x:
            return LegendInfo.OrientationVertical
        elif all_overlap_on_y:
            return LegendInfo.OrientationHorizontal
        else:
            return LegendInfo.OrientationMixed

        """
        all_x_dists = []
        all_y_dists = []
        for idx_1, text_1 in enumerate(self.text_labels):
            cx_1, cy_1 = text_1.get_center()

            for idx_2, text_2 in enumerate(self.text_labels):
                if idx_1 != idx_2:
                    cx_2, cy_2 = text_2.get_center()

                    all_x_dists.append(abs(cx_1 - cx_2))
                    all_y_dists.append(abs(cy_1 - cy_2))

        if np.mean(all_x_dists) < np.mean(all_y_dists):
            # larger vertical distances ...
            return LegendInfo.OrientationVertical
        else:
            # larger horizontal distances ...
            return LegendInfo.OrientationHorizontal
        """

    def get_data_series(self):
        # first, determine the orientation of the text labels ...
        orientation = self.get_legend_orientation()

        all_sorted = []
        for idx, text in enumerate(self.text_labels):
            cx, cy = text.get_center()
            if orientation == LegendInfo.OrientationHorizontal:
                # use X
                all_sorted.append((cx, text))
            else:
                # use Y
                all_sorted.append((cy, text))

        all_sorted = sorted(all_sorted, key=lambda x:x[0])

        return [text for val, text in all_sorted]

    def to_XML(self, indent=""):
        xml_str = indent + "<Legend>\n"
        for text_id in sorted(list(self.marker_per_label.keys())):
            xml_str += indent + "    <MarkPerLabel>\n"
            xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(text_id)
            if self.marker_per_label[text_id] is not None:
                xml_str += indent + "        <Polygon>\n"
                for x, y in self.marker_per_label[text_id]:
                    xml_str += indent + "            <Point>\n"
                    xml_str += indent + "                <X>{0:s}</X>\n".format(str(x))
                    xml_str += indent + "                <Y>{0:s}</Y>\n".format(str(y))
                    xml_str += indent + "            </Point>\n"
                xml_str += indent + "        </Polygon>\n"
            xml_str += indent + "    </MarkPerLabel>\n"
        xml_str += indent + "</Legend>\n"

        return xml_str

    @staticmethod
    def FromXML(xml_root, text_labels):
        # assume xml_root is <Legend>
        info = LegendInfo(text_labels)

        for xml_marker_label in xml_root:
            # <MarkPerLabel> element
            text_id = int(xml_marker_label.find("TextId").text)

            if not text_id in info.marker_per_label:
                raise Exception("Reference to invalid text Id found in legend!")

            # check if it has associated polygon
            xml_polygon = xml_marker_label.find("Polygon")
            if xml_polygon is not None:
                # read polygon data ....
                polygon_points = []
                for xml_point in xml_polygon:
                    point_x = float(xml_point.find("X").text)
                    point_y = float(xml_point.find("Y").text)

                    polygon_points.append([point_x, point_y])

                info.marker_per_label[text_id] = np.array(polygon_points)

        return info

    @staticmethod
    def Copy(other):
        assert isinstance(other, LegendInfo)

        info = LegendInfo([TextInfo.Copy(text) for text in other.text_labels])
        for key in other.marker_per_label:
            info.marker_per_label[key] = other.marker_per_label[key]

        return info
