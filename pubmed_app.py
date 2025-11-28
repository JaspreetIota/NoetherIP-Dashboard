import streamlit as st
import pandas as pd
import numpy as np   # <-- REQUIRED
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

    df_main = pd.read_excel(EXCEL_PATH,
                            sheet_name=xls.sheet_names[sheet_names.index("uat_issues")]) \
                if "uat_issues" in sheet_names else pd.DataFrame()

    df_arch = pd.read_excel(EXCEL_PATH,
                            sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")]) \
                if "architecture_issues" in sheet_names else pd.DataFrame()

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

        required_columns_main = ["Sno.","Date","Issue", *CLIENT_COLUMNS]
        if not all(col in st.session_state.df_main.columns for col in required_columns_main):
            st.warning("Uploaded UAT sheet is missing required columns!")

    except Exception as e:
        st.error(f"Error loading Excel: {e}")


# ======================================================================
#                                DASHBOARD
# ======================================================================
if page == "📊 Dashboard":

    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])
    df = st.session_state.df_main.copy() if dashboard_type == "UAT Issues" else st.session_state.df_arch.copy()

    st.header(f"📊 {dashboard_type} Dashboard")

    # -------- FILTERS --------
    type_options = df["Type"].dropna().unique().tolist() if "Type" in df.columns else []
    selected_types = st.multiselect("Filter by Type", type_options, default=type_options)

    if selected_types:
        df = df[df["Type"].isin(selected_types)]

    if dashboard_type == "UAT Issues":
        client_options = [c for c in CLIENT_COLUMNS if c in df.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options)

        if selected_clients:
            df = df[df[selected_clients].eq("Yes").all(axis=1)]

    else:
        status_options = df["Status"].dropna().unique().tolist() if "Status" in df.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)

        if selected_status:
            df = df[df["Status"].isin(selected_status)]

    # -------- TABLE --------
    columns_to_show = st.multiselect("Select columns to display",
                                     df.columns.tolist(),
                                     default=df.columns.tolist())

    st.dataframe(df[columns_to_show], use_container_width=True)

    # -------- MEDIA VIEWER --------
    with st.expander("📂 Media Viewer"):
        for idx, row in df.iterrows():
            st.markdown(f"**S.No {row.get('Sno.', '')} — {row.get('Issue', '')}**")

            # Images
            for img in set(str(row.get("image", "")).split("|")):
                img = img.strip()
                path = os.path.join(MEDIA_FOLDER, img)
                if img and os.path.exists(path):
                    st.image(path)

            # Videos
            for vid in set(str(row.get("video", "")).split("|")):
                vid = vid.strip()
                path = os.path.join(MEDIA_FOLDER, vid)
                if vid and os.path.exists(path):
                    st.video(path)

    # -------- FIXED CHART BLOCK (SAFE) --------
    st.subheader("📈 Predefined Charts")

    # Type Chart
    if "Type" in df.columns:
        type_counts = df["Type"].dropna().value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]

        if not type_counts.empty:
            fig = px.bar(type_counts, x="Type", y="Count", title="Issues by Type")
            st.plotly_chart(fig)
        else:
            st.info("No data for 'Issues by Type'")

    # Status Chart (Only if exists)
    if "Status" in df.columns:
        status_counts = df["Status"].dropna().value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        if not status_counts.empty:
            fig = px.pie(status_counts, names="Status", values="Count", title="Status Counts")
            st.plotly_chart(fig)
        else:
            st.info("No data for 'Status Counts'")

    # -------- CUSTOM CHARTS --------
    st.subheader("📊 Custom Chart")

    chart_col = st.selectbox("Select column", df.columns.tolist())
    chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"])

    try:
        if chart_type == "Bar":
            fig = px.bar(df, x=chart_col, title=f"{chart_col} (Bar Chart)")
        elif chart_type == "Pie":
            fig = px.pie(df, names=chart_col, title=f"{chart_col} (Pie Chart)")
        else:
            fig = px.histogram(df, x=chart_col, title=f"{chart_col} (Histogram)")

        st.plotly_chart(fig)

    except:
        st.warning("Chart cannot be displayed for this column.")


# ======================================================================
#                        UAT ISSUES EDITABLE PAGE
# ======================================================================
elif page == "📋 UAT Issues (Editable)":

    st.header("📋 Edit UAT Issues")

    save_clicked = st.button("💾 Save Changes")

    edited_main = st.experimental_data_editor(
        st.session_state.df_main,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---------------- MEDIA UPLOAD PER ROW ----------------
    for idx in edited_main.index:
        col1, col2 = st.columns(2)

        with col1:
            img_file = st.file_uploader(
                f"Upload Image for row {idx}",
                type=["png", "jpg", "jpeg"],
                key=f"uat_img_{idx}"
            )
            if img_file:
                img_path = os.path.join(MEDIA_FOLDER, img_file.name)
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())

                existing_images = str(edited_main.at[idx, "image"]) if pd.notna(edited_main.at[idx, "image"]) else ""
                updated_images = list(filter(None, existing_images.split("|"))) + [img_file.name]
                edited_main.at[idx, "image"] = "|".join(sorted(set(updated_images)))

        with col2:
            vid_file = st.file_uploader(
                f"Upload Video for row {idx}",
                type=["mp4", "mov"],
                key=f"uat_vid_{idx}"
            )
            if vid_file:
                vid_path = os.path.join(MEDIA_FOLDER, vid_file.name)
                with open(vid_path, "wb") as f:
                    f.write(vid_file.getbuffer())

                existing_videos = str(edited_main.at[idx, "video"]) if pd.notna(edited_main.at[idx, "video"]) else ""
                updated_videos = list(filter(None, existing_videos.split("|"))) + [vid_file.name]
                edited_main.at[idx, "video"] = "|".join(sorted(set(updated_videos)))

    # ---------------- SAVE ----------------
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

    edited_arch = st.experimental_data_editor(
        st.session_state.df_arch,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---------------- MEDIA UPLOAD PER ROW ----------------
    for idx in edited_arch.index:
        col1, col2 = st.columns(2)

        with col1:
            img_file = st.file_uploader(
                f"Upload Image for row {idx}",
                type=["png", "jpg", "jpeg"],
                key=f"arch_img_{idx}"
            )
            if img_file:
                img_path = os.path.join(MEDIA_FOLDER, img_file.name)
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())

                existing_images = str(edited_arch.at[idx, "image"]) if pd.notna(edited_arch.at[idx, "image"]) else ""
                updated_images = list(filter(None, existing_images.split("|"))) + [img_file.name]
                edited_arch.at[idx, "image"] = "|".join(sorted(set(updated_images)))

        with col2:
            vid_file = st.file_uploader(
                f"Upload Video for row {idx}",
                type=["mp4", "mov"],
                key=f"arch_vid_{idx}"
            )
            if vid_file:
                vid_path = os.path.join(MEDIA_FOLDER, vid_file.name)
                with open(vid_path, "wb") as f:
                    f.write(vid_file.getbuffer())

                existing_videos = str(edited_arch.at[idx, "video"]) if pd.notna(edited_arch.at[idx, "video"]) else ""
                updated_videos = list(filter(None, existing_videos.split("|"))) + [vid_file.name]
                edited_arch.at[idx, "video"] = "|".join(sorted(set(updated_videos)))

    # ---------------- SAVE BUTTON ----------------
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

    edited_fb = st.experimental_data_editor(
        st.session_state.df_feedback, num_rows="dynamic"
    )

    if st.button("💾 Save Feedback Changes"):
        st.session_state.df_feedback = edited_fb
        save_feedback(st.session_state.df_feedback)
        st.success("Changes saved!")

    buf = BytesIO()
    st.session_state.df_feedback.to_excel(buf, index=False)
    buf.seek(0)

    st.download_button("⬇ Download Feedback", buf, "user_feedback.xlsx")

# ======================================================================
#                        SUPPORT TICKETS PAGE  🎫
# ======================================================================
elif page == "🎫 Support Tickets":

    st.title("🎫 Support Tickets Dashboard")
    st.write(
        """
        Manage and track your internal support tickets.
        Create tickets, edit existing ones, visualize stats, 
        and download/export reports.
        """
    )

    # ---------- INITIALIZE SESSION DF ----------
    if "tickets_df" not in st.session_state:

        # Fake data for first-time initialization
        np.random.seed(42)
        issue_descriptions = [
            "Network connectivity issues in the office",
            "Software application crashing on startup",
            "Printer not responding to print commands",
            "Email server downtime",
            "Data backup failure",
            "Login authentication problems",
            "Website performance degradation",
            "Security vulnerability identified",
            "Hardware malfunction in the server room",
            "Employee unable to access shared files",
            "Database connection failure",
            "Mobile application not syncing data",
            "VoIP phone system issues",
            "VPN connection problems for remote employees",
            "System updates causing compatibility issues",
            "File server running out of storage space",
            "Intrusion detection system alerts",
            "Inventory management system errors",
            "Customer data not loading in CRM",
            "Collaboration tool not sending notifications",
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

    df_tickets = st.session_state.tickets_df

    # ===================================================================
    #                           ADD A TICKET
    # ===================================================================
    st.header("Add a Ticket")

    with st.form("add_ticket_form"):
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

    if submitted:
        recent_number = int(max(df_tickets.ID).split("-")[1])
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        df_new = pd.DataFrame([{
            "ID": f"TICKET-{recent_number + 1}",
            "Issue": issue,
            "Status": "Open",
            "Priority": priority,
            "Date Submitted": today,
        }])

        st.success("Ticket submitted!")
        st.dataframe(df_new, use_container_width=True)

        st.session_state.tickets_df = pd.concat([df_new, df_tickets], ignore_index=True)

    # ===================================================================
    #                       EXISTING TICKETS TABLE
    # ===================================================================
    st.header("Existing Tickets")
    st.write(f"Number of tickets: `{len(df_tickets)}`")

    edited_df = st.data_editor(
        df_tickets,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                options=["Open", "In Progress", "Closed"]
            ),
            "Priority": st.column_config.SelectboxColumn(
                options=["High", "Medium", "Low"]
            ),
        },
        disabled=["ID", "Date Submitted"],
    )

    st.session_state.tickets_df = edited_df

    # ===================================================================
    #                       DOWNLOAD TICKETS
    # ===================================================================
    st.subheader("⬇ Download All Tickets")

    ticket_buf = BytesIO()
    edited_df.to_excel(ticket_buf, index=False)
    ticket_buf.seek(0)

    st.download_button("Download Tickets (.xlsx)", ticket_buf, "support_tickets.xlsx")

    # ===================================================================
    #                           STATISTICS
    # ===================================================================
    st.header("Statistics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Open Tickets", len(edited_df[edited_df.Status == "Open"]))
    col2.metric("Avg Response Time (hrs)", 5.2, delta=-1.5)
    col3.metric("Avg Resolution Time (hrs)", 16, delta=2)

    # ===================================================================
    #                       CUSTOM CHARTS (YOUR REQUIREMENT)
    # ===================================================================
    st.subheader("📊 Custom Chart")

    chart_col = st.selectbox("Select column to chart", edited_df.columns)
    chart_type = st.selectbox("Chart type", ["Bar", "Pie", "Histogram"])

    try:
        if chart_type == "Bar":
            fig = px.bar(edited_df, x=chart_col)
        elif chart_type == "Pie":
            fig = px.pie(edited_df, names=chart_col)
        else:
            fig = px.histogram(edited_df, x=chart_col)

        st.plotly_chart(fig)
    except Exception as e:
        st.warning(f"Chart cannot be displayed: {e}")

    # ===================================================================
    #                      ALTAIR PLOTS (Original)
    # ===================================================================
    st.subheader("📈 Ticket Status Per Month")

    status_plot = (
        alt.Chart(edited_df)
        .mark_bar()
        .encode(
            x="month(Date Submitted):O",
            y="count():Q",
            xOffset="Status:N",
            color="Status:N",
        )
    )
    st.altair_chart(status_plot, use_container_width=True)

    st.subheader("📈 Ticket Priority Breakdown")

    priority_plot = (
        alt.Chart(edited_df)
        .mark_arc()
        .encode(
            theta="count():Q",
            color="Priority:N"
        )
    )
    st.altair_chart(priority_plot, use_container_width=True)

