def dfs(G, node, parent, visited):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    
    tin = [-1 for i in range(n+1)]
    low = [-1 for i in range(n+1)]
    time = 0
    
    visited[node] = True
    tin[node] = time
    low[node] = time
    time += 1

    for neighbour in G[node]:
        if neighbour == parent:
            continue
        if visited[neighbour] == True:
            low[node] = min(low[node], tin[neighbour])
        else:
            dfs(G, neighbour, node, visited)
            low[node] = min(low[node], low[neighbour])
            if low[neighbour] > tin[node]:
                print(node, neighbour, 'is a bridge')

def find_bridges(G):
    n = G.number_of_nodes()
    visited = [False for i in range(n + 1)]

    for i in range(n):
        if visited[i] == False:
            dfs(G, i, -1, visited)


    


    

    