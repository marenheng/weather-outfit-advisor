# Weather Outfit Advisor

Et lite Python-program som henter sanntidsvær for et sted i Norge og gir råd om hva du bør ha på deg.

## Hvordan det fungerer

1. Du skriver inn en by.
2. Programmet slår opp koordinatene via **Nominatim (OpenStreetMap)**.
3. Det henter været akkurat nå fra **MET Norway / yr.no** (`locationforecast/2.0`): temperatur, vind, nedbør neste time og værsymbol.
4. Ut fra disse verdiene gir det konkrete antrekksråd for kulde, regn, snø, sludd, vind og tåke.

## Eksempel

```
Enter your city: Bergen

🌡️ Temperature: 9.4°C
💨 Wind speed: 6.1 m/s
🌧️ Precipitation: 0.8 mm
🌤️ Condition: lightrain

👗 Outfit advice:
🧣 Pretty cold – a warm jacket and scarf are a good idea.
☔ Rain expected – bring an umbrella or raincoat.
```

## Kom i gang

Krever Python 3.8 eller nyere. Programmet bruker bare standardbiblioteket, så du trenger ikke installere noe.

```bash
python chatbot.py
```

## Teknisk

| Del | Løsning |
|---|---|
| Språk | Python (kun standardbiblioteket: `urllib`, `json`) |
| Stedsoppslag | Nominatim / OpenStreetMap |
| Værdata | MET Norway / yr.no, `locationforecast/2.0/compact` |
| Antrekksråd | Regelbasert logikk på temperatur, vind, nedbør og værsymbol |

## Videre ideer

- Varsel for flere dager fram i tid
- Råd tilpasset aktivitet, for eksempel løping eller sykling
- Enkelt webgrensesnitt
