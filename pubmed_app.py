import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# ------------------- CONFIG ----------------------
st.set_page_config(page_title="Bug Tracker", layout="wide")

DB_PATH = "database"
MEDIA_PATH = "media"
os.makedirs(DB_PATH, exist_ok=True)
os.makedirs(MEDIA_PATH, exist_ok=True)

UAT_FILE = os.path.join(DB_PATH, "uat_issues.xlsx")
ARCH_FILE = os.path.join(DB_PATH, "architecture_issues.xlsx")
FEEDBACK_FILE = os.path.join(DB_PATH, "feedbacks.xlsx")

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]


# ------------------- LOAD OR CREATE EXCEL ----------------------
def load_or_create_excel(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_excel(path, index=False)
        return df
    return pd.read_excel(path)


df_main = load_or_create_excel(
    UAT_FILE,
    ["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
     *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"]
)

df_arch = load_or_create_excel(
    ARCH_FILE,
    ["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
     "Status", "image", "video", "remarks", "dev status"]
)

df_feedback = load_or_create_excel(
    FEEDBACK_FILE,
    ["Sno.", "Date", "Feedback", "image", "video", "Status"]
)


# ------------------- SAVE TO EXCEL ----------------------
def save_excel(df, path):
    df.to_excel(path, index=False)


# ------------------- UNIQUE MEDIA NAME ----------------------
def save_media(file, row_id):
    if not file:
        return None
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{row_id}_{timestamp}_{file.name}"
    full_path = os.path.join(MEDIA_PATH, filename)
    with open(full_path, "wb") as f:
        f.write(file.getbuffer())
    return filename


# ------------------- SIDEBAR NAVIGATION ----------------------
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 UAT Issues", "🏗️ Architecture Issues", "📝 User Feedback"]
)

# =============================================================
#                       🔷 DASHBOARD
# =============================================================
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    tab = st.radio("Select Table", ["UAT Issues", "Architecture Issues"])

    df = df_main if tab == "UAT Issues" else df_arch

    st.subheader("Media Preview (Click to Expand)")
    with st.expander("View Images and Videos"):
        for idx, row in df.iterrows():
            st.markdown(f"### Row {idx+1}: {row.get('Issue','')}")
            if pd.notna(row.get("image")):
                for img in str(row["image"]).split("|"):
                    path = os.path.join(MEDIA_PATH, img)
                    if os.path.exists(path):
                        st.image(path, use_column_width=True)

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
        st.plotly_chart(px.bar(df["Type"].value_counts(), title="Issues Count by Type"))

    st.subheader("Custom Chart")
    chart_col = st.selectbox("Select Column", df.columns)
    st.plotly_chart(px.histogram(df, x=chart_col))


# =============================================================
#                   🔷 UAT ISSUES (Editable)
# =============================================================
elif page == "📋 UAT Issues":
    st.title("📋 UAT Issues — Permanent Save Edition")

    edited = st.experimental_data_editor(df_main, use_container_width=True)
    save_excel(edited, UAT_FILE)
    df_main = edited.copy()

    st.subheader("Upload Media for Each Row")
    for idx in df_main.index:
        st.markdown(f"### Row {idx+1}: {df_main.at[idx, 'Issue']}")
        img = st.file_uploader(f"Image (Row {idx+1})", type=["png","jpg","jpeg"], key=f"img_uat_{idx}")
        vid = st.file_uploader(f"Video (Row {idx+1})", type=["mp4","mov"], key=f"vid_uat_{idx}")

        if img:
            fname = save_media(img, idx)
            df_main.at[idx, "image"] = fname if pd.isna(df_main.at[idx,"image"]) else df_main.at[idx,"image"] + "|" + fname
            save_excel(df_main, UAT_FILE)

        if vid:
            fname = save_media(vid, idx)
            df_main.at[idx, "video"] = fname if pd.isna(df_main.at[idx,"video"]) else df_main.at[idx,"video"] + "|" + fname
            save_excel(df_main, UAT_FILE)


# =============================================================
#             🔷 ARCHITECTURE ISSUES (Editable)
# =============================================================
elif page == "🏗️ Architecture Issues":
    st.title("🏗️ Architecture Issues — Permanent Save Edition")

    edited = st.experimental_data_editor(df_arch, use_container_width=True)
    save_excel(edited, ARCH_FILE)
    df_arch = edited.copy()

    st.subheader("Upload Media for Each Row")
    for idx in df_arch.index:
        st.markdown(f"### Row {idx+1}: {df_arch.at[idx, 'Issue']}")
        img = st.file_uploader(f"Image (Row {idx+1})", type=["png","jpg","jpeg"], key=f"img_arch_{idx}")
        vid = st.file_uploader(f"Video (Row {idx+1})", type=["mp4","mov"], key=f"vid_arch_{idx}")

        if img:
            fname = save_media(img, idx)
            df_arch.at[idx, "image"] = fname if pd.isna(df_arch.at[idx,"image"]) else df_arch.at[idx,"image"] + "|" + fname
            save_excel(df_arch, ARCH_FILE)

        if vid:
            fname = save_media(vid, idx)
            df_arch.at[idx, "video"] = fname if pd.isna(df_arch.at[idx,"video"]) else df_arch.at[idx,"video"] + "|" + fname
            save_excel(df_arch, ARCH_FILE)


# =============================================================
#                   🔷 USER FEEDBACK PAGE
# =============================================================
elif page == "📝 User Feedback":
    st.title("📝 User Feedback — Permanent Save")

    st.subheader("Add New Feedback")

    feedback_text = st.text_area("Enter Feedback")
    img = st.file_uploader("Upload Screenshot", type=["png","jpg","jpeg"])
    vid = st.file_uploader("Upload Video", type=["mp4","mov"])

    if st.button("Submit Feedback"):
        new_row = {}
        new_row["Sno."] = len(df_feedback) + 1
        new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
        new_row["Feedback"] = feedback_text
        new_row["Status"] = "New"

        new_row["image"] = save_media(img, new_row["Sno."]) if img else ""
        new_row["video"] = save_media(vid, new_row["Sno."]) if vid else ""

        df_feedback.loc[len(df_feedback)] = new_row
        save_excel(df_feedback, FEEDBACK_FILE)
        st.success("Feedback saved permanently!")

    st.subheader("All Feedbacks")
    st.dataframe(df_feedback, use_container_width=True)
