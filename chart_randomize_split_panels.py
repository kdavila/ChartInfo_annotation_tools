
import os
import sys
import shutil

from AM_CommonTools.configuration.configuration import Configuration


def collect_annotations(in_image_dir, in_annot_dir, rel_path, out_data):
    elements = os.listdir(in_annot_dir + rel_path)
    for element in elements:
        element_path = in_annot_dir + rel_path + "/" + element
        if os.path.isdir(element_path):
            collect_annotations(in_image_dir, in_annot_dir, rel_path + "/" + element, out_data)
        else:
            base, ext = os.path.splitext(element)

            if ext.lower() == ".xml":
                base_img_id, panel_num = base.split("_panel_")

                if not base_img_id in out_data:
                    out_data[base_img_id] = []

                out_data[base_img_id].append((rel_path, panel_num))


def create_groups(panels_by_fig_id, K):
    # first, sort the figures by decreasing number of panels ...
    all_figure_ids = []
    for base_img_id in panels_by_fig_id:
        num_panels = len(panels_by_fig_id[base_img_id])
        all_figure_ids.append((num_panels, base_img_id))

    all_figure_ids = sorted(all_figure_ids, reverse=True)

    all_groups = [[] for x in range(K)]

    # for each image ...
    for idx, (num_panels, base_img_id) in enumerate(all_figure_ids):
        # for each panel ...
        for panel_idx, (rel_path, panel_num) in enumerate(panels_by_fig_id[base_img_id]):
            all_groups[(idx + panel_idx) % K].append((rel_path, base_img_id, panel_num))

    return all_groups

def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("\tpython {0:s} config_in K config_out".format(sys.argv[0]))
        return

    config_in_filename = sys.argv[1]
    config_out_filename = sys.argv[3]
    try:
        k_groups = int(sys.argv[2])
    except:
        print("invalid value for K")
        return

    if not os.path.exists(config_in_filename):
        print("Invalid input config file / path")
        return

    if not os.path.exists(config_out_filename):
        print("Invalid output config file / path")
        return

    in_config = Configuration.from_file(config_in_filename)
    out_config = Configuration.from_file(config_out_filename)

    in_charts_dir = in_config.get_str("CHART_DIRECTORY")
    in_annotations_dir = in_config.get_str("CHART_ANNOTATIONS")

    out_charts_dir = out_config.get_str("CHART_DIRECTORY")
    out_annotations_dir = out_config.get_str("CHART_ANNOTATIONS")

    # collect per panel annotations and group them by source image
    panel_annotations_by_id = {}
    collect_annotations(in_charts_dir, in_annotations_dir, "/", panel_annotations_by_id)

    # create the groups
    all_groups = create_groups(panel_annotations_by_id, k_groups)

    # for each group
    for group_idx, group in enumerate(all_groups):
        base_group_img_dir = "{0:s}/{1:d}".format(out_charts_dir, group_idx)
        base_group_annot_dir = "{0:s}/{1:d}".format(out_annotations_dir, group_idx)

        print("processing batch {0:d}".format(group_idx + 1))

        for rel_path, base_img_id, panel_num in group:
            # save copy of annotation
            annot_src = in_annotations_dir + rel_path + base_img_id + "_panel_" + panel_num + ".xml"
            annot_dst = base_group_annot_dir + rel_path + base_img_id + "_panel_" + panel_num + ".xml"
            os.makedirs(base_group_annot_dir + rel_path, exist_ok=True)
            shutil.copy(annot_src, annot_dst)

            # save copy of images
            img_src = in_charts_dir + rel_path + base_img_id + "_panel_" + panel_num + ".jpg"
            img_dst = base_group_img_dir + rel_path + base_img_id + "_panel_" + panel_num + ".jpg"
            os.makedirs(base_group_img_dir + rel_path, exist_ok=True)
            shutil.copy(img_src, img_dst)

    print("finished")

if __name__ == "__main__":
    main()
