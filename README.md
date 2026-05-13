# 🌤️ Weather Outfit Advisor

A Python command-line app that gives you outfit recommendations based on real-time weather data.

## What it does
- Fetches live weather data from the Norwegian Meteorological Institute (yr.no)
- Detects rain, snow, sleet, wind and fog
- Gives clothing advice based on current conditions

## How to run

1. Clone the repository
2. Install dependencies (no external packages needed!)
3. Run the app:

python chatbot.py

## Example output
Enter your city: Stavanger
🌡️ Temperature: 12.4°C
💨 Wind speed: 4.0 m/s
👗 Outfit advice:
👕 Mild weather – a sweater or light jacket should do.

## Technologies used
- Python 3
- Yr.no / Met.no Weather API
- OpenStreetMap Nominatim API (for city coordinates)