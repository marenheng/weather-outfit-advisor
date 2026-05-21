# AI-drevet værmelding for Norge

Et agentisk AI-system som bruker Claude som orkestrator og sanntids-API-er som verktøy. Claude avgjør selv hvilke verktøy som trengs, i hvilken rekkefølge, og når svaret er klart.

## Hva er agentisk AI?

I motsetning til et klassisk script der flyten er fastkodet, fungerer Claude her som en autonom agent:

```
Bruker: "Hva bør jeg ha på meg i Bergen i morgen?"

Claude:
  1. → kaller get_coordinates("Bergen")
  2. → kaller get_forecast(lat, lon, days=2)
  3. → analyserer data og formulerer et konkret antrekksråd
```

Claude bestemmer selv hvilke verktøy den trenger basert på spørsmålet — ikke programmereren.

## Arkitektur

```
┌─────────────────────────────────────────────┐
│                  Claude (LLM)               │
│  • Forstår intensjon                        │
│  • Velger og sekvenserer verktøykall        │
│  • Husker kontekst på tvers av spørsmål     │
└────────────┬────────────────────────────────┘
             │ tool_use / tool_result
     ┌───────┴────────────────────────┐
     │         Verktøylag             │
     ├────────────────────────────────┤
     │ get_coordinates  → Nominatim   │
     │ get_current_weather → yr.no    │
     │ get_forecast        → yr.no    │
     └────────────────────────────────┘
```

### Agentisk løkke (`agent_loop`)

```python
while True:
    response = client.messages.create(model=MODEL, tools=TOOLS, messages=messages)
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        return response          # Claude er ferdig

    # Utfør verktøykallene Claude ba om
    tool_results = [execute_tool(b.name, b.input) for b in response.content if b.type == "tool_use"]
    messages.append({"role": "user", "content": tool_results})
    # → neste iterasjon: Claude får resultatene og fortsetter
```

Løkken kjører til `stop_reason == "end_turn"`. Mellom iterasjonene er det Claude — ikke koden — som bestemmer hva som skjer.

## Funksjoner

- **Nåværende vær** — temperatur, vind, luftfuktighet, nedbør neste time
- **Flerdagers varsel** — opptil 7 dager, representativt klokkeslett per dag (nærmest kl. 12)
- **Antrekksråd** — konkrete råd tilpasset værforholdene
- **Samtalehukommelse** — stilte spørsmål uten at Claude trenger å hente data på nytt

## Eksempel

```
Du: Hvordan er været i Stavanger nå?

  [get_coordinates]
  [get_current_weather]

Assistent: Det er 12°C i Stavanger akkurat nå med lett bris (4 m/s).
Himmelen er overskyet, og det er ikke ventet nedbør den neste timen.
Ha gjerne med en lett jakke.

Du: Hva med de neste dagene?

  [get_forecast]

Assistent: Her er varselet for Stavanger de neste tre dagene:
• Torsdag: 11°C, lett regn, vind 5 m/s — regnjakke anbefales
• Fredag: 14°C, delvis skyet — lett jakke holder
• Lørdag: 16°C, pent vær — fin dag for uteaktivitet!
```

## Komme i gang

**Krav:** Python 3.10+, en [Anthropic API-nøkkel](https://console.anthropic.com/)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...   # Windows: $env:ANTHROPIC_API_KEY = "sk-ant-..."
python weather_agent.py
```

## Teknisk stack

| Komponent | Teknologi |
|---|---|
| LLM / Agent | Claude Opus 4.7 (Anthropic) |
| Geocoding | Nominatim / OpenStreetMap |
| Værvarsling | MET Norway / yr.no (`locationforecast/2.0`) |
| Avhengigheter | `anthropic` (ingen andre) |

## Sammenligning: script vs. agent

| | `weather.py` (klassisk) | `weather_agent.py` (agentisk) |
|---|---|---|
| Flyt | Fastkodet if/elif | Claude bestemmer |
| Verktøyvalg | Hardkodet | Dynamisk |
| Samtale | Enkeltspørsmål | Flertrinns dialog |
| Utvidbarhet | Ny kode per funksjon | Nytt verktøy i `TOOLS`-lista |
| Språkforståelse | Ingen | Full NLU via LLM |