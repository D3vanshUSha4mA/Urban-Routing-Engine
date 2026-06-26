from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import SimulationPayload
import engine
import osmnx as ox

app = FastAPI(title="Logistics Routing Simulator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

G = None

@app.on_event("startup")
def startup_event():
    global G
    print("\n--- INITIALIZING MAP GRAPH ---")
    G = engine.load_or_download_graph()
    print("System Ready!\n------------------------------\n")

@app.post("/simulate-route")
def simulate_route(payload: SimulationPayload):
    if G is None: raise HTTPException(status_code=503, detail="Server is still loading the map. Please wait.")
        
    try:
        start_node = ox.distance.nearest_nodes(G, X=payload.origin.lng, Y=payload.origin.lat)
        end_node = ox.distance.nearest_nodes(G, X=payload.destination.lng, Y=payload.destination.lat)
        waypoint_nodes = [ox.distance.nearest_nodes(G, X=wp.lng, Y=wp.lat) for wp in payload.waypoints]
        
        blocked_edges = set()
        if payload.obstacles:
            obs_x, obs_y = [obs[1] for obs in payload.obstacles], [obs[0] for obs in payload.obstacles]
            for u, v, key in ox.distance.nearest_edges(G, X=obs_x, Y=obs_y): blocked_edges.add((u, v))

        def get_node_coords(n): return float(G.nodes[n]['y']), float(G.nodes[n]['x'])
        
        # Sequencer
        current_node = start_node
        unvisited = waypoint_nodes.copy()
        ordered_stops = []
        while unvisited:
            curr_lat, curr_lng = get_node_coords(current_node)
            next_node = min(unvisited, key=lambda n: engine.haversine(curr_lat, curr_lng, get_node_coords(n)[0], get_node_coords(n)[1]))
            ordered_stops.append(next_node)
            unvisited.remove(next_node)
            current_node = next_node

        full_sequence = [start_node] + ordered_stops + [end_node]
        final_path_dij, final_exp_dij, final_path_ast, final_exp_ast = [], [], [], []
        t_dij, m_dij, d_dij, t_ast, m_ast, d_ast = 0, 0, 0, 0, 0, 0

        # Router
        for i in range(len(full_sequence) - 1):
            s_node, e_node = full_sequence[i], full_sequence[i+1]
            p_d, e_d, t_d, m_d, dist_d = engine.custom_search(G, s_node, e_node, blocked_edges, payload.environment, payload.weather_zones, "dijkstra")
            p_a, e_a, t_a, m_a, dist_a = engine.custom_search(G, s_node, e_node, blocked_edges, payload.environment, payload.weather_zones, "astar")

            if not p_a: raise HTTPException(status_code=404, detail="A roadblock is completely cutting off a destination.")

            if i == 0:
                final_path_dij.extend(p_d); final_path_ast.extend(p_a)
            else:
                final_path_dij.extend(p_d[1:]); final_path_ast.extend(p_a[1:]) 
            
            final_exp_dij.extend(e_d); final_exp_ast.extend(e_a)
            t_dij += t_d; m_dij += m_d; d_dij += dist_d
            t_ast += t_a; m_ast += m_a; d_ast += dist_a

        def edges_to_lines(edge_list): return [[[float(G.nodes[u]['y']), float(G.nodes[u]['x'])], [float(G.nodes[v]['y']), float(G.nodes[v]['x'])]] for u, v in edge_list]

        return {
            "status": "success",
            "metrics": {
                "dijkstra": {"compute_ms": round(t_dij, 2), "edges_explored": len(final_exp_dij), "distance_meters": round(d_dij, 2), "est_time_mins": round(m_dij, 1)},
                "astar": {"compute_ms": round(t_ast, 2), "edges_explored": len(final_exp_ast), "distance_meters": round(d_ast, 2), "est_time_mins": round(m_ast, 1)}
            },
            "geometries": {
                "final_path": engine.get_true_path_geometry(G, final_path_ast), 
                "dijkstra_footprint": edges_to_lines(final_exp_dij), 
                "astar_footprint": edges_to_lines(final_exp_ast)
            }
        }
    except Exception as e: raise HTTPException(status_code=500, detail=f"Graph Error: {str(e)}")