"""Local-only visual system: no web fonts, external stylesheets or scripts."""
CSS = '''<style>
:root{--ink:#182f2b;--muted:#53665f;--line:#d8dfd8;--paper:#f7f8f3;--green:#17624b}
html,body,[data-testid="stApp"]{font-family:"Segoe UI",Arial,sans-serif;color:var(--ink)}
[data-testid="stAppViewContainer"]{background:var(--paper)}
[data-testid="stHeader"]{background:rgba(247,248,243,.96)}
[data-testid="stMainBlockContainer"]{max-width:1240px;padding-top:2.2rem;padding-bottom:4rem}
[data-testid="stSidebar"]{background:#edf1eb;border-right:1px solid var(--line)}
[data-testid="stSidebar"] h2{font-size:1.15rem!important;letter-spacing:-.02em}
h1,h2,h3{color:var(--ink);font-weight:650!important;letter-spacing:-.035em}
h1{font-size:clamp(2.3rem,4vw,3.4rem)!important;line-height:1.1!important}h2{font-size:2rem!important}h3{font-size:1.35rem!important}
p,li{line-height:1.6}[data-testid="stCaptionContainer"]{color:var(--muted);font-size:.9rem}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px}
[data-testid="stMetricValue"]{font-size:1.8rem;font-variant-numeric:tabular-nums;letter-spacing:-.04em}
[data-testid="stMetricLabel"]{color:var(--muted);font-size:.8rem}
[data-testid="stExpander"]{background:#fff;border-radius:9px;border-color:var(--line)}
button{min-height:46px!important;border-radius:7px!important;font-weight:600!important}
button:focus-visible,a:focus-visible{outline:3px solid #bd7b1a!important;outline-offset:3px}
[data-baseweb="tab-list"]{gap:8px;padding:8px;background:#edf1eb;border:1px solid var(--line);border-radius:10px;margin-bottom:24px;overflow-x:auto}
[data-baseweb="tab"]{padding:14px 22px!important;background:transparent;white-space:nowrap;min-height:54px!important}
[data-baseweb="tab"] p{font-size:18px!important;font-weight:650!important}
[data-baseweb="tab"][aria-selected="true"]{background:var(--green)!important;color:white!important}
[data-baseweb="tab"][aria-selected="true"] p{color:white!important}
[data-baseweb="tab-highlight"]{background:var(--green)}
.ml-masthead{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:24px;gap:16px}
.ml-wordmark{font-size:36px;font-weight:750;letter-spacing:-1px}.ml-wordmark span{color:var(--green)}
.ml-edition{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);text-align:right}
.ml-kicker{font-size:12px;text-transform:uppercase;letter-spacing:1.7px;color:var(--green);font-weight:750;margin:0 0 8px}
.ml-intro{font-size:19px;color:var(--muted);max-width:670px;margin-bottom:22px}
.ml-empty{padding:32px;border:1px solid var(--line);border-radius:12px;background:white;margin:12px 0}.ml-empty h2{font-size:1.8rem!important;margin:0 0 12px}.ml-empty p{max-width:580px;color:var(--muted)}
.ml-note{padding:20px 22px;border-left:3px solid var(--green);background:#eaf1eb;border-radius:0 9px 9px 0;margin:8px 0 16px}
.ml-note h3{font-size:11px!important;letter-spacing:1.4px;text-transform:uppercase;margin:0 0 10px}.ml-note p{font-size:16px;margin:0}
[data-testid="stButton"] p,[data-testid="stDownloadButton"] p{font-size:16px!important}
[data-testid="stWidgetLabel"] p{font-size:15px;font-weight:600}
.ml-path{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 24px;color:var(--muted);font-size:15px}.ml-path span{padding:8px 14px;border:1px solid var(--line);border-radius:6px;background:white}.ml-path b{color:var(--green);margin-right:8px}
@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding:1rem}h1{font-size:2rem!important}.ml-edition{font-size:10px}.ml-masthead{margin-bottom:16px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>'''


def masthead():
    return '<div class="ml-masthead"><div class="ml-wordmark">Match<span>Lens</span></div><div class="ml-edition">Recovery outcome studio<br>Northbridge × Riverside · Synthetic replay</div></div>'


def context_note(text, language="English"):
    from html import escape
    title = 'Por qué importa' if language == 'Español' else 'Why this matters'
    return '<div class="ml-note"><h3>'+title+'</h3><p>'+escape(text)+'</p></div>'
