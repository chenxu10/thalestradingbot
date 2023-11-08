"""
Arbitarge problem is a negative circle detection problem

Author: Xu.Shen(xs286@cornell.edu)
"""
import networkx as nx
from networkx import NetworkXUnbounded
import matplotlib.pyplot as plt

def find_path(digraph, start="USD"):
    try:
        path = nx.bellman_ford_predecessor_and_distance(digraph, start)
        return path
    except NetworkXUnbounded:
        cycles = nx.simple_cycles(digraph)
        for cycle in cycles:
            print(cycle)  # do whatever you prefer here of course

if __name__ == '__main__':
    G = nx.DiGraph()
    G = nx.path_graph(5, create_using = nx.DiGraph())
    pred, dist = nx.bellman_ford_predecessor_and_distance(G, 0)
    nx.draw(G)
    plt.show()
    # G.add_edge('USD', 'CNY', weight=6.7)
    # G.add_edge('USD', 'EUR', weight=-0.741)
    # G.add_edge('USD', 'CAD', weight=1.005)
    # G.add_edge('EUR', 'USD', weight=1.349)
    # G.add_edge('EUR', 'CAD', weight=1.366)
    # G.add_edge('CAD', 'EUR', weight=-0.732)
    # G.add_edge('CAD', 'USD', weight=-0.995)
    # find_path(G)


# def arbitarge(A):
#     """
#     This algorithm detects arbitarge opportunities 
#     among different currencies
#     Args:  
#             USD EUR GBP CNY YEN BTC 
#         USD  1
#         EUR      1
#         GBP          1
#         CNY             1
#         YEN                 1  
#         BTC                     1
#     Returns:
#         ["USD"-->"EUR"-->"CAD"-->"USD"]
#     """
#     try:
#         path = 
#     except:

#     BellmanFordSP = BellmanFordSP(G,0)
#     if BellmanFordSP.hasNegativeCircle():
#         raise notImplementedError
#     else:
#         return "No arbitarge opportunities"

# def test_arbitarge():
#     A = [
#         [], 
#         [], 
#         [], 
#         []]
#     assert arbitarge(A) == #

