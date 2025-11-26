import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Bug Tracker", layout="wide")

MEDIA_PATH = "media"
os.makedirs(MEDIA_PATH, exist_ok=True)

UAT_FILE = "uat_issues.xlsx"
ARCH_FILE = "architecture_issues.xlsx"
FEEDBACK_FILE = "feedbacks.xlsx"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]


# ----------------------------------------------------
# LOAD OR CREATE EXCEL FILES
# ----------------------------------------------------
def load_or_create(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_excel(path, index=False)
        return df
    return pd.read_excel(path)


df_main = load_or_create(
    UAT_FILE,
    ["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
     *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"]
)

df_arch = load_or_create(
    ARCH_FILE,
    ["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
     "Status", "image", "video", "remarks", "dev status"]
)

df_feedback = load_or_create(
    FEEDBACK_FILE,
    ["Sno.", "Date", "Feedback", "image", "video", "Status"]
)


# ----------------------------------------------------
# SAVE TO EXCEL
# ----------------------------------------------------
def save_excel(df, path):
    df.to_excel(path, index=False)


# ----------------------------------------------------
# SAVE MEDIA
# ----------------------------------------------------
def save_media(file, row_id):
    if not file:
        return None
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{row_id}_{timestamp}_{file.name}"
    full_path = os.path.join(MEDIA_PATH, filename)
    with open(full_path, "wb") as f:
        f.write(file.getbuffer())
    return filename


# ----------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 UAT Issues", "🏗️ Architecture Issues", "📝 User Feedback"]
)

# ===========================================================
# 📊 DASHBOARD
# ===========================================================
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    tab = st.radio("Select Table", ["UAT Issues", "Architecture Issues"])

    df = df_main if tab == "UAT Issues" else df_arch

    st.subheader("Media Viewer")
    with st.expander("Click to View All Images & Videos"):
        for idx, row in df.iterrows():
            st.markdown(f"### Row {idx+1}: {row.get('Issue','')}")
            # IMAGES
            if pd.notna(row.get("image")):
                for img in str(row["image"]).split("|"):
                    path = os.path.join(MEDIA_PATH, img)
                    if os.path.exists(path):
                        st.image(path, use_column_width=True)
            # VIDEOS
            if pd.notna(row.get("video")):
                for vid in str(row["video"]).split("|"):
                    path = os.path.join(MEDIA_PATH, vid)
                    if os.path.exists(path):
                        st.video(path)

    st.subheader("Table View")
    col_filter = st.multiselect("Select Columns", df.columns, default=df.columns)
    st.dataframe(df[col_filter], use_container_width=True)

    st.subheader("Predefined Charts")
    if "Type" in df.columns:
        st.plotly_chart(px.bar(df["Type"].value_counts(), title="Issues by Type"))

    st.subheader("Custom Chart")
    chart_col = st.selectbox("Select Column", df.columns)
    st.plotly_chart(px.histogram(df, x=chart_col, title=f"{chart_col} Distribution"))


# ===========================================================
# 📋 UAT ISSUES PAGE
# ===========================================================
elif page == "📋 UAT Issues":
    st.title("📋 UAT Issues (Auto-Save Enabled)")

    edited = st.experimental_data_editor(df_main, use_container_width=True)
    save_excel(edited, UAT_FILE)
    df_main = edited.copy()

    st.subheader("Upload Media per Row")
    for idx in df_main.index:
        st.markdown(f"### Row {idx+1}: {df_main.at[idx,'Issue']}")
        img = st.file_uploader(f"Image (Row {idx+1})", type=["png","jpg","jpeg"], key=f"img_uat_{idx}")
        vid = st.file_uploader(f"Video (Row {idx+1})", type=["mp4","mov"], key=f"vid_uat_{idx}")

        if img:
            fname = save_media(img, idx)
            old = df_main.at[idx, "image"]
            df_main.at[idx, "image"] = fname if pd.isna(old) else old + "|" + fname
            save_excel(df_main, UAT_FILE)

        if vid:
            fname = save_media(vid, idx)
            old = df_main.at[idx, "video"]
            df_main.at[idx, "video"] = fname if pd.isna(old) else old + "|" + fname
            save_excel(df_main, UAT_FILE)


# ===========================================================
# 🏗️ ARCHITECTURE ISSUES PAGE
# ===========================================================
elif page == "🏗️ Architecture Issues":
    st.title("🏗️ Architecture Issues (Auto-Save Enabled)")

    edited = st.experimental_data_editor(df_arch, use_container_width=True)
    save_excel(edited, ARCH_FILE)
    df_arch = edited.copy()

    st.subheader("Upload Media per Row")
    for idx in df_arch.index:
        st.markdown(f"### Row {idx+1}: {df_arch.at[idx,'Issue']}")
        img = st.file_uploader(f"Image (Row {idx+1})", type=["png","jpg","jpeg"], key=f"img_arch_{idx}")
        vid = st.file_uploader(f"Video (Row {idx+1})", type=["mp4","mov"], key=f"vid_arch_{idx}")

        if img:
            fname = save_media(img, idx)
            old = df_arch.at[idx, "image"]
            df_arch.at[idx, "image"] = fname if pd.isna(old) else old + "|" + fname
            save_excel(df_arch, ARCH_FILE)

        if vid:
            fname = save_media(vid, idx)
            old = df_arch.at[idx, "video"]
            df_arch.at[idx, "video"] = fname if pd.isna(old) else old + "|" + fname
            save_excel(df_arch, ARCH_FILE)


# ===========================================================
# 📝 USER FEEDBACK PAGE
# ===========================================================
elif page == "📝 User Feedback":
    st.title("📝 User Feedback (Permanent)")

    st.subheader("Submit Feedback")
    fb = st.text_area("Enter Your Feedback")

    img = st.file_uploader("Upload Screenshot")
    vid = st.file_uploader("Upload Video", type=["mp4", "mov"])

    if st.button("Submit"):
        new = {
            "Sno.": len(df_feedback) + 1,
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Feedback": fb,
            "Status": "New",
            "image": save_media(img, len(df_feedback)+1) if img else "",
            "video": save_media(vid, len(df_feedback)+1) if vid else ""
        }
        df_feedback.loc[len(df_feedback)] = new
        save_excel(df_feedback, FEEDBACK_FILE)
        st.success("Saved Successfully!")

    st.subheader("All Feedback")
    st.dataframe(df_feedback, use_container_width=True)
