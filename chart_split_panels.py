
import os
import sys

import cv2

from AM_CommonTools.configuration.configuration import Configuration

from ChartInfo.data.image_info import ImageInfo
from ChartInfo.data.chart_info import ChartInfo

def split_dir_annotations(in_img_dir, in_annot_dir, out_img_dir, out_annot_dir, rel_path):
    input_dir = in_annot_dir + rel_path
    elements = os.listdir(input_dir)

    panels_per_type = {}
    for element in elements:
        element_path = input_dir + element

        if os.path.isdir(element_path):
            sub_dir_stats = split_dir_annotations(in_img_dir, in_annot_dir, out_img_dir, out_annot_dir, element_path + "/")

            # add stats
            for chart_type in sub_dir_stats:
                if chart_type in panels_per_type:
                    # already collected this type ...
                    panels_per_type[chart_type] += sub_dir_stats[chart_type]
                else:
                    # first of this type
                    panels_per_type[chart_type] = sub_dir_stats[chart_type]
        else:
            print("Processing: " + element_path)

            # load the corresponding image
            base, ext = os.path.splitext(element)
            img_path = in_img_dir + rel_path + base + ".jpg"
            current_img = cv2.imread(img_path)

            # load the annotation
            image_info = ImageInfo.FromXML(element_path, current_img)

            # For each panel ....
            for panel_idx, panel in enumerate(image_info.panels):
                type_str, orientation_str = panel.get_description()
                chart_type = type_str + "_" + orientation_str

                if chart_type in panels_per_type:
                    panels_per_type[chart_type] += 1
                else:
                    panels_per_type[chart_type] = 1

                # if the panel is non-chart, then skip
                if panel.type == ChartInfo.TypeNonChart:
                    continue

                # crop the panel from main image
                panel_img = image_info.get_panel_image(panel_idx)

                # Save panel image to output image directory
                os.makedirs(out_img_dir + "/" + chart_type + rel_path, exist_ok=True)
                out_img_panel_path = out_img_dir + "/" + chart_type + rel_path + base + "_panel_" + str(panel_idx + 1) + ".jpg"
                cv2.imwrite(out_img_panel_path, panel_img)

                # Create a new annotation structure ... only for that panel
                panel_annotation = ImageInfo.CreateDefault(panel_img)
                panel_annotation.panels[0] = panel

                # Save panel annotation to output image directory
                os.makedirs(out_annot_dir  + "/" + chart_type + rel_path, exist_ok=True)
                out_panel_annotation = out_annot_dir  + "/" + chart_type + rel_path + base + "_panel_" + str(panel_idx + 1) + ".xml"
                tempo_xml = panel_annotation.to_XML()
                with open(out_panel_annotation, "w") as out_annot_file:
                    out_annot_file.write(tempo_xml)


    return panels_per_type

def main():
    if len(sys.argv) < 3:
        print("Usage: python chart_annotator.py src_config dst_config")
        print("Where")
        print("\tsrc_config\t= Configuration File for input images/annotations")
        print("\tdst_config\t= Configuration File for output images/annotations")
        return

    in_config_filename = sys.argv[1]
    out_config_filename = sys.argv[2]

    if not os.path.exists(in_config_filename):
        print("Invalid input config file / path")
        return

    if not os.path.exists(out_config_filename):
        print("Invalid output config file / path")
        return

    in_config = Configuration.from_file(in_config_filename)
    out_config = Configuration.from_file(out_config_filename)

    in_charts_dir = in_config.get_str("CHART_DIRECTORY")
    in_annotations_dir = in_config.get_str("CHART_ANNOTATIONS")

    out_charts_dir = out_config.get_str("CHART_DIRECTORY")
    out_annotations_dir = out_config.get_str("CHART_ANNOTATIONS")

    stats_per_type = split_dir_annotations(in_charts_dir, in_annotations_dir, out_charts_dir, out_annotations_dir, "/")

    # print stats ...
    for chart_type in stats_per_type:
        print("{0:s}\t{1:d}".format(chart_type, stats_per_type[chart_type]))

if __name__ == "__main__":
    main()

