// Initialize map centered on Midtown Manhattan
const map = L.map('map', {zoomControl: false}).setView([40.7505, -73.9834], 14); 
L.control.zoom({position: 'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', { 
    attribution: '&copy; OpenStreetMap', maxZoom: 19 
}).addTo(map);

// Global State Variables
let startMarker = null; 
let endMarker = null; 
let blockedMarkers = []; 
let activeWeatherZones = []; 
let waypoints = []; 
let animationInterval;

// Leaflet Layer Groups
let astarLayer = L.layerGroup().addTo(map);
let dijkstraLayer = L.layerGroup().addTo(map);
let pathLayer = L.layerGroup().addTo(map);
let roadblockLayer = L.layerGroup().addTo(map);
let weatherLayer = L.layerGroup().addTo(map); 
let waypointLayer = L.layerGroup().addTo(map); 

// Helper function to create map dots
const createDot = (color) => L.circleMarker([0,0], { 
    radius: 5, fillColor: color, color: color, fillOpacity: 1, shadowColor: color, shadowBlur: 10 
});

// Map Click Listener
map.on('click', function(e) {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const lat = e.latlng.lat; 
    const lng = e.latlng.lng;

    if (mode === 'start') {
        if (startMarker) map.removeLayer(startMarker);
        startMarker = createDot('#60a5fa').setLatLng([lat, lng]).addTo(map);
        document.getElementById('startInput').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    } else if (mode === 'end') {
        if (endMarker) map.removeLayer(endMarker);
        endMarker = createDot('#f87171').setLatLng([lat, lng]).addTo(map);
        document.getElementById('endInput').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    } else if (mode === 'waypoint') {
        createDot('#a855f7').setLatLng([lat, lng]).addTo(waypointLayer);
        waypoints.push({lat: lat, lng: lng});
    } else if (mode === 'block') {
        L.circleMarker([lat, lng], { radius: 4, fillColor: '#ef4444', color: 'transparent', fillOpacity: 0.8 }).addTo(roadblockLayer);
        blockedMarkers.push([lat, lng]);
    }
});

// Clear Map Logic
function resetMap() {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    startMarker = null; endMarker = null; blockedMarkers = []; activeWeatherZones = []; waypoints = [];
    
    document.getElementById('startInput').value = ""; 
    document.getElementById('endInput').value = "";
    
    astarLayer.clearLayers(); dijkstraLayer.clearLayers();
    pathLayer.clearLayers(); roadblockLayer.clearLayers(); 
    weatherLayer.clearLayers(); waypointLayer.clearLayers();
    
    document.getElementById('mode-start').checked = true;
    document.getElementById('stats').style.display = 'none';
    
    const runBtn = document.getElementById('runBtn');
    runBtn.innerText = "Execute Sequence"; runBtn.disabled = false;
    clearInterval(animationInterval);
}

// Chaos Monkey Generator
function triggerChaos() {
    document.getElementById('weatherSelect').value = 'snow';
    document.getElementById('trafficSelect').value = 'gridlock';

    roadblockLayer.clearLayers();
    weatherLayer.clearLayers();
    blockedMarkers = []; activeWeatherZones = [];

    // Add 4 Blizzards
    for(let i=0; i<4; i++) {
        let type = Math.random() > 0.5 ? 'rain' : 'snow';
        let lat = 40.7000 + Math.random() * (40.8000 - 40.7000);
        let lng = -74.0200 + Math.random() * (-73.9300 - (-74.0200));
        let radius = 1000 + Math.random() * 1500;
        
        activeWeatherZones.push({type: type, lat: lat, lng: lng, radius: radius});
        let color = type === 'snow' ? '#ffffff' : '#3b82f6';
        L.circle([lat, lng], { radius: radius, color: color, fillColor: color, fillOpacity: 0.1, weight: 1 }).addTo(weatherLayer);
    }

    // Add 60 Roadblocks
    for(let i=0; i<60; i++) {
        let lat = 40.7000 + Math.random() * (40.8000 - 40.7000);
        let lng = -74.0200 + Math.random() * (-73.9300 - (-74.0200));
        L.circleMarker([lat, lng], { radius: 4, fillColor: '#ef4444', color: 'transparent', fillOpacity: 0.8 }).addTo(roadblockLayer);
        blockedMarkers.push([lat, lng]);
    }
    
    // Auto-calculate if points exist
    if (startMarker && endMarker) runSimulation();
}

// API Call and Orchestration
async function runSimulation() {
    if (!startMarker || !endMarker) return alert("Set an Origin and Destination to complete the sequence.");

    astarLayer.clearLayers(); dijkstraLayer.clearLayers(); pathLayer.clearLayers();
    clearInterval(animationInterval);

    const runBtn = document.getElementById('runBtn');
    runBtn.innerText = "Processing..."; runBtn.disabled = true;

    const payload = {
        origin: { lat: startMarker.getLatLng().lat, lng: startMarker.getLatLng().lng },
        destination: { lat: endMarker.getLatLng().lat, lng: endMarker.getLatLng().lng },
        environment: { weather: document.getElementById('weatherSelect').value, traffic: document.getElementById('trafficSelect').value },
        obstacles: blockedMarkers,
        weather_zones: activeWeatherZones,
        waypoints: waypoints
    };

    try {
        const response = await fetch(`http://127.0.0.1:8000/simulate-route`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok && data.status === "success") {
            runBtn.innerText = "Execute Sequence"; runBtn.disabled = false;
            document.getElementById('stats').style.display = 'block';
            
            document.getElementById('time-static').innerText = `${data.metrics.dijkstra.est_time_mins} min`;
            document.getElementById('dist-static').innerText = `${(data.metrics.dijkstra.distance_meters / 1000).toFixed(2)} km`;
            document.getElementById('nodes-static').innerText = data.metrics.dijkstra.edges_explored;
            
            document.getElementById('time-dynamic').innerText = `${data.metrics.astar.est_time_mins} min`;
            document.getElementById('dist-dynamic').innerText = `${(data.metrics.astar.distance_meters / 1000).toFixed(2)} km`;
            document.getElementById('nodes-dynamic').innerText = data.metrics.astar.edges_explored;
            
            animateAlgorithms(data.geometries);
        } else {
            alert("Simulation Error: " + data.detail);
            runBtn.innerText = "Execute Sequence"; runBtn.disabled = false;
        }
    } catch (err) {
        alert("Connection Failure.");
        runBtn.innerText = "Execute Sequence"; runBtn.disabled = false;
    }
}

// Animation Loop
function animateAlgorithms(geoms) {
    const dijEdges = geoms.dijkstra_footprint; 
    const astEdges = geoms.astar_footprint; 
    const finalPath = geoms.final_path;
    let d_idx = 0; let a_idx = 0; const speed = 25;

    animationInterval = setInterval(() => {
        let finished = true;
        
        if (a_idx < astEdges.length) {
            for(let i=0; i<speed && a_idx < astEdges.length; i++) {
                L.polyline(astEdges[a_idx], {color: '#93c5fd', weight: 1, opacity: 0.9}).addTo(astarLayer);
                a_idx++;
            }
            finished = false;
        }
        
        if (d_idx < dijEdges.length) {
            for(let i=0; i<speed && d_idx < dijEdges.length; i++) {
                L.polyline(dijEdges[d_idx], {color: '#334155', weight: 1, opacity: 0.5}).addTo(dijkstraLayer);
                d_idx++;
            }
            finished = false;
        }
        
        if (finished) {
            clearInterval(animationInterval);
            // Draw final glowing path
            L.polyline(finalPath, {color: '#ffffff', weight: 6, opacity: 0.2}).addTo(pathLayer);
            L.polyline(finalPath, {color: '#ffffff', weight: 2, opacity: 1.0}).addTo(pathLayer);
        }
    }, 10); 
}