import streamlit as st
import pandas as pd

# =============================
# Streamlit page configuration
# =============================
st.set_page_config(page_title="Chess Leaderboard", layout="wide")
st.title("🏆 Chess Competition Leaderboard")

# =============================
# Data input: CSV upload or demo data
# =============================
st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV file (columns may include: player, final_standing, win_rate, wins, losses, games, mu_rating, model, prompt)",
    type=["csv"]
)

if uploaded_file:
    # Load user data
    df = pd.read_csv(uploaded_file)
else:
    # Demo dataset for testing
    df = pd.DataFrame([
        {"player":"Alpha",   "final_standing":1, "win_rate":0.92, "games":25, "mu_rating":2100, "model":"Claude 3.5 Sonnet", "prompt":"Careful positional play."},
        {"player":"Bravo",   "final_standing":3, "win_rate":0.78, "games":27, "mu_rating":1980, "model":"Claude 3 Opus",      "prompt":"Dynamic attacking style."},
        {"player":"Charlie", "final_standing":5, "win_rate":0.65, "games":26, "mu_rating":1850, "model":"Claude 3 Haiku",     "prompt":"Stable and defensive."},
        {"player":"Delta",   "final_standing":2, "win_rate":0.84, "games":24, "mu_rating":2050, "model":"Claude 3.5 Sonnet",  "prompt":"Balanced tactics and strategy."},
        {"player":"Echo",    "final_standing":4, "win_rate":0.81, "games":23, "mu_rating":1995, "model":"Claude 3 Sonnet",    "prompt":"Exploiting weak squares."},
    ])

# =============================
# Data cleaning and calculations
# =============================

# Normalize column names and fill in missing ones
df.columns = [c.strip().lower() for c in df.columns]
required_cols = ["player","final_standing","win_rate","wins","losses","games","mu_rating","model","prompt"]
for col in required_cols:
    if col not in df.columns:
        df[col] = pd.NA

# Convert numeric columns safely
for c in ["final_standing","win_rate","wins","losses","games","mu_rating"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Convert win_rate from % to fraction if needed
df.loc[df["win_rate"] > 1, "win_rate"] = df["win_rate"] / 100.0

# Compute missing wins/losses/games/win_rate if possible
if "wins" not in df.columns:
    df["wins"] = pd.NA
if "losses" not in df.columns:
    df["losses"] = pd.NA
if "games" not in df.columns:
    df["games"] = pd.NA

# 1. Estimate wins if win_rate and games exist
mask_wins = df["wins"].isna() & df["games"].notna() & df["win_rate"].notna()
df.loc[mask_wins, "wins"] = (df["games"] * df["win_rate"]).round().astype("Int64")

# 2. Estimate losses if wins and games exist
mask_losses = df["losses"].isna() & df["games"].notna() & df["wins"].notna()
df.loc[mask_losses, "losses"] = (df["games"] - df["wins"]).astype("Int64")

# 3. Estimate games if wins + losses exist
mask_games = df["games"].isna() & df["wins"].notna() & df["losses"].notna()
df.loc[mask_games, "games"] = (df["wins"] + df["losses"]).astype("Int64")

# 4. Estimate win_rate if wins/games exist
mask_wr = df["win_rate"].isna() & df["wins"].notna() & df["games"].notna() & (df["games"] > 0)
df.loc[mask_wr, "win_rate"] = (df["wins"] / df["games"]).astype(float)

# Fill missing numeric values with zero
for c in ["wins","losses","games","win_rate","mu_rating","final_standing"]:
    df[c] = df[c].fillna(0)

# Rename columns for better display
df = df.rename(columns={
    "player":"Player",
    "final_standing":"Final Standing",
    "win_rate":"Win Rate",
    "wins":"Wins",
    "losses":"Losses",
    "games":"Games",
    "mu_rating":"Mu Rating",
    "model":"Model",
    "prompt":"Prompt"
})

# =============================
# Sidebar controls: sorting and pinning
# =============================
st.sidebar.header("Controls")
sort_option = st.sidebar.selectbox(
    "Sort leaderboard by:",
    ["Final Standing","Win Rate","Mu Rating","Wins","Losses"]
)

# Sort ascending only for rankings/losses
ascending = sort_option in ["Final Standing", "Losses"]
df = df.sort_values(by=sort_option, ascending=ascending).reset_index(drop=True)

# Allow user to pin one player at top
pin_choice = st.sidebar.selectbox("📌 Pin one player", ["None"] + df["Player"].tolist())
if pin_choice != "None":
    pinned = df[df["Player"] == pin_choice]
    others = df[df["Player"] != pin_choice]
    df = pd.concat([pinned, others], ignore_index=True)

# =============================
# Sidebar KPIs (summary metrics)
# =============================
st.sidebar.header("Quick Stats")
st.sidebar.metric("Players", len(df))
st.sidebar.metric("Total Games", int(df["Games"].sum()))
avg_wr = (df["Wins"].sum() / df["Games"].sum()) if df["Games"].sum() else 0
st.sidebar.metric("Average Win Rate", f"{avg_wr:.1%}")
st.sidebar.metric("Players >80% WR", int((df["Win Rate"] >= 0.8).sum()))

# =============================
# Style rules for row highlighting
# =============================
def highlight_row(row):
    if pin_choice != "None" and row["Player"] == pin_choice:
        return ["background-color:#e8f0ff"] * len(row)   # Light blue for pinned
    if int(row["Final Standing"]) <= 3:
        return ["background-color:#fff8dc"] * len(row)   # Light yellow for top 3
    if row["Win Rate"] >= 0.80:
        return ["background-color:#eaffea"] * len(row)   # Light green for >80%
    return [""] * len(row)

# =============================
# Leaderboard table
# =============================
st.subheader("Leaderboard")
cols_to_show = ["Player","Wins","Losses","Games","Win Rate","Final Standing","Mu Rating","Model","Prompt"]
styled_df = df[cols_to_show].style.format({"Win Rate":"{:.0%}"}).apply(highlight_row, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# =============================
# Analytics charts
# =============================
st.subheader("Quick Analytics")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Wins and Losses per Player**")
    chart_data = df.set_index("Player")[["Wins","Losses"]]
    st.bar_chart(chart_data)

with col2:
    st.markdown("**Mu Rating vs Final Standing** *(lower is better)*")
    scatter_df = df[["Mu Rating","Final Standing"]].copy()
    scatter_df.index = df["Player"]
    st.scatter_chart(scatter_df, x="Mu Rating", y="Final Standing")

# =============================
# Player detail cards (expandable)
# =============================
st.subheader("Player Details")
for _, row in df.iterrows():
    with st.expander(f"{row['Player']}  —  {int(row['Wins'])}-{int(row['Losses'])}  ({row['Win Rate']:.0%})"):
        st.write(f"**Final Standing:** {int(row['Final Standing'])}")
        st.write(f"**Mu Rating:** {int(row['Mu Rating'])}")
        st.write(f"**Model:** {row['Model']}")
        st.info(f"🧩 **Prompt:** {row['Prompt']}")