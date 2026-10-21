# Intelligence Hub

A personal Streamlit terminal for world news, politics, sports, elections, conflicts, markets and commodity futures. Uses free public feeds; no API keys required.

## Deploy on Streamlit Community Cloud
1. Sign in at https://share.streamlit.io using GitHub.
2. Create an app from `anthmamo1184/intelligence-hub`, branch `main`, file `app.py`.
3. Deploy. Python 3.11 or 3.12 is recommended.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Features
- Dark responsive interface, Oxanium / Share Tech Mono web fonts with monospace fallback.
- RSS headlines and excerpts, search, channel filters, source links and brief dialogs.
- Feed checks every three minutes while the session is open, with cached fetches and source status.
- Session-only keyword watchlist alerts (no background push notifications).
- Yahoo Finance daily market charts and futures watchlist: gold, silver, Brent, WTI, gas, copper, platinum, palladium, wheat, corn and coffee; US index watchlist.
- Wikidata election calendar from seven days ago to 180 days ahead. Community-maintained dates are incomplete and can change.
- Polling CSV uploader with actual individual poll points and clickable source table. Automatic global polling, poll averages, live election counts and seat projections are not connected.

Polling CSV columns: `country,election,pollster,fieldwork_end,party,percent,sample_size,source_url`. Use one row per party per poll, dates in YYYY-MM-DD, percentages from 0 to 100 and positive sample sizes. Upload only published comparable voting-intention polls. Uploaded data and controls are per session and are not saved to the repository.

## Sources and limitations
BBC RSS https://feeds.bbci.co.uk/ ; Al Jazeera https://www.aljazeera.com/xml/rss/all.xml ; Google News election RSS (publisher redirect links); Yahoo Finance https://finance.yahoo.com/markets/commodities/ via yfinance; Wikidata https://query.wikidata.org/ . Headlines and excerpts retain publisher attribution and link to original reports; check publisher feed terms before redistribution or commercial use.

Commodity prices are futures observations with units shown, not spot quotes or dealer prices. Daily changes compare the last two available closes. Contracts can roll, and quotes can be delayed or unavailable. Data is for personal informational use. Free Yahoo endpoints can throttle or change without notice. Missing feeds/prices display unavailable rather than fabricated values. RSS may be cached for 3 minutes, market data 10 minutes and election dates 6 hours. Undated stories are excluded from time-filtered feeds. Story duplication is reduced using normalized headlines; coverage counts describe the retrieved feed only. Conflict channels contain regional reporting, not independently confirmed military events. No map or event verification engine is included in this version.
