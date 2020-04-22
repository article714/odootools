#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sys import exit as sysexit

from odootools import odooscript

try:
    import networkx
    from networkx.readwrite import GraphMLWriter
    from networkx.utils import make_str
except (ModuleNotFoundError, ImportError):
    logging.error("error on import: missing networkx")
    sysexit(1)

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba, to_hex
except (ModuleNotFoundError, ImportError):
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
    def __init__(self):
        super(BuildDependencyGraph, self).__init__()
        self.shells = [
            ["base"],
        ]
        self.depth = 1
        self.nodelevels = {"base": 0}
        self.graph = networkx.DiGraph()

    def add_node(self, node, modlicense, node_colors):

        if node not in self.graph.nodes():
            color = "grey"
            if modlicense in LICENSE_COLOR_MAP:
                color = LICENSE_COLOR_MAP[modlicense]
                node_colors.append(LICENSE_COLOR_MAP[modlicense])
            else:
                print(f"Missing license {modlicense}")
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

    def process_depth(self, fromnode, tonode):
        self.nodelevels[tonode][1] += 1
        self.graph.nodes[tonode]["inlinks"] = self.nodelevels[tonode][1]
        self.graph.nodes[tonode]["weight"] = self.nodelevels[tonode][1]
        if self.nodelevels[fromnode][0] <= self.nodelevels[tonode][0]:
            self.nodelevels[fromnode][0] = self.nodelevels[tonode][0] + 1
            self.graph.nodes[fromnode]["level"] = self.nodelevels[fromnode][0]
        if self.depth < self.nodelevels[fromnode][0]:
            self.depth = self.nodelevels[fromnode][0]

    def process_shells(self):
        i = 0
        while i < self.depth:
            self.shells.insert(0, [])
            i += 1
        for node in self.nodelevels.keys():
            if node not in self.shells[-self.nodelevels[node][0]]:
                self.shells[-self.nodelevels[node][0]].append(node)
        return

    def draw_graph(self, size, name, positions, node_colors, edge_colors):

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

        plt.savefig(f"odoo_dependencies_{name}.png")

    # ***********************************
    # Main

    def run(self):
        if networkx is not None:
            # Build dependency graph
            mods = self.env["ir.module.module"].search(
                [("state", "=", "installed")]
            )
            node_colors = []
            # first add all nodes
            for mod in mods:
                self.add_node(mod.name, mod.license, node_colors)

            # process dep depth
            for i in range(5):
                for mod in mods:
                    for dep in mod.dependencies_id:
                        self.process_depth(mod.name, dep.depend_id.name)
            self.process_shells()

            # then process edges
            edge_colors = []
            for mod in mods:
                for dep in mod.dependencies_id:

                    color = "grey"
                    compatible = False
                    if mod.license in LICENSE_COMPATIBILITY_MATRIX:
                        if dep.depend_id:
                            dep_license = dep.depend_id.license
                            if (
                                dep_license
                                in LICENSE_COMPATIBILITY_MATRIX[mod.license]
                            ):
                                color = "#22aa22"
                                compatible = True
                            else:
                                color = "red"
                        else:
                            color = "grey"
                    else:
                        edge_colors.append("grey")

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

            nb_nodes = len(self.graph.nodes())

            init_positions = {
                "shell": networkx.shell_layout(
                    self.graph, self.shells, scale=5.0
                ),
                "spectral": networkx.spectral_layout(self.graph, scale=5),
            }

            size = 16 + round(nb_nodes / 2)

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
                    size, f"{pos0}_spring", pos1, node_colors, edge_colors
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
    script = BuildDependencyGraph()
    script.run_in_odoo_context()
