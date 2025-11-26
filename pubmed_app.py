import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_PATH = "user_feedback.xlsx"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ------------------------ UTILITIES ------------------------
@st.cache_data
def load_excels():
    """Load UAT and Architecture issues."""
    if not os.path.exists(EXCEL_PATH):
        df_main = pd.DataFrame(columns=[
            "Sno.","Date","Repetitive Count","Repetitive Dates",
            "Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"
        ])
        df_arch = pd.DataFrame(columns=[
            "Sno.","Date","Repetitive Count","Repetitive Dates",
            "Type","Issue","Status","image","video","remarks","dev status"
        ])
        return df_main, df_arch

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")]) \
              if "uat_issues" in sheet_names else pd.DataFrame()
    df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")]) \
              if "architecture_issues" in sheet_names else pd.DataFrame()

    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()

    return df_main, df_arch


def save_excels(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)


def load_feedback():
    if os.path.exists(FEEDBACK_PATH):
        return pd.read_excel(FEEDBACK_PATH)
    else:
        return pd.DataFrame(columns=["Name","Email","Feedback","Date"])


def save_feedback(df_fb):
    df_fb.to_excel(FEEDBACK_PATH, index=False)


# ------------------------ PAGE CONFIG ------------------------
st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Noether IP Status")

df_main, df_arch = load_excels()
df_feedback = load_feedback()

page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "✉️ User Feedback"]
)

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])

    if dashboard_type == "UAT Issues":
        st.header("📊 UAT Issues Dashboard")
        df = df_main.copy()

        # Filters
        type_options = df["Type"].dropna().unique().tolist()
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)

        client_options = CLIENT_COLUMNS
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=client_options)

        if selected_types:
            df = df[df["Type"].isin(selected_types)]
        if selected_clients:
            df = df[df[selected_clients].eq("Yes").all(axis=1)]

    else:
        st.header("🏗️ Architecture Issues Dashboard")
        df = df_arch.copy()

        type_options = df["Type"].dropna().unique().tolist()
        status_options = df["Status"].dropna().unique().tolist()

        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)

        if selected_types:
            df = df[df["Type"].isin(selected_types)]
        if selected_status:
            df = df[df["Status"].isin(selected_status)]

    # Column selector
    columns_to_show = st.multiselect(
        "Select Columns to Display",
        df.columns.tolist(),
        default=df.columns.tolist()
    )
    st.dataframe(df[columns_to_show], use_container_width=True)

    # Media Viewer
    with st.expander("📂 Media Viewer (Expand to view all images/videos)"):
        for idx, row in df.iterrows():
            st.markdown(f"### 🔹 S.No: {row.get('Sno.', '')} — {row.get('Issue', '')}")

            # Images
            images = list(set(str(row.get("image","")).split("|")))
            for img in images:
                img = img.strip()
                if img:
                    img_path = os.path.join(MEDIA_FOLDER, img)
                    if os.path.exists(img_path):
                        st.image(img_path, caption=img, width=400)

            # Videos
            videos = list(set(str(row.get("video","")).split("|")))
            for vid in videos:
                vid = vid.strip()
                if vid:
                    vid_path = os.path.join(MEDIA_FOLDER, vid)
                    if os.path.exists(vid_path):
                        st.video(vid_path)

    # Charts
    st.subheader("📈 Predefined Charts")

    if not df.empty:
        if "Type" in df.columns:
            st.plotly_chart(px.bar(df["Type"].value_counts(), title="Issues by Type"))

        if "Status" in df.columns:
            st.plotly_chart(px.pie(df, names="Status", title="Status Distribution"))

    # Custom chart
    st.subheader("📊 Custom Chart")
    if not df.empty:
        col_sel = st.selectbox("Select column", df.columns)
        chart_type = st.selectbox("Chart Type", ["Bar","Pie","Histogram"])

        try:
            if chart_type == "Bar":
                st.plotly_chart(px.bar(df, x=col_sel))
            elif chart_type == "Pie":
                st.plotly_chart(px.pie(df, names=col_sel))
            else:
                st.plotly_chart(px.histogram(df, x=col_sel))
        except:
            st.warning("Cannot generate chart for this column.")

# ------------------------ EDITABLE UAT ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 UAT Issues (Manual Save Mode)")

    temp_main = st.session_state.get("temp_main", df_main.copy())
    edited_main = st.experimental_data_editor(temp_main, num_rows="dynamic")

    st.session_state["temp_main"] = edited_main

    st.subheader("Upload Media Per Row")

    for idx in edited_main.index:
        st.markdown(f"### Row {idx+1}: {edited_main.at[idx,'Issue']}")

        img = st.file_uploader(f"Upload Image (row {idx+1})", type=["png","jpg","jpeg"], key=f"img_uat_{idx}")
        vid = st.file_uploader(f"Upload Video (row {idx+1})", type=["mp4","mov"], key=f"vid_uat_{idx}")

        if img:
            path = os.path.join(MEDIA_FOLDER, img.name)
            with open(path, "wb") as f:
                f.write(img.getbuffer())

            prev = edited_main.at[idx, "image"] if pd.notna(edited_main.at[idx, "image"]) else ""
            new_list = list(set([*prev.split("|"), img.name]))
            edited_main.at[idx, "image"] = "|".join([x for x in new_list if x])

        if vid:
            path = os.path.join(MEDIA_FOLDER, vid.name)
            with open(path, "wb") as f:
                f.write(vid.getbuffer())

            prev = edited_main.at[idx, "video"] if pd.notna(edited_main.at[idx, "video"]) else ""
            new_list = list(set([*prev.split("|"), vid.name]))
            edited_main.at[idx, "video"] = "|".join([x for x in new_list if x])

    if st.button("💾 Save All Changes"):
        save_excels(edited_main, df_arch)
        st.success("Saved permanently!")

# ------------------------ EDITABLE ARCH ------------------------
elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Architecture Issues (Manual Save Mode)")

    temp_arch = st.session_state.get("temp_arch", df_arch.copy())
    edited_arch = st.experimental_data_editor(temp_arch, num_rows="dynamic")

    st.session_state["temp_arch"] = edited_arch

    st.subheader("Upload Media Per Row")

    for idx in edited_arch.index:
        st.markdown(f"### Row {idx+1}: {edited_arch.at[idx,'Issue']}")

        img = st.file_uploader(f"Upload Image (row {idx+1})", type=["png","jpg","jpeg"], key=f"img_arch_{idx}")
        vid = st.file_uploader(f"Upload Video (row {idx+1})", type=["mp4","mov"], key=f"vid_arch_{idx}")

        if img:
            path = os.path.join(MEDIA_FOLDER, img.name)
            with open(path, "wb") as f:
                f.write(img.getbuffer())

            prev = edited_arch.at[idx, "image"] if pd.notna(edited_arch.at[idx, "image"]) else ""
            new_list = list(set([*prev.split("|"), img.name]))
            edited_arch.at[idx, "image"] = "|".join([x for x in new_list if x])

        if vid:
            path = os.path.join(MEDIA_FOLDER, vid.name)
            with open(path, "wb") as f:
                f.write(vid.getbuffer())

            prev = edited_arch.at[idx, "video"] if pd.notna(edited_arch.at[idx, "video"]) else ""
            new_list = list(set([*prev.split("|"), vid.name]))
            edited_arch.at[idx, "video"] = "|".join([x for x in new_list if x])

    if st.button("💾 Save All Changes"):
        save_excels(df_main, edited_arch)
        st.success("Saved permanently!")

# ------------------------ FEEDBACK PAGE ------------------------
elif page == "✉️ User Feedback":
    st.header("✉️ User Feedback")

    with st.form("feedback_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submitted = st.form_submit_button("Submit")

        if submitted:
            df_feedback.loc[len(df_feedback)] = [name, email, feedback, pd.Timestamp.now()]
            save_feedback(df_feedback)
            st.success("Feedback saved!")

    st.subheader("Edit Previous Feedback")
    edited_fb = st.experimental_data_editor(df_feedback)
    if st.button("💾 Save Feedback Changes"):
        save_feedback(edited_fb)
        st.success("Saved!")
