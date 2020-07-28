
import os

from ChartInfo.data.image_info import ImageInfo

class FileStats:
    def __init__(self, img_dir, annotation_dir, cache_all_annotations=False, load_stats=True):

        self.img_dir = img_dir
        self.annotation_dir = annotation_dir

        # Load image list from dir ...
        self.img_list = []

        self.total_annotation_files = 0
        self.auto_check_stats = None

        self.img_annotations = []
        self.cache_annotations = []
        self.img_statuses = []

        self.all_single_panel = []
        self.all_multi_panel = []
        self.single_per_type = {}

        if load_stats:
            self.__load_data(cache_all_annotations)

    def __load_data(self, cache_all_annotations):
        # Load image list from dir ...
        self.img_list = ImageInfo.ListChartDirectory(self.img_dir, "")
        self.auto_check_stats = {
            "total_no_annotation": 0,
            "total_multi_panel": 0,
            "total_no_test": 0,
            "total_passed": 0,
            "total_failed": 0,
        }

        for idx, chart_path in enumerate(self.img_list):
            current_img = None

            # find annotation path ...
            relative_dir, img_filename = os.path.split(chart_path)

            img_base, ext = os.path.splitext(img_filename)
            # output dir
            output_dir = self.annotation_dir + relative_dir
            annotation_filename = output_dir + "/" + img_base + ".xml"

            if os.path.exists(annotation_filename):
                self.img_annotations.append(annotation_filename)
                self.total_annotation_files += 1

                image_info = ImageInfo.FromXML(annotation_filename, current_img)
                if len(image_info.panels) == 1:
                    # add to single panel index
                    self.all_single_panel.append(idx)

                    type_desc, orientation = image_info.panels[0].get_description()
                    if orientation == "":
                        current_type = type_desc
                    else:
                        current_type = "{0:s} ({1:s})".format(type_desc, orientation)
                    # if type_desc in ["non-chart"]:
                    #     print(annotation_filename)

                    status_ints = ImageInfo.GetAllStatuses(image_info)
                    self.img_statuses.append(status_ints)

                    if current_type in self.single_per_type:
                        self.single_per_type[current_type].append((idx, status_ints))
                    else:
                        self.single_per_type[current_type] = [(idx, status_ints)]

                    if not "auto_check_passed" in image_info.panels[0].properties:
                        self.auto_check_stats["total_no_test"] += 1
                    else:
                        if int(image_info.panels[0].properties["auto_check_passed"]) > 0:
                            self.auto_check_stats["total_passed"] += 1
                        else:
                            self.auto_check_stats["total_failed"] += 1
                else:
                    # add to multi-panel index
                    self.all_multi_panel.append(idx)
                    # TODO: multi-panel case is not handled yet ...

                    self.img_statuses.append(None)
                    self.auto_check_stats["total_multi_panel"] += 1

                # keep or discard the current annotation ...
                if cache_all_annotations:
                    self.cache_annotations.append(image_info)
                else:
                    self.cache_annotations.append(None)
            else:
                self.img_annotations.append(None)
                self.cache_annotations.append(None)
                self.img_statuses.append(ImageInfo.GetNullStatuses())
                self.auto_check_stats["total_no_annotation"] += 1

    def total_images(self):
        return len(self.img_list)

    def total_single_panel(self):
        return len(self.all_single_panel)

    def get_autocheck_stats(self):
        return self.auto_check_stats

    def total_multi_panel(self):
        return len(self.all_multi_panel)

    def single_types_found(self):
        return list(self.single_per_type.keys())

    def summarize_single_type_statuses(self, min_status):
        all_per_type = {}
        totals = [0] * 6
        for current_type in self.single_per_type:
            all_per_type[current_type] = [0] * 6
            # for each chart with annotation
            for offset, (idx, status_ints) in enumerate(self.single_per_type[current_type]):
                # check each status ...
                for status_idx in range(6):
                    # only if above threshold ...
                    if status_ints[status_idx] >= min_status:
                        # count ...
                        all_per_type[current_type][status_idx] += 1
                        totals[status_idx] += 1

        return all_per_type, totals

    def sample_single_type_by_min_statuses(self, min_statuses):
        valid_idxs = []
        # for each chart type ...
        for current_type in self.single_per_type:
            # for each chart in current type ...
            for idx, status_ints in self.single_per_type[current_type]:
                # check if valid ...
                valid = True
                # for all statues
                for status_idx in range(len(min_statuses)):
                    # check ...
                    if status_ints[status_idx] < min_statuses[status_idx]:
                        # given status is below current threshold ...
                        valid = False
                        break

                if valid:
                    # add to sample ...
                    valid_idxs.append(idx)

        return valid_idxs

    def print_general_stats(self):
        # print info ...
        print("Total Raw Images: {0:d}".format(self.total_images()))
        print("Total Images with Annotation: {0:d}".format(self.total_annotation_files))
        print("\nTotal Multi Panel: {0:d}".format(self.total_multi_panel()))
        print("Total Single Panel: {0:d}".format(self.total_single_panel()))
        print("Total Single Panel Types Found: {0:d}".format(len(self.single_types_found())))

    def print_autocheck_stats(self):
        # print
        autocheck_stats = self.get_autocheck_stats()
        print("Total Images Without Annotations: {0:d}".format(autocheck_stats["total_no_annotation"]))
        print("Total Multi-panel Images: {0:d}".format(autocheck_stats["total_multi_panel"]))
        print("Total Single-panel without Test: {0:d}".format(autocheck_stats["total_no_test"]))
        print("Total Single-panel with Failed Tested: {0:d}".format(autocheck_stats["total_failed"]))
        print("Total Single-panel with Passed Tested: {0:d}".format(autocheck_stats["total_passed"]))

    def print_single_panel_annotated_stats(self, validated):
        if validated:
            print("Single Panel Images (Annotated & Validated)")
        else:
            print("Single Panel Images (Annotated)")

        print("Type\tPan\tClass\tText\tLgnd\tAxis\tData")

        summary, totals = self.summarize_single_type_statuses(2 if validated else 1)
        for current_type in sorted(list(summary.keys())):
            print("{0:s}\t{1:s}".format(current_type, "\t".join([str(val) for val in summary[current_type]])))

        print("{0:s}\t{1:s}".format("ALL", "\t".join([str(val) for val in totals])))

    def get_annotation_index(self):
        annotation_index = {}

        for idx, chart_path in enumerate(self.img_list):
            # find annotation path ...
            relative_dir, img_filename = os.path.split(chart_path)
            img_base, ext = os.path.splitext(img_filename)

            if self.img_annotations[idx] is not None:
                annotation_index[img_base] = idx
            else:
                annotation_index[img_base] = None

        return annotation_index

    def find_common_annotations(self, other):
        assert isinstance(other, FileStats)

        local_index = self.get_annotation_index()
        other_index = other.get_annotation_index()

        common_keys = sorted(list(set(local_index.keys()).intersection(set(other_index.keys()))))

        return [(shared_key, local_index[shared_key], other_index[shared_key]) for shared_key in common_keys]

    @staticmethod
    def Merge(stat_list):
        if len(stat_list) == 1:
            # ... nothing to merge ...
            return stat_list[0]

        img_dir = ""
        annot_dir = ""
        offset_idx = 0
        all_img_list = []
        all_annotations_file_list = []
        total_annotation_files = 0
        full_cache_annotations = []
        full_img_statuses = []
        full_single_panel = []
        full_multi_panel = []
        full_single_per_type = {}
        full_check_stats = {
            "total_no_annotation": 0,
            "total_multi_panel": 0,
            "total_no_test": 0,
            "total_passed": 0,
            "total_failed": 0,
        }

        for file_stats in stat_list:
            # expand image filenames ...
            for img_filename in file_stats.img_list:
                all_img_list.append(file_stats.img_dir + img_filename)

            # update relative idxs
            full_single_panel += [offset_idx + original_idx for original_idx in file_stats.all_single_panel]
            full_multi_panel += [offset_idx + original_idx for original_idx in file_stats.all_multi_panel]

            for chart_type in file_stats.single_per_type:
                if not chart_type in full_single_per_type:
                    # first time seeing this chart type, create empty list ...
                    full_single_per_type[chart_type] = []

                # update relative indices ...
                new_spt = [(offset_idx + o_idx, status) for o_idx, status in file_stats.single_per_type[chart_type]]
                # add updated list ...
                full_single_per_type[chart_type] += new_spt

            # add up other list whose member do not need to be modified
            all_annotations_file_list += file_stats.img_annotations
            full_cache_annotations += file_stats.cache_annotations
            full_img_statuses += file_stats.img_statuses

            # add up stats
            total_annotation_files += file_stats.total_annotation_files
            full_check_stats["total_no_annotation"] += file_stats.auto_check_stats["total_no_annotation"]
            full_check_stats["total_multi_panel"] += file_stats.auto_check_stats["total_multi_panel"]
            full_check_stats["total_no_test"] += file_stats.auto_check_stats["total_no_test"]
            full_check_stats["total_passed"] += file_stats.auto_check_stats["total_passed"]
            full_check_stats["total_failed"] += file_stats.auto_check_stats["total_failed"]

            offset_idx += len(file_stats.img_list)

        merged = FileStats(img_dir, annot_dir, False, False)
        merged.img_list = all_img_list
        merged.total_annotation_files = total_annotation_files
        merged.img_annotations = all_annotations_file_list
        merged.cache_annotations = full_cache_annotations
        merged.img_statuses = full_img_statuses
        merged.all_single_panel = full_single_panel
        merged.all_multi_panel = full_multi_panel
        merged.single_per_type = full_single_per_type

        return merged




