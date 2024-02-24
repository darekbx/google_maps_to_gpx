import re
import sys
import polyline
import requests
import googlemaps
from xml.dom import minidom
from urllib.parse import unquote, urlparse, parse_qs

'''Google Maps route url converter to GPX format

Usage:
1. Define route on Google Maps
2. Copy url from the browser and set in script, you can also use short url
3. Set your api key
4. Set mode
5. Run `python ./maps_to_gpx.py`

Note: 
Usage requires your own API Google Maps Directions API key. 
Before executing please install required components, see requirements.txt file

'''

class Colors:
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class GMapsRouteToGPX: 
    
    DEBUG = True

    LAT_PATTERN = r'!2d(-?\d+\.\d+)'
    LNG_PATTERN = r'!1d(-?\d+\.\d+)'

    def convert_to_gxp(self, url, mode, maps_api_key):
        if url == "" or maps_api_key == "":
            print(f"{Colors.FAIL}Please provide url and api key{Colors.ENDC}")
            sys.exit(1)

        # Parse Google Maps url and extract origin, destination and added waypoints
        try:
            map_points = self._extract_points_from_url(url)
        except Exception as e:
            if self.DEBUG:
                print(e)

        if not map_points:
            print(f"{Colors.FAIL}Failed to read points from url{Colors.ENDC}")
            sys.exit(1)

        # Pass locations from url to Google Directions API to create a route in defined mode
        try:
            path_points = self._extract_route(map_points, mode, maps_api_key)
        except Exception as e:
            if self.DEBUG:
                print(e)
              
        if not path_points:
            print(f"{Colors.FAIL}Failed to extract route, check your google maps api key{Colors.ENDC}")
            sys.exit(1)

        # Create GPX file
        self._create_gpx(path_points)

    def _extract_points_from_url(self, url):
        # Extract short url
        if len(url) < 50:
            response = requests.get(url)
            url = unquote(response.url)
        
        url_parts = url.split("/")
        dir_index = url_parts.index("dir") + 1
        end_start_locations = url_parts[dir_index:dir_index + 2]
        match = re.search(r'data=([^&]+)', url)

        if match:
            data_value = match.group(1)
            parts = data_value.split(":")
            points = []
            for part in parts:
                lat_match = re.search(self.LAT_PATTERN, part)
                lng_match = re.search(self.LNG_PATTERN, part)
                if lat_match and lng_match:
                    lat = lat_match.group(1)
                    lng = lng_match.group(1)
                    points.append((lat, lng))

            return [end_start_locations[1]] + points + [end_start_locations[0]]

    def _extract_route(self, points, mode, maps_api_key):
        client = googlemaps.Client(maps_api_key)
        directions_result = client.directions(origin=points[0], destination=points[-1], mode=mode, waypoints=points)
        return polyline.decode(directions_result[0]['overview_polyline']['points'])
    
    def _create_gpx(self, line):
        root = minidom.Document() 
        
        xml = root.createElement('gpx')  
        root.appendChild(xml) 

        # Add metadata
        metadata = root.createElement('metadata') 

        metadata_name = root.createElement('name') 
        metadata_name.appendChild(root.createTextNode("Python Google Maps to GPX"))
        metadata.appendChild(metadata_name)

        metadata_homepage = root.createElement('homepage') 
        metadata_homepage.appendChild(root.createTextNode("https://github.com/darekbx/gmaps_to_gpx"))
        metadata.appendChild(metadata_homepage)

        xml.appendChild(metadata) 

        # Create track with one segment
        trk = root.createElement('trk')
        trkseg = root.createElement('trkseg')
        
        for point in line:
            trkpt = root.createElement('trkpt') 
            trkpt.setAttribute('lat', f"{point[0]}")
            trkpt.setAttribute('lon', f"{point[1]}")
            trkseg.appendChild(trkpt) 
        
        trk.appendChild(trkseg)
        xml.appendChild(trk) 

        # Print xml, with one tab indent
        xml_str = root.toprettyxml(indent="\t")  
        print(xml_str)


if __name__ == "__main__":
    mode = "bicycling" # driving, walking, bicycling, transit

    key = "" # Your Google Directions Api key
    url = "https://maps.app.goo.gl/WAmYXKV8AkDkAdpz6" # Sample url
    
    GMapsRouteToGPX().convert_to_gxp(url, mode, key)
