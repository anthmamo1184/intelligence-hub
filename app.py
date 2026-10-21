from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
import hashlib
import json
from html.parser import HTMLParser
import re
from urllib.parse import quote, urlencode, urlparse
from zoneinfo import ZoneInfo

import feedparser
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
import trafilatura

st.set_page_config(page_title="INTELLIGENCE HUB", page_icon="◈", layout="wide")
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'Share Tech Mono',monospace;}
h1,h2,h3,[data-testid="stMetricLabel"],button,p label {font-family:'Oxanium',monospace!important;}
.stApp {background:radial-gradient(ellipse at 80% 0%,#11283a 0%,#070d17 55%);}
[data-testid="stMainBlockContainer"],.block-container{padding-top:4.5rem!important;max-width:1550px;padding-left:2rem;padding-right:2rem;}
h1,h2,h3{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;}
.brief-title{font-family:Oxanium,monospace;font-size:1.15rem;line-height:1.5;color:#e1edf7;white-space:normal;overflow-wrap:anywhere;margin:0 0 1rem;}
@media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem;}h1{font-size:1.45rem!important;letter-spacing:2px!important;}}
h1{letter-spacing:4px!important;font-size:2.1rem!important;margin-bottom:0!important;}
h2{font-size:1.2rem!important;letter-spacing:2px;}
h3{font-size:1rem!important;}
[data-testid="stMetric"]{background:#0d1928;border:1px solid #214252;border-top:2px solid #40e0d0;padding:12px;border-radius:5px;}
[data-testid="stMetricValue"]{font-size:1.45rem;}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#21374a!important;}
.stButton>button{border:1px solid #285269;background:#101f2e;color:#9eece8;font-size:.8rem;}
.stButton>button:hover{border-color:#40e0d0;box-shadow:0 0 12px #40e0d022;}
.tag{color:#40e0d0;letter-spacing:2px;font-size:.72rem;}
.headline{font-family:'Oxanium',monospace;font-size:1rem;line-height:1.5;color:#e1edf7;}
.sport-headline{font-family:Oxanium,monospace;font-size:.88rem;line-height:1.4;min-height:3.8em;}
.meta{font-size:.73rem;color:#8ba5b9;}
[data-testid="stDialog"]>div{background:#0d1928;border:1px solid #286070;}
.mini-brand{font-family:Oxanium,monospace;font-size:.8rem;letter-spacing:2px;color:#7896aa;margin:0 0 .25rem;}
.st-key-overview_kpis [data-testid="stMetric"]{padding:6px 10px!important;min-height:0!important;}
.st-key-overview_kpis [data-testid="stMetricLabel"] p{font-size:.65rem!important;letter-spacing:.5px;}
.st-key-overview_kpis [data-testid="stMetricValue"]{font-size:1.05rem!important;}
.st-key-commodity_controls [data-testid="stVerticalBlock"]{gap:.25rem!important;}
.st-key-commodity_controls{margin-bottom:.15rem;}
.st-key-overview_pulse [data-testid="stMetric"]{padding:4px 8px!important;border:0;background:transparent;}
.st-key-overview_pulse [data-testid="stMetricValue"]{font-size:1.2rem!important;}
[class*="st-key-desk_kpis_"] [data-testid="stMetric"]{padding:5px 8px!important;}
[class*="st-key-desk_kpis_"] [data-testid="stMetricValue"]{font-size:1.1rem!important;}
.desk-excerpt{font-size:.78rem;line-height:1.5;color:#9db4c7;margin:.25rem 0 .65rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
UTC = timezone.utc
LOCAL = ZoneInfo("Europe/Malta")
HEADERS = {"User-Agent": "IntelligenceHub/1.0 (personal RSS reader)"}
FEEDS = {
    "World": [("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"), ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml")],
    "Politics": [("BBC Politics", "https://feeds.bbci.co.uk/news/politics/rss.xml")],
    "Sports": [("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml")],
    "Markets": [("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml")],
    "Conflicts": [("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"), ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml")],
    "Elections": [("Google News · elections", "https://news.google.com/rss/search?" + urlencode({"q": "election polls voting when:7d", "hl": "en-GB", "gl": "GB", "ceid": "GB:en"}))],
}
ASSETS = {
    "Gold": ("GC=F", "USD / troy oz"), "Silver": ("SI=F", "USD / troy oz"),
    "Brent oil": ("BZ=F", "USD / barrel"), "WTI oil": ("CL=F", "USD / barrel"),
    "Natural gas": ("NG=F", "USD / MMBtu"), "Copper": ("HG=F", "USD / lb"),
    "Platinum": ("PL=F", "USD / troy oz"), "Palladium": ("PA=F", "USD / troy oz"),
    "Wheat": ("ZW=F", "US cents / bushel"), "Corn": ("ZC=F", "US cents / bushel"),
    "Coffee": ("KC=F", "US cents / lb"), "S&P 500": ("^GSPC", "index points"),
    "Nasdaq": ("^IXIC", "index points"), "Dow Jones": ("^DJI", "index points"),
}


MARKET_PRESETS = {
    "S&P 500": ("^GSPC", "index points"), "Nasdaq": ("^IXIC", "index points"),
    "Dow Jones": ("^DJI", "index points"), "FTSE 100": ("^FTSE", "index points"),
    "DAX": ("^GDAXI", "index points"), "CAC 40": ("^FCHI", "index points"),
    "Euro Stoxx 50": ("^STOXX50E", "index points"), "Nikkei 225": ("^N225", "index points"),
    "Hang Seng": ("^HSI", "index points"), "Brazil Bovespa": ("^BVSP", "index points"),
    "EUR / USD": ("EURUSD=X", "USD per EUR"), "GBP / USD": ("GBPUSD=X", "USD per GBP"),
    "USD / BRL": ("BRL=X", "BRL per USD"), "EUR / BRL": ("EURBRL=X", "BRL per EUR"),
    "Bitcoin": ("BTC-USD", "USD"), "Ethereum": ("ETH-USD", "USD"),
}


SPORT_FEEDS = {
    "All Sports": ("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml"),
    "Football": ("BBC Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    "Tennis": ("BBC Tennis", "https://feeds.bbci.co.uk/sport/tennis/rss.xml"),
    "Basketball": ("BBC Basketball", "https://feeds.bbci.co.uk/sport/basketball/rss.xml"),
    "Motorsports": ("BBC Motorsport", "https://feeds.bbci.co.uk/sport/motorsport/rss.xml"),
    "General": ("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml"),
    "Cricket": ("BBC Cricket", "https://feeds.bbci.co.uk/sport/cricket/rss.xml"),
    "Rugby": ("BBC Rugby Union", "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml"),
}


def clean(value):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", str(value)))).strip()


def safe_url(value):
    value = str(value)
    return value if urlparse(value).scheme in {"https", "http"} else ""


@st.cache_data(ttl=180, show_spinner=False)
def fetch_feed(category, source, url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if not parsed.entries:
            raise ValueError("No articles returned")
        items = []
        for entry in parsed.entries[:30]:
            link = safe_url(entry.get("link", ""))
            if not link:
                continue
            try:
                stamp = parsedate_to_datetime(entry.get("published", entry.get("updated", "")))
                stamp = stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp
            except (ValueError, TypeError):
                stamp = None
            publisher = clean(entry.get("source", {}).get("title", source))
            items.append(dict(title=clean(entry.get("title", "Untitled")), url=link,
                              summary=clean(max([entry.get("summary", "")] + [c.get("value", "") for c in entry.get("content", [])], key=lambda text: len(clean(text))))[:6000], source=publisher,
                              category=category, published=stamp.isoformat() if stamp else None))
        return items, None
    except Exception:
        return [], source + ": unavailable on this check"


def news_data():
    jobs = [(c, s, u) for c, feeds in FEEDS.items() for s, u in feeds]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: fetch_feed(*job), jobs))
    seen, articles, errors = set(), [], []
    for rows, error in results:
        if error:
            errors.append(error)
        for row in rows:
            key = re.sub(r"\W", "", row["title"]).lower()
            if key not in seen:
                seen.add(key)
                articles.append(row)
    return sorted(articles, key=lambda a: a["published"] or "", reverse=True), errors


def timestamp(value):
    return datetime.fromisoformat(value).astimezone(LOCAL).strftime("%d %b %H:%M") + " Malta" if value else "Publication time unavailable"


class ArticlePreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_article = 0
        self.in_paragraph = False
        self.in_json = False
        self.buffer = []
        self.scripts = []
        self.paragraphs = []
        self.description = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            self.in_article += 1
        if tag == "p" and self.in_article:
            self.in_paragraph = True
            self.buffer = []
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.in_json = True
            self.json_buffer = []
        if tag == "meta" and (attrs.get("property") == "og:description" or attrs.get("name") == "description"):
            self.description = clean(attrs.get("content", "")) or self.description

    def handle_data(self, data):
        if self.in_json:
            self.json_buffer.append(data)
        elif self.in_paragraph:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "article":
            self.in_article = max(0, self.in_article-1)
        if tag == "p" and self.in_paragraph:
            text = clean(" ".join(self.buffer))
            if len(text.split()) >= 10:
                self.paragraphs.append(text)
            self.in_paragraph = False
        if tag == "script" and self.in_json:
            self.scripts.append("".join(self.json_buffer))
            self.in_json = False


def article_body(node):
    if isinstance(node, dict):
        if isinstance(node.get("articleBody"), str):
            return node["articleBody"]
        for value in node.values():
            found = article_body(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = article_body(value)
            if found:
                return found
    return ""


def short_preview(text, words=280):
    tokens = clean(text).split()
    return " ".join(tokens[:words]) + (" …" if len(tokens)>words else "")


@st.cache_data(ttl=1800, show_spinner=False)
def article_preview(url):
    # Only known public publishers; never follow redirects to another host.
    allowed = {"www.bbc.co.uk", "bbc.co.uk", "www.bbc.com", "bbc.com", "www.aljazeera.com", "aljazeera.com"}
    try:
        for _ in range(3):
            if urlparse(url).scheme != "https" or urlparse(url).hostname not in allowed:
                return ""
            response = requests.get(url, headers=HEADERS, timeout=7, allow_redirects=False)
            if response.is_redirect:
                from urllib.parse import urljoin
                url = urljoin(url, response.headers.get("Location", ""))
                continue
            response.raise_for_status()
            if "html" not in response.headers.get("Content-Type", ""):
                return ""
            extracted = trafilatura.extract(response.text[:2000000], url=url,
                include_comments=False, include_tables=False, favor_precision=True)
            if extracted and len(extracted.split()) >= 80:
                return short_preview(extracted, 280)
            parser = ArticlePreviewParser()
            parser.feed(response.text[:2000000])
            for script in parser.scripts:
                try:
                    body = article_body(json.loads(script))
                    if body:
                        return short_preview(body)
                except (ValueError, TypeError):
                    continue
            if parser.paragraphs:
                return short_preview(" ".join(parser.paragraphs[:10]), 280)
            return short_preview(parser.description)
        return ""
    except Exception:
        return ""


@st.dialog("SOURCE BRIEF", width="large")
def story_dialog(item):
    st.markdown(f'<div class="brief-title">{escape(item["title"])}</div>', unsafe_allow_html=True)
    st.caption(f'{item["source"]} · {timestamp(item["published"])}')
    summary = short_preview(item["summary"], 280)
    with st.spinner("Loading source preview…"):
        preview = article_preview(item["url"])
    # Prefer a longer source excerpt; never pad a short feed with generated claims.
    text = preview if len(preview.split()) > len(summary.split()) else summary
    if text:
        st.markdown("#### REPORT BRIEF")
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"])", text)
        paragraph, length = [], 0
        for sentence in sentences:
            paragraph.append(sentence)
            length += len(sentence.split())
            if length >= 65:
                st.write(" ".join(paragraph))
                paragraph, length = [], 0
        if paragraph:
            st.write(" ".join(paragraph))
    else:
        st.write("Open the original report to read the story.")
    if len(text.split()) < 50:
        st.caption("Only a short preview is available from this source. Read the full report below.")
    st.link_button("OPEN ORIGINAL REPORT ↗", item["url"], use_container_width=True)
    st.caption("Source excerpt · up to 280 words when accessible · not an AI-written analysis. Inclusion does not independently verify claims.")


def stories(items, prefix, limit=18):
    if not items:
        st.info("No matching stories. Try a wider filter, or check source status.")
    for item in items[:limit]:
        with st.container(border=True):
            st.markdown(f'<div class="tag">{escape(item["category"].upper())}</div><div class="headline">{escape(item["title"])}</div>', unsafe_allow_html=True)
            st.caption(f'{item["source"]} · {timestamp(item["published"])}')
            left, right = st.columns([1, 1])
            uid = hashlib.sha256(item["url"].encode()).hexdigest()[:16]
            if left.button("OPEN BRIEF", key=f"{prefix}_{uid}", use_container_width=True):
                story_dialog(item)
            right.link_button("SOURCE ↗", item["url"], use_container_width=True)


def sports_panel():
    st.subheader("SPORTS / NEWS DESK")
    options = list(SPORT_FEEDS)
    if "sports_choice" not in st.session_state:
        st.session_state.sports_choice = "All Sports"
    for start in range(0, len(options), 4):
        for col, label in zip(st.columns(4), options[start:start+4]):
            if col.button(label.upper(), key="sport_filter_"+label,
                          type="primary" if st.session_state.sports_choice == label else "secondary",
                          use_container_width=True):
                st.session_state.sports_choice = label
                st.rerun()
    choice = st.session_state.sports_choice
    source, url = SPORT_FEEDS[choice]
    jobs = [(source, url)]
    if choice == "Motorsports":
        jobs.append(("BBC Formula 1", "https://feeds.bbci.co.uk/sport/formula1/rss.xml"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda job: fetch_feed("Sports", *job), jobs))
    rows, seen = [], set()
    for entries, error in results:
        if error:
            st.caption(error)
        for row in entries:
            if row["url"] not in seen:
                rows.append(row)
                seen.add(row["url"])
    cutoff = datetime.now(UTC)-timedelta(hours=age)
    rows = [r for r in rows if r["published"] and datetime.fromisoformat(r["published"]) >= cutoff]
    if search.strip():
        rows = [r for r in rows if search.casefold() in (r["title"]+" "+r["summary"]).casefold()]
    if choice == "General":
        rows = [r for r in rows if not re.search(r"/(football|tennis|basketball|motorsport|formula1|cricket|rugby-union)/", r["url"])]
    rows.sort(key=lambda r:r["published"] or "", reverse=True)
    st.caption(f"{choice.upper()} · {len(rows)} stories in selected window · General shows other sports from the main feed")
    if not rows:
        st.info("No stories available for this sport in the selected window. Try a wider story window.")
    for start in range(0,len(rows),3):
        for col,item in zip(st.columns(3),rows[start:start+3]):
            with col,st.container(border=True):
                st.markdown(f'<div class="tag">{escape(choice.upper())}</div><div class="sport-headline">{escape(item["title"])}</div>',unsafe_allow_html=True)
                st.caption(f'{item["source"]} · {timestamp(item["published"])}')
                left,right=st.columns(2)
                uid=hashlib.sha256(item["url"].encode()).hexdigest()[:16]
                if left.button("BRIEF",key="sport_brief_"+uid,use_container_width=True):
                    story_dialog(item)
                right.link_button("SOURCE ↗",item["url"],use_container_width=True)


@st.cache_data(ttl=600, show_spinner=False)
def market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1y", interval="1d", auto_adjust=False, timeout=12)
        if data.empty:
            return None
        data = data.dropna(subset=["Close"]).sort_index()
        frame = data.reset_index()
        frame = frame[[c for c in ["Date", "Open", "High", "Low", "Close"] if c in frame.columns]]
        frame.attrs["currency"] = ticker.history_metadata.get("currency", "Quote currency unavailable")
        return frame
    except Exception:
        return None


def chart_window(frame, period):
    days = {"1M": 30, "3M": 90, "6M": 180, "1Y": 366}[period]
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
    return frame.loc[pd.to_datetime(frame["Date"], utc=True) >= cutoff].copy()


def display_price(value, unit):
    # Keep provider quote units exactly as supplied: GBp is pence, not GBP.
    currency = unit if isinstance(unit, str) and re.fullmatch(r"[A-Za-z]{3}", unit) else ""
    return f"{value:,.2f}" + (f" {currency}" if currency else "")


def price_figure(frame, unit, candle=False, compact=False):
    fig = go.Figure()
    if frame.empty:
        return fig
    first, last = float(frame["Close"].iloc[0]), float(frame["Close"].iloc[-1])
    color = "#40e0d0" if last >= first else "#ff6b86"
    candles = candle and {"Open", "High", "Low"}.issubset(frame.columns)
    if candles:
        fig.add_trace(go.Candlestick(x=frame["Date"], open=frame["Open"], high=frame["High"], low=frame["Low"], close=frame["Close"], increasing_line_color="#40e0d0", decreasing_line_color="#ff6b86", name="Daily OHLC"))
        low, high = float(frame["Low"].min()), float(frame["High"].max())
    else:
        fig.add_trace(go.Scatter(x=frame["Date"], y=frame["Close"], mode="lines", line=dict(color=color, width=2), name="Daily close", connectgaps=False, hovertemplate="%{x|%d %b %Y}<br><b>%{y:,.2f}</b> " + unit + "<extra></extra>"))
        low, high = float(frame["Close"].min()), float(frame["Close"].max())
    pad = max((high - low) * .15, abs(last) * .002, .001)
    fig.add_hline(y=first, line_dash="dot", line_color="#516579", line_width=1)
    fig.add_trace(go.Scatter(x=[frame["Date"].iloc[-1]], y=[last], mode="markers", marker=dict(color=color, size=7), showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=1, xref="paper", y=last, text=f"{last:,.2f}", showarrow=False, xanchor="right", yshift=13, font=dict(color=color, size=11), bgcolor="#101c2c")
    fig.update_layout(template="plotly_dark", height=195 if compact else 430,
        margin=dict(l=6, r=8, t=20, b=5), showlegend=False,
        font=dict(family="Share Tech Mono, monospace", color="#a8becf", size=10 if compact else 12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", hoverlabel=dict(bgcolor="#142638", font_size=12),
        dragmode=False if compact else "zoom",
        xaxis=dict(showgrid=False, tickformat="%d %b", nticks=4 if compact else 7, rangeslider_visible=False, fixedrange=compact, showspikes=True, spikemode="across"),
        yaxis=dict(range=[low-pad, high+pad], side="right", gridcolor="#203044", zeroline=False, tickformat=",.2f", nticks=4 if compact else 6, fixedrange=compact))
    return fig


@st.dialog("MARKET DETAIL", width="large")
def market_dialog(name, symbol, unit, frame):
    st.subheader(name.upper())
    st.caption(f"Yahoo Finance · {symbol} · {unit} · Daily observations")
    left, right = st.columns(2)
    period = left.radio("Chart range", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, key="detail_range_"+symbol)
    style = right.radio("Display", ["Line", "Candles"], horizontal=True, key="detail_style_"+symbol)
    view = chart_window(frame, period)
    if view.empty:
        st.info("No observations in this time range.")
        return
    first, last = float(view["Close"].iloc[0]), float(view["Close"].iloc[-1])
    cols = st.columns(3)
    cols[0].metric("LATEST", display_price(last, unit))
    cols[1].metric("PERIOD CHANGE", f"{(last/first-1)*100:+.2f}%" if first else "—")
    cols[2].metric("OBSERVATIONS", len(view))
    st.plotly_chart(price_figure(view, unit, candle=style=="Candles"), use_container_width=True,
        config={"displaylogo":False,"scrollZoom":False,"modeBarButtonsToRemove":["lasso2d","select2d"]}, key="detail_plot_"+symbol)
    st.caption("Hover for prices · drag to zoom · double-click to reset · dotted line = first close in selected range")
    if frame.attrs.get("conversion_note"):
        st.caption(frame.attrs["conversion_note"])
    st.link_button("YAHOO FINANCE ↗", f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/")
    with st.expander("VIEW PRICE DATA"):
        st.dataframe(view.sort_values("Date", ascending=False), hide_index=True, use_container_width=True)
    st.caption("Prices may be delayed. Latest daily bar may still be in progress. Futures, where selected, can roll between contracts and are not spot or physical retail prices. Period change compares first and last available closes in the selected range.")


def convert_commodity(frame, unit, currency="USD", metal_weight="Troy oz", fx=None):
    if frame is None or frame.empty:
        return None, unit
    out = frame.copy()
    columns = [c for c in ["Open","High","Low","Close"] if c in out]
    # Agricultural futures are quoted in US cents; normalise to dollars first.
    if unit.startswith("US cents"):
        out[columns] = out[columns]/100
        unit = unit.replace("US cents", "USD", 1)
    if currency == "EUR":
        if fx is None or fx.empty:
            return None, unit.replace("USD", "EUR")
        out["_date"] = pd.to_datetime(out["Date"]).dt.tz_localize(None).dt.normalize()
        rates = pd.DataFrame({"_fxdate":pd.to_datetime(fx["Date"]).dt.tz_localize(None).dt.normalize(),"_fx":pd.to_numeric(fx["Close"], errors="coerce")})
        rates = rates.dropna().loc[lambda x:x["_fx"]>0].sort_values("_fxdate").drop_duplicates("_fxdate",keep="last")
        if rates.empty:
            return None, unit.replace("USD", "EUR")
        out = pd.merge_asof(out.sort_values("_date"), rates, left_on="_date", right_on="_fxdate", direction="backward", tolerance=pd.Timedelta(days=7))
        out = out.dropna(subset=["_fx"])
        if out.empty:
            return None, unit.replace("USD", "EUR")
        out[columns] = out[columns].div(out["_fx"],axis=0)
        out = out.drop(columns=["_date","_fxdate","_fx"])
        unit = unit.replace("USD", "EUR", 1)
        out.attrs["conversion_note"] = "EUR estimate uses historical EUR/USD daily closes (same date or preceding available date, at most 7 days earlier). Candle OHLC values use one FX close per day, not intraday EUR quotes. Unmatched observations are omitted."
    if "troy oz" in unit and metal_weight == "Grams":
        out[columns] = out[columns]/31.1034768
        unit = unit.replace("troy oz", "gram")
    out.attrs["currency"] = currency
    return out, unit


def market_panel(names, assets=None, compact_controls=False, commodity_currency=None, metal_weight="Troy oz", selected_period=None):
    assets = ASSETS if assets is None else assets
    if selected_period is not None:
        period = selected_period
    elif compact_controls:
        period = st.radio("Chart range", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, label_visibility="collapsed", key="market_range_"+section)
    else:
        st.caption("Yahoo Finance · latest daily observations · prices may be delayed · cached 10 minutes")
        period = st.radio("TIME RANGE", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, key="market_range_"+section)
        st.caption("Price scales adapt to each asset. Teal = up over selected range; pink = down. Daily change appears beside the price.")
    with ThreadPoolExecutor(max_workers=4) as pool:
        frames = list(pool.map(lambda n: market_data(assets[n][0]), names))
    fx = market_data("EURUSD=X") if commodity_currency == "EUR" else None
    if commodity_currency == "EUR" and (fx is None or fx.empty):
        st.warning("EUR conversion unavailable: exchange-rate feed could not be loaded. Select USD to view source prices.")

    # Build actual rows so each asset keeps its position as cards change height.
    for offset in range(0, len(names), 3):
        cols = st.columns(3)
        for col, name, frame in zip(cols, names[offset:offset+3], frames[offset:offset+3]):
            symbol, unit = assets[name]
            if commodity_currency is not None:
                frame, unit = convert_commodity(frame, unit, commodity_currency, metal_weight, fx)
            with col, st.container(border=True):
                if frame is None or frame.empty:
                    st.metric(name, "Unavailable")
                    st.caption("Feed unavailable; no substitute price shown.")
                else:
                    view = chart_window(frame, period)
                    if unit == "Quote currency":
                        unit = frame.attrs.get("currency", "Quote currency unavailable")
                    close = float(frame["Close"].iloc[-1])
                    previous = float(frame["Close"].iloc[-2]) if len(frame)>1 else None
                    delta = f"{(close/previous-1)*100:+.2f}% vs prior close" if previous else None
                    st.metric(name, display_price(close, unit), delta)
                    unit_label = {"GBp": "GBp · British pence (100 GBp = 1 GBP)", "GBX": "GBX · British pence (100 GBX = 1 GBP)", "ZAc": "ZAc · South African cents", "ILA": "ILA · Israeli agorot"}.get(unit, unit)
                    st.caption(f'{unit_label} · {frame["Date"].iloc[-1]:%d %b %Y}')
                    if view.empty:
                        st.info("No observations in selected range.")
                    else:
                        st.plotly_chart(price_figure(view, unit, compact=True), use_container_width=True,
                            config={"displayModeBar":False,"scrollZoom":False}, key="card_plot_"+symbol)
                        first = float(view["Close"].iloc[0])
                        change = (float(view["Close"].iloc[-1])/first-1)*100 if first else None
                        st.caption(f'{period} change {change:+.2f}% · Low {view["Close"].min():,.2f} / High {view["Close"].max():,.2f}' if change is not None else "Period change unavailable")
                    if st.button("EXPAND CHART ↗", key="market_"+symbol, use_container_width=True):
                        market_dialog(name, symbol, unit, frame)
                st.link_button("SOURCE ↗", f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/")
    if compact_controls:
        st.caption("Yahoo Finance · daily prices may be delayed · teal/pink shows selected-period movement · watchlist lasts for this session")


@st.cache_data(ttl=900, show_spinner=False)
def company_search(query):
    try:
        rows = yf.Search(query, max_results=12, news_count=0, timeout=10).quotes
        return [dict(symbol=row["symbol"], name=row.get("longname") or row.get("shortname") or row["symbol"],
                     exchange=row.get("exchDisp") or row.get("exchange") or "Exchange unspecified",
                     kind=row.get("quoteType", "Instrument"))
                for row in rows if row.get("symbol")], None
    except Exception:
        return [], "Company search is temporarily unavailable. You can still use the market watchlist below."


def markets_page():
    st.subheader("MARKETS")
    if "company_watchlist" not in st.session_state:
        st.session_state.company_watchlist = {}
    with st.form("company_search_form", border=False):
        field, button = st.columns([5,1])
        query = field.text_input("Company name or ticker", placeholder="Search company or ticker…", label_visibility="collapsed")
        submitted = button.form_submit_button("SEARCH", use_container_width=True)
    if submitted:
        st.session_state.pop("company_result", None)
        if query.strip():
            with st.spinner("Searching…"):
                rows, error = company_search(query.strip()[:100])
            st.session_state.company_results = rows
            st.session_state.company_error = error
        else:
            st.session_state.company_results = []
            st.session_state.company_error = "Enter a company name or ticker."
    if st.session_state.get("company_error"):
        st.info(st.session_state.company_error)
    results = st.session_state.get("company_results", [])
    if results:
        listing, add, view, dismiss = st.columns([5,1,1,1])
        selected = listing.selectbox("Matching listings — check the exchange", results,
            format_func=lambda r:f'{r["name"]} · {r["symbol"]} · {r["exchange"]}',
            key="company_result", label_visibility="collapsed")
        if add.button("+ ADD", use_container_width=True, help="Add listing to charts below"):
            label = selected["name"]+" · "+selected["symbol"]
            st.session_state.company_watchlist[label] = (selected["symbol"], "Quote currency")
            current = st.session_state.get("global_market_selection", ["S&P 500","Nasdaq","Dow Jones"])
            if label not in current:
                st.session_state.global_market_selection = current+[label]
        if view.button("VIEW", use_container_width=True, help="Open detailed price chart"):
            with st.spinner("Loading chart…"):
                frame = market_data(selected["symbol"])
            if frame is None or frame.empty:
                st.info("Price history unavailable for this listing.")
            else:
                market_dialog(selected["name"],selected["symbol"],frame.attrs.get("currency","Quote currency unavailable"),frame)
        if dismiss.button("CLOSE", use_container_width=True, help="Hide search results"):
            st.session_state.company_results = []
            st.rerun()
    elif submitted and not st.session_state.get("company_error"):
        st.info("No listings found. Try a ticker or shorter name.")
    registry = {**MARKET_PRESETS, **st.session_state.company_watchlist}
    with st.expander("EDIT WATCHLIST", expanded=False):
        choices = st.multiselect("Markets and companies",list(registry),
            default=["S&P 500","Nasdaq","Dow Jones"]+list(st.session_state.company_watchlist),
            key="global_market_selection")
        st.caption("Choose indices, currencies, crypto or added companies. Choices last for this session.")
    if choices:
        market_panel(choices,registry,compact_controls=True)
    else:
        st.info("Open Edit watchlist to choose markets, or search for a company above.")





def election_bar(labels, values, title, percent=False):
    colors = {"Democrats":"#4c9dff", "Republicans":"#ff627d", "Independents":"#bf9bff", "Vacancies":"#5a687b", "Other candidate":"#bf9bff", "Not sure":"#65798e"}
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=[colors.get(x,"#40e0d0") for x in labels],
        text=[str(v)+("%" if percent else "") for v in values], textposition="auto",
        hovertemplate="%{y}: %{x}"+("%" if percent else " seats")+"<extra></extra>"))
    fig.update_layout(title=title, template="plotly_dark", height=270, margin=dict(l=5,r=20,t=45,b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Share Tech Mono, monospace"),
        xaxis=dict(range=[0,100] if percent else [0,max(values)*1.15], title="Percent" if percent else "Seats", gridcolor="#203044"),
        yaxis=dict(autorange="reversed"))
    return fig


def us_elections_panel():
    st.subheader("US ELECTIONS / CONGRESSIONAL CONTROL")
    election_day = datetime(2026,11,3,tzinfo=ZoneInfo("America/New_York"))
    days = (election_day.date()-datetime.now(ZoneInfo("America/New_York")).date()).days
    cols=st.columns(4)
    cols[0].metric("ELECTION DAY", "03 NOV 2026")
    cols[1].metric("DAYS TO ELECTION", max(days,0))
    cols[2].metric("HOUSE SEATS", "435")
    cols[3].metric("SENATE TOTAL", "100")
    st.caption("Congress = House of Representatives + Senate. All House seats and roughly one-third of Senate seats are elected every two years.")
    page=st.radio("US election view",["Control & seats","Published polling","Seat simulator","Reporting & sources"],horizontal=True,key="us_view")
    if page=="Control & seats":
        st.info("Membership snapshots checked 21 Oct 2026. These are existing seats, not projected 2026 winners or election-night results. They do not update automatically.")
        left,right=st.columns(2)
        with left:
            st.plotly_chart(election_bar(["Democrats","Republicans","Independents","Vacancies"],[214,218,1,2],"HOUSE / EXISTING MEMBERSHIP"),use_container_width=True)
            st.caption("435 seats · 218 is a majority of the full chamber. The majority required in a particular vote can depend on attendance and vacancies.")
            st.link_button("OFFICIAL HOUSE BREAKDOWN ↗","https://radiotv.house.gov/house-data/party-breakdown")
            st.caption("Source page last updated 2 Sep 2026; retrieved 21 Oct 2026.")
        with right:
            st.plotly_chart(election_bar(["Democrats","Republicans","Independents"],[45,53,2],"SENATE / EXISTING MEMBERSHIP"),use_container_width=True)
            st.caption("100 seats · 51 is an outright majority. A 50–50 split involves the vice-president's tie-breaking role. The two independents caucus with Democrats; party and caucus totals differ.")
            st.link_button("OFFICIAL SENATE MEMBERSHIP ↗","https://www.senate.gov/senators/")
            st.caption("Senate directory retrieved 21 Oct 2026.")
    elif page=="Published polling":
        st.markdown("### OFFICIAL POLLING SOURCES")
        st.info("No verified official polling dataset is connected. Poll percentages and trends will appear only when a dated dataset can be linked directly to the original polling organisation.")
        st.link_button("PEW RESEARCH / POLITICS ↗", "https://www.pewresearch.org/politics/")
        st.link_button("GALLUP / POLITICS ↗", "https://news.gallup.com/poll/173314/politics.aspx")
        st.caption("These are source directories, not live polling feeds. Opinion polls are surveys from polling organisations; certified results come from election authorities.")
        if days > 0:
            st.info("General-election exit polls are not yet available.")
        else:
            st.info("No verified exit-poll or live results feed is connected.")
    elif page=="Seat simulator":
        st.warning("ILLUSTRATIVE SCENARIO — manually selected seats, not a model, poll estimate or prediction.")
        house=st.slider("Hypothetical Democratic House seats",0,435,214,key="sim_house")
        rep_house=435-house
        st.plotly_chart(election_bar(["Democrats","Republicans"],[house,rep_house],"HOUSE / YOUR SCENARIO"),use_container_width=True)
        st.write(f'{"Democrats" if house>=218 else "Republicans"} hold a majority in this two-party scenario. Assumes all 435 seats filled and no independents.')
        senate=st.slider("Hypothetical Democratic-aligned Senate seats",0,100,47,key="sim_senate")
        st.plotly_chart(election_bar(["Democrats","Republicans"],[senate,100-senate],"SENATE / YOUR CAUCUS SCENARIO"),use_container_width=True)
        st.caption("Democratic-aligned total includes any independents assumed to caucus with Democrats. All remaining seats are assumed Republican-aligned.")
        st.write("50–50 split: vice-presidential tie-breaking role applies." if senate==50 else f'{"Democratic-aligned" if senate>50 else "Republican-aligned"} caucus has an outright majority in this scenario.')
    else:
        st.link_button("USAGOV / HOW CONGRESSIONAL ELECTIONS WORK ↗","https://www.usa.gov/midterm-elections")
        st.link_button("HOUSE / MEMBERSHIP ↗","https://radiotv.house.gov/house-data/party-breakdown")
        st.link_button("SENATE / MEMBERSHIP ↗","https://www.senate.gov/senators/")
        st.link_button("PEW / POLLING REPORT ↗","https://www.pewresearch.org/politics/")
        st.link_button("AP / ELECTION SURVEY METHODS ↗","https://www.ap.org/elections/our-role-in-the-u-s-elections/how-we-survey-the-electorate/")
        entries,error=fetch_feed("US Elections","Google News · US elections","https://news.google.com/rss/search?"+urlencode({"q":"US midterm House Senate election when:7d","hl":"en-US","gl":"US","ceid":"US:en"}))
        if error:st.caption(error)
        st.caption("Latest retrieved reporting below is refreshed from the news feed; membership snapshots above retain their stated dates.")
        stories(entries,"us_election_news",12)


@st.cache_data(ttl=21600, show_spinner=False)
def elections_calendar():
    now = datetime.now(UTC)
    start, end = (now - timedelta(days=7)).date(), (now + timedelta(days=180)).date()
    query = '''SELECT DISTINCT ?election ?electionLabel ?date ?countryLabel WHERE {
      ?election wdt:P31/wdt:P279* wd:Q40231; wdt:P585 ?date.
      FILTER(?date >= "STARTT00:00:00Z"^^xsd:dateTime && ?date <= "ENDT23:59:59Z"^^xsd:dateTime)
      OPTIONAL { ?election wdt:P17 ?country. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } ORDER BY ?date LIMIT 60'''.replace("START", str(start)).replace("END", str(end))
    try:
        r = requests.get("https://query.wikidata.org/sparql", params={"query": query, "format": "json"}, headers=HEADERS, timeout=15)
        r.raise_for_status()
        rows = r.json()["results"]["bindings"]
        return [dict(Election=x["electionLabel"]["value"], Country=x.get("countryLabel", {}).get("value", "Unspecified"), Date=x["date"]["value"][:10], Source=x["election"]["value"]) for x in rows], None
    except Exception:
        return [], "Election calendar feed is unavailable. Election reporting below remains available."


def news_desk(items, channel):
    st.subheader(channel.upper() + " / NEWS DESK")
    rows = [item for item in items if item["category"] == channel]
    topics = {
        "World": {"Diplomacy":r"diploma|summit|treaty|sanction|ambassador", "Economy":r"econom|inflation|trade|bank|budget", "Climate":r"climate|flood|storm|wildfire|earthquake", "Security":r"militar|attack|war|missile|defen[cs]|police"},
        "Politics": {"Elections":r"elect|vot|ballot|poll", "Government":r"government|minister|president|parliament|congress", "Policy":r"policy|reform|legislat|budget|tax", "Diplomacy":r"diploma|summit|treaty|sanction"},
        "Conflicts": {"Military":r"militar|troop|missile|drone|strike|attack", "Diplomacy":r"ceasefire|peace|talks|diploma|negotiat", "Humanitarian":r"humanitarian|refugee|displaced|civilian|aid", "Security":r"security|border|police|terror"}
    }[channel]
    selected = st.radio("TOPIC", ["All"]+list(topics), horizontal=True, key="desk_topic_"+channel, label_visibility="collapsed")
    controls, options = st.columns([3,1])
    sources = sorted({r["source"] for r in rows})
    with controls.popover("SOURCES / FILTER", use_container_width=True):
        selected_sources = st.multiselect("Publishers", sources, default=sources, key="desk_sources_"+channel)
        st.caption("Topic filters match words in headlines and feed summaries; categories can overlap.")
    limit = options.selectbox("Stories shown",[12,24,48],index=1,key="desk_limit_"+channel,label_visibility="collapsed")
    rows = [r for r in rows if r["source"] in selected_sources]
    if selected != "All":
        rows = [r for r in rows if re.search(topics[selected], r["title"]+" "+r["summary"], re.I)]
    rows.sort(key=lambda r:r["published"] or "",reverse=True)
    now = datetime.now(UTC)
    recent = sum(datetime.fromisoformat(r["published"]) >= now-timedelta(hours=6) for r in rows)
    with st.container(key="desk_kpis_"+channel):
        cols=st.columns(4)
        cols[0].metric("ARTICLES",len(rows))
        cols[1].metric("PUBLISHERS",len({r["source"] for r in rows}))
        cols[2].metric("LAST 6H / IN WINDOW",recent)
        latest=timestamp(rows[0]["published"]) if rows else "—"
        cols[3].metric("LATEST / MALTA",datetime.fromisoformat(rows[0]["published"]).astimezone(LOCAL).strftime("%H:%M") if rows else "—")
    if not rows:
        st.info("No stories match these filters. Try All, select a publisher or widen the story window.")
        return
    with st.expander("ACTIVITY & SOURCE BREAKDOWN", expanded=False):
        left,right=st.columns(2)
        data=pd.DataFrame(rows)
        data["Hour"]=pd.to_datetime(data["published"],utc=True).dt.floor("h")
        hours=pd.date_range((now-timedelta(hours=age)).replace(minute=0,second=0,microsecond=0),pd.Timestamp(now).floor("h"),freq="h")
        activity=data.groupby("Hour").size().reindex(hours,fill_value=0).rename("Articles").rename_axis("Hour").reset_index()
        activity["Hour"]=activity["Hour"].dt.tz_convert(LOCAL)
        fig=px.bar(activity,x="Hour",y="Articles",template="plotly_dark",color_discrete_sequence=["#40e0d0"])
        fig.update_layout(height=170,margin=dict(l=0,r=0,t=5,b=0),xaxis_title=None,yaxis_title=None)
        left.plotly_chart(fig,use_container_width=True,key="desk_activity_"+channel)
        counts=data["source"].value_counts().rename_axis("Publisher").reset_index(name="Articles")
        fig=px.bar(counts,x="Articles",y="Publisher",orientation="h",template="plotly_dark",color_discrete_sequence=["#40e0d0"])
        fig.update_layout(height=170,margin=dict(l=0,r=0,t=5,b=0),yaxis_title=None)
        right.plotly_chart(fig,use_container_width=True,key="desk_sources_chart_"+channel)
        st.caption("Counts cover filtered retrieved articles, not all reporting or confirmed events. Feed limits can leave older hours incomplete.")
    st.caption(f"{len(rows)} matching articles · showing {min(limit,len(rows))} · latest {latest}")
    if channel == "Conflicts":
        st.caption("Regional reporting includes non-conflict stories. Claims are attributed to publishers; article counts do not measure military activity.")
    for start in range(0,min(limit,len(rows)),3):
        for col,item in zip(st.columns(3),rows[start:min(start+3,limit)]):
            with col,st.container(border=True):
                st.markdown(f'<div class="sport-headline">{escape(item["title"])}</div>',unsafe_allow_html=True)
                st.caption(f'{item["source"]} · {timestamp(item["published"])}')
                if item["summary"]:
                    st.markdown(f'<div class="desk-excerpt">{escape(short_preview(item["summary"],42))}</div>',unsafe_allow_html=True)
                left,right=st.columns(2)
                uid=hashlib.sha256(item["url"].encode()).hexdigest()[:16]
                if left.button("BRIEF",key=f"desk_{channel}_{uid}",use_container_width=True):
                    story_dialog(item)
                right.link_button("SOURCE ↗",item["url"],use_container_width=True)


def overview_panel(items, errors):
    st.subheader("MARKET PULSE")
    basket = {name: ASSETS[name] if name in ASSETS else MARKET_PRESETS[name]
              for name in ["S&P 500", "Nasdaq", "Gold", "Silver", "Brent oil", "EUR / USD"]}
    with ThreadPoolExecutor(max_workers=4) as pool:
        frames = list(pool.map(lambda name: market_data(basket[name][0]), basket))
    movements = []
    with st.container(key="overview_pulse"):
        for offset in range(0, len(basket), 3):
            for col, name, frame in zip(st.columns(3), list(basket)[offset:offset+3], frames[offset:offset+3]):
                symbol, unit = basket[name]
                with col, st.container(border=True):
                    if frame is None or frame.empty:
                        st.metric(name, "Unavailable")
                        continue
                    close = float(frame["Close"].iloc[-1])
                    previous = float(frame["Close"].iloc[-2]) if len(frame) > 1 else None
                    change = (close / previous - 1) * 100 if previous else None
                    st.metric(name, f"{close:,.4f}" if " / " in name else f"{close:,.2f}",
                              f"{change:+.2f}%" if change is not None else None)
                    st.caption(f'{unit} · {frame["Date"].iloc[-1]:%d %b %Y}')
                    view = chart_window(frame, "1M")
                    if not view.empty:
                        fig = price_figure(view, unit, compact=True)
                        fig.update_layout(height=105, margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False}, key="pulse_"+symbol)
                    if st.button("DETAILS ↗", key="pulse_open_"+symbol, use_container_width=True):
                        market_dialog(name, symbol, unit, frame)
                    if change is not None:
                        movements.append({"Asset":name, "Daily change (%)":change})
    st.caption("Yahoo Finance · daily closes, delayed · mini-charts: 1 month · changes versus each asset’s prior close. Metals and oil are futures.")
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("NEWS ACTIVITY")
        if items:
            data = pd.DataFrame(items)
            data["Hour"] = pd.to_datetime(data["published"], utc=True).dt.floor("h")
            now_hour = pd.Timestamp.now(tz="UTC").floor("h")
            hours = pd.date_range((datetime.now(UTC)-timedelta(hours=age)).replace(minute=0,second=0,microsecond=0), now_hour, freq="h")
            activity = data.groupby("Hour").size().reindex(hours, fill_value=0).rename("Articles").rename_axis("Hour").reset_index()
            activity["Hour"] = activity["Hour"].dt.tz_convert(LOCAL)
            fig = px.bar(activity, x="Hour", y="Articles", template="plotly_dark", color_discrete_sequence=["#40e0d0"])
            fig.update_layout(height=210, margin=dict(l=0,r=0,t=5,b=0), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True, key="overview_activity")
        else:
            st.info("No articles match the current filters.")
        st.caption("Retrieved publication timestamps · Malta time · feed limits mean older hours may be incomplete.")
    with right:
        st.subheader("DAILY MARKET MOVES")
        if movements:
            move_data = pd.DataFrame(movements).sort_values("Daily change (%)")
            fig = px.bar(move_data, x="Daily change (%)", y="Asset", orientation="h", color="Daily change (%)",
                         color_continuous_scale=["#fa708e", "#40e0d0"], color_continuous_midpoint=0, template="plotly_dark")
            fig.update_layout(height=210, margin=dict(l=0,r=0,t=5,b=0), coloraxis_showscale=False, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True, key="overview_moves")
        else:
            st.info("Market feeds unavailable.")
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("CHANNEL COVERAGE")
        if items:
            counts = pd.Series([a["category"] for a in items]).value_counts().rename_axis("Channel").reset_index(name="Stories")
            fig = px.bar(counts, x="Stories", y="Channel", orientation="h", template="plotly_dark", color_discrete_sequence=["#40e0d0"])
            fig.update_layout(height=220, margin=dict(l=0,r=0,t=0,b=0), yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True, key="overview_coverage")
        st.caption("Filtered retrieved articles, not global event frequency or severity.")
    with right:
        st.subheader("NEXT ELECTIONS")
        rows, error = elections_calendar()
        upcoming = [r for r in rows if r["Date"] >= datetime.now(UTC).date().isoformat()]
        if upcoming:
            st.dataframe(pd.DataFrame(upcoming[:5]), hide_index=True, use_container_width=True,
                column_config={"Source":st.column_config.LinkColumn("Source ↗")})
        else:
            st.info(error or "No upcoming elections returned by the calendar.")
        st.caption("Wikidata calendar · dates require source verification. Polls and results remain in the election sections.")
    st.subheader("LATEST INTELLIGENCE")
    channels = ["All", "World", "Politics", "Elections", "Conflicts", "Markets", "Sports"]
    for tab, channel in zip(st.tabs(channels), channels):
        with tab:
            selected = items if channel == "All" else [a for a in items if a["category"] == channel]
            if not selected:
                st.caption("No matching stories in this window.")
            for offset in range(0, min(6, len(selected)), 2):
                for col, item in zip(st.columns(2), selected[offset:offset+2]):
                    with col, st.container(border=True):
                        st.markdown(f'<div class="tag">{escape(item["category"].upper())}</div><div class="sport-headline">{escape(item["title"])}</div>', unsafe_allow_html=True)
                        st.caption(f'{item["source"]} · {timestamp(item["published"])}')
                        a, b = st.columns(2)
                        uid = hashlib.sha256(item["url"].encode()).hexdigest()[:16]
                        if a.button("OPEN BRIEF", key=f"ov_{channel}_{uid}", use_container_width=True):
                            story_dialog(item)
                        b.link_button("SOURCE ↗", item["url"], use_container_width=True)
    with st.expander("FEED HEALTH"):
        st.write(f"{sum(map(len, FEEDS.values())) - len(errors)} / {sum(map(len, FEEDS.values()))} feeds available on last check")
        for error in errors:
            st.caption(error)
        st.caption("Search and story-window filters apply to news only. Market and calendar panels use their own source dates.")


with st.sidebar:
    st.markdown("## ◈ CONTROL PANEL")
    st.caption("REVISION 2026.10.21-13")
    section = st.radio("CHANNEL", ["Overview", "World", "Politics", "Sports", "Conflicts", "Elections", "US Elections", "Commodities", "Markets", "Sources"])
    search = st.text_input("SEARCH FEED", placeholder="Country, team, company…")
    age = st.selectbox("STORY WINDOW", [24, 48, 168], index=1, format_func=lambda n: f"Last {n} hours")
    auto = st.toggle("Auto-refresh every 3 minutes", value=True)
    if st.button("REFRESH FEEDS", use_container_width=True):
        st.cache_data.clear()


if section == "Overview":
    st.markdown('<div class="tag">GLOBAL MONITORING / PERSONAL TERMINAL</div>', unsafe_allow_html=True)
    st.title("INTELLIGENCE HUB")
    st.caption("WORLD • POLITICS • ELECTIONS • MARKETS • COMMODITIES • SPORT")
else:
    st.markdown('<div class="mini-brand">◈ INTELLIGENCE HUB</div>', unsafe_allow_html=True)


@st.fragment(run_every="180s" if auto else None)
def dashboard():
    with st.spinner("Checking source feeds…"):
        all_items, errors = news_data()
    cutoff = datetime.now(UTC) - timedelta(hours=age)
    items = [a for a in all_items if a["published"] and datetime.fromisoformat(a["published"]) >= cutoff]
    if search.strip():
        items = [a for a in items if search.casefold() in (a["title"] + " " + a["summary"]).casefold()]
    if section == "Overview":
        with st.container(key="overview_kpis"):
            a, b, c, d = st.columns(4)
            a.metric("STORIES IN WINDOW", len(items))
            b.metric("AVAILABLE FEEDS", sum(map(len, FEEDS.values())) - len(errors))
            c.metric("CHANNELS", len(FEEDS))
            d.metric("CHECKED · MALTA", datetime.now(LOCAL).strftime("%H:%M"))
        st.caption("Feed check · " + datetime.now(LOCAL).strftime("%H:%M Malta") + " · cached up to 3 minutes")
    if section == "Markets":
        markets_page()
    elif section == "Commodities":
        st.subheader("COMMODITIES")
        with st.container(key="commodity_controls"):
            money, weight, timeframe, assets_control = st.columns([1, 1.25, 2, 1])
            currency = money.selectbox("Currency", ["USD", "EUR"], label_visibility="collapsed", key="commodity_currency", help="Display currency")
            metal_weight = weight.selectbox("Precious-metal weight", ["Troy oz", "Grams"], label_visibility="collapsed", key="metal_weight", help="Weight unit for precious metals")
            period = timeframe.radio("Commodity chart range", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, label_visibility="collapsed", key="compact_commodity_period")
            with assets_control.popover("ASSETS", use_container_width=True):
                choices = st.multiselect("Choose commodities", list(ASSETS)[:11], default=list(ASSETS)[:6], key="commodity_asset_selection")
        market_panel(choices, commodity_currency=currency, metal_weight=metal_weight, selected_period=period)
        with st.expander("Source & units", expanded=False):
            st.caption("Yahoo Finance futures, not spot or dealer prices. Prices may be delayed. Weight applies to precious metals; other commodities keep their trading units.")
            if currency == "EUR":
                st.caption("EUR uses historical daily EUR/USD closes. Converted candles are estimates; unmatched exchange-rate observations are omitted.")
                st.link_button("EUR/USD SOURCE ↗", "https://finance.yahoo.com/quote/EURUSD%3DX/")
    elif section == "Sports":
        sports_panel()
    elif section == "US Elections":
        us_elections_panel()
    elif section == "Elections":
        st.subheader("WORLD ELECTION WATCH")
        st.caption("Calendar covers the previous 7 days and next 180 days. Community-maintained dates may be incomplete or change; verify at source.")
        rows, error = elections_calendar()
        if error:
            st.warning(error)
        elif rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, column_config={"Source": st.column_config.LinkColumn("Calendar source")})
        else:
            st.info("No dated elections returned by the calendar source.")
        st.caption("Poll charts appear only when verified original-source data is connected. No worldwide polling feed is currently connected.")
        st.subheader("ELECTION REPORTING")
        stories([a for a in items if a["category"] == "Elections"], "elections", 12)
    elif section == "Sources":
        st.subheader("SOURCE STATUS")
        for category, feeds in FEEDS.items():
            for source, url in feeds:
                st.write(f"{category} · {source}")
                st.link_button("OPEN FEED ↗", url)
        for error in errors:
            st.warning(error)
        st.write("Markets: Yahoo Finance via yfinance; 10-minute cache; daily observations. Election calendar: Wikidata; 6-hour cache. Polling: original-source datasets only; none connected.")
        st.caption("Google News election links may open its publisher redirect. Conflict channels include regional reporting and do not independently confirm military events. Undated articles are excluded from time-filtered feeds.")
    elif section == "Overview":
        overview_panel(items, errors)
    elif section in ["World", "Politics", "Conflicts"]:
        news_desk(items, section)
    else:
        st.subheader(section.upper() + " / DISPATCHES")
        if section == "Conflicts":
            st.caption("Regional reporting. Claims remain attributed to the reporting source; this is not a verified military event tracker.")
        stories([a for a in items if a["category"] == section], section)
    if errors and section != "Sources":
        st.caption(f"{len(errors)} feed(s) unavailable. Open Sources for details. Other channels remain usable.")


dashboard()
