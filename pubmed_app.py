import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image
from io import BytesIO

EXCEL_PATH = "uat_issues.xlsx"


# -------------------------
# Utility Functions
# -------------------------
@st.cache_data(ttl=5)
def load_excel():
    """Loads Excel file and returns both sheets."""
    df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues")
    df_arch = pd.read_excel(EXCEL_PATH, sheet_name="Architecture_Issues")
    return df_main, df_arch


def save_excel(df_main, df_arch):
    """Save updated data back to Excel."""
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl') as writer:
        df_main.to_excel(writer, sheet_name="UAT_Issues", index=False)
        df_arch.to_excel(writer, sheet_name="Architecture_Issues", index=False)


def get_file_timestamp():
    """Returns last modified timestamp to auto-refresh."""
    return os.path.getmtime(EXCEL_PATH)


# -------------------------
# Streamlit App Layout
# -------------------------
st.set_page_config(page_title="UAT Bug Tracker", layout="wide")

st.title("🧪 UAT Bug & Issue Tracker")

page = st.sidebar.radio(
    "Navigation",
    ("📊 Dashboard", "📋 Editable Table – Main Issues", "🏗️ Architecture Issues")
)

# Monitor file change
st.sidebar.write("Excel last updated:", get_file_timestamp())

df_main, df_arch = load_excel()


# ============================================================
# PAGE 1 — DASHBOARD
# ============================================================
if page == "📊 Dashboard":
    st.header("Interactive Dashboard")

    # --- Filters ---
    type_filter = st.multiselect("Filter by Type", df_main["Type"].unique())
    client_cols = [col for col in df_main.columns if col not in [
        "SNo", "Date", "Repetitive Count", "Repetitive Dates",
        "Type", "Issue", "Image", "Remarks", "Dev Status"
    ]]

    client_filter = st.multiselect("Filter by Client Status", client_cols)

    filtered_df = df_main.copy()

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"].isin(type_filter)]

    if client_filter:
        filtered_df = filtered_df[filtered_df[client_filter].eq("Yes").all(axis=1)]

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.histogram(filtered_df, x="Type", title="Issues by Type")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        if client_cols:
            mdf = filtered_df[client_cols].apply(lambda x: (x == "Yes").sum())
            fig2 = px.bar(mdf, title="Client-Wise Resolved Count")
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Complete Filtered Table")
    st.dataframe(filtered_df)

    # Image Preview
    st.subheader("Image Preview")
    issue_id = st.number_input("Enter SNo to preview image:", min_value=1)
    img_row = df_main[df_main["SNo"] == issue_id]

    if not img_row.empty and isinstance(img_row["Image"].iloc[0], str):
        try:
            img = Image.open(img_row["Image"].iloc[0])
            st.image(img, width=600)
        except:
            st.warning("Image path not accessible.")


# ============================================================
# PAGE 2 — MAIN SHEET EDITOR
# ============================================================
if page == "📋 Editable Table – Main Issues":

    st.header("Edit Main UAT Issues")

    edited_df = st.experimental_data_editor(
        df_main,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Changes"):
        save_excel(edited_df, df_arch)
        st.success("Excel updated successfully!")


    # Download
    st.download_button(
        "⬇️ Download Updated Excel",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="UAT_Issues_Updated.xlsx"
    )


# ============================================================
# PAGE 3 — ARCHITECTURE ISSUES
# ============================================================
if page == "🏗️ Architecture Issues":

    st.header("Architecture Specific Issues")

    edited_df = st.experimental_data_editor(
        df_arch,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Architecture Sheet"):
        save_excel(df_main, edited_df)
        st.success("Architecture Issues Updated!")

    st.download_button(
        "⬇️ Download Architecture Excel",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="Architecture_Issues.xlsx"
    )
