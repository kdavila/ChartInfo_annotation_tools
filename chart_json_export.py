import os
import sys
import json

from AM_CommonTools.configuration.configuration import Configuration
from ChartInfo.util.file_stats import FileStats
from ChartInfo.util.json_exporter import ChartJSON_Exporter

def prepare_json(img_folder, xml_folder, json_folder, task_num=1, mask_output=True):
    print("\n\nLoading annotations from " + xml_folder)
    stats = FileStats(img_folder, xml_folder, True)

    os.makedirs(json_folder, exist_ok=True)

    collected_errors = []
    for img_idx, img_file in enumerate(stats.img_list):
        print("Preparing JSON for " + img_file)

        img_info = stats.cache_annotations[img_idx]
        img_status = stats.img_statuses[img_idx]
        if len(img_info.panels) > 1:
            print("\tWarning: the image has multiple panels! Skipping!")
            continue

        chart_info = img_info.panels[0]

        # prepare_chart_image_json(img_file, chart_info, img_status, task_num, mask_output, json_folder)
        # x = 0 / 0
        try:
            json_output = ChartJSON_Exporter.prepare_chart_image_json(chart_info, img_status, task_num, mask_output)
            ChartJSON_Exporter.SaveChartImageJSON(json_output, img_file, json_folder)
        except Exception as e:
            print("- Exception found! ")
            print(e)

            # try falling back to produce GT for lower tasks only ...
            if not mask_output:
                tempo_task_num = task_num - 1
                success = False
                while tempo_task_num > 1 and not success:
                    try:
                        json_output = ChartJSON_Exporter.prepare_chart_image_json(chart_info, img_status,
                                                                                  tempo_task_num, mask_output)
                        ChartJSON_Exporter.SaveChartImageJSON(json_output, img_file, json_folder)
                        success = True
                    except:
                        # try previous task ...
                        tempo_task_num -= 1

            else:
                # cannot fall back to previous task if using the testing set mode
                tempo_task_num = 0

            collected_errors.append("{0:s}\t{1:s}\tExported Task {2:d}\n".format(img_file, str(e), tempo_task_num))

    if len(collected_errors) > 0:
        error_output_filename = "EXPORT_ERRORS.CSV"
        with open(error_output_filename, "a") as out_file:
            out_file.writelines(collected_errors)

        print("Saved all errors found to " + error_output_filename)

def main():
    if len(sys.argv) < 2:
        print('Usage: python chart_json_export.py config [json_folder] [task_num] [test_mode]')
        return

    config_filename = sys.argv[1]
    config = Configuration.from_file(config_filename)

    charts_dir = config.get_str("CHART_DIRECTORY")
    annotations_dir = config.get_str("CHART_ANNOTATIONS")

    if len(sys.argv) >= 3:
        # override json_folder
        json_dir = sys.argv[2]
    else:
        # use config with default output dir.
        json_dir = config.get_str("CHART_JSON_EXPORT_DIR", "export_JSON")

    if len(sys.argv) >= 4:
        # override task number ..
        task_num = int(sys.argv[3])
    else:
        # use config with default task number
        task_num = config.get_int("CHART_JSON_EXPORT_TASK", 7)

    if len(sys.argv) >= 5:
        # override test mode
        test_mode = int(sys.argv[4]) >= 1
    else:
        # use config with default mode: not testing
        test_mode = config.get_bool("CHART_JSON_EXPORT_TEST_MODE", False)

    print("Chart Images Directory: " + charts_dir)
    print("Input XML Annotations Directory: " + annotations_dir)
    print("Output JSON Annotation Directory: " + json_dir)
    print("Task to export in JSON Format: " + str(task_num))
    print("Export Mode: " + ("Testing" if test_mode else "Training"))

    prepare_json(charts_dir, annotations_dir, json_dir, task_num, test_mode)

if __name__ == '__main__':
    main()


