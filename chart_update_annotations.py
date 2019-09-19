
import os
import sys
import shutil

from AM_CommonTools.configuration.configuration import Configuration

from ChartInfo.util.file_stats import FileStats
from ChartInfo.data.image_info import ImageInfo



def load_stats(config_filename):
    config = Configuration.from_file(config_filename)

    charts_dir = config.get_str("CHART_DIRECTORY")
    annotations_dir = config.get_str("CHART_ANNOTATIONS")

    stats = FileStats(charts_dir, annotations_dir)

    return stats


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("")
        print("python chart_update_annotations.py src_config dst_config")
        print("")
        print("Where")
        print("\tsrc_config\tSource Configuration (newer annotations)")
        print("\tdst_config\tDestination Configuration (annotations to update)")
        return

    #  Load and show general statistics ....
    config1_filename = sys.argv[1]
    config2_filename = sys.argv[2]

    stats1 = load_stats(config1_filename)
    stats2 = load_stats(config2_filename)

    print("Source Info ({0:s})".format(config1_filename))
    stats1.print_general_stats()

    print("")
    print("Destination Info ({0:s})".format(config2_filename))
    stats2.print_general_stats()

    # Find matching files which might be overwritten ...
    common_annotations = stats1.find_common_annotations(stats2)

    print("")
    print("A total of {0:d} shared images were found".format(len(common_annotations)))

    count_src_null = 0
    count_newer = 0
    count_higher = 0
    for base_name, src_idx, dst_idx in common_annotations:
        if src_idx is None:
            # common image with no annotation at source ... skip ...
            count_src_null += 1
            continue

        dst_status = stats2.img_statuses[dst_idx]

        # check if destination does not have annotations for this file or
        #       if the status of the file at source is absolute higher than file at destination ...
        if dst_idx is None or ImageInfo.CheckNewerStatus(dst_status, stats1.img_statuses[src_idx]):
            # source is newer (or destination is inexistent) .. must replace file in destination ...
            count_newer += 1

            src_filename = stats1.img_annotations[src_idx]
            dst_filename = stats2.img_annotations[dst_idx]

            print("Replacing: {0:s}".format(base_name))
            shutil.copy(src_filename, dst_filename)
        else:
            count_higher += 1
            print("Higher Status at Destination: {0:s}".format(base_name))

    print("")
    print("A total of ...")
    print(" - {0:d} images had no annotation at source".format(count_src_null))
    print(" - {0:d} images were replaced at destination".format(count_newer))
    print(" - {0:d} images were not modified at destination".format(count_higher))





if __name__ == '__main__':
    main()
