# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textwrap

from textworld.utils import uniquify


class DependencyTreeElement:
    """
    Representation of an element in the dependency tree.

    The notion of dependency and ordering should be defined for
    these elements.

    Subclasses should override `depends_on`, `__lt__` and
    `__str__` accordingly.
    """

    def __init__(self, value):
        self.value = value

    def depends_on(self, other):
        """
        Check whether this element depends on the `other`.
        """
        return self.value > other.value

    def is_distinct_from(self, others):
        """
        Check whether this element is distinct from `others`.
        """
        return self.value not in [other.value for other in others]

    def __str__(self):
        return str(self.value)


class DependencyTree:
    class _Node:
        def __init__(self, element):
            self.element = element
            self.children = []

        def push(self, node):
            if node == self:
                return

            for child in self.children:
                child.push(node)

            if self.element.depends_on(node.element) and not self.already_added(node):
                self.children.append(node)

        def already_added(self, node):
            # We want to avoid duplicate information about dependencies.
            if node in self.children:
                return True

            # Check whether children nodes already contain the dependency
            # information that `node` would bring.
            if not node.element.is_distinct_from((child.element for child in self.children)):
                return True

            # for child in self.children:
            #     # if node.element.value == child.element.value:
            #     if not node.element.is_distinct_from((child.element):
            #         return True

            return False

        def __str__(self):
            node_text = str(self.element)

            txt = [node_text]
            for child in self.children:
                txt.append(textwrap.indent(str(child), "  "))

            return "\n".join(txt)

        def copy(self):
            node = DependencyTree._Node(self.element)
            node.children = [child.copy() for child in self.children]
            return node

    def __init__(self, element_type=DependencyTreeElement):
        self.root = None
        self.element_type = element_type
        self._update()

    def push(self, value):
        element = self.element_type(value)
        node = DependencyTree._Node(element)
        if self.root is None:
            self.root = node
        else:
            self.root.push(node)

        # Recompute leaves.
        self._update()
        if element in self.leaves_elements:
            return node

        return None

    def pop(self, value):
        if value not in self.leaves_values:
            raise ValueError("That element is not a leaf: {!r}.".format(value))

        def _visit(node):
            for child in list(node.children):
                if child.element.value == value:
                    node.children.remove(child)

        self._postorder(self.root, _visit)
        if self.root.element.value == value:
            self.root = None

        # Recompute leaves.
        self._update()

    def _postorder(self, node, visit):
        for child in node.children:
            self._postorder(child, visit)

        visit(node)

    def _update(self):
        self._leaves_values = []
        self._leaves_elements = set()

        def _visit(node):
            if len(node.children) == 0:
                self._leaves_elements.add(node.element)
                self._leaves_values.append(node.element.value)

        if self.root is not None:
            self._postorder(self.root, _visit)

        self._leaves_values = uniquify(self._leaves_values)

    def copy(self):
        tree = DependencyTree(self.element_type)
        if self.root is not None:
            tree.root = self.root.copy()
            tree._update()

        return tree

    @property
    def leaves_elements(self):
        return self._leaves_elements

    @property
    def leaves_values(self):
        return self._leaves_values

    def __str__(self):
        if self.root is None:
            return ""

        return str(self.root)
