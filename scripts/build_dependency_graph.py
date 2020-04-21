#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sys import exit as sysexit

from odootools import odooscript

try:
    import networkx
except (ModuleNotFoundError, ImportError):
    logging.error("error on import: missing networkx")
    sysexit(1)

try:
    import matplotlib.pyplot as plt
except (ModuleNotFoundError, ImportError):
    logging.error("error on import: missing networkx")
    sysexit(1)


class BuildDependencyGraph(odooscript.AbstractOdooScript):

    # ***********************************
    # Main

    def run(self):
        if networkx is not None:
            # Build dependency graph
            graph = networkx.Graph()
            mods = self.env["ir.module.module"].search(
                [("state", "=", "installed")]
            )
            for mod in mods:
                graph.add_node(mod.name)
                for dep in mod.dependencies_id:
                    if dep.name not in graph.nodes():
                        graph.add_node(dep.name)
                    graph.add_edge(mod.name, dep.name)

                pos = networkx.planar_layout(graph)
                networkx.generate_adjlist(graph)
                networkx.draw_networkx_nodes(
                    graph,
                    pos=pos,
                    node_size=1500,
                    alpha=0.5,
                    node_color=range(len(graph.nodes())),
                    with_edges=False,
                    with_labels=False,
                )

                networkx.draw_networkx_labels(graph, pos)

                networkx.draw_networkx_edges(
                    graph,
                    pos,
                    arrows=True,
                    arrowsize=10,
                    arrowstyle="-|>",
                    connectionstyle="arc3,rad=0.1",
                    min_source_margin=30,
                    min_target_margin=30,
                )

                plt.savefig("odoo_dependencies.png")

        else:
            self.logger.error("Cannot run without networkx")


# *******************************************************
# Launch main function


if __name__ == "__main__":
    script = BuildDependencyGraph()
    script.run_in_odoo_context()
