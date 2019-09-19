
import ast

class Configuration:
    def __init__(self, config_data, key_order=None):
        self.data = config_data
        self.key_order=key_order

    def get(self, name, default=None):
        if name in self.data:
            # let python guess the right class
            try:
                value = ast.literal_eval(self.data[name])
            except:
                # interpret as string
                value = self.data[name]

            return value
        else:
            return default

    def get_str(self, name, default=""):
        if name in self.data:
            return self.data[name]
        else:
            return default

    # This assumes string is integer 1 or 0 (True, False)
    def get_bool(self, name, default=False):
        if name in self.data:
            return int(self.data[name]) > 0
        else:
            return default

    def get_int(self, name, default=0):
        if name in self.data:
            return int(self.data[name])
        else:
            return default

    def get_float(self, name, default=0.0):
        if name in self.data:
            return float(self.data[name])
        else:
            return default

    def set(self, name, value):
        self.data[name] = value

    def contains(self, name):
        return name in self.data

    def get_active_features(self):
        active_features = []
        for parameter in self.data:
            if parameter[0:13] == "FEATURES_USE_" and self.get_bool(parameter):
                active_features.append(parameter)

        return active_features

    def save(self, filename):
        # save current configuration status to output file ...
        lines = []

        if self.key_order is None:
            # save values in a deterministic order (sorted by key,)
            key_order = sorted(list(self.data.keys()))
        else:
            # use source order ...
            key_order = self.key_order

            # check for new or removed keys
            # ... removed ..
            pos = 0
            while pos < len(key_order):
                if not key_order[pos] in self.data:
                    # key has been removed ...
                    del key_order[pos]
                else:
                    pos += 1

            # ... added ...
            for key in self.data:
                if not key in key_order:
                    # append ...
                    key_order.append(key)

        for key in key_order:
            line = key + " = " + str(self.data[key]) + "\n"
            lines.append(line)

        # to output ...
        output_file = open(filename, "w", encoding="utf8")
        output_file.writelines(lines)
        output_file.close()

    @staticmethod
    def from_file(filename):
        input_file = open(filename, "r")
        lines = input_file.readlines()
        input_file.close()

        config_data = {}
        key_order = []
        for line in lines:
            # comment character
            if "#" in line:
                line = line.split("#")[0]

            parts = line.strip().split("=")

            if len(parts) != 2:
                continue

            key = parts[0].strip().upper()
            data = parts[1].strip()

            config_data[key] = data
            key_order.append(key)

        return Configuration(config_data, key_order)

