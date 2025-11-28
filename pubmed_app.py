import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import random
from io import BytesIO
import plotly.express as px
import altair as alt

st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Noether IP Status")

# ------------------------ CONFIG ------------------------
EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_PATH = "user_feedback.xlsx"
CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ------------------------ UTILITIES ------------------------
@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        df_main = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue", *CLIENT_COLUMNS,
                                        "image","video","remarks","dev status"])
        df_arch = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue","Status",
                                        "image","video","remarks","dev status"])
        return df_main, df_arch

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues") if "uat_issues" in sheet_names else pd.DataFrame()
    df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues") if "architecture_issues" in sheet_names else pd.DataFrame()

    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()
    return df_main, df_arch


def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)


def load_feedback():
    return pd.read_excel(FEEDBACK_PATH) if os.path.exists(FEEDBACK_PATH) \
        else pd.DataFrame(columns=["Name","Email","Feedback","Date"])


def save_feedback(df_fb):
    df_fb.to_excel(FEEDBACK_PATH, index=False)

# ------------------------ SESSION STATE INIT ------------------------
if "df_main" not in st.session_state:
    st.session_state.df_main, st.session_state.df_arch = load_excel()

if "df_feedback" not in st.session_state:
    st.session_state.df_feedback = load_feedback()

if "tickets_df" not in st.session_state:
    # Initialize fake support tickets
    np.random.seed(42)
    issue_descriptions = [
        "Network connectivity issues", "Software crash", "Printer issue", "Email server downtime",
        "Data backup failure", "Login problems", "Website slow", "Security alert",
        "Hardware malfunction", "Cannot access shared files", "DB connection failure",
        "Mobile app not syncing", "VoIP phone issues", "VPN connection problem",
        "System update error", "File server storage full", "IDS alerts",
        "Inventory system errors", "CRM data missing", "Collaboration tool notifications"
    ]
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Issue": np.random.choice(issue_descriptions, size=100),
        "Status": np.random.choice(["Open", "In Progress", "Closed"], size=100),
        "Priority": np.random.choice(["High", "Medium", "Low"], size=100),
        "Date Submitted": [
            datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182))
            for _ in range(100)
        ],
    }
    st.session_state.tickets_df = pd.DataFrame(data)

# ------------------------ SIDEBAR PAGE SELECTOR ------------------------
page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "✉️ User Feedback", "🎫 Support Tickets"]
)

# ------------------------ EXCEL UPLOAD ------------------------
uploaded_file = st.file_uploader("Upload Excel to update tables", type=["xlsx"])
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = [s.lower() for s in xls.sheet_names]

        if "uat_issues" in sheet_names:
            st.session_state.df_main = pd.read_excel(uploaded_file, sheet_name="uat_issues")
        if "architecture_issues" in sheet_names:
            st.session_state.df_arch = pd.read_excel(uploaded_file, sheet_name="architecture_issues")
        st.success("Excel loaded successfully!")
    except Exception as e:
        st.error(f"Error loading Excel: {e}")

# ======================================================================
#                                DASHBOARD
# ======================================================================
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])
    df_dashboard = st.session_state.df_main.copy() if dashboard_type == "UAT Issues" else st.session_state.df_arch.copy()
    
    st.header(f"📊 {dashboard_type} Dashboard")

    # -------- FILTERS --------
    if "Type" in df_dashboard.columns:
        selected_types = st.multiselect("Filter by Type", df_dashboard["Type"].dropna().unique(), default=None)
        if selected_types:
            df_dashboard = df_dashboard[df_dashboard["Type"].isin(selected_types)]

    if dashboard_type == "UAT Issues":
        client_options = [c for c in CLIENT_COLUMNS if c in df_dashboard.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options)
        if selected_clients:
            df_dashboard = df_dashboard[df_dashboard[selected_clients].eq("Yes").all(axis=1)]
    else:
        if "Status" in df_dashboard.columns:
            selected_status = st.multiselect("Filter by Status", df_dashboard["Status"].dropna().unique())
            if selected_status:
                df_dashboard = df_dashboard[df_dashboard["Status"].isin(selected_status)]

    # -------- TABLE --------
    columns_to_show = st.multiselect("Select columns to display", df_dashboard.columns.tolist(), default=df_dashboard.columns.tolist())
    st.dataframe(df_dashboard[columns_to_show], use_container_width=True)

    # -------- DASHBOARD STATISTICS --------
    st.subheader("📌 Statistics Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Issues", len(df_dashboard))
    col2.metric("Unique Types", df_dashboard["Type"].nunique() if "Type" in df_dashboard.columns else "N/A")
    col3.metric("Resolved Issues", df_dashboard["dev status"].str.lower().eq("resolved").sum() if "dev status" in df_dashboard.columns else "N/A")

    # -------- CUSTOM CHARTS --------
    st.subheader("📊 Custom Chart")
    chart_col = st.selectbox("Select column to chart", df_dashboard.columns)
    chart_type = st.selectbox("Chart type", ["Bar", "Pie", "Histogram"])
    try:
        if chart_type == "Bar":
            fig = px.bar(df_dashboard, x=chart_col)
        elif chart_type == "Pie":
            fig = px.pie(df_dashboard, names=chart_col)
        else:
            fig = px.histogram(df_dashboard, x=chart_col)
        st.plotly_chart(fig)
    except Exception as e:
        st.warning(f"Chart cannot be displayed: {e}")

# ======================================================================
#                        UAT ISSUES EDITABLE PAGE
# ======================================================================
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")
    save_clicked = st.button("💾 Save Changes")
    edited_main = st.experimental_data_editor(st.session_state.df_main, num_rows="dynamic", use_container_width=True)

    if save_clicked:
        st.session_state.df_main = edited_main
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("UAT Issues saved!")

# ======================================================================
#                   ARCHITECTURE ISSUES EDITABLE PAGE
# ======================================================================
elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")
    save_clicked = st.button("💾 Save Changes")
    edited_arch = st.experimental_data_editor(st.session_state.df_arch, num_rows="dynamic", use_container_width=True)

    if save_clicked:
        st.session_state.df_arch = edited_arch
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("Architecture Issues saved!")

# ======================================================================
#                            USER FEEDBACK PAGE
# ======================================================================
elif page == "✉️ User Feedback":
    st.header("✉️ User Feedback")
    with st.form("fb_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submit = st.form_submit_button("Submit")
        if submit:
            st.session_state.df_feedback.loc[len(st.session_state.df_feedback)] = [
                name, email, feedback, pd.Timestamp.now()
            ]
            save_feedback(st.session_state.df_feedback)
            st.success("Feedback submitted!")

    edited_fb = st.experimental_data_editor(st.session_state.df_feedback, num_rows="dynamic")
    if st.button("💾 Save Feedback Changes"):
        st.session_state.df_feedback = edited_fb
        save_feedback(st.session_state.df_feedback)
        st.success("Changes saved!")

    buf = BytesIO()
    st.session_state.df_feedback.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button("⬇ Download Feedback", buf, "user_feedback.xlsx")

# ======================================================================
#                        SUPPORT TICKETS PAGE
# ======================================================================
elif page == "🎫 Support Tickets":
    st.title("🎫 Support Tickets Dashboard")
    df_tickets = st.session_state.tickets_df

    # ---------- ADD A TICKET ----------
    st.header("Add a Ticket")
    with st.form("add_ticket_form"):
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")
    if submitted:
        recent_number = int(max(df_tickets.ID).str.split("-").str[1]) if len(df_tickets) > 0 else 1000
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        df_new = pd.DataFrame([{
            "ID": f"TICKET-{recent_number + 1}",
            "Issue": issue,
            "Status": "Open",
            "Priority": priority,
            "Date Submitted": today,
        }])
        st.session_state.tickets_df = pd.concat([df_new, df_tickets], ignore_index=True)
        st.success("Ticket submitted!")
        st.dataframe(df_new, use_container_width=True)

    # ---------- EXISTING TICKETS ----------
    st.header("Existing Tickets")
    edited_df = st.data_editor(
        st.session_state.tickets_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(options=["Open","In Progress","Closed"]),
            "Priority": st.column_config.SelectboxColumn(options=["High","Medium","Low"]),
        },
        disabled=["ID","Date Submitted"],
    )
    st.session_state.tickets_df = edited_df

    # ---------- DOWNLOAD ----------
    buf = BytesIO()
    edited_df.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button("⬇ Download Tickets", buf, "support_tickets.xlsx")

    # ---------- STATISTICS ----------
    st.subheader("📌 Tickets Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", len(edited_df))
    col2.metric("Open Tickets", len(edited_df[edited_df["Status"]=="Open"]))
    col3.metric("Closed Tickets", len(edited_df[edited_df["Status"]=="Closed"]))

    # ---------- CUSTOM CHART ----------
    st.subheader("📊 Custom Chart")
    chart_col = st.selectbox("Select column", edited_df.columns)
    chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"])
    try:
        if chart_type=="Bar":
            fig = px.bar(edited_df, x=chart_col)
        elif chart_type=="Pie":
            fig = px.pie(edited_df, names=chart_col)
        else:
            fig = px.histogram(edited_df, x=chart_col)
        st.plotly_chart(fig)
    except Exception as e:
        st.warning(f"Cannot generate chart: {e}")
