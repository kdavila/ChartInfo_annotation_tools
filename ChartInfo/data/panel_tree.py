

class PanelNode:
    def __init__(self, parent, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.parent = parent
        self.children = None

    def __eq__(self, other):
        if isinstance(other, PanelNode):
            # first, check for boundaries ...
            if self.x1 != other.x1 or self.y1 != other.y1 or self.x2 != other.x2 or self.y2 != other.y2:
                return False

            # check based on children ...
            return self.children == other.children
        else:
            return False

    def is_leaf(self):
        return self.children is None

    def merge_with_parent(self):
        # this node will be discarded by parent!
        if self.parent is not None:
            current_parent = self.parent
            for child in self.parent.children:
                # remove link ...
                child.parent = None

            # parent has now become a leaf ..
            current_parent.children = None

    def horizontal_split(self, y_split):
        if self.y1 < y_split < self.y2:
            # could be split ....
            if self.children is None:
                # has no children ... split ...
                child1 = PanelNode(self, self.x1, self.y1, self.x2, y_split - 1)
                child2 = PanelNode(self, self.x1, y_split + 1, self.x2, self.y2)

                self.children = [child1, child2]
            else:
                # ... split children ....
                for child in self.children:
                    child.horizontal_split(y_split)

    def vertical_split(self, x_split):
        if self.x1 < x_split < self.x2:
            # could be split ....
            if self.children is None:
                # has no children ... split ...
                child1 = PanelNode(self, self.x1, self.y1, x_split - 1, self.y2)
                child2 = PanelNode(self, x_split + 1, self.y1, self.x2, self.y2)

                self.children = [child1, child2]
            else:
                # ... split children ....
                for child in self.children:
                    child.vertical_split(x_split)

    def get_leaves(self):
        if self.is_leaf():
            return [self]
        else:
            results = []
            for child in self.children:
                results += child.get_leaves()

            return results

    def find_point_containers(self, x, y, include_non_leaves):
        if self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2:
            # contained ....
            if self.children is None:
                # always return leaves
                return [self]
            else:
                if include_non_leaves:
                    results = [self]
                else:
                    results = []

                for child in self.children:
                    results += child.find_point_containers(x, y, include_non_leaves)

                return results
        else:
            # current node and children do not contain this point
            return []

    def to_XML(self, indent=""):
        xml_str = indent + "<PanelTreeNode>\n"
        xml_str += indent + "    <X1>" + str(self.x1) + "</X1>\n"
        xml_str += indent + "    <Y1>" + str(self.y1) + "</Y1>\n"
        xml_str += indent + "    <X2>" + str(self.x2) + "</X2>\n"
        xml_str += indent + "    <Y2>" + str(self.y2) + "</Y2>\n"
        if self.children is not None:
            xml_str += indent + "    <Children>\n"
            for child in self.children:
                xml_str += child.to_XML(indent + "       ")
            xml_str += indent + "    </Children>\n"

        xml_str += indent + "</PanelTreeNode>\n"
        return xml_str

    @staticmethod
    def FromXML(xml_root):
        # assumes that root is PanelTreeNode
        x1 = int(xml_root.find("X1").text)
        y1 = int(xml_root.find("Y1").text)
        x2 = int(xml_root.find("X2").text)
        y2 = int(xml_root.find("Y2").text)

        node = PanelNode(None, x1, y1, x2, y2)

        children_root = xml_root.find("Children")
        if children_root is not None:
            node.children = []
            for xml_child in children_root:
                child = PanelNode.FromXML(xml_child)
                # link child to current node
                child.parent = node
                # add as child of current node ...
                node.children.append(child)

        return node

    @staticmethod
    def Copy(other):
        assert isinstance(other, PanelNode)

        # create a new node ... set same boundaries ....
        copy = PanelNode(None, other.x1, other.y1, other.x2, other.y2)
        # now ... copy children if any
        if other.children is not None:
            copy.children = []
            for other_child in other.children:
                # copy child. ....
                copied_child = PanelNode.Copy(other_child)
                # link child to parent ...
                copied_child.parent = copy
                # link parent to child ...
                copy.children.append(copied_child)

        return copy

class PanelTree:
    def __init__(self, root):
        self.root = root

    def to_XML(self):
        xml_str = "    <PanelTree>\n"
        xml_str += self.root.to_XML("        ")
        xml_str += "    </PanelTree>\n"
        return xml_str

    def __eq__(self, other):
        if isinstance(other, PanelTree):
            return self.root == other.root
        else:
            return False


    @staticmethod
    def FromXML(xml_tree):
        # xml_root should the <PanelTree> node ....
        # get the root
        xml_root_node = xml_tree.find("PanelTreeNode")
        root = PanelNode.FromXML(xml_root_node)

        return PanelTree(root)

    @staticmethod
    def FromImage(image):
        h = image.shape[0]
        w = image.shape[1]

        root = PanelNode(None, 0, 0, w, h)
        tree = PanelTree(root)

        return tree

    @staticmethod
    def Copy(other):
        assert isinstance(other, PanelTree)

        copy_root = PanelNode.Copy(other.root)

        return PanelTree(copy_root)