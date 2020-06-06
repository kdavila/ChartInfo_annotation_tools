
import datetime

class TimeStats:
    def __init__(self, t_main=0.0, t_panels=0.0, t_class=0.0, t_text=0.0, t_legend=0.0, t_axes=0.0, t_data=0.0):
        self.time_main = t_main
        self.time_panels = t_panels
        self.time_classification = t_class
        self.time_text = t_text
        self.time_legend = t_legend
        self.time_axes = t_axes
        self.time_data = t_data

    def get_total_time(self):
        return (self.time_main + self.time_panels + self.time_classification + self.time_text + self.time_legend +
                self.time_axes + self.time_data)

    def update_stats(self, other_stats):
        assert isinstance(other_stats, TimeStats)

        self.time_main += other_stats.time_main
        self.time_panels += other_stats.time_panels
        self.time_classification += other_stats.time_classification
        self.time_text += other_stats.time_text
        self.time_legend += other_stats.time_legend
        self.time_axes += other_stats.time_axes
        self.time_data += other_stats.time_data

    def __sec_to_str(self, seconds):
        return "{0:.2f} ({1:s})".format(seconds, str(datetime.timedelta(seconds=seconds)))

    def __repr__(self):
        total_time = self.get_total_time()

        result = "<Annotation Time\n"
        result += " -Total: " + self.__sec_to_str(total_time) + "\n"
        result += "\t- Main: " + self.__sec_to_str(self.time_main) + "\n"
        result += "\t- Panels: " + self.__sec_to_str(self.time_panels) + "\n"
        result += "\t- Classification: " + self.__sec_to_str(self.time_classification) + "\n"
        result += "\t- Text: " + self.__sec_to_str(self.time_text) + "\n"
        result += "\t- Legend: " + self.__sec_to_str(self.time_legend) + "\n"
        result += "\t- Axes: " + self.__sec_to_str(self.time_axes) + "\n"
        result += "\t- Data: " + self.__sec_to_str(self.time_data) + "\n"
        result += ">\n"

        return result