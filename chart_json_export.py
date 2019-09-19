import os
import sys
import json
from ChartInfo.data.image_info import ImageInfo


# modify function for multipanel: extract offsets and populate offsets lists
def read_annotation_xml(xml_filename, img_filename):
    info = ImageInfo.FromXML(xml_filename, img_filename)
    if len(info.panels) > 1:
        print('Warning!! Multiple Panels Detected')
    result = [chartinfo for chartinfo in info.panels]
    offsets = [(0, 0)]
    return result, offsets


def prepare_task1(charttype, orientation):
    if charttype.lower() == 'box' or charttype.lower() == 'bar':
        json_charttype = orientation + ' ' + charttype
    else:
        json_charttype = charttype
    task1 = {}
    task1['name'] = 'Chart Classification'
    task1['input'] = {}
    task1['output'] = {
        'chart_type': json_charttype
    }
    return task1


def prepare_task2(task1, text, offset=(0, 0)):
    task2 = {}
    task2['name'] = 'Text Detection and Recognition'
    task2['input'] = {
        'task1_output': task1['output']
    }
    textblocks = []
    for textinfo in text:
        ID = textinfo.id
        x1, y1, x2, y2 = textinfo.get_axis_aligned_rectangle()
        # offset bounding boxes
        textblock = {
            'id': ID,
            'text': textinfo.value,
            'bb': {
                'x0': x1 + offset[0],
                'y0': y1 + offset[0],
                'height': y2 - y1,
                'width': x2 - x1
            }
        }
        textblocks += [textblock]
    task2['output'] = {
        'text_blocks': textblocks
    }
    return task2


# there is no equivalent of value_label in the synthetic set - make it other during eval
def prepare_task3(task1, task2, text):
    task3 = {}
    task3['name'] = 'Text Role Classification'
    task3['input'] = {
        'task1_output': task1['output'],
        'task2_output': task2['output']
    }
    text_roles = []
    for textinfo in text:
        texttype = textinfo.get_type_description()
        if '-' in texttype:
            texttype = texttype.replace('-', '_')
        text_role = {
            'id': textinfo.id,
            'role': texttype.lower()
        }
        text_roles += [text_role]
    task3['output'] = {
        'text_roles': text_roles
    }
    return task3


def prepare_task4(task1, task2, axes, offset=(0, 0)):
    # ASSUMPTION: AXIS TICKS ARE ABSOLUTE POSITIONS. DOUBLE CHECK IF NEEDED FOR MULTIPANEL
    def prepare_axis_ticks(axis):
        axis_ticks = []
        for tick in axis:
            ID, x, y = tick
            # offset wrt panel box is assumed unnecessary
            axis_tick = {
                'id': ID,
                'tick_pt': {
                    'x': x,
                    'y': y
                }
            }
            axis_ticks += [axis_tick]
        return axis_ticks

    task4 = {}
    task4['name'] = 'Axes Analysis'
    task4['input'] = {
        'task1_output': task1['output'],
        'task2_output': task2['output']
    }
    x1, y1, x2, y2 = axes.bounding_box
    # offset wrt panel box
    plot_bb = {
        'x0': x1 + offset[0],
        'y0': y1 + offset[1],
        'height': y2 - y1,
        'width': x2 - x1
    }

    h1_axis = [(tickinfo.label_id, tickinfo.position, y2) for tickinfo in axes.x1_axis.ticks] if axes.x1_axis is not None else []
    h1_tick_type = axes.x1_axis.get_description()[1] if axes.x1_axis is not None else None
    v1_axis = [(tickinfo.label_id, x1, tickinfo.position) for tickinfo in axes.y1_axis.ticks] if axes.y1_axis is not None else []
    v1_tick_type = axes.y1_axis.get_description()[1] if axes.y1_axis is not None else None
    h2_axis = [(tickinfo.label_id, tickinfo.position, y1) for tickinfo in axes.x2_axis.ticks] if axes.x2_axis is not None else []
    h2_tick_type = axes.x2_axis.get_description()[1] if axes.x2_axis is not None else None
    v2_axis = [(tickinfo.label_id, x2, tickinfo.position) for tickinfo in axes.y2_axis.ticks] if axes.y2_axis is not None else []
    v2_tick_type = axes.y2_axis.get_description()[1] if axes.y2_axis is not None else None
    is_horizontal = 'horizontal' in task1['output']['chart_type'].lower()
    x1_axis = v1_axis if is_horizontal else h1_axis
    x1_tick_type = v1_tick_type if is_horizontal else h1_tick_type
    y1_axis = h1_axis if is_horizontal else v1_axis
    y1_tick_type = h1_tick_type if is_horizontal else v1_tick_type
    x2_axis = v2_axis if is_horizontal else h2_axis
    x2_tick_type = v2_tick_type if is_horizontal else h2_tick_type
    y2_axis = h2_axis if is_horizontal else v2_axis
    y2_tick_type = h2_tick_type if is_horizontal else v2_tick_type
    x1_axis_ticks = prepare_axis_ticks(x1_axis)
    y1_axis_ticks = prepare_axis_ticks(y1_axis)
    x2_axis_ticks = prepare_axis_ticks(x2_axis)
    y2_axis_ticks = prepare_axis_ticks(y2_axis)

    task4['output'] = {
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
    return task4


def prepare_task5(task1, task2, legend, offset=(0, 0)):
    task5 = {}
    task5['name'] = 'Legend Analysis'
    task5['input'] = {
        'task1_output': task1['output'],
        'task2_output': task2['output']
    }
    legend_pairs = []
    for ID, polygon in legend.marker_per_label.items():
        # legend text is present but there is no marker, then there is no task5 output required for that text
        if polygon is None:
            continue
        x1 = polygon[:, 0].min()
        x2 = polygon[:, 0].max()
        y1 = polygon[:, 1].min()
        y2 = polygon[:, 1].max()
        # compute offset wrt panel box
        legend_pair = {
            'id': ID,
            'bb': {
                'x0': x1 + offset[0],
                'y0': y1 + offset[1],
                'height': y2 - y1,
                'width': x2 - x1
            }
        }
        legend_pairs += [legend_pair]
    task5['output'] = {
        'legend_pairs': legend_pairs
    }
    return task5


# TO BE COMPLETED
def prepare_task6(task1, task2, task3, task4, task5, offset):
    task6 = {}
    task6['name'] = 'Data Extraction'
    task6['input'] = {
        'task1_output': task1['output'],
        'task2_output': task2['output'],
        'task3_output': task3['output'],
        'task4_output': task4['output'],
        'task5_output': task5['output'],
    }
    return task6


def prepare_json(img_folder, xml_folder, json_folder, task_num=1, mask_output=True):
    os.makedirs(json_folder, exist_ok=True)
    for img_file in os.listdir(img_folder):
        img_id = '.'.join(img_file.split('.')[:-1])
        print('Preparing JSON for', img_id)
        xml_file = os.path.join(xml_folder, img_id + '.xml')
        json_output_file = os.path.join(json_folder, img_id + '.json')
        chartinfos, offsets = read_annotation_xml(xml_file, img_file)
        json_output_strs = []
        for chartinfo, offset in zip(chartinfos, offsets):
            json_output = {}
            charttype, orientation = chartinfo.get_description()
            if task_num >= 1:
                json_output['task1'] = task1 = prepare_task1(charttype, orientation)
                if mask_output and task_num == 1:
                    json_output['task1'].pop('output')
                    json_output['task1'].pop('name')
            if task_num >= 2:
                json_output['task2'] = task2 = prepare_task2(task1, chartinfo.text, offset)
                if mask_output and task_num == 2:
                    json_output['task2'].pop('output')
                    json_output['task2'].pop('name')
                    json_output.pop('task1')
            if task_num >= 3:
                json_output['task3'] = task3 = prepare_task3(task1, task2, chartinfo.text)
                json_output['task4'] = task4 = prepare_task4(task1, task2, chartinfo.axes, offset)
                json_output['task5'] = task5 = prepare_task5(task1, task2, chartinfo.legend, offset)
                if mask_output and 3 <= task_num <= 5:
                    json_output['task3'].pop('output')
                    json_output['task3'].pop('name')
                    json_output['task4'].pop('output')
                    json_output['task4'].pop('name')
                    json_output['task5'].pop('output')
                    json_output['task5'].pop('name')
                    json_output.pop('task1')
                    json_output.pop('task2')
            if task_num >= 6:
                json_output['task6'] = task6 = prepare_task6(task1, task2, task3, task4, task5, offset)
                print('task6 output is not ready yet, gt json wont be produced!!')
                if mask_output and task_num == 6:
                    # json_output['task6'].pop('output')
                    json_output['task6'].pop('name')
                    json_output.pop('task1')
                    json_output.pop('task2')
                    json_output.pop('task3')
                    json_output.pop('task4')
                    json_output.pop('task5')
            json_output_strs += [json.dumps(json_output, indent=4, sort_keys=True)]
        # currently supporting only single panel charts or first panel of multi-panel
        json_output_str = json_output_strs[0]
        with open(json_output_file, 'w') as f:
            f.write(json_output_str)

def main():
    if len(sys.argv) < 6:
        print('Usage: python chart_json_export.py img_folder xml_folder json_folder task_num test_mode')
        return

    prepare_json(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5].lower() == 'true')

if __name__ == '__main__':
    main()


