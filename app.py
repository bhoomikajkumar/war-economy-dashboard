"""
Economic Impact of War - Interactive Dashboard (animated, multi-chart version)
Run with:  streamlit run app.py
Put these 3 files in the SAME folder: app.py, cleaned_data.csv, recovery_rates.csv
Requires: pandas numpy plotly streamlit
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Economic Impact of War", page_icon="📉", layout="wide")

NAVY = "#1E2761"
FONT = "Poppins, Segoe UI, Arial, sans-serif"
ORDER = ["Iraq", "Kuwait", "Rwanda", "Ukraine"]
ISO3 = {"Iraq": "IRQ", "Rwanda": "RWA", "Kuwait": "KWT", "Ukraine": "UKR"}
COLORS = {"Iraq": "#d62728", "Kuwait": "#2ca02c", "Rwanda": "#1f77b4", "Ukraine": "#ff7f0e"}
PERIOD_COLORS = {"pre-war": "#5B6B9E", "during-war": "#d62728", "post-war": "#2ca02c"}
IDX_LABEL = "GDP index (100 = last pre-war year)"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
h1, h2, h3, h4, .stTabs [data-baseweb="tab"] {font-family: 'Poppins', 'Segoe UI', sans-serif !important;}
h3 {border-left: 5px solid #F96167; padding-left: 12px !important;}
h4 {color: #1E2761;}

/* ---------- animated hero ---------- */
.hero {position: relative; overflow: hidden; padding: 32px 38px; border-radius: 20px; margin-bottom: 18px;
       background: linear-gradient(120deg, #1E2761, #3A4A9F, #6C3FC5, #3A4A9F, #1E2761);
       background-size: 300% 300%; animation: flow 14s ease infinite;
       box-shadow: 0 10px 30px rgba(30,39,97,0.28);}
.hero::before {content: ""; position: absolute; width: 240px; height: 240px; right: -60px; top: -90px;
               border-radius: 50%; background: rgba(255,255,255,0.09); animation: float 7s ease-in-out infinite;}
.hero::after {content: ""; position: absolute; width: 150px; height: 150px; right: 190px; bottom: -70px;
              border-radius: 50%; background: rgba(249,97,103,0.28); animation: float 9s ease-in-out infinite reverse;}
.hero h1 {color: #FFFFFF; margin: 0; padding: 0; font-size: 2.4rem; font-weight: 800;
          animation: slidein 0.9s ease both; position: relative; z-index: 2;}
.hero p {color: #CADCFC; margin: 8px 0 14px 0; font-size: 1.05rem; position: relative; z-index: 2;
         animation: slidein 1.2s ease both;}
.chips {position: relative; z-index: 2; animation: slidein 1.5s ease both;}
.chips span {display: inline-block; background: rgba(255,255,255,0.16); color: #FFFFFF; font-size: 0.82rem;
             padding: 5px 14px; border-radius: 999px; margin-right: 8px; backdrop-filter: blur(4px);}
@keyframes flow {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
@keyframes float {0%, 100% {transform: translateY(0);} 50% {transform: translateY(18px);}}
@keyframes slidein {from {opacity: 0; transform: translateX(-30px);} to {opacity: 1; transform: none;}}
@keyframes fadeup {from {opacity: 0; transform: translateY(18px);} to {opacity: 1; transform: none;}}

/* ---------- tabs, charts, sidebar ---------- */
.stTabs [data-baseweb="tab"] {font-weight: 600; padding: 10px 16px;}
.stTabs [data-baseweb="tab-panel"] {animation: fadeup 0.55s ease both;}
[data-testid="stPlotlyChart"] {background: #FFFFFF; border-radius: 16px; padding: 6px 6px 0 6px;
                               box-shadow: 0 2px 14px rgba(30,39,97,0.09); transition: box-shadow 0.3s;}
[data-testid="stPlotlyChart"]:hover {box-shadow: 0 8px 26px rgba(30,39,97,0.18);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #F4F6FC 0%, #E6EAFA 100%);}

/* ---------- insight box ---------- */
.insight {background: #F4F6FC; border-left: 5px solid #F96167; padding: 14px 20px; margin-top: 14px;
          border-radius: 12px; color: #1E2761; line-height: 1.8; animation: slidein 0.8s ease both;}

/* ---------- animated progress bars ---------- */
.pbar {margin: 14px 0;}
.plabel {display: flex; justify-content: space-between; color: #1E2761; margin-bottom: 6px; font-size: 0.95rem;}
.ptrack {background: #E6EAFA; border-radius: 999px; height: 16px; overflow: hidden;}
.pfill {height: 100%; border-radius: 999px; animation: grow 1.6s cubic-bezier(.2,.8,.2,1) both;}
@keyframes grow {from {width: 0;}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def load():
    d = pd.read_csv("cleaned_data.csv")
    r = pd.read_csv("recovery_rates.csv")
    d["iso3"] = d["country"].map(ISO3)
    return d, r


df, rec = load()


def style(fig, h=450, bottom=10):
    """Common look for every chart: left title, legend on the right, no overlaps."""
    fig.update_layout(
        template="plotly_white", height=h,
        font=dict(family=FONT, size=13, color=NAVY),
        title=dict(x=0.01, xanchor="left", y=0.96, yanchor="top", font=dict(size=16, color=NAVY)),
        margin=dict(l=10, r=10, t=75, b=bottom),
        legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top",
                    bgcolor="rgba(0,0,0,0)", title_text=""),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def kpi_cards_html(recs):
    """Animated KPI cards (cards rise in, numbers count up). Rendered in an iframe."""
    css = """
    <style>
    body {margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: transparent;}
    .row {display: flex; gap: 16px; flex-wrap: wrap; padding: 6px 4px 14px 4px;}
    .kpi {flex: 1 1 190px; min-width: 170px; background: #fff; border-radius: 16px; padding: 16px 18px;
          border-top: 5px solid var(--c); box-shadow: 0 4px 16px rgba(30,39,97,0.14);
          animation: rise 0.8s ease both; transition: transform .25s, box-shadow .25s;}
    .kpi:hover {transform: translateY(-6px); box-shadow: 0 12px 26px rgba(30,39,97,0.24);}
    .name {color: var(--c); font-weight: 700; font-size: 13px; letter-spacing: .7px; text-transform: uppercase;}
    .big {font-size: 38px; font-weight: 800; color: #1E2761; line-height: 1.15; margin-top: 4px;}
    .sub {color: #5B6B9E; font-size: 13px; margin-top: 2px;}
    .badge {display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 12px;
            font-weight: 600; margin-top: 10px;}
    .ok {background: #E3F6E8; color: #1E7B3A;}
    .warn {background: #FFF1D6; color: #9A6200;}
    @keyframes rise {from {opacity: 0; transform: translateY(26px);} to {opacity: 1; transform: none;}}
    </style>
    """
    cards = []
    for i, (_, row) in enumerate(recs.iterrows()):
        c = row["country"]
        drop = 100 - row["trough_index"]
        if pd.isna(row["years_to_recover"]):
            cls, txt = "warn", f'Still recovering · {row["pct_of_loss_regained"]:.0f}% regained'
        else:
            cls, txt = "ok", f'Recovered in {int(row["years_to_recover"])} yrs'
        cards.append(
            f'<div class="kpi" style="--c:{COLORS[c]}; animation-delay:{i * 0.13:.2f}s">'
            f'<div class="name">{c}</div>'
            f'<div class="big">−<span class="count" data-to="{drop:.0f}">{drop:.0f}</span>%</div>'
            f'<div class="sub">GDP at its lowest ({int(row["trough_year"])})</div>'
            f'<span class="badge {cls}">{txt}</span></div>'
        )
    js = """
    <script>
    document.querySelectorAll('.count').forEach(function (el) {
      var to = parseFloat(el.getAttribute('data-to')), start = null, dur = 1300;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      }
      el.textContent = '0';
      requestAnimationFrame(step);
    });
    </script>
    """
    return css + '<div class="row">' + "".join(cards) + "</div>" + js


def draw_animation(data, countries):
    """Line chart that 'draws itself' year by year, with Play / Pause and a slider."""
    years = sorted(int(y) for y in data["years_since_war_start"].unique())

    def traces_upto(cutoff):
        out = []
        for c in countries:
            s = data[(data["country"] == c) & (data["years_since_war_start"] <= cutoff)]
            s = s.sort_values("years_since_war_start")
            out.append(go.Scatter(x=s["years_since_war_start"], y=s["GDP_index"], name=c,
                                  mode="lines+markers", line=dict(color=COLORS[c], width=3),
                                  marker=dict(size=7)))
        return out

    fig = go.Figure(data=traces_upto(years[0]),
                    frames=[go.Frame(data=traces_upto(y), name=str(y)) for y in years])
    ymin = max(0.0, float(data["GDP_index"].min()) - 10)
    ymax = float(data["GDP_index"].max()) * 1.08
    play = dict(frame=dict(duration=380, redraw=True), transition=dict(duration=250),
                fromcurrent=True, mode="immediate")
    pause = dict(frame=dict(duration=0, redraw=False), transition=dict(duration=0), mode="immediate")
    fig.update_layout(
        title="Recovery drawn year by year (press ▶)",
        xaxis=dict(range=[years[0] - 0.5, years[-1] + 0.5], title=""),
        yaxis=dict(range=[ymin, ymax], title=IDX_LABEL),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.2, xanchor="left", yanchor="top",
                          showactive=False,
                          buttons=[dict(label="▶ Play", method="animate", args=[None, play]),
                                   dict(label="⏸ Pause", method="animate", args=[[None], pause])])],
        sliders=[dict(active=0, x=0.16, len=0.84, y=-0.2, xanchor="left", yanchor="top",
                      currentvalue=dict(prefix="Years since war start: "),
                      steps=[dict(method="animate", label=str(y),
                                  args=[[str(y)], dict(mode="immediate", frame=dict(duration=300, redraw=True),
                                                       transition=dict(duration=200))])
                             for y in years])],
    )
    fig.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig.add_vline(x=0, line_dash="dot", line_color="grey")
    return style(fig, 560, bottom=120)


# ---------- Sidebar ----------
st.sidebar.header("🎛️ Filters")
countries = [c for c in ORDER if c in df["country"].unique()]
selected = st.sidebar.multiselect("Countries", countries, default=countries)
lo, hi = int(df["years_since_war_start"].min()), int(df["years_since_war_start"].max())
rng = st.sidebar.slider("Years since war start", lo, hi, (max(lo, -10), hi))
log_scale = st.sidebar.checkbox("Log scale (for the Overview chart)")
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About this project"):
    st.write(
        "Real GDP index built from World Bank GDP growth rates, with 100 set to the "
        "last year before each war. Recovery is modelled as 100 − A·exp(−k·t) from the "
        "trough until the index regains 100."
    )
st.sidebar.caption("Data: World Bank Open Data. War dates: UCDP / historical record.")

# ---------- Hero ----------
st.markdown(
    '<div class="hero"><h1>📉 Economic Impact of War</h1>'
    '<p>How Iraq, Kuwait, Rwanda and Ukraine’s economies fell and recovered around major conflicts</p>'
    f'<div class="chips"><span>🌍 4 conflicts</span><span>📅 {int(df["year"].min())}–{int(df["year"].max())}</span>'
    '<span>🏦 World Bank data</span><span>🐍 Python · Plotly · Streamlit</span></div></div>',
    unsafe_allow_html=True,
)

if not selected:
    st.warning("Select at least one country in the sidebar.")
    st.stop()

view = df[df["country"].isin(selected) & df["years_since_war_start"].between(*rng)]
if view.empty:
    st.info("No data for this filter. Widen the year range in the sidebar.")
    st.stop()
rec_sel = rec[rec["country"].isin(selected)].copy()

# ---------- Animated KPI cards ----------
if len(rec_sel):
    st.components.v1.html(kpi_cards_html(rec_sel), height=200)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["📈 Overview", "🎬 Animated story", "🔍 Country deep-dive", "🎨 Chart gallery",
     "⚖️ Compare all 4", "⏱️ Recovery", "🗺️ Map", "📋 Data"]
)

# =====================================================================
# Tab 1: Overview (switchable chart type)
# =====================================================================
with tab1:
    kind = st.radio("Chart type", ["Line", "Area", "Bar", "Scatter"], horizontal=True, key="overview_kind")
    lbl = {"years_since_war_start": "Years since war start", "GDP_index": IDX_LABEL, "country": ""}

    if kind == "Line":
        fig1 = px.line(view, x="years_since_war_start", y="GDP_index", color="country",
                       markers=True, color_discrete_map=COLORS, labels=lbl,
                       title="Line chart: real GDP index on one timeline")
        fig1.update_traces(line=dict(width=3))
    elif kind == "Area":
        fig1 = go.Figure()
        for c in selected:
            s = view[view["country"] == c].sort_values("years_since_war_start")
            fig1.add_trace(go.Scatter(x=s["years_since_war_start"], y=s["GDP_index"], name=c,
                                      mode="lines", fill="tozeroy", opacity=0.45,
                                      line=dict(color=COLORS[c], width=2)))
        fig1.update_layout(title="Area chart: real GDP index on one timeline",
                           xaxis_title=lbl["years_since_war_start"], yaxis_title=IDX_LABEL)
    elif kind == "Bar":
        fig1 = px.bar(view, x="years_since_war_start", y="GDP_index", color="country",
                      barmode="group", color_discrete_map=COLORS, labels=lbl,
                      title="Bar chart: real GDP index by year since war start")
    else:
        fig1 = px.scatter(view, x="years_since_war_start", y="GDP_index", color="country",
                          color_discrete_map=COLORS, labels=lbl,
                          title="Scatter chart: real GDP index, one dot per year")
        fig1.update_traces(marker=dict(size=9))

    fig1.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig1.add_vline(x=0, line_dash="dot", line_color="grey",
                   annotation_text="War starts", annotation_position="top right")
    if log_scale:
        fig1.update_yaxes(type="log")
    st.plotly_chart(style(fig1, 480), use_container_width=True)

    lines = []
    done = rec_sel.dropna(subset=["years_to_recover"])
    if not done.empty:
        fast = done.loc[done["years_to_recover"].idxmin()]
        lines.append(f'⚡ <b>Fastest recovery:</b> {fast["country"]} regained its pre-war GDP in '
                     f'{int(fast["years_to_recover"])} years.')
        if len(done) > 1:
            slow = done.loc[done["years_to_recover"].idxmax()]
            lines.append(f'🐢 <b>Slowest recovery:</b> {slow["country"]} took '
                         f'{int(slow["years_to_recover"])} years.')
    if not rec_sel.empty:
        deep = rec_sel.loc[rec_sel["trough_index"].idxmin()]
        lines.append(f'📉 <b>Deepest fall:</b> {deep["country"]}, where GDP dropped '
                     f'{100 - deep["trough_index"]:.0f}% below its pre-war level in {int(deep["trough_year"])}.')
        for _, p in rec_sel[rec_sel["years_to_recover"].isna()].iterrows():
            lines.append(f'⏳ <b>{p["country"]}</b> has not recovered yet: '
                         f'{p["pct_of_loss_regained"]:.0f}% of the loss regained so far.')
    if lines:
        st.markdown('<div class="insight">' + "<br>".join(lines) + "</div>", unsafe_allow_html=True)

# =====================================================================
# Tab 2: Animated story
# =====================================================================
with tab2:
    st.markdown("### 🎬 Watch the story unfold")
    st.caption("Press ▶ under each chart. These use the countries and year range chosen in the sidebar.")

    st.markdown("#### 1 · The recovery, drawn year by year")
    st.plotly_chart(draw_animation(view, selected), use_container_width=True)

    a1, a2 = st.columns(2)

    with a1:
        st.markdown("#### 2 · Bar race")
        race = view.sort_values("years_since_war_start")
        fb = px.bar(race, x="country", y="GDP_index", color="country", color_discrete_map=COLORS,
                    animation_frame="years_since_war_start", text_auto=".0f",
                    range_y=[0, float(view["GDP_index"].max()) * 1.12],
                    labels={"GDP_index": IDX_LABEL, "country": "",
                            "years_since_war_start": "Years since war start"},
                    title="Bar race: GDP index at each point in time")
        fb.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
        fb.update_layout(showlegend=False)
        st.plotly_chart(style(fb, 480, bottom=100), use_container_width=True)

    with a2:
        st.markdown("#### 3 · Level vs growth")
        if "GDP_growth_pct" in view.columns:
            sc = view.dropna(subset=["GDP_growth_pct"]).sort_values("years_since_war_start").copy()
            sc["size"] = 20
            fs = px.scatter(sc, x="GDP_index", y="GDP_growth_pct", color="country", size="size",
                            size_max=24, text="country", animation_frame="years_since_war_start",
                            animation_group="country", color_discrete_map=COLORS,
                            range_x=[0, float(sc["GDP_index"].max()) * 1.1],
                            range_y=[float(sc["GDP_growth_pct"].min()) - 5, float(sc["GDP_growth_pct"].max()) + 5],
                            labels={"GDP_index": IDX_LABEL, "GDP_growth_pct": "Real GDP growth (%)",
                                    "years_since_war_start": "Years since war start"},
                            title="Bubbles move as years pass")
            fs.update_traces(textposition="top center")
            fs.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            fs.update_layout(showlegend=False)
            st.plotly_chart(style(fs, 480, bottom=100), use_container_width=True)
        else:
            st.info("No growth column in the data.")

# =====================================================================
# Tab 3: Country deep-dive
# =====================================================================
with tab3:
    one = st.selectbox("Choose a country", selected)
    sub = df[df["country"] == one]
    ws, we = int(sub["war_start"].iloc[0]), int(sub["war_end"].iloc[0])
    sub = sub[sub["year"] >= ws - 10]

    show_usd = False
    if "GDP_index_usd" in sub.columns:
        show_usd = st.checkbox("Also show the USD-based index (distorted by exchange rates)")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sub["year"], y=sub["GDP_index"], mode="lines+markers",
                              name="Real GDP index",
                              line=dict(color=COLORS.get(one, NAVY), width=3)))
    if show_usd:
        fig2.add_trace(go.Scatter(x=sub["year"], y=sub["GDP_index_usd"], mode="lines",
                                  name="USD-based index", line=dict(dash="dot", color="grey")))
    fig2.add_vrect(x0=ws - 0.5, x1=we + 0.5, fillcolor="grey", opacity=0.22, line_width=0,
                   annotation_text="War years", annotation_position="top left")
    fig2.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig2.update_layout(title=f"{one}: real GDP index", xaxis_title="Year", yaxis_title=IDX_LABEL)
    st.plotly_chart(style(fig2, 430), use_container_width=True)

    if "GDP_growth_pct" in sub.columns:
        g = sub.dropna(subset=["GDP_growth_pct"])
        bar_colors = ["#d62728" if v < 0 else "#2ca02c" for v in g["GDP_growth_pct"]]
        fig2b = go.Figure(go.Bar(x=g["year"], y=g["GDP_growth_pct"], marker_color=bar_colors))
        fig2b.add_vrect(x0=ws - 0.5, x1=we + 0.5, fillcolor="grey", opacity=0.22, line_width=0)
        fig2b.update_layout(title=f"{one}: annual real GDP growth (%)",
                            xaxis_title="Year", yaxis_title="Growth %")
        st.plotly_chart(style(fig2b, 330), use_container_width=True)

# =====================================================================
# Tab 4: Chart gallery (same data, many chart types)
# =====================================================================
with tab4:
    st.markdown("### 🎨 The same story in different chart types")
    st.caption("Uses the countries and year range chosen in the sidebar.")

    g1, g2 = st.columns(2)

    with g1:
        if "Inflation_pct" in view.columns:
            inf = view.dropna(subset=["Inflation_pct"]).copy()
            inf["Inflation (%, capped at 100)"] = inf["Inflation_pct"].clip(upper=100)
            f = px.line(inf, x="year", y="Inflation (%, capped at 100)", color="country",
                        markers=True, color_discrete_map=COLORS, labels={"year": "Year", "country": ""},
                        title="Line: inflation over time")
            f.update_traces(line=dict(width=2.5))
            st.plotly_chart(style(f, 400), use_container_width=True)
        else:
            st.info("No inflation column in the data.")

    with g2:
        off = st.slider("Bar chart: years since war start", -5, 10, 2, key="off_bar")
        one_year = df[df["country"].isin(selected) & (df["years_since_war_start"] == off)]
        if one_year.empty:
            st.info("No country has data for that year. Try another value.")
        else:
            f = px.bar(one_year, x="country", y="GDP_index", color="country",
                       color_discrete_map=COLORS, text=one_year["GDP_index"].round(0),
                       labels={"GDP_index": IDX_LABEL, "country": ""},
                       title=f"Bar: GDP index at year {off:+d} (0 = war start)")
            f.update_traces(textposition="outside")
            f.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
            f.update_layout(showlegend=False)
            st.plotly_chart(style(f, 400), use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        y_lo, y_hi = int(df["year"].min()), int(df["year"].max())
        yr = st.slider("Donut chart: year", y_lo, y_hi, y_hi, key="pie_year")
        py = df[df["country"].isin(selected) & (df["year"] == yr)].copy()
        if py.empty:
            st.info("No data for that year.")
        else:
            py["GDP (USD bn)"] = py["GDP_current_USD"] / 1e9
            f = px.pie(py, names="country", values="GDP (USD bn)", hole=0.45,
                       color="country", color_discrete_map=COLORS,
                       title=f"Donut: share of combined GDP in {yr}")
            f.update_traces(textinfo="label+percent")
            st.plotly_chart(style(f, 400), use_container_width=True)

    with g4:
        f = go.Figure()
        for c in selected:
            s = view[view["country"] == c].sort_values("year")
            f.add_trace(go.Scatter(x=s["year"], y=s["GDP_current_USD"] / 1e9, name=c, mode="lines",
                                   fill="tozeroy", opacity=0.45, line=dict(color=COLORS[c], width=2)))
        f.update_layout(title="Area: size of each economy (USD bn)",
                        xaxis_title="Year", yaxis_title="GDP (USD bn)")
        st.plotly_chart(style(f, 400), use_container_width=True)

    g5, g6 = st.columns(2)

    with g5:
        if "GDP_growth_pct" in view.columns:
            sc2 = view.dropna(subset=["GDP_growth_pct"]).copy()
            sc2["size"] = sc2["GDP_growth_pct"].abs() + 1
            f = px.scatter(sc2, x="years_since_war_start", y="GDP_growth_pct", color="country",
                           size="size", size_max=22, opacity=0.7, color_discrete_map=COLORS,
                           labels={"years_since_war_start": "Years since war start",
                                   "GDP_growth_pct": "Real GDP growth (%)", "country": ""},
                           title="Bubble: yearly growth shocks")
            f.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            st.plotly_chart(style(f, 400), use_container_width=True)
        else:
            st.info("No growth column in the data.")

    with g6:
        if "GDP_growth_pct" in view.columns:
            bx = view.dropna(subset=["GDP_growth_pct"])
            f = px.box(bx, x="country", y="GDP_growth_pct", color="period",
                       color_discrete_map=PERIOD_COLORS,
                       labels={"GDP_growth_pct": "Real GDP growth (%)", "country": "", "period": ""},
                       title="Box plot: growth before, during, after war")
            f.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            st.plotly_chart(style(f, 400), use_container_width=True)

    pv = view.pivot_table(index="country", columns="years_since_war_start", values="GDP_index")
    z = pv.clip(lower=40, upper=250)
    fh = go.Figure(go.Heatmap(z=z.values, x=[int(c) for c in z.columns], y=list(z.index),
                              colorscale="RdYlGn", zmin=40, zmax=250, hoverongaps=False,
                              colorbar=dict(title="GDP index")))
    fh.update_layout(title="Heatmap: GDP index by country and year (green = strong, red = weak)",
                     xaxis_title="Years since war start")
    st.plotly_chart(style(fh, 330), use_container_width=True)

# =====================================================================
# Tab 5: Compare all four countries
# =====================================================================
with tab5:
    st.markdown("### ⚖️ All four countries side by side")
    st.caption("This tab always compares all four countries, whatever the sidebar filter says.")

    all_c = [c for c in ORDER if c in df["country"].unique() and c in rec["country"].values]
    latest = df.sort_values("year").groupby("country").tail(1).set_index("country")
    war_df = df[df["period"] == "during-war"]

    comp = rec.set_index("country").loc[all_c].copy()
    comp["GDP drop (%)"] = 100 - comp["trough_index"]
    comp["Latest index"] = latest["GDP_index"]
    comp["Latest year"] = latest["year"]
    comp["Peak war inflation (%)"] = (war_df.groupby("country")["Inflation_pct"].max()
                                      if "Inflation_pct" in df.columns else np.nan)
    comp["Avg war growth (%)"] = (war_df.groupby("country")["GDP_growth_pct"].mean()
                                  if "GDP_growth_pct" in df.columns else np.nan)

    st.markdown("#### 📊 Scorecard")
    score = comp.reset_index()[["country", "GDP drop (%)", "years_to_recover", "Latest index",
                                "Latest year", "Peak war inflation (%)", "Avg war growth (%)"]]
    score = score.rename(columns={"country": "Country", "years_to_recover": "Years to recover"})
    score = score.round(1).fillna("-")
    st.dataframe(score, hide_index=True, use_container_width=True)

    sm_data = df[df["country"].isin(all_c) & (df["years_since_war_start"] >= -10)]
    fm = px.line(sm_data, x="year", y="GDP_index", color="country", facet_col="country",
                 facet_col_wrap=2, color_discrete_map=COLORS,
                 labels={"year": "Year", "GDP_index": "GDP index"},
                 title="Four panels: each country on its own scale")
    fm.update_xaxes(matches=None, showticklabels=True)
    fm.update_yaxes(matches=None, showticklabels=True)
    fm.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fm.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.4)
    fm.update_layout(showlegend=False)
    st.plotly_chart(style(fm, 560), use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        gb = pd.concat([
            pd.DataFrame({"country": comp.index, "Point": "At trough", "GDP index": comp["trough_index"].values}),
            pd.DataFrame({"country": comp.index, "Point": "Latest year", "GDP index": comp["Latest index"].values}),
        ])
        fgb = px.bar(gb, x="country", y="GDP index", color="Point", barmode="group",
                     text=gb["GDP index"].round(0),
                     color_discrete_map={"At trough": "#d62728", "Latest year": "#2ca02c"},
                     labels={"country": ""},
                     title="Grouped bar: lowest point vs latest year")
        fgb.update_traces(textposition="outside")
        fgb.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
        st.plotly_chart(style(fgb, 420), use_container_width=True)

    with c2:
        rad = pd.DataFrame(index=comp.index)
        rad["Shock depth"] = comp["GDP drop (%)"]
        yrs = comp["years_to_recover"]
        worst = (yrs.max() if yrs.notna().any() else 0) + 2
        rad["Recovery time"] = yrs.fillna(worst)
        rad["Wartime inflation"] = comp["Peak war inflation (%)"].fillna(0).clip(upper=100)
        rad["Unrecovered loss"] = (100 - comp["Latest index"]).clip(lower=0)
        scaled = rad.div(rad.max().replace(0, np.nan)).fillna(0) * 100
        cats = list(scaled.columns)
        fr = go.Figure()
        for c in scaled.index:
            vals = scaled.loc[c].tolist()
            fr.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself",
                                         name=c, line=dict(color=COLORS[c]), opacity=0.55))
        fr.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                         title="Radar: how hard each country was hit")
        st.plotly_chart(style(fr, 420), use_container_width=True)
        st.caption("Larger area = harder hit. Each axis is scaled 0–100 against the worst country.")

    st.markdown("#### 🥊 Head to head")
    h1, h2 = st.columns(2)
    a = h1.selectbox("Country A", all_c, index=0, key="h2h_a")
    b = h2.selectbox("Country B", all_c, index=min(1, len(all_c) - 1), key="h2h_b")
    hh = df[df["country"].isin([a, b]) & (df["years_since_war_start"] >= -5)]
    fhh = px.line(hh, x="years_since_war_start", y="GDP_index", color="country", markers=True,
                  color_discrete_map=COLORS,
                  labels={"years_since_war_start": "Years since war start", "GDP_index": IDX_LABEL, "country": ""},
                  title=f"{a} vs {b}: real GDP index")
    fhh.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fhh.add_vline(x=0, line_dash="dot", line_color="grey")
    st.plotly_chart(style(fhh, 400), use_container_width=True)
    for box, name in ((h1, a), (h2, b)):
        rr = rec[rec["country"] == name]
        if not rr.empty:
            rr = rr.iloc[0]
            box.metric(f"{name}: GDP fall at trough", f"{100 - rr['trough_index']:.0f}%")
            if pd.isna(rr["years_to_recover"]):
                box.caption("Not back to its pre-war level yet.")
            else:
                box.caption(f"Back to its pre-war level in {int(rr['years_to_recover'])} years.")

# =====================================================================
# Tab 6: Recovery
# =====================================================================
with tab6:
    st.markdown("#### 🏁 Recovery progress")
    bars = ""
    for _, row in rec_sel.iterrows():
        pct = float(row["pct_of_loss_regained"]) if pd.notna(row["pct_of_loss_regained"]) else 0.0
        pct = max(0.0, min(100.0, pct))
        bars += (f'<div class="pbar"><div class="plabel"><b>{row["country"]}</b>'
                 f'<span>{pct:.0f}% of the loss regained</span></div>'
                 f'<div class="ptrack"><div class="pfill" style="width:{pct}%; '
                 f'background:{COLORS[row["country"]]}"></div></div></div>')
    st.markdown(bars, unsafe_allow_html=True)

    r = rec_sel.copy()
    r["trough_depth"] = 100 - r["trough_index"]
    r["years_plot"] = r["years_to_recover"].fillna(0)
    r["label"] = r["years_to_recover"].apply(lambda v: "not yet" if pd.isna(v) else str(int(v)))

    c1, c2 = st.columns(2)
    with c1:
        f = px.bar(r, x="country", y="trough_depth", color="country",
                   color_discrete_map=COLORS, text=r["trough_depth"].round(1),
                   title="How far GDP fell (index points lost)")
        f.update_traces(textposition="outside")
        f.update_layout(showlegend=False, xaxis_title="", yaxis_title="Points lost")
        st.plotly_chart(style(f, 400), use_container_width=True)
    with c2:
        f = px.bar(r, x="country", y="years_plot", color="country",
                   color_discrete_map=COLORS, text="label",
                   title="Years to regain the pre-war level")
        f.update_traces(textposition="outside")
        f.update_layout(showlegend=False, xaxis_title="", yaxis_title="Years")
        st.plotly_chart(style(f, 400), use_container_width=True)

    st.markdown("#### Recovery summary")
    nice = rec_sel.rename(columns={
        "country": "Country", "trough_year": "Trough year", "trough_index": "Trough index",
        "years_to_recover": "Years to recover", "pct_of_loss_regained": "% of loss regained",
        "shock_size_A": "Shock size (A)", "recovery_rate_k": "Recovery rate (k)",
        "half_life_yrs": "Half-life (yrs)"}).fillna("-")
    st.dataframe(nice, hide_index=True, use_container_width=True)
    st.caption("Model: index = 100 − A·exp(−k·t), fitted from the trough until the index regains 100. "
               "Fits for Iraq and Kuwait use only 3–4 points, so treat k as indicative. "
               "Ukraine has not recovered yet, so it shows progress instead of a fit.")

# =====================================================================
# Tab 7: Map
# =====================================================================
with tab7:
    m = view.copy().sort_values("year")
    m["GDP_index_capped"] = m["GDP_index"].clip(lower=40, upper=250)
    fig7 = px.choropleth(m, locations="iso3", color="GDP_index_capped",
                         hover_name="country", animation_frame="year",
                         color_continuous_scale="RdYlGn", range_color=(40, 250),
                         labels={"GDP_index_capped": "GDP index"},
                         title="GDP index by country, year by year (press ▶)")
    st.plotly_chart(style(fig7, 600, bottom=100), use_container_width=True)
    st.caption("Green = at or above the pre-war level, red = below it. Colour scale capped between 40 and 250.")

# =====================================================================
# Tab 8: Data
# =====================================================================
with tab8:
    want = ["country", "year", "period", "GDP_current_USD", "GDP_index", "GDP_index_usd",
            "GDP_growth_pct", "Inflation_pct"]
    show_cols = [c for c in want if c in view.columns]
    st.dataframe(view[show_cols], hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download this data as CSV",
                       view[show_cols].to_csv(index=False).encode("utf-8"),
                       file_name="war_economy_filtered.csv", mime="text/csv")

st.markdown("---")
st.caption("Built with Python · pandas · SciPy · Plotly · Streamlit  |  Data: World Bank Open Data")
