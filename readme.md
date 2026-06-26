# Urban Logistics & Routing Simulator

A high-performance pathfinding engine that demonstrates the efficiency gains of **A* DPRD (Dynamic Pathfinding with Real-time Data)** over standard Dijkstra algorithms in complex, obstacle-filled urban environments like New York City.

## Key Features
- **Cinematic Visualization:** Uses Leaflet and custom CSS to provide a professional, dark-mode geospatial dashboard.
- **Dynamic DPRD Engine:** Routes are calculated based on real-time weights including traffic severity and weather conditions.
- **Chaos Monkey Testing:** A stress-testing feature that generates randomized weather zones and roadblocks to force the algorithm into complex detours.
- **Logistics Sequencer:** Implements a Greedy Traveling Salesperson approach to order unlimited waypoints before routing.

## Technology Stack
- **Backend:** FastAPI, NetworkX, OSMnx, Python.
- **Frontend:** HTML5, Leaflet.js, CSS3 (Cinematic Styling).

## How to Run
1. Navigate to the backend: `cd backend`
2. Run server: `uvicorn main:app --reload`
3. Navigate to the frontend: `cd frontend`
4. Run server: `python -m http.server 5500`