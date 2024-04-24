from flask import Flask, render_template
from flask import Flask, jsonify, request
import pandas as pd
import geopy.geocoders
from geopy.distance import geodesic
import folium
app = Flask(__name__, static_url_path='/static')

# Define routes
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/BicycleApp', methods=['GET'])
def map():
    return get_nearest_bicycles()

@app.route('/login')
def login():
    return render_template('login.html')

def get_nearest_bicycles():
    bicycle_data = pd.read_parquet("bicycle_data.parquet")

    geolocator = geopy.geocoders.Nominatim(user_agent="bicycle_app")

    default_location = ""

    location_type = request.args.get('location_type', 'live')
    if location_type == 'live':
        user_location = geolocator.geocode("me")
    else:
        city_name = request.args.get('city_name', default_location)
        user_location = geolocator.geocode(city_name)

    if user_location:
        user_latitude = user_location.latitude
        user_longitude = user_location.longitude

        mymap = folium.Map(location=[user_latitude, user_longitude], zoom_start=5)

        folium.Marker([user_latitude, user_longitude], popup="Me", icon=folium.Icon(color='red')).add_to(mymap)

        def calculate_distance(bicycle):
            bicycle_latitude = bicycle['Latitude']
            bicycle_longitude = bicycle['Longitude']
            distance = geodesic((user_latitude, user_longitude), (bicycle_latitude, bicycle_longitude)).kilometers
            return round(distance, 2)

        nearest_bicycles = bicycle_data.copy()
        nearest_bicycles['Distance'] = nearest_bicycles.apply(calculate_distance, axis=1)
        nearest_bicycles = nearest_bicycles.sort_values(by='Distance').head(10)

        for idx, bicycle in nearest_bicycles.iterrows():
            popup_text = f"Bicycle ID: {bicycle['BicycleID']}<br>Distance: {bicycle['Distance']} km"
            folium.Marker([bicycle['Latitude'], bicycle['Longitude']], popup=popup_text).add_to(mymap)

        list_html = "<h2 style='margin-bottom: 20px;'>Nearest Bicycles</h2><ul style='list-style-type: none; padding: 0;'>"
        for idx, bicycle in nearest_bicycles.iterrows():
            list_html += f"<li style='margin-bottom: 10px;'>Bicycle ID: {bicycle['BicycleID']} - Distance: {bicycle['Distance']} km</li>"
        list_html += "</ul>"

        html_content = f"""
       <div style="text-align: center; background-color: black; color: white; padding: 20px;">
    <h1>Bicycle Locator</h1>
    <form action="/" method="get" style="font-size: 18px;">
        <input type="radio" id="live_location" name="location_type" value="live" {'' if location_type == 'live' else ''}>
        <label for="live_location">Live Location</label>
        <input type="radio" id="input_city" name="location_type" value="input" {'' if location_type == 'input' else ''}>
        <label for="input_city" style="font-size: 18px;">City Name:</label>
        <input type="text" id="city_name" name="city_name" value="{default_location}" style="font-size: 18px;">
        <input type="submit" value="Submit" style="font-size: 18px;">
    </form>

        <p style="font-size: 18px;"> City: {city_name if location_type == 'input' else 'Live Location'}</p>
        <div style="margin: 0 auto; width: 1600px; height: 400px; margin-top: 20px;">{mymap.get_root().render()}</div>
        <div style="margin: 0 auto;">{list_html}</div>
    </div>
        """

        return html_content
    else:
        return jsonify({"error": "Please check your internet connection."})

if __name__ == '__main__':
    app.run(debug=True)
