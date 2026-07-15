from flask import Flask, render_template, request, jsonify
import folium
import requests
import os
import webbrowser
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

# Haversine formula to calculate distance between any two points in India instantly
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Radius of Earth in KM
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return 2 * R * asin(sqrt(a))

def get_loc(name):
    try:
        # We search specifically for locations in India
        url = f"https://nominatim.openstreetmap.org/search?q={name}, India&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'IndiaNavigatorPro'}, timeout=3).json()
        return [float(r[0]['lat']), float(r[0]['lon'])] if r else None
    except: return None

@app.route('/')
def index():
    return render_template('mylocation.html')

@app.route('/generate_ai_route', methods=['POST'])
def generate_ai_route():
    data = request.get_json()
    s_txt, e_txt = data.get('start', '').lower(), data.get('end', '').lower()
    
    s_coords = [data.get('lat'), data.get('lon')] if s_txt == "my location" else get_loc(s_txt)
    e_coords = get_loc(e_txt)

    if not s_coords or not e_coords:
        return jsonify({"status": "Error", "msg": "Location not found in India."})

    all_routes = []
    # AI TRY: 
    for p in ['driving', 'walking', 'cycling']:
        try:
            url = f"http://router.project-osrm.org/route/v1/{p}/{s_coords[1]},{s_coords[0]};{e_coords[1]},{e_coords[0]}?overview=full&geometries=geojson"
            res = requests.get(url, timeout=5).json()
            if "routes" in res:
                path = [[c[1], c[0]] for c in res['routes'][0]['geometry']['coordinates']]
                dist = res['routes'][0]['distance'] / 1000
                all_routes.append({"path": path, "dist": dist})
        except: continue 

    # MAP GENERATION
    m = folium.Map(location=s_coords, zoom_start=6) # Zoomed out for India-wide view
    
    if all_routes:
        shortest = min(all_routes, key=lambda x: x['dist'])
        for r in all_routes:
            is_best = (r['dist'] == shortest['dist'])
            folium.PolyLine(r['path'], color="#00008B" if is_best else "#8A2BE2", weight=6 if is_best else 3).add_to(m)
        msg = f"AI Success! {round(shortest['dist'], 2)} km via road."
    else:
        # FAIL-SAFE: Instant Mathematical Path for any two points in India
        direct_dist = haversine(s_coords[0], s_coords[1], e_coords[0], e_coords[1])
        folium.PolyLine([s_coords, e_coords], color="red", weight=4, dash_array='10', tooltip="Direct Path").add_to(m)
        msg = f"AI Timeout: Displaying direct Indian path ({round(direct_dist, 2)} km)."
    
    folium.Marker(s_coords, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(e_coords, popup="End", icon=folium.Icon(color='red')).add_to(m)

    map_file = os.path.abspath("india_route.html")
    m.save(map_file)
    webbrowser.open(f"file://{map_file}")
    #------distance-------
    print(dist)
    #-----------------------
    return jsonify({"status": "Success", "msg": msg})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
print(dist)







