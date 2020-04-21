import networkx
G=networkx.Graph()
G.add_node("a")
G.add_node("b")
G.add_node("c")
G.add_edge("a","c")
G.add_edge("a","b")
G.add_edge("b","c")
networkx.draw(G)
import matplotlib.pyplot as plt
plt.savefig("toto.png")

