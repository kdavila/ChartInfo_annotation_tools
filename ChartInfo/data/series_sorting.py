
class SeriesSorting:
    def __init__(self, n_series):
        self.order = [[s_idx] for s_idx in range(n_series)]

    def add_series(self):
        if len(self.order) == 0:
            next_idx = 0
        else:
            next_idx = max([max(group) for group in self.order]) + 1

        self.order.append([next_idx])

    def stacking_layers(self):
        if len(self.order) == 0:
            return 0
        else:
            return max([len(group) for group in self.order])

    def get_layer_elements(self, layer_idx):
        elements = []
        for group in self.order:
            if layer_idx < len(group):
                elements.append(group[layer_idx])

        return elements

    def remove_series(self, series_idx):
        tempo_order = []
        for group in self.order:
            tempo_group = []

            for idx in group:
                if idx < series_idx:
                    # unaffected ... add
                    tempo_group.append(idx)
                elif idx > series_idx:
                    # reduce ...
                    tempo_group.append(idx - 1)
                else:
                    # element being removed ... ignore ..
                    pass

            if len(tempo_group) > 0:
                tempo_order.append(tempo_group)

        # replace ...
        self.order = tempo_order

    def move_group_up(self, group_idx):
        if 0 < group_idx < len(self.order):
            tempo = self.order[group_idx]
            del self.order[group_idx]
            self.order.insert(group_idx - 1, tempo)

            return True
        else:
            return False

    def move_group_down(self, group_idx):
        if 0 <= group_idx < len(self.order) - 1:
            tempo = self.order[group_idx]
            del self.order[group_idx]
            self.order.insert(group_idx + 1, tempo)

            return True
        else:
            return False

    def move_series_up(self, series_idx):
        # locate group of series ...
        group_idx = 0
        while group_idx < len(self.order):
            if series_idx in self.order[group_idx]:
                # group located ... check case ...
                local_idx = self.order[group_idx].index(series_idx)
                if local_idx > 0:
                    # move up inside of local group ...
                    del self.order[group_idx][local_idx]
                    self.order[group_idx].insert(local_idx - 1, series_idx)

                    return True
                else:
                    # first in its group ... is it alone?
                    if len(self.order[group_idx]) == 1:
                        # it is alone on its group ... move it to end of previous and remove current group
                        # if it is not on the first group already ...
                        if group_idx > 0:
                            # move ...
                            self.order[group_idx - 1].append(series_idx)
                            del self.order[group_idx]

                            return True
                        else:
                            # already at the very beginning, cannot move up any further ...
                            return False
                    else:
                        # it is not alone in its group ...
                        # create a new group before current group and add it to that group ...

                        # new group
                        new_group = [series_idx]
                        # ... remove from current location
                        del self.order[group_idx][local_idx]
                        self.order.insert(group_idx, new_group)

                        return True

            else:
                group_idx += 1

        raise Exception("Series specified not found!")

    def move_series_down(self, series_idx):
        # locate group of series ...
        group_idx = 0
        while group_idx < len(self.order):
            if series_idx in self.order[group_idx]:
                # group located ... check case ...
                local_idx = self.order[group_idx].index(series_idx)
                if local_idx < len(self.order[group_idx]) - 1:
                    # move down inside of local group ...
                    del self.order[group_idx][local_idx]
                    self.order[group_idx].insert(local_idx + 1, series_idx)

                    return True
                else:
                    # last in its group ... is it alone?
                    if len(self.order[group_idx]) == 1:
                        # it is alone on its group ... move it to beginning of next and remove current group
                        # if it is not on the last group already ...
                        if group_idx < len(self.order) - 1:
                            # move ...
                            self.order[group_idx + 1].insert(0, series_idx)
                            del self.order[group_idx]

                            return True
                        else:
                            # already at the very end, cannot move down any further ...
                            return False
                    else:
                        # it is not alone in its group ...
                        # create a new group after current group and add it to that group ...

                        # new group
                        new_group = [series_idx]
                        # ... remove from current location
                        del self.order[group_idx][local_idx]
                        self.order.insert(group_idx + 1, new_group)

                        return True

            else:
                group_idx += 1

        raise Exception("Series specified not found!")

    def to_XML(self, indent=""):
        xml_str = indent + "<SeriesSorting>\n"
        for group in self.order:
            xml_str += indent + "    <Group>\n"
            for series_idx in group:
                xml_str += indent + "        <Index>{0:d}</Index>\n".format(series_idx)
            xml_str += indent + "    </Group>\n"
        xml_str += indent + "</SeriesSorting>\n"

        return xml_str

    @staticmethod
    def Copy(other):
        assert isinstance(other, SeriesSorting)

        sorting = SeriesSorting(0)
        sorting.order = [list(group) for group in other.order]

        return sorting

    @staticmethod
    def FromXML(xml_root):
        # assume xml_root is SeriesSorting
        sorting = SeriesSorting(0)

        for xml_group_root in xml_root:
            group_elements = []
            for xml_index in xml_group_root:
                group_elements.append(int(xml_index.text))

            sorting.order.append(group_elements)

        return sorting

