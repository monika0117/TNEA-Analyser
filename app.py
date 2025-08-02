import streamlit as st
import pandas as pd
import base64
import os

# ----- PAGE CONFIG -----
st.set_page_config(page_title="TNEA Cutoff Viewer", layout="wide")

# ----- ROUND SETTINGS -----
round_files = {
    "Round 1": "Round_1.xlsx",
    "Round 2": "Round_2.xlsx",
    "Round 3": "Round_3.xlsx"
}

# ----- BACKGROUND IMAGE SETUP -----
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

if not os.path.exists("9781304.jpg"):
    st.error("Background image not found. Please place '9781304.jpg' in the app directory.")
    st.stop()

bg_image = get_base64_image("9781304.jpg")

def load_css_with_bg(css_file_path, bg_base64):
    with open(css_file_path, "r") as f:
        css = f.read()
    css = css.replace("{bg_image}", bg_base64)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css_with_bg("style.css", bg_image)

# ----- LOAD MULTI-ROUND DATA -----
@st.cache_data
def load_all_rounds(file_dict):
    all_data = []
    with st.spinner("Loading round data..."):
        for round_name, path in file_dict.items():
            try:
                df = pd.read_excel(path)
                df.columns = df.columns.str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
                df = df.rename(columns={
                    "COLLEGE CODE": "CollegeCode",
                    "COLLEGE NAME": "CollegeName",
                    "BRANCH CODE": "BranchCode",
                    "COMMU NITY": "Community",
                    "AGGR MARK": "Mark"
                })

                expected_cols = ["CollegeCode", "CollegeName", "BranchCode", "Community", "Mark"]
                missing = [col for col in expected_cols if col not in df.columns]
                if missing:
                    continue

                df.dropna(subset=["CollegeCode", "BranchCode", "Community", "Mark"], inplace=True)
                df["CollegeCode"] = df["CollegeCode"].astype(str).str.strip()
                df["BranchCode"] = df["BranchCode"].astype(str).str.strip()
                df["Community"] = df["Community"].astype(str).str.strip()
                df["Mark"] = pd.to_numeric(df["Mark"], errors="coerce")
                df["Round"] = round_name

                grouped = df.groupby(["CollegeCode", "CollegeName", "BranchCode", "Community"]).agg(
                    Min_Cutoff=("Mark", "min"),
                    Max_Cutoff=("Mark", "max"),
                    No_of_Students=("Mark", "count")
                ).reset_index()
                grouped["Round"] = round_name

                all_data.append(grouped)
            except Exception as e:
                st.warning(f"⚠️ Could not process {path}: {e}")
                continue

    if not all_data:
        st.error("No valid round data found.")
        st.stop()

    return pd.concat(all_data, ignore_index=True)

# Load data once
data = load_all_rounds(round_files)

# ----- MAIN APP -----
def main():
    if "start" not in st.session_state:
        st.session_state.start = False

    if not st.session_state.start:
        with st.container():
            st.markdown("""
                <div class="bento-wrapper">
                    <div class="grid0"><h1>TNEA 2024 Cutoff Search Tool</h1></div>
                    <div class="grid1">
                        <h4>🎯 Predict Eligible Colleges</h4>
                        <p>Based on your cutoff & community</p>
                    </div>
                    <div class="grid2">
                        <h4>🔷 Explore Branch-wise Cutoffs</h4>
                        <p>View community cutoffs across all rounds</p>
                    </div>
                    <div class="grid3">
                        <h4>📊 Dive into Detailed Stats</h4>
                        <p>Gain insights on college-level trends</p>
                    </div>
                    <div class="grid4">
                        <h4>Welcome to TNEA 2024</h4>
                        <p>Cutoff Viewer App</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div style="display: flex; justify-content: center; margin-top: 20px;">', unsafe_allow_html=True)
            if st.button("Start App", key="start_button"):
                st.session_state.start = True
            st.markdown('</div>', unsafe_allow_html=True)

        return None  # ✅ Prevents DeltaGenerator display

    # ---- App Mode UI ----
    st.sidebar.title("⚙️ App Mode")
    mode = st.sidebar.radio("Select Module", [
        "Cutoff-based Predictor", 
        "Community-based Predictor", 
        "College-wise Viewer",
        "Rank-wise Predictor"
    ])
    round_selected = st.sidebar.radio("Choose Counseling Round:", sorted(data["Round"].unique()))
    df = data[data["Round"] == round_selected]

    # ---- Mode 1: Cutoff-based Predictor ----
    if mode == "Cutoff-based Predictor":
        st.markdown("<h2 class='main-title'>Predict Colleges from Your Cutoff and Community</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            cutoff_input = st.number_input("Cutoff Mark", min_value=0.0, max_value=200.0, step=0.5)
        with col2:
            community_input = st.selectbox("Community", sorted(df["Community"].unique()))
        with col3:
            selected_branch = st.selectbox("Branch (optional)", ["All Branches"] + sorted(df["BranchCode"].unique()))

        if st.button("Find Eligible Colleges"):
            eligible = df[
                (df["Community"] == community_input) &
                (df["Min_Cutoff"] <= cutoff_input) &
                (df["Max_Cutoff"] >= cutoff_input)
            ]
            if selected_branch != "All Branches":
                eligible = eligible[eligible["BranchCode"] == selected_branch]
            eligible = eligible.sort_values(by="Min_Cutoff", ascending=False)

            if not eligible.empty:
                with st.container():
                    st.dataframe(eligible, use_container_width=True, hide_index=True)
            else:
                st.warning("No eligible colleges found.")

        return None

    # ---- Mode 2: Community-based Predictor (✅ Fixed) ----
    elif mode == "Community-based Predictor":
        st.markdown("<h2 class='main-title'>Explore Community Cutoffs</h2>", unsafe_allow_html=True)
        community_input = st.selectbox("Select your community:", sorted(df["Community"].unique()))
        selected_branch = st.selectbox("Select Branch (optional):", ["All Branches"] + sorted(df["BranchCode"].unique()))

        filtered = df[df["Community"] == community_input]
        if selected_branch != "All Branches":
            filtered = filtered[filtered["BranchCode"] == selected_branch]
        filtered = filtered.sort_values(by="Min_Cutoff", ascending=False)

        if not filtered.empty:
            with st.container():
                st.dataframe(filtered, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found.")

        return None

    # ---- Mode 3: College-wise Viewer ----
    elif mode == "College-wise Viewer":
        college_codes = sorted(df["CollegeCode"].unique())
        college_names = df[["CollegeCode", "CollegeName"]].drop_duplicates()
        name_map = {row["CollegeCode"]: row["CollegeName"] for _, row in college_names.iterrows()}
        display_list = [f"{code} - {name_map.get(code, 'Unknown College')}" for code in college_codes]
        selected_index = st.selectbox("Select College:", range(len(college_codes)), format_func=lambda i: display_list[i])
        selected_code = college_codes[selected_index]
        branch_options = sorted(df[df["CollegeCode"] == selected_code]["BranchCode"].unique())
        selected_branch = st.selectbox("Select Branch:", branch_options)
        filtered = df[(df["CollegeCode"] == selected_code) & (df["BranchCode"] == selected_branch)]

        if not filtered.empty:
            with st.container():
                st.dataframe(filtered, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found.")

        return None
    
        # ---- Mode 4: Rank-wise Predictor (Simplified) ----
    elif mode == "Rank-wise Predictor":
        st.markdown("<h2 class='main-title'>🎯 Colleges Eligible for Your Rank</h2>", unsafe_allow_html=True)

        # Input: Rank only
        user_rank = st.number_input("Enter Your TNEA Rank", min_value=1, max_value=100000, step=1)

        if st.button("Find Eligible Colleges"):
            # Work with full data for all communities and branches
            df_rank = df.copy()

            # Sort by cutoff descending (highest cutoff first → priority admission)
            df_rank = df_rank.sort_values(by="Min_Cutoff", ascending=False).reset_index(drop=True)

            # Calculate cumulative seats per (Community, Branch) group
            # We group by Community and BranchCode to simulate real seat-wise ranking
            results = []
            for (branch, community), group in df_rank.groupby(["BranchCode", "Community"]):
                group = group.sort_values(by="Min_Cutoff", ascending=False).reset_index(drop=True)
                group["Last_Admitted_Rank"] = group["No_of_Students"].cumsum()
                group["First_Admitted_Rank"] = group["Last_Admitted_Rank"] - group["No_of_Students"] + 1
                # Filter rows where user rank falls in range
                eligible_in_group = group[
                    (group["First_Admitted_Rank"] <= user_rank) &
                    (group["Last_Admitted_Rank"] >= user_rank)
                ]
                results.append(eligible_in_group)

            # Combine all eligible rows
            eligible = pd.concat(results, ignore_index=True) if results else pd.DataFrame()

            # Select only the clean columns to display
            if not eligible.empty:
                display_df = eligible[[
                    "CollegeCode", "CollegeName", "BranchCode", "Community",
                    "Min_Cutoff", "Max_Cutoff", "No_of_Students"
                ]].sort_values(by="Min_Cutoff", ascending=False).reset_index(drop=True)

                st.success(f"✅ {len(display_df)} college(s) found where your rank ({user_rank}) may qualify.")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.warning("❌ No colleges found for your rank. Try checking previous rounds or lower cutoff trends.")

        # Optional: Add info note
        st.caption("💡 *Colleges are predicted based on cutoff order and seat availability per community & branch.*")

        return None
    return None  # ✅ Prevent Streamlit from showing internal objects

    
    # ----- RUN THE APP -----
if __name__ == "__main__":
    main()
