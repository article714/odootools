#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple OdooScript to build a graph of installed module deps
"""

import logging
from sys import exit as sysexit

from odootools import odooscript

try:
    import networkx
    from networkx.readwrite import GraphMLWriter
    from networkx.utils import make_str
except ImportError:
    logging.error("error on import: missing networkx")
    sysexit(1)

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba, to_hex
except ImportError:
    logging.error("error on import: missing networkx")
    sysexit(1)


LICENSE_COLOR_MAP = {
    "LGPL-3": to_rgba("#22aa2299"),
    "AGPL-3": to_rgba("#2222aa99"),
    "OPL-1": to_rgba("#aa222299"),
}
LICENSE_COMPATIBILITY_MATRIX = {
    "LGPL-3": ["LGPL-3"],
    "AGPL-3": ["AGPL-3", "LGPL-3"],
    "OPL-1": ["OPL-1", "LGPL-3"],
}

NAMED_ATTR = ["label", "edgelabel", "x", "y", "size", "r", "g", "b"]


class GephiGraphMLWriter(GraphMLWriter):
    """
    Customized GraphML writer for gephi compatibility
    """

    def get_key(self, name, attr_type, scope, default):
        keys_key = (name, attr_type, scope)
        try:
            return self.keys[keys_key]
        except KeyError:
            if name in NAMED_ATTR:
                new_id = name
            else:
                new_id = "d%i" % len(list(self.keys))
            self.keys[keys_key] = new_id
            key_kwargs = {
                "id": new_id,
                "for": scope,
                "attr.name": name,
                "attr.type": attr_type,
            }
            key_element = self.myElement("key", **key_kwargs)
            # add subelement for data default value if present
            if default is not None:
                default_element = self.myElement("default")
                default_element.text = make_str(default)
                key_element.append(default_element)
            self.xml.insert(0, key_element)
        return new_id


class BuildDependencyGraph(odooscript.AbstractOdooScript):
    """
    Main class to build dependency graph
    """

    def __init__(self):
        super(BuildDependencyGraph, self).__init__()
        self.shells = [
            ["base"],
        ]
        self.depth = 1
        self.nodelevels = {"base": 0}
        self.graph = networkx.DiGraph()

    def add_node(self, node, modlicense, node_colors):
        """
        add a Node to the Graph
        """
        if node not in self.graph.nodes():
            color = "grey"
            if modlicense in LICENSE_COLOR_MAP:
                color = LICENSE_COLOR_MAP[modlicense]
                node_colors.append(LICENSE_COLOR_MAP[modlicense])
            else:
                self.logger.warning("Missing license %s", modlicense)
                node_colors.append("grey")

            self.graph.add_node(
                node,
                license=modlicense,
                color=to_hex(color),
                r=round(255 * color[0]),
                g=round(255 * color[1]),
                b=round(255 * color[2]),
                level=0,
                inlinks=0,
                size=10.0,
                label=node,
                weight=1,
                x=0,
                y=0,
            )
            self.nodelevels[node] = [0, 0]

    def process_depth(self, mods, first=True):
        """
        Calculate depth of dependency tree
        """
        changed = False
        for node in mods:
            fromnode = node.name
            for dep in fromnode.dependencies:
                tonode = dep.depend_id.name
                if first:
                    self.nodelevels[tonode][1] += 1
                    self.graph.nodes[tonode]["inlinks"] = self.nodelevels[
                        tonode
                    ][1]
                    self.graph.nodes[tonode]["weight"] = self.nodelevels[
                        tonode
                    ][1]
                if self.nodelevels[fromnode][0] <= self.nodelevels[tonode][0]:
                    self.nodelevels[fromnode][0] = (
                        self.nodelevels[tonode][0] + 1
                    )
                    self.graph.nodes[fromnode]["level"] = self.nodelevels[
                        fromnode
                    ][0]
                    changed = True
                if self.depth < self.nodelevels[fromnode][0]:
                    self.depth = self.nodelevels[fromnode][0]
                    changed = True
        if changed:
            self.process_depth(mods, first=False)

    def process_shells(self):
        """
        process the layout rings of dependencies
        """
        i = 0
        while i < self.depth:
            self.shells.insert(0, [])
            i += 1
        for node in self.nodelevels:
            if node not in self.shells[-self.nodelevels[node][0]]:
                self.shells[-self.nodelevels[node][0]].append(node)

    def draw_graph(
        self, size, name, positions, node_colors, edge_colors
    ):  # pylint: disable=too-many-arguments
        """
        Draw a graph and saves PNG
        """
        plt.figure(figsize=(size, size))
        networkx.draw_networkx_nodes(
            self.graph,
            pos=positions,
            node_size=5000,
            node_color=node_colors,
            alpha=0.4,
            with_edges=False,
            with_labels=False,
        )

        networkx.draw_networkx_labels(self.graph, positions)

        networkx.draw_networkx_edges(
            self.graph,
            positions,
            arrows=True,
            arrowsize=20,
            alpha=0.7,
            edge_color=edge_colors,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            min_source_margin=35,
            min_target_margin=40,
        )

        # write outputs

        plt.savefig("odoo_dependencies_{}.png".format(name))

    # ***********************************
    # Main

    def run(self):
        """
        Main method (OdooScript)
        """
        if networkx is not None:
            # Build dependency graph
            mods = self.env["ir.module.module"].search(
                [("state", "=", "installed")]
            )
            node_colors = []
            # first add all nodes

            mods.mapped(
                lambda x: self.add_node(x.name, x.license, node_colors)
            )

            self.process_depth(mods)
            self.process_shells()

            # then process edges
            edge_colors = []
            for mod in mods:
                for dep in mod.dependencies_id:

                    color = "grey"
                    compatible = False
                    if mod.license in LICENSE_COMPATIBILITY_MATRIX:
                        if (
                            dep.depend_id
                            and dep.depend_id.license
                            in LICENSE_COMPATIBILITY_MATRIX[mod.license]
                        ):
                            color = "#22aa22"
                            compatible = True
                        elif dep.depend_id:
                            color = "red"
                        else:
                            color = "grey"

                    edge_colors.append(color)

                    self.graph.add_edge(
                        mod.name,
                        dep.name,
                        color=color,
                        edgelabel="",
                        compatible=compatible,
                        aweight=1
                        / (
                            1
                            + (
                                self.nodelevels[mod.name][0]
                                - self.nodelevels[dep.depend_id.name][0]
                            )
                            * self.nodelevels[dep.name][1]
                        ),
                    )

            init_positions = {
                "shell": networkx.shell_layout(
                    self.graph, self.shells, scale=5.0
                ),
                "spectral": networkx.spectral_layout(self.graph, scale=5),
            }

            size = 16 + round(len(self.graph.nodes()) / 2)

            for pos0 in init_positions:

                pos1 = networkx.spring_layout(
                    self.graph,
                    k=3,
                    pos=init_positions[pos0],
                    weight="aweight",
                    fixed=None,
                    iterations=300,
                    scale=1.0,
                )

                self.draw_graph(
                    size, pos0, init_positions[pos0], node_colors, edge_colors
                )

                self.draw_graph(
                    size,
                    "{}_spring".format(pos0),
                    pos1,
                    node_colors,
                    edge_colors,
                )

            for node in self.graph.nodes:
                self.graph.nodes[node]["x"] = 256 * pos1[node][0]
                self.graph.nodes[node]["y"] = 256 * pos1[node][1]

            writer = GephiGraphMLWriter(
                encoding="utf-8", prettyprint=True, infer_numeric_types=False
            )
            writer.add_graph_element(self.graph)
            writer.dump("odoo_dependencies.graphml")

        else:
            self.logger.error("Cannot run without networkx")


# *******************************************************
# Launch main function


if __name__ == "__main__":
    SCRIPT = BuildDependencyGraph()
    SCRIPT.run_in_odoo_context()
