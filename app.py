import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_prep import LEVEL_ORDER, load

st.set_page_config(page_title="Where Education Diverges in Lebanon", layout="wide")

# ---------- palette (validated categorical order, fixed per district) ----------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
REF_GREY = "#7a7975"
CONTEXT_GREY = "#d6d5d0"
NAVY = "#1F3A5F"


@st.cache_data
def get_data():
    df, report = load("lebanon_education.csv")
    df["Tertiary"] = df["University"] + df["Higher education"]
    df["Basic or less"] = df["Illiterate"] + df["Elementary"]
    return df, report


df, report = get_data()
national = df[LEVEL_ORDER + ["Tertiary", "School dropout"]].mean()

# ---------- header and context ----------
st.title("Where education diverges in Lebanon")
st.markdown(
    "Each of Lebanon's towns reported what share of its residents stopped at each education level, "
    "from illiterate to higher education. Governorate averages make the country look like a simple "
    "coast-versus-periphery story. This page lets you pick a governorate and then drill into its "
    "districts to see where that story holds and where it breaks."
)
st.caption(
    f"Source: Impact Open Data (Central Inspection Board, Lebanon), published via AUB CODEC linked data. "
    f"{report['kept']} of {report['raw_rows']} town records used after cleaning; see Data notes at the bottom."
)

st.subheader("Two things the data shows")
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        "**1. The North is the most unequal governorate, not a uniformly strong one.** "
        "Its average tertiary share (30%) sits second only to Mount Lebanon, but inside it Batroun "
        "reaches 39% while Miniyeh-Danniyeh is at 21% with a 13% school dropout rate, close to "
        "three times the national average. Select *North* below to see the split."
    )
with c2:
    st.markdown(
        "**2. Towns with more illiteracy have fewer graduates, but the link is moderate.** "
        "Across towns the correlation between illiteracy and tertiary share is about -0.33. "
        "Almost half (48%) of towns with below-median illiteracy still have below-average tertiary shares, so "
        "low illiteracy alone does not explain who reaches university. The scatter below shows this spread."
    )

st.divider()

# ---------- linked controls ----------
gov_order = (df.groupby("Governorate")["Tertiary"].mean().sort_values(ascending=False).index.tolist())
ctrl1, ctrl2 = st.columns([1, 2])
with ctrl1:
    gov = st.selectbox(
        "1. Choose a governorate",
        gov_order,
        index=gov_order.index("North"),
        help="Governorates are listed from highest to lowest average tertiary share.",
    )

gdf = df[df["Governorate"] == gov]
district_list = sorted(gdf["District"].unique())
color_of = {d: SERIES[i % len(SERIES)] for i, d in enumerate(district_list)}
counts = gdf["District"].value_counts()

with ctrl2:
    # key depends on governorate so the options and defaults reset when it changes
    districts = st.multiselect(
        f"2. Drill into districts of {gov}",
        district_list,
        default=district_list,
        key=f"districts_{gov}",
        format_func=lambda d: f"{d} ({counts[d]} towns)",
        help="Only districts inside the chosen governorate are offered. Remove some to compare fewer.",
    )

if not districts:
    st.warning("Select at least one district to draw the charts.")
    st.stop()

sel = gdf[gdf["District"].isin(districts)]
dist_stats = (sel.groupby("District")[["Tertiary", "Illiterate", "School dropout"]].mean()
              .sort_values("Tertiary", ascending=False))

# ---------- KPI row ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Towns in selection", f"{len(sel)}")
k2.metric("Tertiary share", f"{sel['Tertiary'].mean():.1f}%",
          f"{sel['Tertiary'].mean() - national['Tertiary']:+.1f} pts vs Lebanon")
k3.metric("Illiterate", f"{sel['Illiterate'].mean():.1f}%",
          f"{sel['Illiterate'].mean() - national['Illiterate']:+.1f} pts vs Lebanon", delta_color="inverse")
k4.metric("School dropout", f"{sel['School dropout'].mean():.1f}%",
          f"{sel['School dropout'].mean() - national['School dropout']:+.1f} pts vs Lebanon", delta_color="inverse")

if len(dist_stats) > 1:
    top, bottom = dist_stats.index[0], dist_stats.index[-1]
    gap = dist_stats.loc[top, "Tertiary"] - dist_stats.loc[bottom, "Tertiary"]
    st.info(
        f"Within your selection, **{top}** has the highest tertiary share "
        f"({dist_stats.loc[top, 'Tertiary']:.1f}%) and **{bottom}** the lowest "
        f"({dist_stats.loc[bottom, 'Tertiary']:.1f}%): a gap of {gap:.1f} percentage points."
    )

small = [d for d in districts if counts[d] < 10]
if small:
    st.caption(f"Caution: {', '.join(small)} has fewer than 10 towns with usable data, so its averages are fragile.")

# ---------- chart 1: education profile ----------
st.subheader("Education profile: where do residents stop?")
st.caption("Average share of residents at each level, per district. Dashed grey line is the Lebanon average.")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=LEVEL_ORDER, y=national[LEVEL_ORDER].values, name="Lebanon average",
    mode="lines", line=dict(color=REF_GREY, width=2, dash="dash"),
    hovertemplate="Lebanon average<br>%{x}: %{y:.1f}%<extra></extra>",
))
for d in dist_stats.index:
    prof = sel[sel["District"] == d][LEVEL_ORDER].mean()
    fig1.add_trace(go.Scatter(
        x=LEVEL_ORDER, y=prof.values, name=d, mode="lines+markers",
        line=dict(color=color_of[d], width=2), marker=dict(size=8, line=dict(color="white", width=2)),
        hovertemplate=f"{d}<br>%{{x}}: %{{y:.1f}}%<extra></extra>",
    ))
fig1.update_layout(
    height=430, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", hovermode="closest",
    yaxis=dict(title="% of residents", ticksuffix="%", gridcolor="#eeeeec", zeroline=False),
    xaxis=dict(title=None, showgrid=False),
    legend=dict(orientation="h", y=-0.15, x=0),
)
st.plotly_chart(fig1, use_container_width=True)

# ---------- chart 2: town scatter ----------
st.subheader("Town by town: illiteracy against tertiary education")
st.caption("Each dot is a town. Grey dots are every other town in Lebanon, kept for context. "
           "Hover a dot for the town name. Towns reported rounded values (0, 1, 2, 5, 10%...), so dots stack in columns.")

rest = df[~df.index.isin(sel.index)]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=rest["Illiterate"], y=rest["Tertiary"], mode="markers", name="Rest of Lebanon",
    marker=dict(color=CONTEXT_GREY, size=7), text=rest["Town"] + " (" + rest["District"] + ")",
    hovertemplate="%{text}<br>Illiterate: %{x:.1f}%<br>Tertiary: %{y:.1f}%<extra></extra>",
))
for d in dist_stats.index:
    s = sel[sel["District"] == d]
    fig2.add_trace(go.Scatter(
        x=s["Illiterate"], y=s["Tertiary"], mode="markers", name=d,
        marker=dict(color=color_of[d], size=9, opacity=0.85, line=dict(color="white", width=1.5)),
        text=s["Town"],
        hovertemplate=f"%{{text}} ({d})<br>Illiterate: %{{x:.1f}}%<br>Tertiary: %{{y:.1f}}%<extra></extra>",
    ))
fig2.add_hline(y=national["Tertiary"], line=dict(color=REF_GREY, dash="dash", width=1),
               annotation_text="Lebanon avg tertiary", annotation_position="top right",
               annotation_font_color=REF_GREY)
fig2.add_vline(x=national["Illiterate"], line=dict(color=REF_GREY, dash="dash", width=1),
               annotation_text="Lebanon avg illiterate", annotation_position="top right",
               annotation_font_color=REF_GREY)
fig2.update_layout(
    height=480, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
    xaxis=dict(title="Illiterate residents (%)", ticksuffix="%", gridcolor="#eeeeec", zeroline=False),
    yaxis=dict(title="University + higher education (%)", ticksuffix="%", gridcolor="#eeeeec", zeroline=False),
    legend=dict(orientation="h", y=-0.18, x=0),
)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("Table view of the selection"):
    tbl = sel.groupby("District")[LEVEL_ORDER + ["Tertiary", "School dropout"]].mean().round(1)
    tbl.insert(0, "Towns", sel["District"].value_counts())
    st.dataframe(tbl.sort_values("Tertiary", ascending=False), use_container_width=True)

st.divider()

# ---------- design justifications ----------
st.subheader("Design justifications")
with st.expander("Feature 1: governorate dropdown", expanded=False):
    st.markdown(
        "**User question.** How does my region compare with the rest of Lebanon, and is its average "
        "hiding anything?\n\n"
        "**Why this widget.** A single-select dropdown fits because the governorate is the entry point "
        "of the drill-down: exactly one must be active so the district list below it has a clear scope. "
        "I considered radio buttons, which show all seven options at once, but they take a full row of "
        "space for a choice made once per visit. A multiselect was rejected because mixing governorates "
        "would break the parent-child logic. The list is ordered by average tertiary share, so the "
        "ordering itself gives a first ranking before any chart is read.\n\n"
        "**Course concept.** This applies *overview first, zoom and filter, then details on demand*: the "
        "headline insights give the overview, the dropdown is the zoom step. It also reduces clutter, "
        "since drawing all 25 districts on one line chart would be unreadable."
    )
with st.expander("Feature 2: district multiselect (linked to feature 1)", expanded=False):
    st.markdown(
        "**User question.** Within the chosen governorate, which districts pull the average up or down, "
        "and do their towns behave alike?\n\n"
        "**Why this widget.** Its options are generated from the governorate selection, so the user can "
        "only pick districts that belong to it, and it resets when the governorate changes. A multiselect "
        "was chosen over a single dropdown because the question is comparative: users need two or more "
        "districts side by side. Checkboxes were considered, but with up to six districts they push the "
        "charts below the fold, while the multiselect stays compact and shows town counts next to each "
        "name so thin samples are visible before selection.\n\n"
        "**Course concept.** It focuses attention through highlighting: selected districts are drawn in "
        "color while every other town in Lebanon stays as light grey dots, and the dashed Lebanon average "
        "stays on both charts. That keeps context visible while directing the eye to the comparison the "
        "user asked for. Each district keeps the same color when others are removed, so the encoding "
        "stays consistent."
    )

with st.expander("Data notes"):
    st.markdown(
        f"- Raw file: {report['raw_rows']} town records across 7 governorates and 25 districts.\n"
        f"- {report['missing']} records dropped because one or more education levels were blank.\n"
        f"- {report['bad_total']} records dropped because their seven levels did not add up to roughly 100% "
        "(between 80 and 120). One town, Miriata, reported counts instead of percentages "
        "(values up to 6,000), which by itself inflated national averages by several points.\n"
        "- Remaining towns were rescaled so their seven levels sum to exactly 100%.\n"
        "- *Tertiary* = University + Higher education. School dropout is reported separately and is not "
        "part of the 100%.\n"
        "- District names had encoding errors in the source (Miniyeh-Danniyeh, Zahle) and were repaired.\n"
        "- Figures are unweighted town averages: a small village counts as much as a large town."
    )
