from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
import hashlib
import json
from html.parser import HTMLParser
import re
from urllib.parse import quote, urlencode, urlparse, parse_qsl, urlunparse
from zoneinfo import ZoneInfo

import feedparser
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import folium
import pycountry
from shapely.geometry import shape, Point
from streamlit_folium import st_folium
import yfinance as yf
import trafilatura

st.set_page_config(page_title="INTELLIGENCE HUB", page_icon="◈", layout="wide")
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

/* Operations-room treatment: restrained instrumentation, readable text. */
.st-key-overview_command{position:relative;border:1px solid #284557;border-radius:5px;padding:14px 16px 10px;background:linear-gradient(135deg,#0c1c2999,#07111c55);box-shadow:inset 0 1px 0 #5babb517,0 12px 35px #0002}
.st-key-overview_command:before,.st-key-overview_command:after{content:"";position:absolute;width:14px;height:14px;pointer-events:none;z-index:1}.st-key-overview_command:before{top:-1px;left:-1px;border-top:2px solid #55d5d0;border-left:2px solid #55d5d0}.st-key-overview_command:after{bottom:-1px;right:-1px;border-bottom:2px solid #55d5d0;border-right:2px solid #55d5d0}
.st-key-overview_wire{border:1px solid #223c4d;border-top:2px solid #357984;border-radius:4px;padding:12px 16px;background:#09162188;margin-top:12px}
.ops-strip{display:flex;align-items:center;justify-content:space-between;gap:8px;color:#809fae;font:10px monospace;letter-spacing:1px;margin:0 0 8px}.ops-strip strong{color:#68d3ce;font-weight:400}.ops-dot{display:inline-block;width:5px;height:5px;background:#57c6bc;border-radius:50%;margin-right:6px;box-shadow:0 0 7px #40e0d055}.monitor-heading{color:#d6e9f5;text-shadow:0 0 12px #2ac4d01a}.focus-label{border-left:2px solid currentColor;padding-left:8px}.ticker-strip{box-shadow:inset 0 1px 0 #6bd0d00c}.intel-row{border-top-color:#31506488}.wire-row:hover{background:#15314366}.st-key-explore_desks button:hover{border-color:#62c5cc!important;background:#173447!important}
@media(max-width:700px){.ops-strip{font-size:9px;letter-spacing:0;flex-wrap:wrap}.st-key-overview_command,.st-key-overview_wire{padding:10px}}

.st-key-explore_desks{max-width:850px}.st-key-explore_desks [data-testid="stHorizontalBlock"]{gap:6px!important}.st-key-explore_desks [data-testid="stVerticalBlock"]{gap:3px!important}.st-key-explore_desks button{min-height:25px!important;padding:1px 8px!important;border-color:#29435488!important;background:#10233266!important}.st-key-explore_desks button p{font-size:10px!important;letter-spacing:.5px}.intel-preview{font:11px/1.5 Oxanium,sans-serif;color:#92aabb;margin:0 0 4px}.wire-sub{font:9px monospace;color:#7896a9;letter-spacing:1px;margin-left:14px}.wire-row{display:flex;gap:12px;border-top:1px solid #203645;padding:9px 0}.wire-index{font-size:11px;color:#426c82;padding-top:3px}.wire-headline{font:12px/1.5 Oxanium,sans-serif;color:#dbeaf5}.wire-meta{font:10px monospace;color:#87a1b4}.st-key-overview_wire .stButton button,.st-key-overview_wire .stLinkButton a{min-height:26px;padding:2px 8px;font-size:10px}.st-key-overview_wire [data-testid="stVerticalBlock"]{gap:5px}.desk-label{font-size:9px;color:#8398a7;letter-spacing:1px}.monitor-legend{display:flex;gap:8px 14px;flex-wrap:wrap;padding:7px 0;border-top:1px solid #2a455488;font:10px/1.5 monospace;color:#b0c3cf}.monitor-legend span{display:inline-flex;align-items:center;gap:5px}.monitor-legend i{width:8px;height:8px;border-radius:2px;border:1px solid #5f778766;display:inline-block}.watch-heading{font:10px monospace;letter-spacing:1px;color:#8ca5b5;margin:10px 0 7px}.vote-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.vote-card{padding:9px 11px;border:1px solid #554d35;border-left:2px solid #c7a15d;border-radius:3px;background:#b9903010;text-decoration:none!important;min-width:0}.vote-card:hover{background:#b9903020}.vote-country{font:11px Oxanium,monospace;color:#d9e4ec;overflow-wrap:anywhere}.vote-countdown{font:22px monospace;color:#d6b76f;margin:3px 0}.vote-countdown small{font-size:9px;color:#9c967d}.vote-date{font:10px monospace;color:#8ca5b5}.st-key-overview_command [data-testid="stSegmentedControl"] button{border-radius:4px!important;padding:5px 12px!important;min-height:30px!important}.st-key-overview_command [data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#1a414b!important;border-color:#4cbbb8!important;color:#a8fff5!important}
.overview-title{font:600 1.6rem Oxanium,monospace;letter-spacing:2px;margin:4px 0 16px}.overview-title span{font:11px monospace;color:#91a8ba;letter-spacing:1px;margin-left:20px}
.ticker-strip{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border:1px solid #294354;border-radius:6px;background:#0b1823;margin-top:8px}.ticker-cell{padding:9px 12px;border-right:1px solid #294354;min-width:0}.ticker-cell:last-child{border:0}.ticker-name{font:11px Oxanium,monospace;color:#a8bfd1}.ticker-value{font-size:16px;white-space:nowrap}.ticker-value small{font-size:11px}.ticker-bottom{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10px;color:#8ca5b7}.ticker-bottom svg{width:65px;height:24px;flex-shrink:0}.intel-row{padding:6px 0 0;border-top:1px solid #213b4b;font-size:13px;line-height:1.45}.intel-row .tag{font-size:10px}.monitor-heading{font:600 15px Oxanium,monospace;letter-spacing:1px;margin:8px 0}.focus-label{font:11px monospace;margin:8px 0 12px}.st-key-overview_command [data-testid="stCaptionContainer"]{font-size:11px}.st-key-overview_command .stButton button{min-height:26px;padding:2px 10px;font-size:11px}.st-key-overview_command [data-testid="stVerticalBlock"]{gap:.5rem}
@media(max-width:700px){.st-key-explore_desks [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important}.st-key-explore_desks [data-testid="stColumn"]{min-width:0!important;width:auto!important}.ticker-strip{grid-template-columns:repeat(3,minmax(0,1fr))}.ticker-cell{padding:8px}.ticker-value{font-size:13px}.ticker-value small{font-size:10px}.ticker-bottom svg{width:35px}.overview-title span{display:block;margin:8px 0 0}.st-key-overview_command [data-testid="stHorizontalBlock"]{flex-wrap:wrap}.st-key-overview_command [data-testid="stColumn"]{min-width:100%!important}.st-key-overview_command > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child{order:2}.st-key-overview_command > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child{order:1}}

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
.pulse-name{font-family:Oxanium,monospace;font-size:.7rem;color:#9ebdca;}
.pulse-price{font-family:"Share Tech Mono",monospace;font-size:1.05rem;color:#e1edf7;white-space:nowrap;}
.st-key-overview_pulse [data-testid="stVerticalBlock"]{gap:.4rem!important;}
.pulse-header{display:block;min-height:94px;box-sizing:border-box;}
.pulse-header .pulse-name{display:block;line-height:18px;margin:0 0 5px;}
.pulse-header .pulse-price{display:block;line-height:26px;margin:0 0 4px;font-size:1.05rem;}
.pulse-detail{display:block;font-size:.68rem;line-height:17px;color:#91a8ba;overflow-wrap:anywhere;}
.pulse-delta{display:block;font-size:.72rem;line-height:18px;}
.st-key-overview_pulse [data-testid="stCaptionContainer"] p{font-size:.62rem;}
.st-key-markets_compact_page [data-testid="stMetric"]{padding:5px 8px!important;}
.st-key-markets_compact_page [data-testid="stMetricValue"]{font-size:1.12rem!important;line-height:1.4!important;}
.st-key-markets_compact_page [data-testid="stCaptionContainer"] p{font-size:.68rem;line-height:1.45;}

/* Fluid phone/tablet layout; keep the full desktop grid. */
@media (max-width: 1024px) {
  [data-testid="stMainBlockContainer"],.block-container{padding-left:1rem!important;padding-right:1rem!important;}
  .st-key-overview_pulse [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.6rem!important;}
  .st-key-overview_pulse [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:0 0 calc(33.333% - .6rem)!important;min-width:0!important;width:calc(33.333% - .6rem)!important;}
}
@media (max-width: 767px) {
  [data-testid="stMainBlockContainer"],.block-container{padding-top:3.8rem!important;padding-left:.7rem!important;padding-right:.7rem!important;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:1 1 100%!important;width:100%!important;min-width:0!important;}
  h1{font-size:1.35rem!important;letter-spacing:1.3px!important;line-height:1.4!important;}
  h2{font-size:1.05rem!important;letter-spacing:1px!important;line-height:1.4!important;}
  h3{font-size:.95rem!important;letter-spacing:.6px!important;}
  .tag{letter-spacing:1px;font-size:.7rem;line-height:1.5;}
  .stButton>button,.stLinkButton>a,[data-testid="stFormSubmitButton"] button{min-height:44px!important;font-size:.8rem!important;white-space:normal!important;}
  [data-testid="stTextInput"] input{font-size:16px!important;}
  [data-testid="stRadio"] [role="radiogroup"]{flex-wrap:wrap!important;gap:.4rem .8rem!important;}
  [data-testid="stTabs"] [role="tablist"]{overflow-x:auto!important;flex-wrap:nowrap!important;gap:.8rem!important;}
  [data-testid="stTabs"] [role="tab"]{flex-shrink:0!important;min-height:44px!important;}
  [data-testid="stDialog"] [role="dialog"]{width:calc(100vw - 1rem)!important;max-width:calc(100vw - 1rem)!important;max-height:90dvh!important;}
  .brief-title{font-size:1rem;line-height:1.5;}
  .sport-headline{font-size:.93rem;min-height:0;line-height:1.5;}
  .desk-excerpt{font-size:.83rem;line-height:1.55;}
  .st-key-overview_pulse [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:0 0 calc(50% - .35rem)!important;min-width:0!important;width:calc(50% - .35rem)!important;}
  .pulse-header{min-height:100px;}
  .pulse-header .pulse-name{font-size:.78rem;line-height:20px;}
  .pulse-header .pulse-price{font-size:1.1rem;line-height:26px;}
  .pulse-detail{font-size:.74rem;line-height:18px;}
  .pulse-delta{font-size:.78rem;line-height:20px;}
  .st-key-overview_pulse [data-testid="stCaptionContainer"] p{font-size:.7rem!important;line-height:1.45!important;}
  .st-key-overview_kpis [data-testid="stHorizontalBlock"],
  [class*="st-key-desk_kpis_"] [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.5rem!important;}
  .st-key-overview_kpis [data-testid="stColumn"],
  [class*="st-key-desk_kpis_"] [data-testid="stColumn"]{flex:0 0 calc(50% - .3rem)!important;width:calc(50% - .3rem)!important;min-width:0!important;}
  .st-key-markets_compact_page [data-testid="stMetricValue"]{font-size:1.25rem!important;}
  .st-key-markets_compact_page [data-testid="stCaptionContainer"] p{font-size:.76rem!important;}
  .st-key-sports_desk [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)){flex-wrap:wrap!important;gap:.5rem!important;}
  .st-key-sports_desk [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) > [data-testid="stColumn"]{flex:0 0 calc(50% - .3rem)!important;width:calc(50% - .3rem)!important;min-width:0!important;}
}


/* Preserve the native accessible toggle and support both Streamlit header variants. */
:is([data-testid="stSidebarCollapsedControl"] button, button[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] button, button[data-testid="stExpandSidebarButton"], button[aria-label="Expand sidebar"]){min-width:46px!important;min-height:44px!important;color:#9eece8!important;background:#101f2e!important;border:1px solid #285269!important;border-radius:6px!important;}
:is([data-testid="stSidebarCollapsedControl"] button, button[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] button, button[data-testid="stExpandSidebarButton"], button[aria-label="Expand sidebar"]) > *{display:none!important;}
:is([data-testid="stSidebarCollapsedControl"] button, button[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] button, button[data-testid="stExpandSidebarButton"], button[aria-label="Expand sidebar"])::after{content:"☰";font-family:Arial,sans-serif;font-size:25px;line-height:1;}
@media(max-width:767px){
    [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.6rem!important;}
    [data-testid="stSidebar"]{max-width:86vw!important;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label{min-height:40px;align-items:center;}
    [data-testid="stSelectbox"] input,[data-testid="stMultiSelect"] input{font-size:16px!important;}
    [data-testid="stMetric"]{padding:7px 9px!important;}
    [data-testid="stMetricValue"]{font-size:1.3rem!important;line-height:1.4!important;white-space:normal!important;}
    [data-testid="stMetricLabel"] p{font-size:.76rem!important;line-height:1.4!important;}
    [data-testid="stCaptionContainer"] p{line-height:1.5;}
    .st-key-commodity_controls > [data-testid="stVerticalBlock"]{gap:.4rem!important;}
    .st-key-commodity_controls [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:0 0 calc(50% - .35rem)!important;width:calc(50% - .35rem)!important;min-width:0!important;}
    .st-key-commodity_controls [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3){flex-basis:100%!important;width:100%!important;}
    .st-key-markets_compact_page [data-testid="stForm"] [data-testid="stColumn"]:first-child{flex:1 1 calc(100% - 100px)!important;width:calc(100% - 100px)!important;min-width:0!important;}
    .st-key-markets_compact_page [data-testid="stForm"] [data-testid="stColumn"]:last-child{flex:0 0 84px!important;width:84px!important;min-width:0!important;}
    .st-key-us_election_kpis [data-testid="stColumn"]{flex:0 0 calc(50% - .35rem)!important;width:calc(50% - .35rem)!important;min-width:0!important;}
    [data-testid="stPopover"] button{min-height:44px!important;width:100%;}
    [data-testid="stDialog"] [data-testid="stVerticalBlock"]{min-width:0!important;}
    .headline{font-size:.95rem;line-height:1.5;}
}


/* Constrain the popup to the viewport and scroll the brief independently. */
[data-testid="stDialog"] [role="dialog"],
[data-testid="stDialog"][role="dialog"],
[data-baseweb="modal"] [role="dialog"]{
    max-height:calc(100vh - 2rem)!important;
    max-height:calc(100dvh - 2rem)!important;
    overflow-y:auto!important;
    overscroll-behavior-y:contain;
    -webkit-overflow-scrolling:touch;
}
.st-key-brief_scroll{
    max-height:65vh!important;max-height:65dvh!important;
    overflow-y:auto!important;overflow-x:hidden!important;
    min-height:0!important;padding-right:.6rem;
    overscroll-behavior-y:contain;-webkit-overflow-scrolling:touch;
    scrollbar-gutter:stable;
}
.st-key-brief_scroll::-webkit-scrollbar{width:7px;}
.st-key-brief_scroll::-webkit-scrollbar-thumb{background:#426275;border-radius:4px;}
@media(max-width:767px){
    .st-key-brief_scroll{max-height:60vh!important;max-height:60dvh!important;padding-right:.35rem;}
}


.st-key-changes_strip{border:1px solid #214252;border-radius:5px;background:#0c1723;padding:5px 9px;margin-bottom:6px;}
.changes-summary{font: .78rem/1.5 "Share Tech Mono",monospace;padding:8px 0;color:#b1c8d6;}
.st-key-changes_strip [data-testid="stVerticalBlock"]{gap:0!important;}
.st-key-changes_strip button{font-size:.7rem!important;min-height:32px!important;}
@media(max-width:767px){
 .st-key-changes_strip [data-testid="stColumn"]:first-child{flex:1 1 58%!important;width:58%!important;min-width:0!important;}
 .st-key-changes_strip [data-testid="stColumn"]:last-child{flex:0 0 35%!important;width:35%!important;min-width:0!important;}
 .changes-summary{font-size:.72rem;line-height:1.4;padding:5px 0;}
}


.brief-note{font-family:Arial,sans-serif;font-size:10.5px;line-height:1.5;font-weight:400;color:#8c9faf;margin:2px 0 5px;}
.brief-notes{font-family:Arial,sans-serif;font-size:10.5px;line-height:1.5;font-weight:400;color:#8296a8;border-top:1px solid #263848;margin-top:6px;padding-top:7px;}
.brief-note-label{font-size:9px;letter-spacing:1px;font-weight:500;color:#92a8bb;}
@media(max-width:767px){.brief-note,.brief-notes{font-size:11px;}.brief-note-label{font-size:9.5px;}}

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

def publisher_search_feed(domain, terms=""):
    return "https://news.google.com/rss/search?"+urlencode({"q":f"site:{domain} ({terms}) when:7d" if terms else f"site:{domain} when:7d","hl":"en-GB","gl":"GB","ceid":"GB:en"})


# Fox publishes section RSS. CNN/Reuters headlines are indexed by Google News;
# these are not represented as direct publisher RSS or licensed article feeds.
FEEDS["World"] += [
    ("Fox News · World", "https://moxie.foxnews.com/google-publisher/world.xml"),
    ("CNN · via Google News", publisher_search_feed("cnn.com", "world")),
    ("Reuters · via Google News", publisher_search_feed("reuters.com", "world")),
]
FEEDS["Politics"] += [
    ("Fox News · Politics", "https://moxie.foxnews.com/google-publisher/politics.xml"),
    ("CNN · Politics via Google News", publisher_search_feed("cnn.com", "politics OR government OR congress")),
    ("Reuters · Politics via Google News", publisher_search_feed("reuters.com", "politics OR government OR congress")),
]
FEEDS["Markets"] += [
    ("CNN · Markets via Google News", publisher_search_feed("cnn.com", "business OR markets OR economy")),
    ("Reuters · Markets via Google News", publisher_search_feed("reuters.com", "business OR markets OR economy")),
]
FEEDS["Conflicts"] += [
    ("CNN · Conflicts via Google News", publisher_search_feed("cnn.com", "war OR ceasefire OR military")),
    ("Reuters · Conflicts via Google News", publisher_search_feed("reuters.com", "war OR ceasefire OR military")),
    ("Fox News · Conflicts via Google News", publisher_search_feed("foxnews.com", "war OR ceasefire OR military")),
]
FEEDS["Elections"] += [
    ("CNN · Elections via Google News", publisher_search_feed("cnn.com", "election OR voting")),
    ("Reuters · Elections via Google News", publisher_search_feed("reuters.com", "election OR voting")),
    ("Fox News · Elections via Google News", publisher_search_feed("foxnews.com", "election OR voting")),
]

FEEDS["Crypto"] = [
    ("Reuters · Crypto via Google News", publisher_search_feed("reuters.com", "bitcoin OR ethereum OR cryptocurrency")),
    ("CNN · Crypto via Google News", publisher_search_feed("cnn.com", "bitcoin OR cryptocurrency")),
    ("BBC · Crypto via Google News", publisher_search_feed("bbc.com", "bitcoin OR cryptocurrency")),
]

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


MAJOR_COMPANIES = {
    "NVIDIA": ("NVDA", "Quote currency"), "Microsoft": ("MSFT", "Quote currency"),
    "Apple": ("AAPL", "Quote currency"), "Amazon": ("AMZN", "Quote currency"),
    "Alphabet / Google": ("GOOGL", "Quote currency"), "Meta": ("META", "Quote currency"),
    "Tesla": ("TSLA", "Quote currency"), "AMD": ("AMD", "Quote currency"),
    "Broadcom": ("AVGO", "Quote currency"),
}
MARKET_PRESETS.update(MAJOR_COMPANIES)
DEFAULT_MARKETS = ["NVIDIA", "Microsoft", "Apple", "S&P 500", "Amazon", "Alphabet / Google", "Meta", "Nasdaq", "Tesla", "AMD", "Broadcom", "Dow Jones"]


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
def feed_snapshot(category, source, url):
    checked = datetime.now(UTC).isoformat()
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
                              category=category, published=stamp.isoformat() if stamp else None, fetched_at=checked))
        dated=[a["published"] for a in items if a["published"]]
        return items, None, dict(Channel=category,Feed=source,URL=url,Checked=checked,Success=checked,Latest=max(dated,key=datetime.fromisoformat) if dated else None,Articles=len(items))
    except Exception:
        return [], source + ": unavailable on this check", dict(Channel=category,Feed=source,URL=url,Checked=checked,Success=None,Latest=None,Articles=0)


def fetch_feed(category,source,url):
    rows,error,_=feed_snapshot(category,source,url)
    return rows,error


def required_news_channels(page):
    if page == "Overview":
        return tuple(c for c in FEEDS if c not in ("Sports","Crypto"))
    if page=="Sources":
        return tuple(FEEDS)
    if page in ("World", "Politics", "Conflicts", "Elections", "Crypto"):
        return (page,)
    # Sports, country briefings and US reporting already have dedicated feeds.
    return ()


def news_data(categories=None):
    categories=tuple(FEEDS) if categories is None else tuple(categories)
    jobs = [(c, source, url) for c in categories for source, url in FEEDS.get(c, [])]
    if not jobs:
        return [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: feed_snapshot(*job), jobs))
    seen, articles, errors = set(), [], []
    health=[]
    history=st.session_state.get("feed_success_history",{})
    for rows, error, metadata in results:
        if metadata["Success"]:
            history[metadata["URL"]]=metadata["Success"]
        else:
            metadata=dict(metadata,Success=history.get(metadata["URL"]))
        health.append(dict(metadata,Available=not bool(error)))
        if error:
            errors.append(error)
        for row in rows:
            key = (row["category"], row["source"], re.sub(r"\W", "", row["title"]).lower())
            if key not in seen:
                seen.add(key)
                articles.append(row)
    st.session_state.feed_success_history=history
    st.session_state.feed_health=health
    return sorted(articles, key=lambda a: a["published"] or "", reverse=True), errors


def elapsed_label(value,now=None):
    if not value:
        return "Unknown"
    stamp=pd.Timestamp(value)
    stamp=stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
    seconds=max(0,((now or datetime.now(UTC))-stamp.to_pydatetime()).total_seconds())
    if seconds<60:return "<1m ago"
    if seconds<3600:return f"{int(seconds/60)}m ago"
    if seconds<86400:return f"{int(seconds/3600)}h ago"
    return f"{int(seconds/86400)}d ago"


def market_freshness(frame):
    last=pd.Timestamp(frame["Date"].iloc[-1])
    day=last.date()
    lag=(datetime.now(UTC).date()-day).days
    # Daily bars are not live ticks. A weekend/holiday alone is not a feed failure.
    status="OLDER DAILY QUOTE" if lag>4 else "DAILY BAR"
    fetched=frame.attrs.get("fetched_at")
    return f"{status} · {day:%d %b}"+(f" · fetched {elapsed_label(fetched)}" if fetched else "")


def report_key(item):
    parsed=urlparse(item["url"])
    # Retain article identifiers while discarding campaign tracking and fragments.
    query=[(k,v) for k,v in parse_qsl(parsed.query,keep_blank_values=True)
           if not k.casefold().startswith("utm_") and k.casefold() not in {"fbclid","gclid","ocid","cmpid"}]
    return urlunparse((parsed.scheme,parsed.netloc.casefold(),parsed.path,parsed.params,urlencode(query),""))


def normalized_headline(item):
    title=clean(item["title"]).replace("’", "'").replace("–","-").replace("—","-")
    publisher=re.escape(item.get("source", ""))
    if publisher:
        title=re.sub(r"\s+[-|]\s+"+publisher+r"\s*$","",title,flags=re.I)
    return re.sub(r"\s+[-|]\s+(?:Reuters|CNN|Fox News|BBC(?: News)?).*$","",title,flags=re.I)


def headline_terms(item):
    title=normalized_headline(item)
    stop=set("a an the to of in on for and or as at by with from is are was were be been says said say after over amid about new latest news live updates update breaking report reports what how why".split())
    equivalents={"freed":"release","frees":"release","free":"release","released":"release","releases":"release","prisoners":"prisoner","elections":"election","talks":"talk","negotiations":"talk"}
    return {equivalents.get(w,w) for w in re.findall(r"[a-z0-9]+",title.casefold()) if len(w)>2 and w not in stop}


@st.cache_data(ttl=180, max_entries=64, show_spinner=False)
def group_reporting(items):
    # Precompute each lead's terms/time and compare only groups sharing terms.
    groups, leads, group_urls = [], [], []
    index, exact, lead_urls = {}, {}, {}
    for item in sorted(items,key=lambda x:x.get("published") or "",reverse=True):
        terms=headline_terms(item)
        key=report_key(item)
        stamp=pd.Timestamp(item["published"]) if item.get("published") else None
        candidates=set(exact.get(frozenset(terms),[])) if terms else set()
        shared_counts={}
        for term in terms:
            for group_id in index.get(term,()):
                shared_counts[group_id]=shared_counts.get(group_id,0)+1
        candidates.update(i for i,count in shared_counts.items() if count>=4)
        if key in lead_urls:
            candidates.add(lead_urls[key])
        match=None
        for group_id in sorted(candidates):
            other,other_stamp=leads[group_id]
            same_url=key==report_key(groups[group_id][0])
            within=bool(stamp is not None and other_stamp is not None and abs((stamp-other_stamp).total_seconds())<=48*3600)
            shared=len(terms & other)
            other_title=groups[group_id][0]["title"].casefold()
            title=item["title"].casefold()
            opposites=[(r"\b(?:wins?|won|victory)\b",r"\b(?:loses?|lost|defeat)\b"),(r"\b(?:approves?|approved|passes?|passed)\b",r"\b(?:rejects?|rejected|blocks?|blocked)\b")]
            opposed=any((re.search(a,title) and re.search(b,other_title)) or (re.search(b,title) and re.search(a,other_title)) for a,b in opposites)
            numbers_a=set(re.findall(r"\b\d+(?:[.,]\d+)?\b",title))
            numbers_b=set(re.findall(r"\b\d+(?:[.,]\d+)?\b",other_title))
            different_numbers=bool(numbers_a and numbers_b and numbers_a!=numbers_b)
            similar=not opposed and not different_numbers and shared>=4 and shared/max(1,len(terms|other))>=.50 and shared/max(1,min(len(terms),len(other)))>=.72
            if same_url or (within and (bool(terms) and terms==other and not opposed and not different_numbers or similar)):
                match=group_id
                break
        if match is None:
            group_id=len(groups)
            groups.append([item]);leads.append((terms,stamp));group_urls.append({key})
            lead_urls.setdefault(key,group_id)
            exact.setdefault(frozenset(terms),[]).append(group_id)
            for term in terms:
                index.setdefault(term,[]).append(group_id)
        elif key not in group_urls[match]:
            groups[match].append(item)
            group_urls[match].add(key)
    return groups


def related_reports(group,scope="related"):
    if len(group)<2:
        return
    publishers=len({r["source"] for r in group})
    with st.expander(f"RELATED REPORTING · {len(group)} reports / {publishers} publishers"):
        st.caption("Matched by headline similarity and publication time; related reports may differ in facts or framing.")
        for report in group:
            st.markdown(f"**{report['source']}** · {timestamp(report['published'])}")
            st.write(report["title"])
            if report["summary"]:
                st.caption(short_preview(report["summary"],55))
            st.link_button("READ SOURCE ↗",report["url"])


def feed_health_panel():
    health=st.session_state.get("feed_health",[])
    if not health:
        st.caption("Feed status will appear after a feed check.")
        return
    data=[]
    for row in health:
        latest=row.get("Latest")
        status="Unavailable" if not row["Available"] else "No dated articles" if not latest else "Older headlines" if (datetime.now(UTC)-pd.Timestamp(latest).to_pydatetime()).total_seconds()>86400 else "Available"
        data.append({"Channel":row["Channel"],"Feed":row["Feed"],"Status":status,"Last checked":timestamp(row["Checked"]),"Last success":timestamp(row["Success"]) if row["Success"] else "Not observed this session","Latest article":timestamp(latest) if latest else "Unavailable","Articles":row["Articles"]})
    st.dataframe(pd.DataFrame(data),hide_index=True,use_container_width=True)
    st.caption("Available means a successful fetch, not a guarantee of complete or current coverage. Older headlines = newest retrieved article over 24h old. Successful times survive failed fetches during this session; unavailable feeds do not serve old stories.")


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
    allowed = {"www.bbc.co.uk", "bbc.co.uk", "www.bbc.com", "bbc.com", "www.aljazeera.com", "aljazeera.com", "www.foxnews.com", "foxnews.com", "www.cnn.com", "cnn.com", "edition.cnn.com", "www.reuters.com", "reuters.com"}
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
    with st.container(key="brief_scroll",border=False):
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
            st.markdown('<div class="brief-note">Limited source preview · the full report is available below.</div>',unsafe_allow_html=True)
        st.link_button("OPEN ORIGINAL REPORT ↗", item["url"], use_container_width=True)
        st.markdown('<aside class="brief-notes"><span class="brief-note-label">SOURCE NOTES</span><br>'+escape(report_context(item))+' · Excerpt up to 280 words where available. Source claims are not independently verified.</aside>',unsafe_allow_html=True)


def stories(items, prefix, limit=18):
    if not items:
        st.info("No matching stories. Try All reporting in News coverage, widen the story window or check source status.")
    for story_index, item in enumerate(items[:limit]):
        with st.container(border=True):
            st.markdown(f'<div class="tag">{escape(item["category"].upper())}</div><div class="headline">{escape(item["title"])}</div>', unsafe_allow_html=True)
            st.caption(f'{item["source"]} · {timestamp(item["published"])}')
            left, right = st.columns([1, 1])
            uid = hashlib.sha256(item["url"].encode()).hexdigest()[:16]
            if left.button("OPEN BRIEF", key=f"{prefix}_{story_index}_{uid}", use_container_width=True):
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
        frame.attrs["fetched_at"] = datetime.now(UTC).isoformat()
        return frame
    except Exception:
        return None


def chart_window(frame, period):
    days = {"1M": 30, "3M": 90, "6M": 180, "1Y": 366}[period]
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
    return frame.loc[pd.to_datetime(frame["Date"], utc=True) >= cutoff].copy()


def display_price(value, unit):
    # Keep provider quote units exactly as supplied: GBp is pence, not GBP.
    label = unit if isinstance(unit, str) else ""
    # Include both quote currency and physical unit beside commodity prices.
    show_unit = bool(re.fullmatch(r"[A-Za-z]{3}", label)) or " / " in label
    return f"{value:,.2f}" + (f" {label}" if show_unit else "")


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
    fig.add_annotation(x=1, xref="paper", y=last, text=display_price(last, unit), showarrow=False, xanchor="right", yshift=13, font=dict(color=color, size=11), bgcolor="#101c2c")
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
    st.caption(f"Yahoo Finance · {symbol} · {unit} · {market_freshness(frame)}")
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


def quote_currency(unit,frame):
    currency=frame.attrs.get("currency","") if unit=="Quote currency" and frame is not None else unit
    subunits={"GBp":("GBP",.01),"GBX":("GBP",.01),"ZAc":("ZAR",.01),"ILA":("ILS",.01)}
    if currency in subunits:return subunits[currency]
    return currency,1.0


def market_fx_pair(frame,unit,target):
    if frame is None or frame.empty or target=="Native quote":return None
    currency,_=quote_currency(unit,frame)
    if isinstance(currency,str) and re.fullmatch(r"[A-Z]{3}",currency) and currency!=target:
        return target+currency+"=X"
    return None


def convert_market_quote(frame,unit,target,fx=None):
    if frame is None or frame.empty:return None,unit
    if target=="Native quote":return frame,frame.attrs.get("currency","Quote currency unavailable") if unit=="Quote currency" else unit
    currency,scale=quote_currency(unit,frame)
    if not isinstance(currency,str) or not re.fullmatch(r"[A-Z]{3}",currency):
        # Index levels and currency-pair ratios retain their meaningful native units.
        return (None,target) if unit=="Quote currency" else (frame,unit)
    out=frame.copy();attrs=dict(frame.attrs)
    columns=[c for c in ["Open","High","Low","Close"] if c in out]
    out[columns]=out[columns]*scale
    if currency!=target:
        if fx is None or fx.empty:return None,target
        out["_day"]=pd.to_datetime(out["Date"]).dt.tz_localize(None).dt.normalize()
        rates=pd.DataFrame({"_fxday":pd.to_datetime(fx["Date"]).dt.tz_localize(None).dt.normalize(),"_rate":pd.to_numeric(fx["Close"],errors="coerce")})
        rates=rates.dropna().loc[lambda f:(f["_rate"]>0)&(f["_rate"]<float("inf"))].sort_values("_fxday").drop_duplicates("_fxday",keep="last")
        out=pd.merge_asof(out.sort_values("_day"),rates,left_on="_day",right_on="_fxday",direction="backward",tolerance=pd.Timedelta(days=7))
        out=out.dropna(subset=["_rate"])
        if out.empty:return None,target
        out[columns]=out[columns].div(out["_rate"],axis=0)
        out=out.drop(columns=["_day","_fxday","_rate"])
        attrs["conversion_note"]=f"{target} estimate converted from {currency} using historical daily FX closes (same date or preceding available date, up to 7 days). Candle OHLC uses one FX close per day. The source listing remains in its original currency. Percentage changes include currency movements."
        attrs["fx_estimate"]=True
    attrs["currency"]=target;out.attrs=attrs
    return out,target


def market_panel(names, assets=None, compact_controls=False, commodity_currency=None, metal_weight="Troy oz", selected_period=None, display_currency=None):
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

    market_rates={}
    if display_currency:
        pairs=list(dict.fromkeys(pair for name,frame in zip(names,frames) if (pair:=market_fx_pair(frame,assets[name][1],display_currency))))
        with ThreadPoolExecutor(max_workers=4) as pool:
            market_rates=dict(zip(pairs,pool.map(market_data,pairs)))

    # Build actual rows so each asset keeps its position as cards change height.
    columns_per_row = 4 if compact_controls else 3
    for offset in range(0, len(names), columns_per_row):
        cols = st.columns(columns_per_row)
        for col, name, frame in zip(cols, names[offset:offset+columns_per_row], frames[offset:offset+columns_per_row]):
            symbol, unit = assets[name]
            if commodity_currency is not None:
                frame, unit = convert_commodity(frame, unit, commodity_currency, metal_weight, fx)
            elif display_currency:
                pair=market_fx_pair(frame,unit,display_currency)
                frame,unit=convert_market_quote(frame,unit,display_currency,market_rates.get(pair))
            with col, st.container(border=True):
                if frame is None or frame.empty:
                    st.metric(name, "Unavailable")
                    st.caption("Price or required FX feed unavailable; no substitute price shown.")
                else:
                    view = chart_window(frame, period)
                    if unit == "Quote currency":
                        unit = frame.attrs.get("currency", "Quote currency unavailable")
                    close = float(frame["Close"].iloc[-1])
                    previous = float(frame["Close"].iloc[-2]) if len(frame)>1 else None
                    delta = f"{(close/previous-1)*100:+.2f}% vs prior close" if previous else None
                    st.metric(name, display_price(close, unit), delta)
                    unit_label = {"GBp": "GBp · British pence (100 GBp = 1 GBP)", "GBX": "GBX · British pence (100 GBX = 1 GBP)", "ZAc": "ZAc · South African cents", "ILA": "ILA · Israeli agorot"}.get(unit, unit)
                    st.caption(f'{unit_label}'+(' · FX estimate' if frame.attrs.get("fx_estimate") else '')+f' · {market_freshness(frame)}')
                    if view.empty:
                        st.info("No observations in selected range.")
                    else:
                        figure=price_figure(view, unit, compact=True)
                        if compact_controls:
                            figure.update_layout(height=125,margin=dict(l=2,r=5,t=15,b=2))
                            figure.update_xaxes(nticks=3)
                            figure.update_yaxes(nticks=3)
                        st.plotly_chart(figure, use_container_width=True,
                            config={"displayModeBar":False,"scrollZoom":False}, key="card_plot_"+symbol)
                        first = float(view["Close"].iloc[0])
                        change = (float(view["Close"].iloc[-1])/first-1)*100 if first else None
                        st.caption(f'{period} change {change:+.2f}% · Low {view["Close"].min():,.2f} / High {view["Close"].max():,.2f}' if change is not None else "Period change unavailable")
                    if compact_controls:
                        detail,source=st.columns([2,1])
                        if detail.button("EXPAND ↗", key="market_"+symbol, use_container_width=True):
                            market_dialog(name, symbol, unit, frame)
                        source.link_button("SOURCE",f"https://finance.yahoo.com/quote/{quote(symbol,safe='')}/",use_container_width=True)
                    elif st.button("EXPAND CHART ↗", key="market_"+symbol, use_container_width=True):
                        market_dialog(name, symbol, unit, frame)
                if not compact_controls or frame is None or frame.empty:
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
    title,currency_control=st.columns([4,1])
    title.subheader("MARKETS")
    currency=currency_control.selectbox("Display currency",["EUR","USD","Native quote"],key="market_currency",label_visibility="collapsed")
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
            current = st.session_state.get("global_market_selection", DEFAULT_MARKETS)
            if label not in current:
                st.session_state.global_market_selection = current+[label]
        if view.button("VIEW", use_container_width=True, help="Open detailed price chart"):
            with st.spinner("Loading chart…"):
                frame = market_data(selected["symbol"])
            if frame is None or frame.empty:
                st.info("Price history unavailable for this listing.")
            else:
                unit=frame.attrs.get("currency","Quote currency unavailable")
                pair=market_fx_pair(frame,unit,currency)
                converted,unit=convert_market_quote(frame,unit,currency,market_data(pair) if pair else None)
                if converted is None:st.info("Required FX rate unavailable for this listing.")
                else:market_dialog(selected["name"],selected["symbol"],unit,converted)
        if dismiss.button("CLOSE", use_container_width=True, help="Hide search results"):
            st.session_state.company_results = []
            st.rerun()
    elif submitted and not st.session_state.get("company_error"):
        st.info("No listings found. Try a ticker or shorter name.")
    registry = {**MARKET_PRESETS, **st.session_state.company_watchlist}
    with st.expander("EDIT WATCHLIST", expanded=False):
        if st.button("LOAD MAJOR COMPANIES + INDICES",key="load_market_defaults"):
            st.session_state.global_market_selection=DEFAULT_MARKETS.copy()
        choices = st.multiselect("Markets and companies",list(registry),
            default=DEFAULT_MARKETS+list(st.session_state.company_watchlist),
            key="global_market_selection")
        st.caption("Choose indices, currencies, crypto or added companies. Choices last for this session.")
    if choices:
        market_panel(choices,registry,compact_controls=True,display_currency=currency)
        st.caption("Currency applies to quoted prices; indices retain points and FX pairs retain their ratio units. Converted prices are daily FX estimates.")
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
    with st.container(key="us_election_kpis"):
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


def is_national_election(title, country, jurisdiction="", election_type=""):
    # Conservative scope: uncertain events are omitted rather than shown as national.
    text=(title+" "+election_type).casefold()
    excluded=r"\b(regional|local|municipal|mayoral|governor|gubernatorial|provincial|state|district|county|council|assembly constituency|by[ -]?elections?|special elections?|primar(?:y|ies)|leadership|party presidential|referend(?:um|a))\b"
    if re.search(excluded,text):
        return False
    if not country or country in ["Unspecified", ""]:
        return False
    if jurisdiction and jurisdiction.casefold() != country.casefold():
        return False
    office=r"\b(presidential|parliamentary|general election|general elections|legislative|national assembly|national council|federal election|federal elections|congressional|senate election|senate elections|house of representatives election|house of representatives elections)\b"
    if not re.search(office,text):
        return False
    if jurisdiction.casefold()==country.casefold():
        return True
    # Missing jurisdiction must still have a country-level name, not a regional name.
    demonyms = {
        "Brazil":"Brazilian", "United States":"American", "France":"French", "United Kingdom":"British",
        "Germany":"German", "Italy":"Italian", "Spain":"Spanish", "Portugal":"Portuguese",
        "Netherlands":"Dutch", "Belgium":"Belgian", "Austria":"Austrian", "Switzerland":"Swiss",
        "Sweden":"Swedish", "Norway":"Norwegian", "Denmark":"Danish", "Finland":"Finnish",
        "Poland":"Polish", "Czech Republic":"Czech", "Czechia":"Czech", "Greece":"Greek",
        "Turkey":"Turkish", "Türkiye":"Turkish", "Hungary":"Hungarian", "Romania":"Romanian",
        "Russia":"Russian", "Ukraine":"Ukrainian", "Ireland":"Irish", "Iceland":"Icelandic",
        "Malta":"Maltese", "Cyprus":"Cypriot", "Canada":"Canadian", "Mexico":"Mexican",
        "Argentina":"Argentine", "Chile":"Chilean", "Colombia":"Colombian", "Peru":"Peruvian",
        "Australia":"Australian", "New Zealand":"New Zealand", "Japan":"Japanese", "South Korea":"South Korean",
        "India":"Indian", "Pakistan":"Pakistani", "Bangladesh":"Bangladeshi", "Indonesia":"Indonesian",
        "Philippines":"Philippine", "Malaysia":"Malaysian", "Thailand":"Thai", "Israel":"Israeli",
        "South Africa":"South African", "Nigeria":"Nigerian", "Kenya":"Kenyan", "Ghana":"Ghanaian",
        "Egypt":"Egyptian", "Morocco":"Moroccan", "Senegal":"Senegalese", "Taiwan":"Taiwanese"
    }
    names=[country,demonyms.get(country, country)]
    return any(re.search(r"(?<!\w)"+re.escape(name)+r"(?!\w)",title,re.I) for name in names)


@st.cache_data(ttl=21600, show_spinner=False)
def elections_calendar():
    now = datetime.now(UTC)
    start, end = (now - timedelta(days=7)).date(), (now + timedelta(days=180)).date()
    query = '''SELECT DISTINCT ?election ?electionLabel ?date ?countryLabel ?jurisdictionLabel ?electionTypeLabel WHERE {
      ?election wdt:P31/wdt:P279* wd:Q40231; wdt:P585 ?date.
      FILTER(?date >= "STARTT00:00:00Z"^^xsd:dateTime && ?date <= "ENDT23:59:59Z"^^xsd:dateTime)
      ?election wdt:P17 ?country.
      OPTIONAL { ?election wdt:P1001 ?jurisdiction. }
      OPTIONAL { ?election wdt:P31 ?electionType. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } ORDER BY ?date LIMIT 1000'''.replace("START", str(start)).replace("END", str(end))
    try:
        r = requests.get("https://query.wikidata.org/sparql", params={"query": query, "format": "json"}, headers=HEADERS, timeout=15)
        r.raise_for_status()
        rows = r.json()["results"]["bindings"]
        result,seen=[],set()
        for x in rows:
            title=x["electionLabel"]["value"]
            country=x.get("countryLabel",{}).get("value","")
            jurisdiction=x.get("jurisdictionLabel",{}).get("value","")
            kind=x.get("electionTypeLabel",{}).get("value","")
            key=(x["election"]["value"],x["date"]["value"][:10])
            if key in seen or not is_national_election(title,country,jurisdiction,kind):
                continue
            seen.add(key)
            result.append(dict(Election=title,Country=country,Date=key[1],Source=key[0]))
        return result, None
    except Exception:
        return [], "Election calendar feed is unavailable. Election reporting below remains available."


def news_desk(items, channel, scope=None):
    scope = scope or channel
    st.subheader(channel.upper() + " / NEWS DESK")
    rows = [item for item in items if item["category"] == channel]
    topics = {
        "World": {"Diplomacy":r"diploma|summit|treaty|sanction|ambassador", "Economy":r"econom|inflation|trade|bank|budget", "Climate":r"climate|flood|storm|wildfire|earthquake", "Security":r"militar|attack|war|missile|defen[cs]|police"},
        "Politics": {"Elections":r"elect|vot|ballot|poll", "Government":r"government|minister|president|parliament|congress", "Policy":r"policy|reform|legislat|budget|tax", "Diplomacy":r"diploma|summit|treaty|sanction"},
        "Conflicts": {"Military":r"militar|troop|missile|drone|strike|attack", "Diplomacy":r"ceasefire|peace|talks|diploma|negotiat", "Humanitarian":r"humanitarian|refugee|displaced|civilian|aid", "Security":r"security|border|police|terror"}
    }[channel]
    selected = st.radio("TOPIC", ["All"]+list(topics), horizontal=True, key="desk_topic_"+scope, label_visibility="collapsed")
    controls, options = st.columns([3,1])
    sources = sorted({r["source"] for r in rows})
    with controls.popover("SOURCES / FILTER", use_container_width=True):
        selected_sources = st.multiselect("Publishers", sources, default=sources, key="desk_sources_"+scope)
        st.caption("Topic filters match words in headlines and feed summaries; categories can overlap.")
    limit = options.selectbox("Stories shown",[12,24,48],index=1,key="desk_limit_"+scope,label_visibility="collapsed")
    rows = [r for r in rows if r["source"] in selected_sources]
    if selected != "All":
        rows = [r for r in rows if re.search(topics[selected], r["title"]+" "+r["summary"], re.I)]
    rows.sort(key=lambda r:r["published"] or "",reverse=True)
    now = datetime.now(UTC)
    recent = sum(datetime.fromisoformat(r["published"]) >= now-timedelta(hours=6) for r in rows)
    with st.container(key="desk_kpis_"+scope):
        cols=st.columns(4)
        cols[0].metric("ARTICLES",len(rows))
        cols[1].metric("PUBLISHERS",len({r["source"] for r in rows}))
        cols[2].metric("LAST 6H / IN WINDOW",recent)
        latest=timestamp(rows[0]["published"]) if rows else "—"
        cols[3].metric("LATEST / MALTA",datetime.fromisoformat(rows[0]["published"]).astimezone(LOCAL).strftime("%H:%M") if rows else "—")
    if not rows:
        st.info("No stories match these filters. Try All reporting in News coverage, choose a publisher or widen the story window.")
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
        left.plotly_chart(fig,use_container_width=True,key="desk_activity_"+scope)
        counts=data["source"].value_counts().rename_axis("Publisher").reset_index(name="Articles")
        fig=px.bar(counts,x="Articles",y="Publisher",orientation="h",template="plotly_dark",color_discrete_sequence=["#40e0d0"])
        fig.update_layout(height=170,margin=dict(l=0,r=0,t=5,b=0),yaxis_title=None)
        right.plotly_chart(fig,use_container_width=True,key="desk_sources_chart_"+scope)
        st.caption("Counts cover filtered retrieved articles, not all reporting or confirmed events. Feed limits can leave older hours incomplete.")
    groups=group_reporting(rows)
    cards=[g[0] for g in groups]
    st.caption(f"{len(rows)} articles · {len(cards)} story groups · showing {min(limit,len(cards))} groups · latest {latest}")
    if channel == "Conflicts":
        st.caption("Regional reporting includes non-conflict stories. Claims are attributed to publishers; article counts do not measure military activity.")
    for start in range(0,min(limit,len(cards)),3):
        for card_index,(col,item) in enumerate(zip(st.columns(3),cards[start:min(start+3,limit)]),start=start):
            with col,st.container(border=True):
                st.markdown(f'<div class="sport-headline">{escape(item["title"])}</div>',unsafe_allow_html=True)
                st.caption(f'{item["source"]} · {timestamp(item["published"])}')
                if item["summary"]:
                    st.markdown(f'<div class="desk-excerpt">{escape(short_preview(item["summary"],42))}</div>',unsafe_allow_html=True)
                left,right=st.columns(2)
                uid=hashlib.sha256(item["url"].encode()).hexdigest()[:16]
                if left.button("BRIEF",key=f"desk_{scope}_{card_index}_{uid}",use_container_width=True):
                    story_dialog(item)
                right.link_button("SOURCE ↗",item["url"],use_container_width=True)
                related_reports(groups[card_index],scope=f"desk_{scope}_{card_index}")


COUNTRY_ALIASES = {
    "USA":["United States", "U.S.", "US", "American"], "GBR":["United Kingdom", "UK", "Britain", "British"],
    "RUS":["Russia", "Russian"], "UKR":["Ukraine", "Ukrainian"], "ISR":["Israel", "Israeli"],
    "PSE":["Palestine", "Palestinian", "Gaza", "West Bank"], "IRN":["Iran", "Iranian"],
    "CHN":["China", "Chinese"], "PRK":["North Korea"], "KOR":["South Korea"],
    "SYR":["Syria", "Syrian"], "SDN":["Sudan", "Sudanese"], "SSD":["South Sudan"],
    "MMR":["Myanmar", "Burma", "Burmese"], "COD":["DR Congo", "DRC", "Democratic Republic of the Congo"],
    "COG":["Republic of the Congo", "Congo-Brazzaville"], "LBN":["Lebanon", "Lebanese"],
    "YEM":["Yemen", "Yemeni"], "BRA":["Brazil", "Brazilian"], "MLT":["Malta", "Maltese"],
    "TUR":["Turkey", "Türkiye", "Turkish"], "CZE":["Czechia", "Czech Republic"],
    "CIV":["Ivory Coast", "Côte d’Ivoire", "Côte d'Ivoire"], "TWN":["Taiwan", "Taiwanese"],
}
CONFLICT_WORDS = r"\b(war|conflict|fighting|troops?|military|missiles?|airstrikes?|ceasefire|armed|bombing|drone attack|invasion)\b"
ELECTION_WORDS = r"\b(elections?|ballots?|voting|voters?|polling|runoff|run-off)\b"


@st.cache_data(ttl=86400, show_spinner=False)
def country_catalog():
    return {c.alpha_3: {"name": c.name, "aliases": COUNTRY_ALIASES.get(c.alpha_3, list(dict.fromkeys([c.name, getattr(c,"common_name",c.name),getattr(c,"official_name",c.name)])))} for c in pycountry.countries}


@lru_cache(maxsize=2048)
def country_alias_pattern(alias):
    return re.compile(r"(?<!\w)"+re.escape(alias)+r"(?!\w)",re.I if alias != "US" else 0)


def country_mentions(text, catalog):
    found=[]
    for code, country in catalog.items():
        if any(country_alias_pattern(alias).search(text) for alias in country["aliases"]):
            found.append(code)
    # Do not count a South Sudan mention as Sudan unless Sudan occurs separately.
    if "SSD" in found and not re.search(r"(?<!South )\bSudan\b",text,re.I):
        found=[c for c in found if c != "SDN"]
    return found


@st.cache_data(ttl=86400,show_spinner=False)
def world_geometry():
    try:
        r=requests.get("https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json",timeout=12,headers=HEADERS)
        r.raise_for_status()
        data=r.json()
        if data.get("type") != "FeatureCollection":
            return None
        return data
    except Exception:
        return None


@st.cache_data(ttl=180,show_spinner=False)
def country_news(code, layer, hours):
    country=country_catalog()[code]
    aliases=country["aliases"][:2]
    country_query="("+" OR ".join('"'+a+'"' for a in aliases)+")"
    topic={"All":"", "Conflicts":" (war OR conflict OR ceasefire OR military OR humanitarian)", "Elections":" (election OR voting OR ballot OR polling)", "Economy":" (economy OR inflation OR energy OR central bank OR trade)", "Policy":" (diplomacy OR sanctions OR treaty OR legislation OR policy)"}[layer]
    query=country_query+topic+f" when:{hours}h"
    url="https://news.google.com/rss/search?"+urlencode({"q":query,"hl":"en-GB","gl":"GB","ceid":"GB:en"})
    return fetch_feed("World", "Google News · "+country["name"], url)


def open_country(code):
    st.session_state.monitor_country=code
    st.session_state.monitor_country_layer=(st.session_state.get("world_layer") or "All")
    st.rerun()


def country_monitor(code):
    catalog=country_catalog()
    if code not in catalog:
        st.session_state.pop("monitor_country",None)
        st.rerun()
    if st.button("← BACK TO WORLD MONITOR",key="back_monitor"):
        st.session_state.pop("monitor_country",None)
        st.rerun()
    country=catalog[code]
    st.subheader(country["name"].upper()+" / COUNTRY BRIEFING")
    views=["Briefing","Economy & energy","Diplomacy & policy","Elections"]
    view=st.radio("COUNTRY VIEW",views,horizontal=True,key="country_view_"+code)
    topic={"Economy & energy":"Economy","Diplomacy & policy":"Policy","Elections":"Elections"}.get(view,"All")
    if view=="Briefing":
        focus=st.radio("REPORTING FOCUS",["All","Conflicts","Elections"],index=["All","Conflicts","Elections"].index(st.session_state.get("monitor_country_layer","All")),horizontal=True,key="country_layer_"+code)
        topic=focus
    with st.spinner("Loading country reporting…"):
        rows,error=country_news(code,topic,age)
    rows=filter_reports(rows)
    if error:st.warning(error)
    st.caption("English-language publisher reporting about this country · indexed by Google News · source attribution does not independently verify a claim")
    st.caption("Feed fetched "+(elapsed_label(rows[0].get("fetched_at")) if rows else "time unavailable")+" · selected story window applies")
    if view in ("Briefing","Elections"):
        dates,calendar_error=elections_calendar()
        matching=[r for r in election_countdowns(dates) if code in country_mentions(r["Country"],catalog)]
        with st.expander("NATIONAL ELECTION WATCH",expanded=view=="Elections"):
            if matching:
                st.dataframe(pd.DataFrame(matching),hide_index=True,use_container_width=True,column_config={"Source":st.column_config.LinkColumn("Calendar source")})
            else:
                st.caption(calendar_error or "No upcoming national election returned for this country.")
            st.caption("Community-maintained dates require verification at election authorities. Official polling/results are not connected.")
    if view=="Briefing" and rows:
        st.markdown("#### KEY DEVELOPMENTS / RETRIEVED REPORTS")
        for group in group_reporting(rows)[:3]:
            st.markdown("**"+group[0]["title"]+"**")
            st.caption(group[0]["source"]+" · "+timestamp(group[0]["published"])+" · "+report_context(group[0]))
        st.caption("Headlines selected by publication time; this is a source digest, not an independently verified assessment.")
    category="Conflicts" if topic=="Conflicts" else "Politics" if topic in ("Elections","Policy") else "Markets" if topic=="Economy" else "World"
    # The reusable desk uses its topic configuration; economic reports use the World configuration.
    desk_category=category if category in ("World","Politics","Conflicts") else "World"
    news_desk([dict(r,category=desk_category) for r in rows],desk_category,scope="country_"+code+"_"+topic)


def election_countdowns(rows):
    today=datetime.now(UTC).date()
    result=[]
    for row in rows:
        try:
            days=(datetime.fromisoformat(row["Date"]).date()-today).days
        except (ValueError,TypeError,KeyError):
            continue
        if days>=0:
            result.append(dict(row,**{"Days to vote":days}))
    return sorted(result,key=lambda r:r["Days to vote"])


def map_highlight(conflict,election,coverage):
    if conflict and election:return "#8b8296"
    if conflict:return "#ca6976"
    if election:return "#c7a15d"
    return "#40e0d0" if coverage else "#102537"




@st.cache_resource
def globe_component(markup):
    import tempfile
    from pathlib import Path
    from streamlit.components.v1 import declare_component
    directory=Path(tempfile.mkdtemp(prefix="intel_globe_"))
    (directory/"index.html").write_text(markup,encoding="utf-8")
    return declare_component("intel_globe_"+hashlib.sha256(markup.encode()).hexdigest()[:10],path=str(directory))


GLOBE_HTML = r"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script><style>html{background:transparent}body{margin:0;background:transparent;color:#a6c0d2;font:12px monospace}body{position:relative}#leader{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:1;overflow:visible}#globe{display:block;width:100%;height:360px;touch-action:none;cursor:grab}#globe:active{cursor:grabbing}#tip{position:absolute;top:5px;left:5px;pointer-events:auto;background:#0c1c2af5;padding:10px;border-radius:5px;border:1px solid #31566a;box-shadow:0 5px 20px #0005;width:238px;max-width:calc(100% - 10px);display:none;overflow:visible;box-sizing:border-box;font-size:10px;line-height:1.4;z-index:2}#tip strong{font-size:13px;color:#dceef9;display:block;letter-spacing:.7px}#tip .eyebrow{font-size:9px;letter-spacing:1px;margin-bottom:4px}#tip .detail{color:#9ab0c0;margin:4px 0}#tip .headline{border-top:1px solid #294354;margin-top:6px;padding-top:5px;color:#d5e4ee}#tip .bars{display:flex;height:22px;align-items:flex-end;gap:3px;margin-top:5px}#tip .bar{flex:1;min-height:2px;opacity:.75}#tip .foot{font-size:9px;color:#849eaf;margin-top:5px}#help{text-align:center;font-size:11px;color:#8299ab}.profile-actions{display:flex;gap:5px;margin-top:8px}.profile-actions button{background:#183744;color:#b8eeea;border:1px solid #426673;border-radius:3px;font:10px monospace;padding:5px;cursor:pointer}#zoom-controls{position:absolute;left:8px;top:8px;display:flex;gap:3px;z-index:3}#zoom-controls button{font:12px monospace;background:#0d2231;color:#a5e9e4;border:1px solid #34596b;border-radius:3px;min-width:26px;height:25px;cursor:pointer}#zoom-controls button:focus-visible{outline:2px solid #65d6d0}#zoom-value{font:10px monospace;color:#8caebb;padding:7px 4px}
</style></head><body><div id="zoom-controls"><button id="zoom-out" aria-label="Zoom out">−</button><button id="zoom-in" aria-label="Zoom in">+</button><button id="zoom-reset" aria-label="Reset globe view">Reset</button><span id="zoom-value">1.0×</span></div><div id="tip"></div><svg id="globe" aria-label="Interactive world globe" role="img"></svg><svg id="leader" aria-hidden="true"><polyline id="callout-line" fill="none" stroke="#65d6d0" stroke-width="1"/><circle id="callout-dot" r="3" fill="#65d6d0"/></svg><script>
let lastFrameHeight=null;const send=(type,extra={})=>{if(type==='streamlit:setFrameHeight'){if(extra.height===lastFrameHeight)return;lastFrameHeight=extra.height;}parent.postMessage({isStreamlitMessage:true,type,...extra},'*');};
send('streamlit:componentReady',{apiVersion:1});send('streamlit:setFrameHeight',{height:360});
const tip=document.getElementById('tip');
function calloutLayout(width){const card=Math.min(340,Math.max(280,width*.38));return width>=640?{x:width-card-6,y:14,cx:(width-card-24)/2,card:card,mobile:false}:{x:6,y:368,cx:width/2,card:width-12,mobile:true};}
function resetIntel(force=false,resize=true){if(pinnedCode&&!force)return;cancelHover();activeHoverCode=null;tip.replaceChildren();tip.style.display='none';document.getElementById('leader').style.display='none';if(resize)send('streamlit:setFrameHeight',{height:360});}
function positionIntel(e){
 const width=document.body.clientWidth,layout=calloutLayout(width);
 tip.style.display='block';tip.style.left=layout.x+'px';tip.style.top=layout.y+'px';tip.style.width=layout.card+'px';
 const leader=document.getElementById('leader'),line=document.getElementById('callout-line'),dot=document.getElementById('callout-dot');
 leader.style.display='block';const endX=layout.mobile?layout.x+20:layout.x-3,endY=layout.mobile?layout.y:layout.y+Math.min(tip.offsetHeight/2,110);
 line.setAttribute('points',layout.mobile?`${e.clientX},${e.clientY} ${endX},350 ${endX},${endY}`:`${e.clientX},${e.clientY} ${endX-16},${endY} ${endX},${endY}`);
 dot.setAttribute('cx',e.clientX);dot.setAttribute('cy',e.clientY);
 const fullHeight=pinnedCode?Math.max(360,layout.y+tip.offsetHeight+10):360;leader.style.height=fullHeight+'px';send('streamlit:setFrameHeight',{height:fullHeight});
}
function showIntel(e,d){
 const info=d.properties.intel||{},focus=info.focus||'All',tone=focus==='Conflicts'?'#ca6976':focus==='Elections'?'#c7a15d':'#40e0d0';tip.replaceChildren();
 const add=(tag,text,cls)=>{const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;tip.appendChild(el);return el;};
 add('div',(focus==='All'?'COUNTRY INTELLIGENCE':focus.toUpperCase()+' FOCUS'),'eyebrow').style.color=tone;
 add('strong',d.properties.Country);add('div','Retrieved reporting · selected story window','detail');
 if(focus==='Elections'){
  if(info.election){add('div',info.election.name.slice(0,pinnedCode?90:64),'headline');add('div',info.election.date+' · '+info.election.days+' days to vote','detail');add('div','Wikidata calendar · verify with election authority','foot');}
  else add('div','No upcoming national vote in connected calendar','detail');
  add('div','Official polls/results not connected','foot');
 }
 if(pinnedCode&&(info.bars||[]).some(n=>n>0)){
  add('div','Retrieved reports by publication day (UTC)','foot');const chart=add('div','','bars'),max=Math.max(...info.bars,1);
  info.bars.forEach((v,i)=>{const bar=document.createElement('span');bar.className='bar';bar.style.height=Math.max(2,v/max*22)+'px';bar.style.background=tone;bar.title=info.barDates[i]+': '+v+' reports';chart.appendChild(bar);});
  add('div',info.barDates[0]+' — '+info.barDates[6]+' · selected window only','foot');
 }
 (info.headlines||[]).slice(0,pinnedCode===d.properties.code?2:1).forEach(r=>{add('div',r.title.slice(0,105),'headline');add('div',r.source.slice(0,45)+' · '+r.time,'foot');});
 if(!(info.headlines||[]).length)add('div','No matching retrieved headlines','detail');
 const actions=add('div','','profile-actions');
 function button(label,action){const b=document.createElement('button');b.textContent=label;b.onclick=()=>send('streamlit:setComponentValue',{value:{code:d.properties.code,action:action,nonce:Date.now()},dataType:'json'});actions.appendChild(b);}
 if(pinnedCode===d.properties.code){button('OPEN COUNTRY ↗','open');button('UNPIN','clear');}
 else add('div','Click country to pin this dossier','foot');
 positionIntel(e);
}
let hoverTimer=null,hideTimer=null,activeHoverCode=null,pendingHoverCode=null;
function cancelHover(){clearTimeout(hoverTimer);clearTimeout(hideTimer);hoverTimer=null;hideTimer=null;pendingHoverCode=null;}
function queueHover(e,d){
 clearTimeout(hideTimer);
 if(activeHoverCode===d.properties.code){clearTimeout(hoverTimer);pendingHoverCode=null;return;}
 clearTimeout(hoverTimer);pendingHoverCode=d.properties.code;
 const point={clientX:e.clientX,clientY:e.clientY};
 hoverTimer=setTimeout(()=>{if(pinnedCode)return;activeHoverCode=d.properties.code;pendingHoverCode=null;showIntel(point,d);},90);
}
function delayedHide(){clearTimeout(hoverTimer);pendingHoverCode=null;clearTimeout(hideTimer);hideTimer=setTimeout(()=>resetIntel(),240);}
tip.addEventListener('mouseenter',cancelHover);tip.addEventListener('mouseleave',delayedHide);
document.getElementById('globe').addEventListener('mouseenter',()=>clearTimeout(hideTimer));
document.getElementById('globe').addEventListener('mouseleave',delayedHide);
let pinnedCode=null;
let args,rotation=[-15,-20],draw,lastRegion,zoomLevel=1;
addEventListener('message',e=>{if(e.data.type!=='streamlit:render')return;args=e.data.args;pinnedCode=args.pinned||null;resetIntel(true,false);if(args.region!==lastRegion){rotation=[-args.center[1],-args.center[0]];lastRegion=args.region;}
if(!window.d3){document.getElementById('tip').textContent='Globe unavailable — use Flat map or country search';return;}
const width=document.body.clientWidth,height=360,r=Math.min((calloutLayout(width).mobile?width:width-calloutLayout(width).card-24)/2-16,164),root=d3.select('#globe').attr('viewBox',`0 0 ${width} ${height}`);root.selectAll('*').remove();
const clip=root.append('defs').append('clipPath').attr('id','globe-viewport');clip.append('rect').attr('x',0).attr('y',0).attr('width',calloutLayout(width).mobile?width:calloutLayout(width).x-12).attr('height',height);const svg=root.append('g').attr('clip-path','url(#globe-viewport)');
const projection=d3.geoOrthographic().translate([calloutLayout(width).cx,height/2]).scale(r*zoomLevel).rotate(rotation).clipAngle(90),path=d3.geoPath(projection);
const defs=svg.append('defs'),grad=defs.append('radialGradient').attr('id','ocean');grad.append('stop').attr('offset','0%').attr('stop-color','#13394b');grad.append('stop').attr('offset','100%').attr('stop-color','#071420');
svg.append('circle').attr('cx',calloutLayout(width).cx).attr('cy',height/2).attr('r',r+5).attr('fill','none').attr('stroke','#29bdb655').attr('stroke-width',3);
svg.append('circle').attr('cx',calloutLayout(width).cx).attr('cy',height/2).attr('r',r+10).attr('fill','none').attr('stroke','#315266').attr('stroke-width',.6).attr('stroke-dasharray','2 8');
[0,90,180,270].forEach(a=>{const rad=a*Math.PI/180;svg.append('line').attr('x1',calloutLayout(width).cx+Math.cos(rad)*(r+6)).attr('y1',height/2+Math.sin(rad)*(r+6)).attr('x2',calloutLayout(width).cx+Math.cos(rad)*(r+12)).attr('y2',height/2+Math.sin(rad)*(r+12)).attr('stroke','#80a7b9').attr('stroke-width',1);});
svg.append('path').datum({type:'Sphere'}).attr('fill','url(#ocean)').attr('stroke','#487587');
svg.append('path').datum(d3.geoGraticule10()).attr('fill','none').attr('stroke','#2c5265').attr('stroke-width',.4);
const features=args.features.map(f=>{const g=JSON.parse(JSON.stringify(f));const polys=g.geometry.type==='Polygon'?[g.geometry.coordinates]:g.geometry.type==='MultiPolygon'?g.geometry.coordinates:[];polys.forEach(rings=>{if(d3.geoArea({type:'Polygon',coordinates:rings})>2*Math.PI)rings.forEach(ring=>ring.reverse());});return g;});
svg.selectAll('.country').data(features).enter().append('path').attr('class','country').attr('fill',d=>d.properties.fill).attr('fill-opacity',d=>d.properties.highlight?.58:.35).attr('stroke','#567889').attr('stroke-width',.45)
.on('mouseenter',function(e,d){d3.select(this).attr('stroke','#d4ffff').attr('stroke-width',1.5);if(!pinnedCode)queueHover(e,d);})
.on('mousemove',function(e,d){if(!pinnedCode&&activeHoverCode===d.properties.code)positionIntel(e);})
.on('mouseleave',function(){d3.select(this).attr('stroke','#567889').attr('stroke-width',.45);})
.on('click',(e,d)=>{if(e.defaultPrevented)return;cancelHover();pinnedCode=d.properties.code;showIntel(e,d);send('streamlit:setComponentValue',{value:{code:d.properties.code,action:'pin',nonce:Date.now()},dataType:'json'});});
draw=()=>{svg.selectAll('path').attr('d',path);if(pinnedCode){const f=features.find(f=>f.properties.code===pinnedCode);if(f){const center=d3.geoCentroid(f),xy=projection(center),visible=d3.geoDistance(center,[-rotation[0],-rotation[1]])<Math.PI/2;showIntel({clientX:visible?xy[0]:calloutLayout(width).cx,clientY:visible?xy[1]:180},f);if(!visible)document.getElementById('leader').style.display='none';}}};draw();if(!pinnedCode)send('streamlit:setFrameHeight',{height:360});
function changeZoom(next){zoomLevel=Math.max(1,Math.min(3.5,next));projection.scale(r*zoomLevel);document.getElementById('zoom-value').textContent=zoomLevel.toFixed(1)+'×';resetIntel();draw();}
document.getElementById('zoom-in').onclick=()=>changeZoom(zoomLevel+.3);document.getElementById('zoom-out').onclick=()=>changeZoom(zoomLevel-.3);
document.getElementById('zoom-reset').onclick=()=>{rotation=[-args.center[1],-args.center[0]];projection.rotate(rotation);changeZoom(1);};
document.getElementById('zoom-value').textContent=zoomLevel.toFixed(1)+'×';
document.getElementById('globe').onwheel=e=>{if(!e.ctrlKey)return;e.preventDefault();changeZoom(zoomLevel*(e.deltaY<0?1.12:1/1.12));};

root.call(d3.drag().on('start',()=>resetIntel()).on('drag',e=>{rotation=[rotation[0]+e.dx*.35,Math.max(-80,Math.min(80,rotation[1]-e.dy*.35))];projection.rotate(rotation);draw();}));
});</script></body></html>"""


def monitor_reports(items,layer):
    pattern={"Conflicts":CONFLICT_WORDS,"Elections":ELECTION_WORDS}.get(layer)
    return [item for item in items if not pattern or re.search(pattern,item.get("title","")+" "+item.get("summary",""),re.I)]


def overview_developments(items):
    layer=(st.session_state.get("world_layer") or "All")
    heading={"All":"CURRENT DEVELOPMENTS","Conflicts":"CONFLICT DEVELOPMENTS","Elections":"ELECTION DEVELOPMENTS"}[layer]
    tone={"All":"#40e0d0","Conflicts":"#ca6976","Elections":"#c7a15d"}[layer]
    st.markdown('<div class="monitor-heading">'+heading+'</div>',unsafe_allow_html=True)
    st.markdown('<div class="focus-label" style="color:'+tone+'">● '+("All reporting topics" if layer=="All" else layer+" active")+'</div>',unsafe_allow_html=True)
    groups=group_reporting(monitor_reports(items,layer))[:5]
    if not groups:st.caption("No matching reports in this window.")
    for index,group in enumerate(groups):
        item=group[0]
        st.markdown('<div class="intel-row"><span class="tag">'+escape(item['category'].upper())+'</span><div>'+escape(item['title'])+'</div></div>',unsafe_allow_html=True)
        st.caption(item['source']+' · '+timestamp(item['published']))
        summary=short_preview(item.get('summary',''),24)
        if summary and summary.casefold()!=item['title'].casefold():
            st.markdown('<div class="intel-preview">'+escape(summary)+'</div>',unsafe_allow_html=True)
        if st.button("BRIEF ↗",key="focus_brief_"+str(index)):story_dialog(item)
    if layer=="Elections":
        rows,error=elections_calendar()
        dates=election_countdowns(rows)[:3]
        st.markdown('<div class="focus-label">UPCOMING NATIONAL VOTES</div>',unsafe_allow_html=True)
        for row in dates:
            st.markdown("**"+escape(row["Country"])+"** · "+row["Date"]+" · "+str(row["Days to vote"])+" days")
            st.link_button("CALENDAR SOURCE ↗",row["Source"])
        if not dates:st.caption(error or "No upcoming national election dates returned.")
        st.caption("Wikidata calendar · verify dates with national election authorities")


def overview_navigate(channel):
    st.session_state.channel=channel
    st.session_state.pop("monitor_country",None)


def compact_pulse():
    basket={name:ASSETS[name] if name in ASSETS else MARKET_PRESETS[name] for name in ["S&P 500","Nasdaq","Gold","Silver","Brent oil","EUR / USD"]}
    with ThreadPoolExecutor(max_workers=4) as pool:
        frames=list(pool.map(lambda name:market_data(basket[name][0]),basket))
    fx=market_data("EURUSD=X")
    cells=[]
    for (name,(symbol,unit)),frame in zip(basket.items(),frames):
        if name in ("Gold","Silver","Brent oil"):
            frame,unit=convert_commodity(frame,unit,"EUR","Grams",fx)
        if frame is None or frame.empty:
            cells.append('<div class="ticker-cell">'+escape(name)+'<br>Unavailable</div>');continue
        close=float(frame.Close.iloc[-1]);prior=float(frame.Close.iloc[-2]) if len(frame)>1 else None
        change=(close/prior-1)*100 if prior else None
        tone="#40e0d0" if change is not None and change>=0 else "#ff6b86"
        values=chart_window(frame,"1M").Close.tolist();low=min(values);span=max(values)-low or 1
        points=' '.join(f'{i*100/max(1,len(values)-1):.1f},{25-(v-low)*22/span:.1f}' for i,v in enumerate(values))
        value=f"{close:,.4f}" if name=="EUR / USD" else f"{close:,.2f}"
        delta=f"{change:+.2f}%" if change is not None else "—"
        cells.append(f'<div class="ticker-cell" title="{escape(market_freshness(frame),quote=True)}"><span class="ticker-name">{escape(name)}</span><div class="ticker-value">{value} <small style="color:{tone}">{delta}</small></div><div class="ticker-bottom"><span>{escape(unit)}</span><svg viewBox="0 0 100 28" aria-hidden="true"><polyline points="{points}" fill="none" stroke="{tone}" stroke-width="1.6"/></svg></div></div>')
    st.markdown('<div class="ticker-strip">'+''.join(cells)+'</div>',unsafe_allow_html=True)
    st.caption("MARKET PULSE · delayed daily quotes",help="Yahoo Finance daily closes · 1M sparklines · metals/oil futures · gold/silver EUR per gram, oil EUR per barrel · EUR estimates use historical daily FX. Hover a quote for its source date; open Markets or Commodities for full charts.")


def country_hover_details(code,items,election_rows,catalog,layer,already_matched=False):
    matches=list(items) if already_matched else [item for item in monitor_reports(items,layer) if code in country_mentions(item.get("title","")+" "+item.get("summary",""),catalog)]
    matches=sorted(matches,key=lambda row:row.get("published") or "",reverse=True)
    today=datetime.now(UTC).date()
    days=[today-timedelta(days=i) for i in range(6,-1,-1)]
    daily=[sum(1 for row in matches if (row.get("published") or "")[:10]==day.isoformat()) for day in days]
    dates=election_countdowns(election_rows)
    return {"focus":layer,"reports":len(matches),"headlines":[{"title":row["title"][:108]+("…" if len(row["title"])>108 else ""),"source":row["source"],"time":timestamp(row.get("published"))} for row in matches[:2]],"bars":daily,"barDates":[day.strftime("%d %b") for day in days],"election":({"name":dates[0].get("Election","National election"),"date":dates[0]["Date"],"days":dates[0]["Days to vote"]} if dates else None)}


def world_monitor(items):
    st.markdown('<div class="monitor-heading">WORLD MONITOR</div>',unsafe_allow_html=True)
    controls,selector,settings=st.columns([2,2,1])
    layer=controls.segmented_control("Monitor focus",["All","Conflicts","Elections"],default="All",selection_mode="single",key="world_layer",label_visibility="collapsed") or "All"
    catalog=country_catalog()
    ordered=sorted(catalog,key=lambda code:catalog[code]["name"])
    with selector:
        selection=st.selectbox("Find a country",[None]+ordered,format_func=lambda code:"Find a country…" if code is None else catalog[code]["name"],key="country_picker",label_visibility="collapsed")
        if selection and st.button("OPEN COUNTRY ↗",key="open_picked_country",use_container_width=True):open_country(selection)
    with settings.popover("⚙",use_container_width=True):
        map_view=st.radio("Display",["Globe","Flat map"],horizontal=True,key="monitor_display")
        coverage_slot=st.container()
        region=st.selectbox("Map region",["World","Europe","Middle East","Americas","Asia-Pacific","Africa"],key="map_region")
        favourites=st.multiselect("Favourite countries",ordered,default=st.session_state.get("saved_country_favourites",[]),format_func=lambda code:catalog[code]["name"],max_selections=6,key="country_favourites")
        st.session_state.saved_country_favourites=list(favourites)
        st.caption("Country-level mentions in retrieved news. Colours indicate reporting topics; they are not verified war-zone boundaries or threat ratings.")
        for code in favourites:
            if st.button("★ "+catalog[code]["name"],key="favourite_country_"+code,use_container_width=True):open_country(code)
    counts={}
    hover_by_country={}
    conflict_counts,election_counts={},{}
    for item in monitor_reports(items,layer):
        text=item["title"]+" "+item["summary"]
        for code in country_mentions(text,catalog):
            hover_by_country.setdefault(code,[]).append(item)
            counts[code]=counts.get(code,0)+1
            if re.search(CONFLICT_WORDS,text,re.I):
                conflict_counts[code]=conflict_counts.get(code,0)+1
            if re.search(ELECTION_WORDS,text,re.I):
                election_counts[code]=election_counts.get(code,0)+1
    calendar_rows,calendar_error=elections_calendar() if layer in ["All","Elections"] else ([],None)
    elections={}
    today=datetime.now(UTC).date().isoformat()
    for row in calendar_rows:
        if row["Date"]<today:
            continue
        codes=country_mentions(row["Country"],catalog)
        for code in codes:
            elections.setdefault(code,[]).append(row)
    data=world_geometry()
    if data:
        color="#ca6976" if layer=="Conflicts" else "#c7a15d" if layer=="Elections" else "#40e0d0"
        regions={"World":([22,10],2),"Europe":([52,15],4),"Middle East":([30,43],4),"Americas":([15,-80],3),"Asia-Pacific":([24,115],3),"Africa":([1,20],3)}
        center,zoom=regions[region]
        if map_view=="Flat map":
            m=folium.Map(location=center,zoom_start=zoom,min_zoom=1,max_zoom=7,tiles=None,control_scale=True,prefer_canvas=True,scrollWheelZoom=False)
            from folium.plugins import Fullscreen
            Fullscreen(position="topright",title="Full-screen map",title_cancel="Exit full screen").add_to(m)
            m.get_root().header.add_child(folium.Element("<style>.leaflet-container{background:#070d17!important}.leaflet-tooltip{background:#101c2c;color:#dce9f5;border:1px solid #426275;font:12px monospace}</style>"))
            for latitude in range(-60,90,30):
                folium.PolyLine([[latitude,-180],[latitude,180]],color="#183040",weight=.5,opacity=.6,interactive=False).add_to(m)
            for longitude in range(-180,181,30):
                folium.PolyLine([[-80,longitude],[85,longitude]],color="#183040",weight=.5,opacity=.6,interactive=False).add_to(m)
        features=[]
        for original in data["features"]:
            f=dict(original)
            props=dict(f["properties"])
            code=f.get("id", "")
            # The boundary source uses three-letter country codes.
            props["code"]=code
            props["Country"]=catalog.get(code,{}).get("name",props.get("name","Unknown"))
            props["Articles"]=counts.get(code,0)
            props["Calendar elections"]=len(elections.get(code,[]))
            props["highlight"]=bool(props["Articles"] or props["Calendar elections"])
            conflict=bool(conflict_counts.get(code)) if layer in ["All","Conflicts"] else False
            election=bool(election_counts.get(code) or elections.get(code)) if layer in ["All","Elections"] else False
            props["fill"]=("#ca6976" if conflict else "#102537") if layer=="Conflicts" else ("#c7a15d" if election else "#102537") if layer=="Elections" else map_highlight(conflict,election,props["Articles"])
            dates=election_countdowns(elections.get(code,[]))
            props["Next national vote"]=f'{dates[0]["Date"]} · {dates[0]["Days to vote"]} days' if dates else "No calendar entry"
            props["intel"]=country_hover_details(code,hover_by_country.get(code,[]),elections.get(code,[]),catalog,layer,already_matched=True)
            f["properties"]=props
            features.append(f)
        boundaries={"type":"FeatureCollection","features":features}

        if map_view=="Globe":
            result=globe_component(GLOBE_HTML)(features=features,region=region,center=center,pinned=st.session_state.get("pinned_country"),key="overview_globe",default=None)
            if result and result.get("nonce")!=st.session_state.get("globe_last_nonce"):
                st.session_state.globe_last_nonce=result.get("nonce")
                action=result.get("action","pin")
                if action=="clear":
                    st.session_state.pop("pinned_country",None)
                    st.rerun()
                elif result.get("code") in catalog:
                    code=result["code"]
                    if action=="open":open_country(code)
                    st.session_state.pinned_country=code
                    st.rerun()
        else:
            folium.GeoJson(boundaries,name="Countries",style_function=lambda f:{"fillColor":f["properties"]["fill"],"color":"#426275","weight":.6,"fillOpacity":.32 if f["properties"]["highlight"] else .10},highlight_function=lambda f:{"weight":2,"color":"#8cffff","fillOpacity":.7},tooltip=folium.GeoJsonTooltip(fields=["Country","Articles","Calendar elections","Next national vote"],aliases=["Country","Retrieved articles","Upcoming calendar entries","Next national vote"],sticky=False),embed=True).add_to(m)
            result=st_folium(m,height=330,use_container_width=True,key="world_map_"+layer+"_"+region,returned_objects=["last_clicked"])
            click=result.get("last_clicked") if result else None
            fingerprint=(layer,click.get("lat"),click.get("lng")) if click else None
            if click and fingerprint != st.session_state.get("monitor_last_click"):
                st.session_state.monitor_last_click=fingerprint
                point=Point(((click["lng"]+180)%360)-180,click["lat"])
                for f in features:
                    code=f["properties"]["code"]
                    if code in catalog and shape(f["geometry"]).covers(point):
                        open_country(code)
                        break
    else:
        st.info("Map boundaries are unavailable. Select a country above to open its briefing.")
    entries=([("#ca6976","Conflict reports"),("#c7a15d","Election reports / dates"),("#8b8296","Both topics"),("#40e0d0","Other reports"),("#102537","No matched coverage")] if layer=="All" else [("#ca6976","Conflict reports"),("#102537","No matching reports")] if layer=="Conflicts" else [("#c7a15d","Election reports / dates"),("#102537","No matched coverage")])
    st.markdown('<div class="monitor-legend">'+''.join('<span><i style="background:'+color+'"></i>'+label+'</span>' for color,label in entries)+'</div>',unsafe_allow_html=True)
    st.caption("Reporting topics · not a risk rating",help="Countries may be mentioned without being the location of an event. Unhighlighted areas indicate no matching data in connected sources, not absence of events. Use + / − to zoom; Ctrl + wheel also zooms on desktop.")
    with st.expander("OFFICIAL ECONOMIC WATCH",expanded=False):
        st.caption("US economic releases and Fed / ECB meetings · load separately to keep the globe responsive")
        if st.button("LOAD / REFRESH EVENTS",key="overview_load_economic"):
            with st.spinner("Checking official calendars…"):
                with ThreadPoolExecutor(max_workers=4) as pool:
                    results=list(pool.map(economic_calendar_source,ECONOMIC_SOURCES))
                st.session_state.overview_economic_events=[row for rows,status in results for row in rows]
                st.session_state.overview_economic_health=[status for rows,status in results]
        if "overview_economic_events" in st.session_state:
            now=datetime.now(UTC);today=now.date().isoformat()
            upcoming=[]
            for row in st.session_state.overview_economic_events:
                if row["Date"]<today:continue
                when=row.get("WhenUTC")
                if when and datetime.fromisoformat(when)<=now:continue
                upcoming.append(row)
            for row in sorted(upcoming,key=lambda row:(row["Date"],row.get("WhenUTC") or ""))[:3]:
                when=row.get("WhenUTC")
                time_label=datetime.fromisoformat(when).astimezone(ZoneInfo("Europe/Malta")).strftime("%H:%M Malta") if when else row.get("TimeNote","Time not published")
                st.markdown("**"+row["Date"]+" · "+time_label+"**")
                st.link_button(row["Event"]+" ↗",row["Source"],use_container_width=True)
                st.caption(row["Publisher"]+" · "+row["Region"])
            if not upcoming:st.caption("No upcoming supported events returned.")
            statuses=st.session_state.get("overview_economic_health",[])
            if any(status.get("Status")!="Available" for status in statuses):st.caption("Some official calendars are unavailable; coverage is incomplete.")
            st.caption("Official calendar dates · six-hour source cache · no forecasts or actual release values connected")
    with coverage_slot:
        with st.expander("Coverage / election dates",expanded=False):
            st.caption("Highlights use country mentions in retrieved reporting, not verified war-zone boundaries or risk ratings. No highlight does not establish absence of events.")
            if calendar_error:st.caption("Election calendar unavailable on this check.")
            upcoming=election_countdowns(calendar_rows)
            if upcoming:st.dataframe(pd.DataFrame(upcoming[:12]),hide_index=True,use_container_width=True,column_config={"Source":st.column_config.LinkColumn("Source ↗")})
            st.caption("National votes: Wikidata calendar; verify with election authorities. Boundaries: world.geo.json / Natural Earth, illustrative.")


def update_overview_changes(items, previous=None):
    reports={report_key(r):r for r in items if r.get("category")!="Sports"}
    signature=tuple(sorted((key,r.get("published"),r["title"]) for key,r in reports.items()))
    if previous is None:
        return dict(known=dict.fromkeys(reports),signature=signature,pending={},started=datetime.now(UTC).isoformat())
    if signature==previous["signature"]:
        return previous
    state=dict(previous,known=dict(previous["known"]),pending=dict(previous["pending"]),signature=signature)
    for key,report in reports.items():
        if key not in state["known"]:
            state["pending"][key]=report
        state["known"][key]=None
    # Bound session memory; retain discovery order for the most recent 5,000 URLs.
    while len(state["known"])>5000:
        state["known"].pop(next(iter(state["known"])))
    pending=sorted(state["pending"].items(),key=lambda pair:pair[1].get("published") or "",reverse=True)
    state["pending"]=dict(pending[:50])
    return state


@st.dialog("NEW REPORTS / THIS VISIT",width="large")
def updates_dialog(groups):
    with st.container(key="brief_scroll",border=False):
        st.caption("Newly retrieved reporting during this session. Publication time may precede discovery; these are not independently verified event changes.")
        selected=st.selectbox("Choose report",list(range(len(groups))),format_func=lambda i:groups[i][0]["title"],key="updates_selected_report")
        item=groups[selected][0]
        st.write(item["title"])
        st.caption(item["source"]+" · "+timestamp(item["published"]))
        st.write(short_preview(item.get("summary",""),180))
        if st.button("LOAD LONGER SOURCE PREVIEW",key="updates_load_preview"):
            with st.spinner("Loading source preview…"):
                text=article_preview(item["url"])
            if text:st.write(text)
            else:st.caption("No longer preview available; open the original source.")
        st.link_button("OPEN SOURCE ↗",item["url"],use_container_width=True)
        with st.expander("ALL NEW HEADLINES"):
            for group in groups:st.link_button(group[0]["title"],group[0]["url"])
        if st.button("MARK UPDATES AS READ",key="clear_overview_changes",use_container_width=True):
            state=st.session_state.overview_change_state
            state["pending"]={}
            st.session_state.overview_change_state=state
            st.rerun()


def overview_changes(all_items, visible_items):
    state=update_overview_changes(all_items,st.session_state.get("overview_change_state"))
    st.session_state.overview_change_state=state
    visible={report_key(r) for r in visible_items}
    groups=group_reporting([r for key,r in state["pending"].items() if key in visible])
    with st.container(key="changes_strip"):
        summary,action=st.columns([4,1])
        label=f"{len(groups)} new reporting groups" if groups else "No new reports · monitoring this visit"
        summary.markdown('<div class="changes-summary" title="Newly retrieved reports in your current filters, tracked during this browser session"><span style="color:#40e0d0">UPDATES</span> &nbsp; '+escape(label)+'</div>',unsafe_allow_html=True)
        if action.button("VIEW UPDATES" if groups else "UP TO DATE",key="open_updates",disabled=not bool(groups),use_container_width=True):updates_dialog(groups)


def overview_panel(items, errors, change_items=None):
    if st.session_state.get("monitor_country"):
        country_monitor(st.session_state.monitor_country)
        return
    items=[r for r in items if r["category"]!="Sports"]
    now=datetime.now(UTC)
    st.markdown('<div class="ops-strip"><span><span class="ops-dot"></span><strong>GLOBAL SITUATION DESK</strong> / '+escape(st.session_state.get("news_scope","Major developments").upper())+'</span><span>'+now.strftime("%d %b %Y · %H:%M UTC")+' / '+now.astimezone(ZoneInfo("Europe/Malta")).strftime("%H:%M MALTA")+'</span></div>',unsafe_allow_html=True)
    overview_changes(items if change_items is None else change_items,items)
    with st.container(key="overview_pulse_tight"):
        compact_pulse()
    with st.container(key="explore_desks"):
        for col,channel in zip(st.columns(6),["World","Politics","Conflicts","Elections","Economic Calendar","Markets"]):
            label="CALENDAR" if channel=="Economic Calendar" else channel.upper()
            col.button(label+" ↗",key="branch_"+channel,on_click=overview_navigate,args=(channel,),use_container_width=True)
    with st.container(key="overview_command"):
        globe,developments=st.columns([1.8,1],gap="medium")
        with globe:world_monitor(items)
        with developments:overview_developments(items)
    with st.container(key="overview_wire"):
        st.markdown('<div class="monitor-heading">INTELLIGENCE WIRE <span class="wire-sub">EXPAND YOUR COVERAGE</span></div>',unsafe_allow_html=True)
        channel=st.radio("WIRE DESK",["All","World","Politics","Elections","Conflicts","Markets"],horizontal=True,label_visibility="collapsed",key="overview_wire_channel")
        selected=items if channel=="All" else [row for row in items if row["category"]==channel]
        lead_keys={report_key(row) for group in group_reporting(monitor_reports(items,(st.session_state.get("world_layer") or "All")))[:5] for row in group}
        groups=[group for group in group_reporting(selected) if not any(report_key(row) in lead_keys for row in group)][:8]
        if not groups:st.caption("No additional reporting in this desk and story window.")
        for index,group in enumerate(groups):
            item=group[0]
            with st.container(border=False):
                content,brief,source=st.columns([8,1,1])
                with content:
                    st.markdown('<div class="wire-row"><span class="wire-index">'+f'{index+1:02d}'+'</span><div><span class="tag">'+escape(item['category'].upper())+'</span><div class="wire-headline">'+escape(item['title'])+'</div><span class="wire-meta">'+escape(item['source']+' · '+timestamp(item['published']))+'</span></div></div>',unsafe_allow_html=True)
                if brief.button("BRIEF ↗",key="wire_brief_"+str(index),use_container_width=True):story_dialog(item)
                source.link_button("SOURCE ↗",item['url'],use_container_width=True)
    with st.expander("FEED STATISTICS & HEALTH",expanded=False):
        health=st.session_state.get("feed_health",[])
        st.caption(f"{len(items)} retrieved articles in your filters · {sum(bool(r['Available']) for r in health)} / {len(health)} checked feeds available")
        feed_health_panel()
        st.caption("Search and story-window filters apply to news only. Market and calendar panels use their own source dates.")



def filter_reports(rows):
    cutoff=datetime.now(UTC)-timedelta(hours=age)
    filtered=[r for r in rows if r.get("published") and datetime.fromisoformat(r["published"])>=cutoff
        and (not search.strip() or search.casefold() in (r["title"]+" "+r.get("summary","")).casefold())]
    return scope_reports(filtered)


def report_context(item):
    title=item["title"].casefold()
    if re.match(r"^(opinion|editorial)\s*[:|\-]",title):return "Opinion · labelled in headline"
    if re.match(r"^analysis\s*[:|\-]",title):return "Analysis · labelled in headline"
    host=urlparse(item["url"]).hostname or ""
    if host.endswith((".gov",".gov.uk",".gov.mt",".gov.br",".europa.eu")):
        return "Official-domain publication · statement remains attributed"
    return "Publisher reporting · claims remain attributed"



















CRYPTO_DEFAULTS={"Bitcoin":"BTC","Ethereum":"ETH","Solana":"SOL","XRP":"XRP"}
CRYPTO_PRESETS={**CRYPTO_DEFAULTS,"Cardano":"ADA","Dogecoin":"DOGE","BNB":"BNB","Chainlink":"LINK","Avalanche":"AVAX","Litecoin":"LTC"}


@st.cache_data(ttl=300,show_spinner=False,max_entries=100)
def crypto_history(symbol,period):
    try:
        settings={"1D":("1d","15m",None),"1W":("1mo","1h",7),"1M":("1mo","1d",None),"1Y":("1y","1d",None)}
        window,interval,days=settings[period]
        ticker=yf.Ticker(symbol)
        data=ticker.history(period=window,interval=interval,auto_adjust=False,timeout=12)
        if data.empty:return None
        frame=data.dropna(subset=["Close"]).reset_index()
        frame.rename(columns={"Datetime":"Date"},inplace=True)
        frame=frame[[c for c in ["Date","Open","High","Low","Close"] if c in frame]]
        if days:
            cutoff=pd.Timestamp.now(tz="UTC")-pd.Timedelta(days=days)
            frame=frame[pd.to_datetime(frame["Date"],utc=True)>=cutoff].copy()
        frame.attrs["fetched_at"]=datetime.now(UTC).isoformat()
        return frame if not frame.empty else None
    except Exception:return None


@st.cache_data(ttl=900,show_spinner=False)
def crypto_global(currency):
    try:
        r=requests.get("https://api.coingecko.com/api/v3/global",headers=HEADERS,timeout=10);r.raise_for_status()
        data=r.json()["data"];key=currency.casefold()
        return dict(cap=float(data["total_market_cap"][key]),volume=float(data["total_volume"][key]),dominance=float(data["market_cap_percentage"]["btc"]),updated=data.get("updated_at")),None
    except Exception:return None,"Global crypto statistics unavailable or rate-limited on this check."


@st.dialog("CRYPTO CHART",width="large")
def crypto_dialog(name,symbol,currency,frame,period):
    st.subheader(name.upper()+" / "+currency)
    fig=price_figure(frame,currency)
    if period=="1D":fig.update_xaxes(tickformat="%H:%M");fig.update_traces(hovertemplate="%{x|%d %b %H:%M}<br>%{y:,.4f} "+currency+"<extra></extra>",selector=dict(type="scatter"))
    st.plotly_chart(fig,use_container_width=True,key="crypto_detail_"+symbol)
    st.caption("Yahoo Finance · "+period+" · latest observation "+str(frame["Date"].iloc[-1])+" · prices may be delayed")
    st.link_button("PRICE SOURCE ↗","https://finance.yahoo.com/quote/"+quote(symbol,safe="")+"/")


def crypto_page(items):
    st.subheader("CRYPTO / MARKET MONITOR")
    currency_col,period_col=st.columns([1,3])
    currency=currency_col.selectbox("Currency",["EUR","USD"],key="crypto_currency",label_visibility="collapsed")
    period=period_col.radio("Chart range",["1D","1W","1M","1Y"],horizontal=True,index=2,key="crypto_period",label_visibility="collapsed")
    summary,error=crypto_global(currency)
    if summary:
        with st.container(key="overview_kpis"):
            cap,volume,dominance=st.columns(3)
            cap.metric("TOTAL MARKET CAP",f'{summary["cap"]/1e12:,.2f}T {currency}')
            volume.metric("24H TRADING VOLUME",f'{summary["volume"]/1e9:,.2f}B {currency}')
            dominance.metric("BITCOIN DOMINANCE",f'{summary["dominance"]:.1f}%')
        stamp=datetime.fromtimestamp(summary["updated"],UTC).strftime("%d %b %H:%M UTC") if summary.get("updated") else "Timestamp unavailable"
        st.caption("CoinGecko aggregate statistics · "+stamp+" · cached up to 15 minutes")
    else:st.caption(error)
    st.link_button("GLOBAL DATA / COINGECKO ↗","https://www.coingecko.com/en/global-charts")
    st.session_state.setdefault("crypto_added",{})
    with st.form("crypto_search_form",border=False):
        field,button=st.columns([5,1]);query=field.text_input("Find cryptocurrency",placeholder="Search cryptocurrency name or ticker…",label_visibility="collapsed")
        submitted=button.form_submit_button("SEARCH",use_container_width=True)
    if submitted:
        matches,error=company_search(query.strip()) if query.strip() else ([],None)
        st.session_state.crypto_results=[r for r in matches if r["kind"]=="CRYPTOCURRENCY" and r["symbol"].endswith(("-USD","-EUR"))]
        if error:st.caption(error)
    if st.session_state.get("crypto_results"):
        match=st.selectbox("Search results",st.session_state.crypto_results,format_func=lambda r:r["name"]+" · "+r["symbol"],key="crypto_search_result")
        if st.button("ADD TO CRYPTO WATCHLIST",key="crypto_add"):
            base=match["symbol"].rsplit("-",1)[0];label=match["name"].removesuffix(" USD").removesuffix(" EUR")
            st.session_state.crypto_added[label]=base
            current=st.session_state.get("crypto_choices",st.session_state.get("crypto_selection",list(CRYPTO_DEFAULTS)))
            st.session_state.crypto_choices=list(dict.fromkeys(current+[label]))
    elif submitted:st.caption("No matching supported cryptocurrency listings returned.")
    registry={**CRYPTO_PRESETS,**st.session_state.crypto_added}
    with st.expander("EDIT CRYPTO WATCHLIST"):
        names=st.multiselect("Coins",list(registry),default=st.session_state.get("crypto_selection",list(CRYPTO_DEFAULTS)),key="crypto_choices")
    st.session_state.crypto_selection=list(names)
    unique_names=[];seen_symbols=set()
    for name in names:
        if registry[name] not in seen_symbols:
            unique_names.append(name);seen_symbols.add(registry[name])
    names=unique_names
    symbols=[registry[name]+"-"+currency for name in names]
    with ThreadPoolExecutor(max_workers=4) as pool:frames=list(pool.map(lambda symbol:crypto_history(symbol,period),symbols))
    for offset in range(0,len(names),4):
        for col,name,symbol,frame in zip(st.columns(4),names[offset:offset+4],symbols[offset:offset+4],frames[offset:offset+4]):
            with col,st.container(border=True):
                if frame is None or frame.empty:
                    st.metric(name,"Unavailable");st.caption(symbol+" · no substitute quote shown");continue
                first,last=float(frame["Close"].iloc[0]),float(frame["Close"].iloc[-1])
                change=(last/first-1)*100 if first else None
                st.metric(name,display_price(last,currency),f"{change:+.2f}% / {period}" if change is not None else None)
                fig=price_figure(frame,currency,compact=True);fig.update_layout(height=135)
                if period=="1D":fig.update_xaxes(tickformat="%H:%M")
                if period in ("1D","1W"):
                    fig.update_traces(hovertemplate="%{x|%d %b %H:%M}<br>%{y:,.4f} "+currency+"<extra></extra>",selector=dict(type="scatter"))
                st.plotly_chart(fig,use_container_width=True,key="crypto_card_"+symbol,config={"displayModeBar":False})
                st.caption("Observation "+pd.Timestamp(frame["Date"].iloc[-1]).strftime("%d %b %H:%M %Z"))
                if st.button("EXPAND ↗",key="crypto_expand_"+symbol,use_container_width=True):crypto_dialog(name,symbol,currency,frame,period)
    st.caption("Yahoo Finance · prices may be delayed · changes compare first/last observations in the selected range; 1D is the provider’s current day, not a rolling 24h return")
    st.subheader("CRYPTO / REGULATION & DEVELOPMENTS")
    focus=st.radio("CRYPTO NEWS FOCUS",["All","Regulation","Exchange incidents","Institutions"],horizontal=True,key="crypto_news_focus")
    filters={"Regulation":r"regulat|law|court|sec\b|legislat|ban\b", "Exchange incidents":r"exchange|hack|breach|outage|fraud|stolen", "Institutions":r"bank|fund|etf\b|institution|treasur|corporat"}
    reports=items if focus=="All" else [r for r in items if re.search(filters[focus],r["title"]+" "+r.get("summary",""),re.I)]
    grouped_news(reports,"crypto_news",12)


def grouped_news(rows,scope,limit=12):
    groups=group_reporting(rows)
    if not groups:st.info("No matching reports in the selected story window.")
    for offset in range(0,min(limit,len(groups)),3):
        for index,(col,group) in enumerate(zip(st.columns(3),groups[offset:offset+3]),start=offset):
            item=group[0]
            with col,st.container(border=True):
                st.markdown(f'<div class="sport-headline">{escape(item["title"])}</div>',unsafe_allow_html=True)
                st.caption(item["source"]+" · "+timestamp(item["published"]))
                st.caption(report_context(item))
                if item.get("summary"):st.write(short_preview(item["summary"],45))
                if st.button("OPEN BRIEF",key=f"group_{scope}_{index}",use_container_width=True):story_dialog(item)
                st.link_button("SOURCE ↗",item["url"])
                related_reports(group,scope=scope+str(index))





def is_major_development(item):
    text=clean(item["title"]+" "+item.get("summary","")).casefold()
    if item.get("category")=="Sports":return True
    if re.match(r"^(?:opinion|editorial|commentary)\s*[:|\-]",item["title"],re.I):return False
    if re.search(r"\b(?:horoscope|celebrity gossip|red carpet|recipe|beauty tips|lottery numbers)\b",text):return False
    major=r"\b(?:supreme court|constitutional court|parliament|congress|central bank|interest rates?|inflation|gross domestic product|gdp|federal budget|national budget|national debt|trade (?:deal|war|agreement|tariffs?)|tariffs?|sanctions?|treaty|diplomatic|diplomacy|nuclear|military|invasion|airstrikes?|missiles?|ceasefire|armed conflict|war crimes|humanitarian|refugees?|earthquake|tsunami|hurricane|mass shooting|nationwide|national strike|supply chain|oil prices?|gas prices?|energy crisis|power grid|pandemic|public health emergency|bank failure|financial crisis|stock markets?|antitrust|bitcoin|ethereum|crypto(?:currency)?)\b"
    if re.search(major,text):return True
    election=bool(re.search(r"\b(?:elections?|voting|ballots?|polling|runoff|run-off)\b",text))
    local=bool(re.search(r"\b(?:municipal|mayoral|city council|county|by-election|by election|local election|regional election|state assembly)\b",text))
    if election and not local:return True
    policy=r"\b(?:president|prime minister|government|cabinet|minister)\b.{0,70}\b(?:signs?|approves?|approved|announces?|announced|resigns?|resigned|appoints?|appointed|legislation|reforms?|budget|peace|trade)\b"
    if re.search(policy,text):return True
    companies=r"\b(?:nvidia|microsoft|apple|amazon|alphabet|google|meta|tesla)\b"
    action=r"\b(?:earnings|revenue|profits?|layoffs|merger|acquisition|regulat|antitrust|launches|unveils)\b"
    return bool(re.search(companies,text) and re.search(action,text))


def scope_reports(rows,mode=None):
    mode=mode or st.session_state.get("news_scope","Major developments")
    return list(rows) if mode=="All reporting" else [r for r in rows if is_major_development(r)]


ECONOMIC_SOURCES={
    "BLS":("https://www.bls.gov/schedule/news_release/bls.ics","https://www.bls.gov/schedule/","United States"),
    "BEA":("https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics","https://www.bea.gov/news/schedule","United States"),
    "Federal Reserve":("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm","https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm","United States"),
    "ECB":("https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html","https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html","Euro area"),
}


def economic_category(title):
    text=title.casefold()
    if re.search(r"consumer price|producer price|personal income|personal consumption",text):return "Inflation & spending"
    if re.search(r"employment situation|job openings|labor turnover|employment cost|productivity",text):return "Jobs & wages"
    if re.search(r"gross domestic product|international trade|international transactions",text):return "Growth & trade"
    if re.search(r"fomc|monetary policy",text):return "Central banks"
    return None


def economic_event(title,day,publisher,source,region,when=None,time_note="Time not published"):
    return dict(Event=clean(title),Date=day,Region=region,Category=economic_category(title),Publisher=publisher,Source=source,WhenUTC=when,TimeNote=time_note)


def parse_release_ics(text,publisher,source,region):
    # Unfold continuation lines before parsing; retain explicit source time zones.
    text=re.sub(r"\r?\n[ \t]","",text)
    rows=[]
    aliases={"US-Eastern":"America/New_York","Eastern Standard Time":"America/New_York"}
    for block in re.findall(r"BEGIN:VEVENT\s*(.*?)END:VEVENT",text,re.S):
        fields={}
        for line in block.splitlines():
            if ":" in line:
                key,value=line.split(":",1);fields[key]=value.strip()
        summary=next((v for k,v in fields.items() if k.split(";")[0]=="SUMMARY"),"")
        title=summary.replace(r"\,",",").replace(r"\;",";").replace(r"\n"," ")
        if not economic_category(title):continue
        start=next(((k,v) for k,v in fields.items() if k.split(";")[0]=="DTSTART"),None)
        if not start:continue
        key,value=start;when=None;note="Time not published"
        try:
            date=datetime.strptime(value[:8],"%Y%m%d").date()
            if "T" in value:
                local=datetime.strptime(value.rstrip("Z"),"%Y%m%dT%H%M%S")
                zone_match=re.search(r"TZID=([^;:]+)",key)
                zone="UTC" if value.endswith("Z") else aliases.get(zone_match.group(1),zone_match.group(1)) if zone_match else None
                if zone:
                    aware=local.replace(tzinfo=ZoneInfo(zone));when=aware.astimezone(UTC).isoformat();note=zone
                else:note=local.strftime("%H:%M")+" · source time zone unspecified"
            url=fields.get("URL",source)
            rows.append(economic_event(title,date.isoformat(),publisher,safe_url(url) or source,region,when,note))
        except (ValueError,KeyError):continue
    return rows


def parse_policy_calendar(html,publisher,source,region):
    rows=[]
    if publisher=="ECB":
        for raw_date,raw_title in re.findall(r"<dt\b[^>]*>(.*?)</dt>\s*<dd\b[^>]*>(.*?)</dd>",html,re.S|re.I):
            title=clean(raw_title)
            if "monetary policy meeting" not in title.casefold() or "non-monetary" in title.casefold() or "day 2" not in title.casefold():continue
            try:day=datetime.strptime(clean(raw_date),"%d/%m/%Y").date().isoformat()
            except ValueError:continue
            rows.append(economic_event("ECB monetary policy meeting / press conference",day,publisher,source,region))
    else:
        sections=list(re.finditer(r"(20\d{2}) FOMC Meetings",html))
        for i,match in enumerate(sections):
            chunk=html[match.end():sections[i+1].start() if i+1<len(sections) else len(html)]
            pattern=r'class=["\'][^"\']*fomc-meeting__month[^"\']*["\'][^>]*>(.*?)</div>\s*<div[^>]*class=["\'][^"\']*fomc-meeting__date[^"\']*["\'][^>]*>(.*?)</div>'
            for raw_month,raw_days in re.findall(pattern,chunk,re.S|re.I):
                month=clean(raw_month).split("/")[-1].strip();days=re.findall(r"\d+",clean(raw_days))
                if not days:continue
                for fmt in ("%B %d %Y","%b %d %Y"):
                    try:day=datetime.strptime(month+" "+days[-1]+" "+match.group(1),fmt).date().isoformat();break
                    except ValueError:day=None
                if day:rows.append(economic_event("FOMC meeting / final day",day,publisher,source,region))
    return rows


@st.cache_data(ttl=21600,show_spinner=False)
def economic_calendar_source(publisher):
    url,source,region=ECONOMIC_SOURCES[publisher];checked=datetime.now(UTC).isoformat()
    try:
        response=requests.get(url,headers=HEADERS,timeout=15);response.raise_for_status()
        rows=parse_release_ics(response.text,publisher,source,region) if publisher in ("BLS","BEA") else parse_policy_calendar(response.text,publisher,source,region)
        if not rows:raise ValueError("No supported events parsed")
        return rows,dict(Publisher=publisher,Status="Available",Checked=checked,Events=len(rows),Source=source)
    except Exception:
        return [],dict(Publisher=publisher,Status="Unavailable / no supported events",Checked=checked,Events=0,Source=source)


def economic_calendar_page():
    st.subheader("ECONOMIC CALENDAR")
    st.caption("Selected official US releases and US/euro-area monetary policy meetings · dates can change · forecasts and actual release values are not connected")
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(economic_calendar_source,ECONOMIC_SOURCES))
    rows=[];statuses=[];seen=set()
    for events,status in results:
        statuses.append(status)
        for event in events:
            key=(event["Publisher"],event["Event"],event["Date"],event["WhenUTC"])
            if key not in seen:seen.add(key);rows.append(event)
    region_col,category_col,time_col=st.columns([1,1.5,1])
    region=region_col.selectbox("Region",["All","United States","Euro area"],key="econ_region")
    category=category_col.selectbox("Release type",["All","Inflation & spending","Jobs & wages","Growth & trade","Central banks"],key="econ_category")
    zone=time_col.selectbox("Display time",["Malta","UTC"],key="econ_zone")
    today=datetime.now(LOCAL).date()
    dates=st.date_input("Date range",value=(today,today+timedelta(days=30)),key="econ_dates")
    if not isinstance(dates,(list,tuple)) or len(dates)!=2:
        st.info("Select both a start and end date.");return
    start,end=dates
    display=[];upcoming=[]
    for row in rows:
        when=datetime.fromisoformat(row["WhenUTC"]).astimezone(LOCAL if zone=="Malta" else UTC) if row["WhenUTC"] else None
        day=when.date() if when else datetime.fromisoformat(row["Date"]).date()
        if not start<=day<=end or (region!="All" and row["Region"]!=region) or (category!="All" and row["Category"]!=category):continue
        record={"Date":day.isoformat(),"Time":when.strftime("%H:%M %Z") if when else row["TimeNote"],"Event":row["Event"],"Region":row["Region"],"Type":row["Category"],"Publisher":row["Publisher"],"Source":row["Source"]}
        display.append(record)
        if (when and when>=datetime.now(UTC)) or (not when and day>=today):upcoming.append(record)
    display.sort(key=lambda r:(r["Date"],r["Time"]))
    if display:
        upcoming.sort(key=lambda r:(r["Date"],r["Time"]))
        if upcoming:st.caption("NEXT IN RANGE · "+upcoming[0]["Date"]+" · "+upcoming[0]["Time"]+" · "+upcoming[0]["Event"])
        frame=pd.DataFrame(display)
        st.dataframe(frame,hide_index=True,use_container_width=True,column_config={"Source":st.column_config.LinkColumn("Official source ↗")},height=min(540,40+35*len(frame)))
        st.download_button("DOWNLOAD FILTERED CALENDAR",frame.to_csv(index=False).encode("utf-8"),"economic_calendar.csv","text/csv")
    else:st.info("No supported releases returned for these dates and filters. Check source coverage below.")
    failed=sum(status["Status"]!="Available" for status in statuses)
    if failed:st.caption(f"{failed} official source(s) unavailable; coverage is partial.")
    with st.expander("SOURCES & COVERAGE"):
        st.dataframe(pd.DataFrame(statuses),hide_index=True,use_container_width=True,column_config={"Source":st.column_config.LinkColumn("Official calendar")})
        st.caption("BLS: selected inflation, employment and wage releases. BEA: GDP, spending/income and international trade releases. Fed/ECB: policy meeting final days. Meeting calendars without explicit release times show time not published. All calendars are cached up to 6 hours; use Refresh page data to recheck.")


def refresh_page_data(page, country_open=False):
    if page=="Overview" and country_open:
        country_news.clear()
        elections_calendar.clear()
        feed_snapshot.clear()
        return
    if page in ("Overview","World","Politics","Conflicts","Elections","Sports","US Elections","Sources","Crypto"):
        feed_snapshot.clear()
    if page in ("Overview","Markets","Commodities"):
        market_data.clear()
    if page in ("Overview","Elections"):
        elections_calendar.clear()
    if page=="Markets":
        company_search.clear()
    if page=="Economic Calendar":
        economic_calendar_source.clear()
    if page=="Crypto":
        crypto_history.clear()
        crypto_global.clear()


# Apply the new defaults once per session, then honour subsequent user changes.
if not st.session_state.get("grams_default_20261022_05"):
    st.session_state.metal_weight="Grams"
    st.session_state.grams_default_20261022_05=True

if not st.session_state.get("eur_defaults_20261022_04"):
    for currency_key in ("market_currency","commodity_currency","crypto_currency"):
        st.session_state[currency_key]="EUR"
    st.session_state.eur_defaults_20261022_04=True


with st.sidebar:
    st.markdown("## ◈ CONTROL PANEL")
    st.caption("REVISION 2026.10.22-14")
    section = st.radio("CHANNEL", ["Overview", "World", "Politics", "Sports", "Conflicts", "Elections", "US Elections", "Commodities", "Markets", "Crypto", "Economic Calendar", "Sources"],key="channel")
    news_scope=st.selectbox("NEWS COVERAGE",["Major developments","All reporting"],key="news_scope",help="Keyword-based filter for policy, elections, conflicts and major economic developments. Sports keeps its own coverage. Choose All reporting for broader coverage.")
    search = st.text_input("SEARCH FEED", placeholder="Country, team, company…")
    age = st.selectbox("STORY WINDOW", [24, 48, 168], index=1, format_func=lambda n: f"Last {n} hours")
    auto = st.toggle("Automatic refresh", value=True, help="News: 3 minutes · crypto: 5 minutes · market pages: 10 minutes · calendar: 6-hour cache")
    if st.button("REFRESH PAGE DATA", use_container_width=True):
        refresh_page_data(section,bool(st.session_state.get("monitor_country")))


if section == "Overview":
    st.markdown('<style>[data-testid="stMainBlockContainer"],.block-container{padding-top:2.8rem!important}[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{gap:.5rem!important}.ticker-strip{margin-top:0}.ticker-cell{padding:5px 10px}.ticker-value{font-size:14px}.ticker-bottom svg{height:16px;width:50px}.ops-masthead{padding:5px 0 9px}.ops-eyebrow{font:10px/1.5 monospace;letter-spacing:2px;color:#40e0d0;margin-bottom:7px}.overview-title{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px 28px;line-height:1.25;margin:0 0 7px}.overview-title span{margin-left:0;line-height:1.5}.ops-strip{padding-top:3px}.ops-strip{margin-bottom:2px}.st-key-overview_pulse_tight [data-testid="stVerticalBlock"],.st-key-explore_desks{gap:3px!important}.st-key-overview_command{padding-top:8px}.st-key-overview_pulse_tight [data-testid="stCaptionContainer"]{font-size:10px!important}</style>',unsafe_allow_html=True)
    st.markdown('<header class="ops-masthead"><div class="ops-eyebrow">GLOBAL OPERATIONS / OPEN-SOURCE INTELLIGENCE</div><div class="overview-title">INTELLIGENCE HUB <span>WORLD / POLICY / CONFLICT / ECONOMY</span></div></header>',unsafe_allow_html=True)
else:
    st.markdown('<div class="mini-brand">◈ INTELLIGENCE HUB</div>', unsafe_allow_html=True)


refresh_interval = "3600s" if section=="Economic Calendar" else "600s" if section in ("Markets","Commodities") else "300s" if section=="Crypto" else "180s"


@st.fragment(run_every=refresh_interval if auto else None)
def dashboard():
    if section=="Overview" and st.session_state.get("monitor_country"):
        country_monitor(st.session_state.monitor_country)
        return
    channels=required_news_channels(section)
    if channels:
        with st.spinner("Checking source feeds…"):
            all_items, errors = news_data(channels)
    else:
        all_items, errors = [], []
    cutoff = datetime.now(UTC) - timedelta(hours=age)
    items = [a for a in all_items if a["published"] and datetime.fromisoformat(a["published"]) >= cutoff]
    if search.strip():
        items = [a for a in items if search.casefold() in (a["title"] + " " + a["summary"]).casefold()]
    items=scope_reports(items)
    if section == "Economic Calendar":
        economic_calendar_page()
    elif section == "Markets":
        with st.container(key="markets_compact_page"):
            markets_page()
    elif section == "Commodities":
        st.subheader("COMMODITIES")
        with st.container(key="commodity_controls"):
            money, weight, timeframe, assets_control = st.columns([1, 1.25, 2, 1])
            currency = money.selectbox("Currency", ["EUR", "USD"], label_visibility="collapsed", key="commodity_currency", help="Display currency")
            metal_weight = weight.selectbox("Precious-metal weight", ["Grams", "Troy oz"], label_visibility="collapsed", key="metal_weight", help="Weight unit for precious metals")
            period = timeframe.radio("Commodity chart range", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, label_visibility="collapsed", key="compact_commodity_period")
            with assets_control.popover("ASSETS", use_container_width=True):
                choices = st.multiselect("Choose commodities", list(ASSETS)[:11], default=list(ASSETS)[:6], key="commodity_asset_selection")
        market_panel(choices, commodity_currency=currency, metal_weight=metal_weight, selected_period=period)
        with st.expander("Source & units", expanded=False):
            st.caption("Yahoo Finance futures, not spot or dealer prices. Prices may be delayed. Weight applies to precious metals; other commodities keep their trading units.")
            if currency == "EUR":
                st.caption("EUR uses historical daily EUR/USD closes. Converted candles are estimates; unmatched exchange-rate observations are omitted.")
                st.link_button("EUR/USD SOURCE ↗", "https://finance.yahoo.com/quote/EURUSD%3DX/")
    elif section == "Crypto":
        with st.container(key="markets_compact_page"):
            crypto_page(items)
    elif section == "Sports":
        with st.container(key="sports_desk"):
            sports_panel()
    elif section == "US Elections":
        us_elections_panel()
    elif section == "Elections":
        st.subheader("WORLD ELECTION WATCH")
        st.caption("Major national presidential and parliamentary/congressional elections only · previous 7 days / next 180 days. Regional, local, by-elections and primaries excluded. Unclear scope is omitted; verify dates at source.")
        rows, error = elections_calendar()
        if error:
            st.warning(error)
        elif rows:
            display_rows=[]
            for row in rows:
                days=(datetime.fromisoformat(row["Date"]).date()-datetime.now(UTC).date()).days
                display_rows.append(dict(row,**{"Days to vote":days if days>=0 else "Held"}))
            st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True, column_config={"Source": st.column_config.LinkColumn("Calendar source")})
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
        feed_health_panel()
        for error in errors:
            st.warning(error)
        st.caption("Fox News section feeds are direct RSS. CNN/Reuters and topic-specific publisher feeds use Google News indexing, not a licensed publisher newswire. Publisher links can redirect; full previews may be limited.")
        st.write("Markets: Yahoo Finance via yfinance; 10-minute cache; daily observations. Election calendar: Wikidata; 6-hour cache. Polling: original-source datasets only; none connected.")
        st.caption("Google News election links may open its publisher redirect. Conflict channels include regional reporting and do not independently confirm military events. Undated articles are excluded from time-filtered feeds.")
    elif section == "Overview":
        overview_panel(items, errors, change_items=all_items)
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
