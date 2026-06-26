import networkx as nx
import osmnx as ox
import heapq
import math
import time
import os

ox.settings.timeout = 300 
ox.settings.use_cache = True 
GRAPH_FILENAME = "nyc_grid.graphml"
BASE_SPEED_MPS = 11.1 

def load_or_download_graph():
    if os.path.exists(GRAPH_FILENAME):
        print(f"Loading local map data ({GRAPH_FILENAME})...")
        return ox.load_graphml(GRAPH_FILENAME)
    print("Downloading NYC road network... (1-3 mins)")
    G = ox.graph_from_point((40.7505, -73.9834), dist=8000, network_type='drive')
    ox.save_graphml(G, GRAPH_FILENAME)
    return G

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    lambda1, lambda2 = math.radians(lon1), math.radians(lon2)
    a = math.sin((phi2 - phi1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin((lambda2 - lambda1)/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def custom_search(graph, start_node, goal_node, blocked_edges, env, weather_zones, algorithm="astar"):
    start_time = time.perf_counter()
    pq = [(0, start_node)]
    came_from = {start_node: None}
    cost_so_far = {start_node: 0.0} 
    explored_edges_list = [] 

    goal_lat, goal_lng = float(graph.nodes[goal_node]['y']), float(graph.nodes[goal_node]['x'])
    global_weather_mult = {'clear': 1.0, 'rain': 1.4, 'snow': 2.2}.get(env.weather, 1.0)
    traffic_mult = {'light': 1.0, 'heavy': 1.8, 'gridlock': 3.5}.get(env.traffic, 1.0)

    while pq:
        current_priority, current = heapq.heappop(pq)
        if came_from[current] is not None: explored_edges_list.append((came_from[current], current))
        if current == goal_node: break

        for neighbor in graph.neighbors(current):
            if (current, neighbor) in blocked_edges or (neighbor, current) in blocked_edges: continue 

            min_length = min([data.get('length', 1.0) for data in graph.get_edge_data(current, neighbor).values()])
            n_lat, n_lng = float(graph.nodes[neighbor]['y']), float(graph.nodes[neighbor]['x'])
            
            local_weather_mult = global_weather_mult
            for zone in weather_zones:
                if haversine(n_lat, n_lng, zone.lat, zone.lng) <= zone.radius:
                    local_weather_mult = 1.4 if zone.type == 'rain' else 2.2
                    break 

            new_cost = cost_so_far[current] + ((min_length / BASE_SPEED_MPS) * local_weather_mult * traffic_mult)

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + (haversine(n_lat, n_lng, goal_lat, goal_lng) / BASE_SPEED_MPS) if algorithm == "astar" else new_cost
                heapq.heappush(pq, (priority, neighbor))
                came_from[neighbor] = current

    end_time = time.perf_counter()
    path, final_distance = [], 0.0
    if goal_node in came_from:
        curr = goal_node
        while curr is not None:
            path.append(curr)
            prev = came_from[curr]
            if prev is not None: final_distance += min([float(data.get('length', 1.0)) for data in graph.get_edge_data(prev, curr).values()])
            curr = prev
        path.reverse() 

    return path, explored_edges_list, round((end_time - start_time) * 1000, 2), round(cost_so_far.get(goal_node, 0.0) / 60, 1), final_distance

def get_true_path_geometry(graph, path_nodes):
    coords = []
    if not path_nodes: return coords
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i+1]
        min_edge = min(graph.get_edge_data(u, v).values(), key=lambda x: x.get('length', float('inf')))
        if 'geometry' in min_edge: coords.extend([[float(lat), float(lon)] for lon, lat in min_edge['geometry'].coords])
        else: coords.append([float(graph.nodes[u]['y']), float(graph.nodes[u]['x'])])
    coords.append([float(graph.nodes[path_nodes[-1]]['y']), float(graph.nodes[path_nodes[-1]]['x'])])
    return coords