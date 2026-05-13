import urllib.request
import json
from urllib.parse import quote

def get_coordinates(city):
    url = f"https://nominatim.openstreetmap.org/search?q={quote(city)},Norway&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "weatherapp/1.0"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    if not data:
        return None, None
    return data[0]["lat"], data[0]["lon"]

def get_weather(lat, lon):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    req = urllib.request.Request(url, headers={"User-Agent": "weatherapp/1.0"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    timeseries = data["properties"]["timeseries"][0]
    details = timeseries["data"]["instant"]["details"]
    next_hour = timeseries["data"].get("next_1_hours", {})
    symbol = next_hour.get("summary", {}).get("symbol_code", "")
    return {
        "temperature": details["air_temperature"],
        "wind_speed": details["wind_speed"],
        "precipitation": next_hour.get("details", {}).get("precipitation_amount", 0),
        "symbol": symbol
    }

def get_outfit_advice(weather):
    temp = weather["temperature"]
    wind = weather["wind_speed"]
    rain = weather["precipitation"]
    symbol = weather["symbol"]

    advice = []

    # Temperature advice
    if temp < 0:
        advice.append("🧥 Freezing outside! Wear a winter coat, hat and gloves.")
    elif temp < 10:
        advice.append("🧣 Pretty cold – a warm jacket and scarf are a good idea.")
    elif temp < 18:
        advice.append("👕 Mild weather – a sweater or light jacket should do.")
    else:
        advice.append("☀️ Warm and nice! T-shirt and shorts are perfect.")

    # Snow advice
    if "heavysnow" in symbol:
        advice.append("❄️ Heavy snowfall! Wear waterproof boots and thick wool layers.")
    elif "snow" in symbol:
        advice.append("🌨️ Snow expected – wear warm waterproof boots and layers.")
    elif "sleet" in symbol:
        advice.append("🌧️❄️ Sleet expected – waterproof jacket and boots are a must!")

    # Rain advice
    elif "heavyrain" in symbol:
        advice.append("🌧️ Heavy rain – definitely bring a raincoat and waterproof shoes!")
    elif "rain" in symbol:
        advice.append("☔ Rain expected – bring an umbrella or raincoat.")
    elif "drizzle" in symbol:
        advice.append("🌦️ Light drizzle – a light rain jacket should be enough.")

    # Wind advice
    if wind > 15:
        advice.append("💨 Very windy! Avoid loose clothing and hold on to your hat!")
    elif wind > 10:
        advice.append("💨 Quite windy – avoid loose clothing.")

    # Fog advice
    if "fog" in symbol:
        advice.append("🌫️ Foggy outside – wear bright or reflective clothing if possible.")

    return "\n".join(advice)

# Main program
city = input("Enter your city: ")
lat, lon = get_coordinates(city)

if not lat:
    print("City not found, please try again.")
else:
    weather = get_weather(lat, lon)
    print(f"\n🌡️ Temperature: {weather['temperature']}°C")
    print(f"💨 Wind speed: {weather['wind_speed']} m/s")
    print(f"🌧️ Precipitation: {weather['precipitation']} mm")
    print(f"🌤️ Condition: {weather['symbol']}\n")
    print("👗 Outfit advice:")
    print(get_outfit_advice(weather))