import os
import googlemaps
from dotenv import load_dotenv
load_dotenv()


class GMapsService:
    def __init__(self):
        self._api_key = os.getenv('GOOGLE_MAPS_API_KEY', None)
        self._instance = googlemaps.Client(key=self._api_key)
    
    def get_api_key(self):
        return self._api_key

    def get_instance(self):
        return self._instance
    
    def search_nearby(self, current_place):
        gmaps = self.get_instance()
        places_nearby = gmaps.places_nearby(
            location=current_place,
            radius=30*1000,
            language='id',
            keyword='psikolog, psikiater, terdekat',
            type='health'
        )
        return places_nearby['results']

    def get_details(self, place_id):
        gmaps = self.get_instance()
        place = gmaps.place(place_id=place_id, language='id')
        return place['result']

    def get_places_nearby(self, location):
        search_results = self.search_nearby(location)
        formatted_result = []
        i = 0
        for result in search_results:
            if (i >= 5):
                break
            else:
                i = i + 1
            detail = self.get_details(result['place_id'])
            res = {
                'url': detail.get('url'),
                'name': detail.get('name'),
                'formatted_address': detail.get('vicinity'),
                'rating': result.get('rating', 0.0),
                'rating_user': result.get('user_ratings_total', 0),
                'rank': i,
                'open_now': result.get('opening_hours', {}).get('open_now')
            }
            formatted_result.append(res)
        return formatted_result

    def get_geocode_result(self, query):
        gmaps = self.get_instance()
        geocode_result = gmaps.geocode(address=query, language='id')
        print(geocode_result)
        if len(geocode_result) == 0:
            return None, None
        else:
            result = geocode_result[0]
            location = result.get('geometry', {}).get('location')
            if location == None:
                return None, None
            else:
                lat = location.get('lat')
                long = location.get('lng')
                return lat, long
