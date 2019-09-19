
import sys

from AM_CommonTools.configuration.configuration import Configuration

# from ChartInfo.data.image_info import ImageInfo
from ChartInfo.util.file_stats import FileStats

def main():
    if len(sys.argv) < 2:
        print("Usage: python chart_stats.py config")
        print("Where")
        print("\tconfig\t= Configuration File")
        print("")
        return

    config_filename = sys.argv[1]
    config = Configuration.from_file(config_filename)

    charts_dir = config.get_str("CHART_DIRECTORY")
    annotations_dir = config.get_str("CHART_ANNOTATIONS")

    stats = FileStats(charts_dir, annotations_dir)

    print("")
    stats.print_general_stats()

    print("")
    stats.print_single_panel_annotated_stats(False)

    print("")
    stats.print_single_panel_annotated_stats(True)


if __name__ == "__main__":
    main()
