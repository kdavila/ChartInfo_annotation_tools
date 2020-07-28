
import os
import json

from ChartInfo.data.axis_values import AxisValues
from ChartInfo.data.chart_info import ChartInfo

class ChartJSON_Exporter:
    @staticmethod
    def get_axis_info(axes, axis_values, axis_pos, is_horizontal):
        if axis_values is None:
            # this axes does not exists on this chart
            axis_ticks = []
            tick_type = None
        else:
            # general validations
            if axis_values.has_invalid_assignments():
                raise Exception("Found axis with ticks associated with invalid Labels")

            # check the type of tick ....
            axis_ticks = []
            if axis_values.ticks_type == AxisValues.TicksTypeMarkers:
                tick_type = "markers"

                # Validate ....
                if axis_values.has_unassigned_labels():
                    raise Exception("Found axis with Labels not associated with their corresponding markers")

                # use positions marked by annotators ...
                # only use ticks which have associated tick labels (axis_values.ticks_with_labels())
                for tick_info in axis_values.ticks_with_labels():
                    if is_horizontal:
                        # x1/x2 axes on the original annotations ...
                        # use y1 or y2 position as the fixed y coordinate, and x coordinates change
                        export_tick_info = (tick_info.label_id, tick_info.position, axis_pos)
                    else:
                        # y1/y2 axes on the original annotations ...
                        # use x1 or x2 position as the fixed x coordinate, and y coordinates change
                        export_tick_info = (tick_info.label_id, axis_pos, tick_info.position)

                    axis_ticks.append(export_tick_info)
            else:
                tick_type = "separators"

                # validate
                if axis_values.has_rotated_labels(axes.tick_labels):
                    # cannot have Rotated labels with separator ticks ... they need to be forced as markers
                    # and their ideal correspondence with the axis need to be marked explicitly
                    # because the center of these labels is unlikely to be a good default for tick location.
                    raise Exception(
                        "Found Axis With Rotated Labels and Separator Ticks. Please convert these to Markers")

                # use the centers of the bounding boxes of tick labels instead ... (ignore tick mark annotations)
                for label_id in axis_values.labels:
                    text_label = axes.tick_labels[label_id]
                    cx, cy = text_label.get_center()

                    if is_horizontal:
                        # x1/x2 axes on the original annotations ...
                        # use y1 or y2 position as the fixed y coordinate, and x coordinates change
                        export_tick_info = (label_id, cx, axis_pos)
                    else:
                        # y1/y2 axes on the original annotations ...
                        # use x1 or x2 position as the fixed x coordinate, and y coordinates change
                        export_tick_info = (label_id, axis_pos, cy)

                    axis_ticks.append(export_tick_info)

        return axis_ticks, tick_type

    @staticmethod
    def prepare_axis_ticks(axis):
        axis_ticks = []
        for ID, x, y in axis:
            axis_ticks.append({
                'id': ID,
                'tick_pt': {
                    'x': int(round(x)),
                    'y': int(round(y))
                }
            })

        return axis_ticks

    @staticmethod
    def prepare_task_1(chart_info, test_mode):
        chart_type, orientation = chart_info.get_description()
        if chart_type.lower() in ['box', 'bar', "interval"]:
            json_chart_type = orientation + ' ' + chart_type
        else:
            json_chart_type = chart_type

        task_1 = {"input": {}}
        if not test_mode:
            task_1["name"] = 'Chart Classification'
            task_1["output"] = {'chart_type': json_chart_type}

        return task_1

    @staticmethod
    def prepare_task_2(chart_info, task_1, test_mode, offset=(0, 0)):
        task_2 = {
            'input': {
                'task1_output': task_1['output']
            }
        }

        if not test_mode:
            text_blocks = []
            for text_info in chart_info.text:
                ID = text_info.id

                x1, y1 = text_info.position_polygon[0, :]
                x2, y2 = text_info.position_polygon[1, :]
                x3, y3 = text_info.position_polygon[2, :]
                x4, y4 = text_info.position_polygon[3, :]

                # offset bounding boxes
                text_region = {
                    'id': ID,
                    'text': text_info.value,
                    'polygon': {
                        'x0': int(x1 + offset[0]),
                        'y0': int(y1 + offset[1]),
                        'x1': int(x2 + offset[0]),
                        'y1': int(y2 + offset[1]),
                        'x2': int(x3 + offset[0]),
                        'y2': int(y3 + offset[1]),
                        'x3': int(x4 + offset[0]),
                        'y3': int(y4 + offset[1]),
                    }
                }

                text_blocks.append(text_region)

            task_2["name"] = "Text Detection and Recognition"
            task_2["output"] = {'text_blocks': text_blocks}

        return task_2

    @staticmethod
    def prepare_task_3(chart_info, task_1, task_2, test_mode):
        task_3 = {
            'input': {
                'task1_output': task_1['output'],
                'task2_output': task_2['output'],
            }
        }

        if not test_mode:
            text_roles = []
            for text_info in chart_info.text:
                text_type = text_info.get_type_description()
                if '-' in text_type:
                    text_type = text_type.replace('-', '_')
                text_role = {
                    'id': text_info.id,
                    'role': text_type.lower()
                }
                text_roles.append(text_role)

            task_3['name'] = 'Text Role Classification'
            task_3['output'] = {'text_roles': text_roles}

        return task_3

    @staticmethod
    def prepare_task_4(chart_info, task_1, task_2, test_mode, offset=(0, 0)):
        task_4 = {
            'input': {
                'task1_output': task_1['output'],
                'task2_output': task_2['output']
            }
        }

        if not test_mode:
            x1, y1, x2, y2 = chart_info.axes.bounding_box
            # get the bounding box .... add panel offset (for multi-panel charts)
            plot_bb = {
                'x0': int(round(x1 + offset[0])),
                'y0': int(round(y1 + offset[1])),
                'height': int(round(y2 - y1)),
                'width': int(round(x2 - x1))
            }

            h1_axis, h1_tick_type = ChartJSON_Exporter.get_axis_info(chart_info.axes, chart_info.axes.x1_axis, y2, True)
            h2_axis, h2_tick_type = ChartJSON_Exporter.get_axis_info(chart_info.axes, chart_info.axes.x2_axis, y1, True)
            v1_axis, v1_tick_type = ChartJSON_Exporter.get_axis_info(chart_info.axes, chart_info.axes.y1_axis, x1, True)
            v2_axis, v2_tick_type = ChartJSON_Exporter.get_axis_info(chart_info.axes, chart_info.axes.y2_axis, x2, True)

            # TODO: should there be any special handling when a less common dependent axis is used?
            # ..... for example using Y-2 instead of Y-1 and X-2 instead of X-1 when the common option is empty?

            if chart_info.is_vertical():
                # keep original axis assignments ..
                x1_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(h1_axis)
                x2_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(h2_axis)
                y1_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(v1_axis)
                y2_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(v2_axis)

                x1_tick_type = h1_tick_type
                x2_tick_type = h2_tick_type
                y1_tick_type = v1_tick_type
                y2_tick_type = v2_tick_type
            else:
                # invert axis assignments
                x1_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(v1_axis)
                x2_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(v2_axis)
                y1_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(h1_axis)
                y2_axis_ticks = ChartJSON_Exporter.prepare_axis_ticks(h2_axis)

                x1_tick_type = v1_tick_type
                x2_tick_type = v2_tick_type
                y1_tick_type = h1_tick_type
                y2_tick_type = h2_tick_type

            task_4['name'] = 'Axes Analysis'
            task_4['output'] = {
                '_plot_bb': plot_bb,
                'axes': {
                    'x-axis': x1_axis_ticks,
                    'x-tick-type': x1_tick_type,
                    'y-axis': y1_axis_ticks,
                    'y-tick-type': y1_tick_type,
                    'x-axis-2': x2_axis_ticks,
                    'x2-tick-type': x2_tick_type,
                    'y-axis-2': y2_axis_ticks,
                    'y2-tick-type': y2_tick_type
                }
            }

        return task_4

    @staticmethod
    def prepare_task_5(chart_info, task_1, task_2, test_mode, offset=(0, 0)):
        task_5 = {
            'input': {
                'task1_output': task_1['output'],
                'task2_output': task_2['output'],
            }
        }

        if not test_mode:
            legend_pairs = []
            for ID, polygon in chart_info.legend.marker_per_label.items():
                # All text regions marked as legend must have a corresponding data mark entry
                if polygon is None:
                    raise Exception("Incomplete Legend Annotations")

                x1 = polygon[:, 0].min()
                x2 = polygon[:, 0].max()
                y1 = polygon[:, 1].min()
                y2 = polygon[:, 1].max()
                # compute offset wrt panel box
                legend_pair = {
                    'id': ID,
                    'bb': {
                        'x0': int(round(x1 + offset[0])),
                        'y0': int(round(y1 + offset[1])),
                        'height': int(round(y2 - y1)),
                        'width': int(round(x2 - x1))
                    }
                }
                legend_pairs.append(legend_pair)

            task_5['name'] = 'Legend Analysis'
            task_5['output'] = {
                'legend_pairs': legend_pairs
            }

        return task_5

    @staticmethod
    def prepare_task_6(chart_info, task_1, task_2, task_3, task_4, task_5, mask_output, offset=(0, 0)):
        task_6 = {
            'input': {
                'task1_output': task_1['output'],
                'task2_output': task_2['output'],
                'task3_output': task_3['output'],
                'task4_output': task_4['output'],
                'task5_output': task_5['output'],
            }
        }

        if not mask_output:
            task_6['name'] = 'Data Extraction'

            bars = []
            boxes = []
            lines = []
            scatter_points = []

            # run the parsing function .... (chart type dependent)
            if chart_info.type == ChartInfo.TypeBar:
                bars, data_series = chart_info.data.parse_data(chart_info)
            elif chart_info.type == ChartInfo.TypeBox:
                boxes, data_series = chart_info.data.parse_data(chart_info)
            elif chart_info.type == ChartInfo.TypeLine:
                lines, data_series = chart_info.data.parse_data(chart_info)
            elif chart_info.type == ChartInfo.TypeScatter:
                scatter_points, data_series = chart_info.data.parse_data(chart_info)
            else:
                raise Exception("Cannot Export Data for Type of Chart: " + str(chart_info.type))

            # print(json.dumps(data_series))
            task_6['output'] = {
                "data series": data_series,
                "visual elements": {
                    "bars": bars,
                    "boxplots": boxes,
                    "lines": lines,
                    "scatter points": scatter_points,
                }
            }

        return task_6

    @staticmethod
    def prepare_chart_image_json(chart_info, img_status, task_num, mask_output):
        # prepare the per-task output ...
        # (only there are validated annotations for the task)
        # Task 1. Chart Image Classification
        if task_num >= 1 and img_status[1] == 2:
            task_1 = ChartJSON_Exporter.prepare_task_1(chart_info, mask_output and task_num == 1)
        else:
            task_1 = None

        # Task 2. Text Detection and Recognition
        if task_num >= 2 and img_status[2] == 2:
            task_2 = ChartJSON_Exporter.prepare_task_2(chart_info, task_1, mask_output and task_num == 2)
        else:
            task_2 = None

        # Task 3. Text Role Classification
        if task_num >= 3 and img_status[2] == 2:
            task_3 = ChartJSON_Exporter.prepare_task_3(chart_info, task_1, task_2, mask_output and 3 <= task_num <= 5)
        else:
            task_3 = None

        # Task 4. Axis Recognition
        if task_num >= 4 and img_status[4] == 2:
            task_4 = ChartJSON_Exporter.prepare_task_4(chart_info, task_1, task_2, mask_output and 3 <= task_num <= 5)
        else:
            task_4 = None

        # Task 5. Legend Recognition
        if task_num >= 5 and img_status[3] == 2:
            task_5 = ChartJSON_Exporter.prepare_task_5(chart_info, task_1, task_2, mask_output and 3 <= task_num <= 5)
        else:
            task_5 = None

        # Task 6. Data Element Recognition and Parsing
        if task_num >= 6 and img_status[5] == 2:
            task_6 = ChartJSON_Exporter.prepare_task_6(chart_info, task_1, task_2, task_3, task_4, task_5,
                                                       mask_output and task_num == 6)
        else:
            task_6 = None

        # add per-task GT to the final structure as required
        json_output = {}
        if (mask_output and task_num == 1) or (not mask_output and task_num >= 1):
            json_output['task1'] = task_1
        if (mask_output and task_num == 2) or (not mask_output and task_num >= 2):
            json_output['task2'] = task_2
        if (mask_output and 3 <= task_num <= 5) or (not mask_output and task_num >= 3):
            json_output['task3'] = task_3
        if (mask_output and 3 <= task_num <= 5) or (not mask_output and task_num >= 4):
            json_output['task4'] = task_4
        if (mask_output and 3 <= task_num <= 5) or (not mask_output and task_num >= 5):
            json_output['task5'] = task_5
        if (mask_output and task_num == 6) or (not mask_output and task_num >= 6):
            json_output['task6'] = task_6

        return json_output

    @staticmethod
    def SaveChartImageJSON(json_output, img_file, json_folder):
        img_id = '.'.join(img_file.split('.')[:-1])
        json_output_file = json_folder + img_id + '.json'
        local_json_output_dir, final_filename = os.path.split(json_output_file)

        os.makedirs(local_json_output_dir, exist_ok=True)

        print("- Saving " + json_output_file)
        json_output_str = json.dumps(json_output, indent=4, sort_keys=True)
        with open(json_output_file, 'w') as f:
            f.write(json_output_str)
