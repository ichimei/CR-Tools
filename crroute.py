import pandas as pd
import crnet as crn
import util

class CRGraph:
    def __init__(self, adj=None):
        if adj is None:
            adj = {}
        self.adj = adj
        self.removed = []

    def copy(self):
        adj = {key: value.copy() for key, value in self.adj.items()}
        return type(self)(adj)

    def rawInsert(self, edge):
        start, end, line, mile, dire = edge
        try:
            self.adj[start].append((end, line, mile, dire))
        except KeyError:
            self.adj[start] = [(end, line, mile, dire)]

    def insert(self, edge):
        start, end, line, mile = edge
        self.rawInsert((start, end, line, mile, True))
        self.rawInsert((end, start, line, mile, False))

    def rawRemoveEdge(self, edge):
        start, end, line, mile, dire = edge
        try:
            self.adj[start].remove((end, line, mile, dire))
        except (KeyError, ValueError):
            pass
        else:
            self.removed.append(edge)

    def removeEdge(self, edge):
        start, end, line, mile, dire = edge
        self.rawRemoveEdge((start, end, line, mile, dire))
        self.rawRemoveEdge((end, start, line, mile, not dire))

    def restoreEdges(self):
        for edge in self.removed:
            self.rawInsert(edge)
        self.removed.clear()

    def removeNode(self, node):
        # remove edges from node
        if node in self.adj:
            for rest in self.adj[node]:
                self.removed.append((node, *rest))
            self.adj[node].clear()

        # remove edges to node
        for start in self.adj:
            edges = self.adj[start]
            newEdges = []
            for rest in edges:
                edge = (start, *rest)
                if rest[0] != node:
                    newEdges.append(rest)
                else:
                    self.removed.append(edge)
            self.adj[start] = newEdges

    def getSucc(self, node):
        try:
            return self.adj[node]
        except:
            return []

    def __eq__(self, other):
        if not self.adj.keys() == other.adj.keys():
            return False
        for key in self.adj.keys():
            if sorted(self.adj[key]) != sorted(other.adj[key]):
                return False

        return True

class CRPath:
    def __init__(self, nodes, edges, dist):
        assert len(nodes) - len(edges) == 1
        self.nodes = nodes
        self.edges = edges
        self.dist = dist

    def getNode(self, i):
        return self.nodes[i]

    def getNodes(self, i, j):
        return self.nodes[i:j+1]

    def getEdge(self, i):
        return (self.nodes[i], self.nodes[i+1], *self.edges[i])

    def getSubpath(self, i, j):
        nodes = self.nodes[i:j+1]
        edges = self.edges[i:j]
        dist = sum(edge[1] for edge in edges)
        return type(self)(nodes, edges, dist)

    def __add__(self, other):
        assert self.nodes[-1] == other.nodes[0]
        nodes = self.nodes[:-1] + other.nodes
        edges = self.edges + other.edges
        dist = sum(edge[1] for edge in edges)
        return type(self)(nodes, edges, dist)

    def __eq__(self, other):
        return self.nodes == other.nodes and self.edges == other.edges

    def __len__(self):
        return len(self.nodes)

    # def print(self):
    #     print('Distance:', self.dist)
    #     print('Route: ', end='')
    #     for i in range(len(self.edges)):
    #         print(f'({self.nodes[i]})', end='')
    #         d = '下行' if self.edges[i][2] else '上行'
    #         print(f'-[{self.edges[i][0]} ({d}), {self.edges[i][1]}]-', end='')
    #     print(f'({self.nodes[-1]})')
    #     print()

class CRRoute(crn.CRNetwork):
    def __init__(self, network, stations):
        super().__init__(network, stations)

    def getGraph(self, start, end, via=()):
        teleps = (start, end, *via)
        graph = CRGraph()
        for line, crline in self.network.items():
            edges = crline.getEdges(*teleps)
            for edge in edges:
                graph.insert(edge)
        return graph

    def genPath(self, name, edge, prev, dist):
        nodes = []
        edges = []
        while prev is not None:
            nodes.append(name)
            edges.append(tuple(edge))
            (name, _, *edge), prev, *_ = prev
        nodes.append(name)
        nodes.reverse()
        edges.reverse()
        return CRPath(nodes, edges, dist)

    def findRoute(self, start, end, via=(), graph=None):
        if graph is None:
            graph = self.getGraph(start, end, via=via)
        fringe = util.PriorityQueue()
        closed = []
        lenVia = len(via)
        # cost is (transfer times, distance)
        # (name, via, line, mile, dire), prev, cost
        fringe.push(((start, 0, None, None, None), None, (0, 0)), (0, 0))
        goalState = (end, lenVia)

        while not fringe.isEmpty():
            node = fringe.pop()
            state, prev, cost = node
            name, nowVia, line, mile, dire = state
            trans, dist = cost
            if (name, nowVia) == goalState:
                return self.genPath(name, (line, mile, dire), prev, dist)

            if state not in closed:
                closed.append(state)
                for succ, newLine, newMile, newDire in graph.getSucc(name):
                    # encountered via?
                    newVia = nowVia
                    if nowVia < lenVia and succ == via[nowVia]:
                        newVia += 1
                    # encountered trans?
                    newTrans = trans
                    if line != newLine:
                        newTrans += 1
                    newDist = dist + newMile
                    newCost = (newTrans, newDist)
                    fringe.push(((succ, newVia, newLine, newMile, newDire),
                        node, newCost), newCost)

    def findRouteK(self, start, end, K, via=(), graph=None):
        if graph is None:
            graph = self.getGraph(start, end, via=via)
        fringe = util.PriorityQueue()
        lenVia = len(via)
        # cost is (transfer times, distance)
        # (name, via, line, mile, dire), prev, pathNodes, cost
        fringe.push(((start, 0, None, None, None), None, (start,), (0, 0)), (0, 0))
        goalState = (end, lenVia)
        count = 0
        while not fringe.isEmpty():
            node = fringe.pop()
            state, prev, pathNodes, cost = node
            name, nowVia, line, mile, dire = state
            trans, dist = cost
            if (name, nowVia) == goalState:
                yield self.genPath(name, (line, mile, dire), prev, dist)
                count += 1
                if count >= K:
                    break

            for succNode in graph.getSucc(name):
                succ, newLine, newMile, newDire = succNode
                if succ in pathNodes:
                    continue
                # encountered via?
                newVia = nowVia
                if nowVia < lenVia and succ == via[nowVia]:
                    newVia += 1
                # encountered trans?
                newTrans = trans
                if line != newLine or dire != newDire:
                    newTrans += 1
                newDist = dist + newMile
                newCost = (newTrans, newDist)
                fringe.push(((succ, newVia, newLine, newMile, newDire),
                    node, pathNodes + (succ,), newCost), newCost)

if __name__ == '__main__':
    with open('lines.txt') as f:
        lines = f.read().split()
    lines.remove('广肇城际线佛肇线')
    # lines = ['京沪线', '宁启线林南段(南京)']
    crr = CRRoute.readLines(lines)
    crr.findRoute('-SHH', '-NUH', via=('-XCH',)).print()
