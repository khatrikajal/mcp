import requests



from server.config import WEATHER_API_KEY

class WeatherService:
    
    def get_weather(self, city:str):
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric",
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    
    
