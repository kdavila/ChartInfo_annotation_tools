
import sys

from AM_CommonTools.configuration.configuration import Configuration

# from ChartInfo.data.image_info import ImageInfo
from ChartInfo.util.file_stats import FileStats

def main():
    if len(sys.argv) < 2:
        print("Usage: python chart_stats.py config [config2] [...]")
        print("Where")
        print("\tconfig\t= Configuration File")
        print("")
        return

    all_stats = []

    for config_filename in sys.argv[1:]:
        print("Processing: " + config_filename, flush=True)
        config = Configuration.from_file(config_filename)

        charts_dir = config.get_str("CHART_DIRECTORY")
        annotations_dir = config.get_str("CHART_ANNOTATIONS")

        stats = FileStats(charts_dir, annotations_dir)
        all_stats.append(stats)

    stats = FileStats.Merge(all_stats)

    print("")
    stats.print_general_stats()

    print("")
    stats.print_single_panel_annotated_stats(False)

    print("")
    stats.print_single_panel_annotated_stats(True)

    print("")
    stats.print_autocheck_stats()

if __name__ == "__main__":
    main()
