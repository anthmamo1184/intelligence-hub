from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
import hashlib
import re
from urllib.parse import quote, urlencode, urlparse
from zoneinfo import ZoneInfo

import feedparser
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="INTELLIGENCE HUB", page_icon="◈", layout="wide")
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'Share Tech Mono',monospace;}
h1,h2,h3,[data-testid="stMetricLabel"],button,p label {font-family:'Oxanium',monospace!important;}
.stApp {background:radial-gradient(ellipse at 80% 0%,#11283a 0%,#070d17 55%);}
.block-container{padding-top:2rem;max-width:1550px;}
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
.meta{font-size:.73rem;color:#8ba5b9;}
[data-testid="stDialog"]>div{background:#0d1928;border:1px solid #286070;}
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
                              summary=clean(entry.get("summary", ""))[:1800], source=publisher,
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


@st.dialog("SOURCE BRIEF", width="large")
def story_dialog(item):
    st.subheader(item["title"])
    st.caption(f'{item["source"]} · {timestamp(item["published"])}')
    st.write(item["summary"] or "Open the original report to read the story.")
    st.link_button("OPEN ORIGINAL REPORT ↗", item["url"], use_container_width=True)
    st.caption("Publisher report. Inclusion does not independently verify claims. Excerpts may be truncated.")


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


@st.cache_data(ttl=600, show_spinner=False)
def market_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="3mo", interval="1d", auto_adjust=False, timeout=12)
        if data.empty:
            return None
        data = data.dropna(subset=["Close"])
        if data.empty:
            return None
        frame = data.reset_index()
        return frame[["Date", "Close"]]
    except Exception:
        return None


@st.dialog("MARKET DETAIL", width="large")
def market_dialog(name, symbol, unit, frame):
    st.subheader(name)
    st.caption(f"Yahoo Finance · {symbol} · {unit} · Daily observations")
    fig = px.line(frame, x="Date", y="Close", template="plotly_dark")
    fig.update_traces(line_color="#40e0d0")
    fig.update_layout(height=320, margin=dict(l=5, r=5, t=10, b=5), yaxis_title=unit, paper_bgcolor="#0d1928", plot_bgcolor="#0d1928")
    st.plotly_chart(fig, use_container_width=True)
    st.link_button("YAHOO FINANCE ↗", f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/")
    st.caption("Futures series may roll between contracts. Prices may be delayed; not spot metal or physical retail prices.")


def market_panel(names):
    st.caption("Yahoo Finance · latest available daily observations · cached 10 minutes · commodities are futures, not spot quotes")
    with ThreadPoolExecutor(max_workers=4) as pool:
        frames = list(pool.map(lambda n: market_data(ASSETS[n][0]), names))
    cols = st.columns(3)
    for i, (name, frame) in enumerate(zip(names, frames)):
        symbol, unit = ASSETS[name]
        with cols[i % 3], st.container(border=True):
            if frame is None:
                st.metric(name, "Unavailable")
                st.caption("Feed unavailable; no substitute price shown.")
            else:
                close = float(frame["Close"].iloc[-1])
                previous = float(frame["Close"].iloc[-2]) if len(frame) > 1 else None
                delta = f"{(close / previous - 1) * 100:+.2f}%" if previous else None
                st.metric(name, f"{close:,.2f}", delta)
                st.caption(f'{unit} · observation {frame["Date"].iloc[-1]:%d %b %Y}')
                st.line_chart(frame.set_index("Date")["Close"], height=90, color="#40e0d0")
                if st.button("EXPAND CHART", key="market_" + symbol, use_container_width=True):
                    market_dialog(name, symbol, unit, frame)
            st.link_button("SOURCE ↗", f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/")


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


def polling_panel():
    st.subheader("POLLING LAB")
    st.caption("Real polling only. No automatic worldwide polling provider is connected in this first version.")
    upload = st.file_uploader("Load a sourced polling CSV", type="csv", key="polls")
    st.download_button("DOWNLOAD CSV TEMPLATE", "country,election,pollster,fieldwork_end,party,percent,sample_size,source_url\n", "polling_template.csv", "text/csv")
    if upload is None:
        st.info("Upload polling data to unlock country filters, poll points and trend graphs. No invented poll figures are displayed.")
        return
    try:
        df = pd.read_csv(upload)
        required = {"country", "election", "pollster", "fieldwork_end", "party", "percent", "sample_size", "source_url"}
        if not required.issubset(df.columns):
            raise ValueError("CSV must include: " + ", ".join(sorted(required)))
        if df.empty or df[list(required)].isna().any().any():
            raise ValueError("Provide complete polling rows, including source links and sample sizes.")
        df["fieldwork_end"] = pd.to_datetime(df["fieldwork_end"], errors="raise", utc=True)
        df["percent"] = pd.to_numeric(df["percent"], errors="raise")
        df["sample_size"] = pd.to_numeric(df["sample_size"], errors="raise")
        if not df["percent"].between(0, 100).all() or not (df["sample_size"] > 0).all():
            raise ValueError("Percent must be between 0 and 100; sample size must be positive.")
        if not df["source_url"].map(lambda u: bool(safe_url(u))).all():
            raise ValueError("Each poll needs an HTTP or HTTPS source link.")
        country = st.selectbox("Country", sorted(df["country"].unique()))
        df = df[df["country"] == country]
        election = st.selectbox("Election", sorted(df["election"].unique()))
        df = df[df["election"] == election].sort_values("fieldwork_end")
        fig = px.scatter(df, x="fieldwork_end", y="percent", color="party", symbol="pollster", hover_data=["pollster", "sample_size", "source_url"], template="plotly_dark", labels={"fieldwork_end": "Fieldwork end", "percent": "Voting intention (%)"})
        fig.update_layout(height=400, yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Individual published poll points; no poll average or seat projection calculated. Uploaded data lasts for this session only.")
        st.dataframe(df, hide_index=True, column_config={"source_url": st.column_config.LinkColumn("Source")})
    except Exception as exc:
        st.error(f"Polling CSV could not be loaded: {exc}")


with st.sidebar:
    st.markdown("## ◈ CONTROL PANEL")
    section = st.radio("CHANNEL", ["Overview", "World", "Politics", "Sports", "Conflicts", "Elections", "Commodities", "Markets", "Alerts", "Sources"])
    search = st.text_input("SEARCH FEED", placeholder="Country, team, company…")
    watch = st.text_area("ALERT KEYWORDS · comma separated", value="Malta, Brazil, Juventus, Betsson")
    age = st.selectbox("STORY WINDOW", [24, 48, 168], index=1, format_func=lambda n: f"Last {n} hours")
    auto = st.toggle("Auto-refresh every 3 minutes", value=True)
    if st.button("REFRESH FEEDS", use_container_width=True):
        st.cache_data.clear()
    st.caption("Alerts are keyword matches while this page is open. Phone notifications are not connected.")

st.markdown('<div class="tag">GLOBAL MONITORING / PERSONAL TERMINAL</div>', unsafe_allow_html=True)
st.title("INTELLIGENCE HUB")
st.caption("WORLD • POLITICS • ELECTIONS • MARKETS • COMMODITIES • SPORT")


@st.fragment(run_every="180s" if auto else None)
def dashboard():
    with st.spinner("Checking source feeds…"):
        all_items, errors = news_data()
    cutoff = datetime.now(UTC) - timedelta(hours=age)
    items = [a for a in all_items if a["published"] and datetime.fromisoformat(a["published"]) >= cutoff]
    if search.strip():
        items = [a for a in items if search.casefold() in (a["title"] + " " + a["summary"]).casefold()]
    keywords = [s.strip().casefold() for s in watch.split(",") if s.strip()]
    matches = [a for a in items if any(k in (a["title"] + " " + a["summary"]).casefold() for k in keywords)]
    a, b, c, d = st.columns(4)
    a.metric("STORIES IN WINDOW", len(items))
    b.metric("AVAILABLE FEEDS", sum(map(len, FEEDS.values())) - len(errors))
    c.metric("KEYWORD MATCHES", len(matches))
    d.metric("CHECKED · MALTA", datetime.now(LOCAL).strftime("%H:%M"))
    st.caption("Checked time is this dashboard check; publication times appear on each story. Feed responses may be cached for 3 minutes.")
    st.divider()
    if section in {"Commodities", "Markets"}:
        st.subheader(section.upper())
        defaults = list(ASSETS)[:6] if section == "Commodities" else list(ASSETS)[11:]
        choices = st.multiselect("Watchlist", list(ASSETS), default=defaults)
        market_panel(choices)
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
        polling_panel()
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
        st.write("Markets: Yahoo Finance via yfinance; 10-minute cache; daily observations. Election calendar: Wikidata; 6-hour cache. Polling: sourced CSV uploads.")
        st.caption("Google News election links may open its publisher redirect. Conflict channels include regional reporting and do not independently confirm military events. Undated articles are excluded from time-filtered feeds.")
    elif section == "Alerts":
        st.subheader("KEYWORD ALERTS")
        st.caption("Matches within fetched headlines and excerpts; not an exhaustive monitoring service.")
        stories(matches, "alerts")
    elif section == "Overview":
        left, right = st.columns([2, 1])
        with left:
            st.subheader("LATEST DISPATCHES")
            stories(items, "overview", 15)
        with right:
            st.subheader("WATCHLIST SIGNALS")
            stories(matches, "watch", 5)
            st.subheader("COVERAGE")
            if items:
                counts = pd.Series([a["category"] for a in items]).value_counts().rename_axis("Channel").reset_index(name="Stories")
                fig = px.bar(counts, x="Stories", y="Channel", orientation="h", template="plotly_dark", color_discrete_sequence=["#40e0d0"])
                fig.update_layout(height=250, margin=dict(l=0, r=0, t=5, b=0))
                st.plotly_chart(fig, use_container_width=True)
            st.caption("Counts describe retrieved articles, not global event frequency.")
    else:
        st.subheader(section.upper() + " / DISPATCHES")
        if section == "Conflicts":
            st.caption("Regional reporting. Claims remain attributed to the reporting source; this is not a verified military event tracker.")
        stories([a for a in items if a["category"] == section], section)
    if errors and section != "Sources":
        st.caption(f"{len(errors)} feed(s) unavailable. Open Sources for details. Other channels remain usable.")


dashboard()
