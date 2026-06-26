import osmnx as ox
import os

def download_and_save_graph(center_point, distance, filepath):
    print(f"Downloading street network within {distance} meters of {center_point}...")
    
    try:
        # Fetch the driving network as a MultiDiGraph
        G = ox.graph_from_point(center_point, dist=distance, network_type='drive')
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Use OSMnx's native save function to handle LineString geometries correctly
    ox.save_graphml(G, filepath)
    
    print(f"Graph successfully saved to {filepath}")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

if __name__ == "__main__":
    # Coordinates centered near the main academic area
    iit_coords = (22.3149, 87.3105) 
    output_path = "../data/kharagpur_drive.graphml"
    
    # 5000 meters (5km) radius
    download_and_save_graph(iit_coords, 5000, output_path)