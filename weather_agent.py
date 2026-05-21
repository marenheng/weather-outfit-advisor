#!/usr/bin/env python3
"""
AI-drevet værmelding for norske byer.

Claude fungerer som agent med tre verktøy:
  - get_coordinates   → finn koordinater via OpenStreetMap
  - get_current_weather → nåværende vær fra yr.no
  - get_forecast       → flerdagers varsel fra yr.no

Bruk: python weather_agent.py
Krever: ANTHROPIC_API_KEY som miljøvariabel
"""

import json
import urllib.request
from datetime import datetime
from urllib.parse import quote

import anthropic

MODEL = "claude-opus-4-7"
client = anthropic.Anthropic()

SYSTEM_PROMPT = """\
Du er en norsk værmelding-assistent. Du hjelper brukere med vær og antrekksråd \
for norske byer ved hjelp av sanntidsdata fra yr.no.

Arbeidsflyt:
1. Bruk get_coordinates for å finne koordinater til ønsket by.
2. Bruk get_current_weather for nåværende vær og/eller get_forecast for flerdagers varsel.
3. Gi klare, konkrete råd tilpasset temperatur, vind og nedbør.

Du husker data du allerede har hentet og kan svare på oppfølgingsspørsmål uten å \
kalle verktøyene på nytt.\
"""

TOOLS = [
    {
        "name": "get_coordinates",
        "description": "Finn geografiske koordinater (bredde- og lengdegrad) for en norsk by.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Navn på norsk by, f.eks. 'Stavanger'",
                }
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_current_weather",
        "description": "Hent nåværende værforhold for en posisjon via yr.no.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "string", "description": "Breddegrad"},
                "lon": {"type": "string", "description": "Lengdegrad"},
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "get_forecast",
        "description": "Hent flerdagers værvarsel (representativt tidspunkt per dag) via yr.no.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "string", "description": "Breddegrad"},
                "lon": {"type": "string", "description": "Lengdegrad"},
                "days": {
                    "type": "integer",
                    "description": "Antall dager fremover (1–7). Standard: 3.",
                },
            },
            "required": ["lat", "lon"],
        },
    },
]


# ── Tool implementations ───────────────────────────────────────────────────────

def get_coordinates(city: str) -> dict:
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={quote(city)},Norway&format=json&limit=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weatherapp/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    if not data:
        return {"error": f"Finner ikke '{city}' i Norge."}
    return {
        "lat": data[0]["lat"],
        "lon": data[0]["lon"],
        "display_name": data[0]["display_name"],
    }


def get_current_weather(lat: str, lon: str) -> dict:
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weatherapp/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    ts = data["properties"]["timeseries"][0]
    details = ts["data"]["instant"]["details"]
    next_hour = ts["data"].get("next_1_hours", {})
    return {
        "time": ts["time"],
        "temperature_c": details["air_temperature"],
        "wind_speed_ms": details["wind_speed"],
        "humidity_pct": details.get("relative_humidity"),
        "precipitation_next_hour_mm": next_hour.get("details", {}).get(
            "precipitation_amount", 0
        ),
        "condition": next_hour.get("summary", {}).get("symbol_code", ""),
    }


def get_forecast(lat: str, lon: str, days: int = 3) -> dict:
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weatherapp/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())

    days = max(1, min(days, 7))
    daily: dict[str, dict] = {}

    for entry in data["properties"]["timeseries"]:
        dt = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")

        if len(daily) >= days and date_str not in daily:
            break

        hour = dt.hour
        # Prefer the reading closest to noon as representative for each day
        if date_str not in daily or abs(hour - 12) < abs(daily[date_str]["_h"] - 12):
            d = entry["data"]["instant"]["details"]
            next6 = entry["data"].get("next_6_hours", {})
            daily[date_str] = {
                "_h": hour,
                "date": date_str,
                "temperature_c": d["air_temperature"],
                "wind_speed_ms": d["wind_speed"],
                "precipitation_6h_mm": next6.get("details", {}).get(
                    "precipitation_amount", 0
                ),
                "condition": next6.get("summary", {}).get("symbol_code", ""),
            }

    forecast = []
    for entry in list(daily.values())[:days]:
        entry.pop("_h", None)
        forecast.append(entry)

    return {"forecast": forecast}


# ── Tool dispatch ──────────────────────────────────────────────────────────────

TOOL_FNS = {
    "get_coordinates": lambda i: get_coordinates(i["city"]),
    "get_current_weather": lambda i: get_current_weather(i["lat"], i["lon"]),
    "get_forecast": lambda i: get_forecast(i["lat"], i["lon"], i.get("days", 3)),
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FNS.get(name)
    if fn is None:
        return json.dumps({"error": f"Ukjent verktøy: {name}"})
    try:
        result = fn(tool_input)
    except Exception as exc:
        result = {"error": str(exc)}
    return json.dumps(result, ensure_ascii=False)


# ── Agent loop ─────────────────────────────────────────────────────────────────

def agent_loop(messages: list) -> str:
    """
    Run the Claude agentic loop.

    Claude decides which tools to call and when. The loop continues until
    stop_reason == 'end_turn', at which point we return Claude's final reply.
    """
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Always append the assistant turn before processing
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return next(b.text for b in response.content if b.type == "text")

        # Execute tool calls and collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [{block.name}]", flush=True)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": execute_tool(block.name, block.input),
                }
            )

        messages.append({"role": "user", "content": tool_results})


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("🌤️  AI-drevet værmelding for Norge")
    print("Spør om vær, antrekk eller varsel for norske byer.")
    print("Skriv 'avslutt' for å avslutte.\n")

    messages: list = []

    while True:
        try:
            user_input = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHa det bra!")
            break

        if user_input.lower() in {"avslutt", "exit", "quit", "q"}:
            print("Ha det bra!")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        reply = agent_loop(messages)
        print(f"\nAssistent: {reply}\n")


if __name__ == "__main__":
    main()
