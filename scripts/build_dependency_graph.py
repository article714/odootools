#!/usr/bin/env python
# -*- coding: utf-8 -*-

import odoo
from odoo.tools import config
from odootools import OdooScript
try:
    import networkx
except Exception:
    networkx = None


class BuildDependencyGraph(OdooScript.Script):

    # ***********************************
    # Main

    
    def run(self):
        if networkx is not None:
            # Build dependency graph
            graph = networkx.Graph()
            mods = self.env["ir.module.module"].search([("state", "=", "installed")])
            for mod in mods:
                graph.add_node(mod.name)
                for dep in mod.dependencies_id:
                    if dep.name not in graph.nodes():
                        graph.add_node(dep.name)
                    graph.add_edge(mod.name,dep.name)
        else:
            self.logger.error("Cannot run without networkx")
                

# *******************************************************
# Launch main function


if __name__ == "__main__":
    script = BuildDependencyGraph()
    script.runInOdooContext()
