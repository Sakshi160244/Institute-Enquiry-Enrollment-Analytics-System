import os
import streamlit as st
from pathlib import Path
from courses import courses
from database import (
    insert_enquiry,
    get_all_enquiries,
    update_enquiry_status,
    add_followup,
    get_followup_history,
    add_enrollment,
    get_enrollment_by_enquiry,
    add_payment,
    get_payment_history,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Institute Enquiry & Enrollment Analytics System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_DIR / "images"

# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "courses"

if "enquiry_course" not in st.session_state:
    st.session_state.enquiry_course = "Select Course"

if "admin_status_success" not in st.session_state:
    st.session_state.admin_status_success = None

# =========================================================
# COMPLETE APP CSS
# =========================================================

st.markdown(
    """
<style>
/* White page, professional blue text, light sidebar. */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
    background: #FFFFFF !important;
    color: #2563EB !important;
    color-scheme: light !important;
}
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
    background: transparent !important;
}
header[data-testid="stHeader"] {
    background: #FFFFFF !important;
    border-bottom: 1px solid #DBEAFE;
}
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stDecoration"] { background: #DBEAFE !important; }
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
    background: #F8FBFF !important;
}
section[data-testid="stSidebar"] { border-right: 1px solid #DBEAFE; }
h1, h2, h3 { color: #3B82F6 !important; }
h1 { font-weight: 750 !important; }
h2 { font-weight: 700 !important; }
h3 { font-weight: 650 !important; }
p, label, [data-testid="stWidgetLabel"] p { color: #2563EB !important; }
[data-testid="stCaptionContainer"] p { color: #52739C !important; }

/* Covers current Streamlit selectboxes AND older BaseWeb versions.
   Do not restrict selectors to div[data-baseweb="select"]:
   newer selectboxes no longer use that element. */
[data-testid="stSelectbox"],
[data-testid="stSelectbox"] :is(div, span, input, button, svg) {
    background: transparent !important;
    background-image: none !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    box-shadow: none !important;
    color-scheme: light !important;
}
/* Reset nested borders; the outer field gets exactly one border below. */
[data-testid="stSelectbox"] :is(div, input, button) {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
/* The direct control wrapper contains both the value and the arrow. */
[data-testid="stSelectbox"] > div:has([role="combobox"]),
[data-testid="stSelectbox"] > button[role="combobox"] {
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
}
[data-testid="stSelectbox"] > div:has([role="combobox"]):hover,
[data-testid="stSelectbox"] > button[role="combobox"]:hover {
    border-color: #3B82F6 !important;
}
[data-testid="stSelectbox"] > div:has([role="combobox"]):focus-within,
[data-testid="stSelectbox"] > button[role="combobox"]:focus-visible {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px #DBEAFE !important;
}
/* Arrow stays visible; its surrounding background is transparent. */
[data-testid="stSelectbox"] :is(button, [aria-hidden="true"]) {
    background: transparent !important;
    box-shadow: none !important;
}
[data-testid="stSelectbox"] svg {
    background: transparent !important;
    color: #2563EB !important;
    fill: currentColor !important;
}

/* Open menus are portaled outside the sidebar/form.
   Use white here so page text cannot show through the options. */
[data-testid="stSelectboxVirtualDropdown"],
[data-testid="stVirtualDropdown"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"], [role="listbox"] {
    background: #FFFFFF !important;
    color: #2563EB !important;
    color-scheme: light !important;
    border-radius: 8px !important;
}
[data-testid="stSelectboxVirtualDropdown"] *,
[data-testid="stVirtualDropdown"] *,
[role="listbox"] *, [role="option"], [role="option"] * {
    background-color: transparent !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
}
[role="listbox"], [data-testid="stSelectboxVirtualDropdown"] {
    border: 1px solid #BFDBFE !important;
    box-shadow: 0 5px 18px rgba(59, 130, 246, 0.12) !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"],
[role="option"]:focus, [role="option"][data-highlighted],
[data-testid="stSelectboxVirtualDropdown"] li:hover,
[data-testid="stVirtualDropdown"] li:hover {
    background: #EFF6FF !important;
}

/* Reset EVERY input wrapper, including current non-BaseWeb wrappers.
   Transparent input alone is insufficient when its parent is dark. */
:is([data-testid="stTextInput"], [data-testid="stTextArea"]),
:is([data-testid="stTextInput"], [data-testid="stTextArea"])
    :is(div, input, textarea, button, span) {
    background: transparent !important;
    background-image: none !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    caret-color: #2563EB !important;
    color-scheme: light !important;
}
/* Put one border around the complete field, not the inner input. */
[data-testid="stTextInput"] > div:has(input),
[data-testid="stTextArea"] > div:has(textarea) {
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] > div:has(input):hover,
[data-testid="stTextArea"] > div:has(textarea):hover {
    border-color: #60A5FA !important;
}
[data-testid="stTextInput"] > div:has(input):focus-within,
[data-testid="stTextArea"] > div:has(textarea):focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px #DBEAFE !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #6483A8 !important;
    -webkit-text-fill-color: #6483A8 !important;
    opacity: 1 !important;
}
[data-testid="stCheckbox"], [data-testid="stCheckbox"] label {
    background: transparent !important;
}

/* Light Enrollment Date and Final Fee fields */
[data-testid="stDateInput"] :is(div, input, button, span, svg),
[data-testid="stNumberInput"] :is(div, input, button, span, svg) {
    background: transparent !important;
    background-image: none !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    color-scheme: light !important;
    box-shadow: none !important;
}
[data-testid="stDateInput"] > div:has(input),
[data-testid="stNumberInput"] > div:has(input) {
    background: #FFFFFF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input {
    background: #FFFFFF !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: none !important;
    outline: none !important;
}
[data-testid="stDateInput"] button,
[data-testid="stNumberInput"] button {
    background: #EFF6FF !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: none !important;
}
[data-testid="stDateInput"] svg,
[data-testid="stNumberInput"] svg {
    color: #2563EB !important;
    fill: currentColor !important;
}

[data-testid="stCheckbox"] input { accent-color: #3B82F6; }
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-of-type {
    background: #FFFFFF !important;
    border-color: #93C5FD !important;
}
[data-testid="stCheckbox"] [data-baseweb="checkbox"]:has(input:checked) > span:first-of-type {
    background: #3B82F6 !important;
    border-color: #3B82F6 !important;
}
.stButton > button, .stFormSubmitButton > button {
    background: #3B82F6 !important;
    color: #FFFFFF !important;
    border: 1px solid #3B82F6 !important;
    border-radius: 8px !important;
    min-height: 42px;
    font-weight: 600;
    box-shadow: none;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #2563EB !important;
    border-color: #2563EB !important;
}
.stButton > button p, .stFormSubmitButton > button p {
    color: #FFFFFF !important;
}
[data-testid="stMetric"] {
    background: #F8FBFF !important;
    border: 1px solid #DBEAFE;
    padding: 15px;
    border-radius: 12px;
}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    color: #2563EB !important;
}
[data-testid="stAlert"] {
    background: #F8FBFF !important;
    border: 1px solid #DBEAFE;
    border-radius: 10px;
}
[data-testid="stForm"] { background: transparent !important; border: none !important; }
hr { border-color: #DBEAFE !important; }
a { color: #2563EB !important; }

/* =========================================================
   FINAL LIGHT-BLUE BORDER OVERRIDE
   Enrollment Date + Final Fee + Selectboxes
   ========================================================= */

/* Date input outer field */
[data-testid="stDateInput"] > div,
[data-testid="stDateInput"] > div > div {
    background: #FFFFFF !important;
    border-color: #BFDBFE !important;
    box-shadow: none !important;
}

[data-testid="stDateInput"] > div:has(input) {
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    box-shadow: none !important;
}

[data-testid="stDateInput"] input {
    background: #FFFFFF !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}

/* Number input / Final Fee outer field */
[data-testid="stNumberInput"] > div,
[data-testid="stNumberInput"] > div > div {
    background: #FFFFFF !important;
    border-color: #BFDBFE !important;
    box-shadow: none !important;
}

[data-testid="stNumberInput"] > div:has(input) {
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    box-shadow: none !important;
}

[data-testid="stNumberInput"] input {
    background: #FFFFFF !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}

/* Number +/- controls */
[data-testid="stNumberInput"] button {
    background: #EFF6FF !important;
    color: #2563EB !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Selectboxes: Batch + Enrollment Status */
[data-testid="stSelectbox"] > div:has([role="combobox"]),
[data-testid="stSelectbox"] > button[role="combobox"] {
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    box-shadow: none !important;
}

/* Keep the same light-blue border even on hover/focus */
[data-testid="stDateInput"] > div:has(input):hover,
[data-testid="stDateInput"] > div:has(input):focus-within,
[data-testid="stNumberInput"] > div:has(input):hover,
[data-testid="stNumberInput"] > div:has(input):focus-within,
[data-testid="stSelectbox"] > div:has([role="combobox"]):hover,
[data-testid="stSelectbox"] > div:has([role="combobox"]):focus-within,
[data-testid="stSelectbox"] > button[role="combobox"]:hover,
[data-testid="stSelectbox"] > button[role="combobox"]:focus-visible {
    border-color: #BFDBFE !important;
    box-shadow: none !important;
}


/* =========================================================
   COMPACT SIDEBAR SPACING
   ========================================================= */

/* Reduce overall top/bottom spacing inside sidebar */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1rem !important;
}

/* Reduce vertical gaps between sidebar elements */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.45rem !important;
}

/* Compact headings and captions */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p {
    margin-top: 0.15rem !important;
    margin-bottom: 0.15rem !important;
}

/* Reduce divider spacing */
section[data-testid="stSidebar"] hr {
    margin-top: 0.45rem !important;
    margin-bottom: 0.45rem !important;
}

/* Compact selectbox spacing */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] {
    margin-top: 0 !important;
    margin-bottom: 0.2rem !important;
}

/* Compact sidebar buttons */
section[data-testid="stSidebar"] .stButton {
    margin-top: 0 !important;
    margin-bottom: 0.15rem !important;
}

section[data-testid="stSidebar"] .stButton > button {
    min-height: 38px !important;
    padding-top: 0.35rem !important;
    padding-bottom: 0.35rem !important;
}

/* Keep captions close to their related controls */
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    margin-top: 0 !important;
    margin-bottom: 0.1rem !important;
}

</style>
""",
    unsafe_allow_html=True
)

# =========================================================
# SIDEBAR
# =========================================================


# =========================================================
# ADMIN AUTHENTICATION
# =========================================================

def get_admin_credentials():
    """Read admin credentials without hard-coding them in app.py."""
    username = None
    password = None

    try:
        username = st.secrets.get("ADMIN_USERNAME")
        password = st.secrets.get("ADMIN_PASSWORD")
    except Exception:
        pass

    if not username:
        username = os.getenv("ADMIN_USERNAME")

    if not password:
        password = os.getenv("ADMIN_PASSWORD")

    return username, password


def show_admin_login():
    st.subheader("🔐 Admin Login")

    st.write(
        "Only authorized institute administration can access "
        "enquiries, follow-ups and enrollments."
    )

    admin_username, admin_password = get_admin_credentials()

    if not admin_username or not admin_password:
        st.warning(
            "Admin credentials are not configured yet. "
            "Configure ADMIN_USERNAME and ADMIN_PASSWORD first."
        )
        return

    with st.form("admin_login_form"):
        username = st.text_input(
            "Username",
            key="admin_login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="admin_login_password"
        )

        login_button = st.form_submit_button(
            "Login",
            use_container_width=True
        )

    if login_button:
        if (
            username == admin_username
            and password == admin_password
        ):
            st.session_state.admin_logged_in = True
            st.success("✅ Admin login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")


def show_admin_logout():
    if st.button(
        "Logout",
        key="admin_logout_button",
        use_container_width=True
    ):
        st.session_state.admin_logged_in = False
        st.session_state.page = "courses"
        st.rerun()


if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


with st.sidebar:

    st.title("🎓 Institute")

    st.caption(
        "Enquiry & Enrollment Analytics System"
    )

    st.divider()

    # =====================================================
    # EXPLORE COURSES
    # =====================================================

    st.subheader(
        "📚 Explore Courses"
    )

    course_names = [
        "Select Course"
    ] + list(courses.keys())

    selected_course = st.selectbox(
        "Choose a Course",
        course_names,
        key="sidebar_course"
    )

    st.write(
        f"**Total Courses:** {len(courses)}"
    )

    st.caption(
        "Select any course to view complete course details."
    )

    if selected_course != "Select Course":

        if st.button(
            "View Course Details",
            use_container_width=True,
            key="view_course_button"
        ):

            st.session_state.page = "courses"

            st.rerun()

    # =====================================================
    # STUDENT ENQUIRY
    # =====================================================

    st.divider()

    st.subheader(
        "📝 Student Enquiry"
    )

    if st.button(
        "Student Enquiry Form",
        use_container_width=True,
        key="sidebar_enquiry_button"
    ):

        if selected_course != "Select Course":

            st.session_state.enquiry_course = selected_course

        else:

            st.session_state.enquiry_course = "Select Course"

        st.session_state.page = "enquiry"

        st.rerun()

    st.caption(
        "Submit an enquiry for any available course."
    )

    # =====================================================
    # ADMIN ENQUIRY MANAGEMENT
    # =====================================================

    st.divider()

    st.subheader(
        "👩‍💼 Admin"
    )

    if st.button(
        "Enquiry Management",
        use_container_width=True,
        key="admin_enquiry_button"
    ):

        st.session_state.page = "admin_enquiries"

        st.rerun()

    st.caption(
        "View submitted student enquiries."
    )

# =========================================================
# MAIN HEADER
# =========================================================

st.title(
    "Institute"
)

st.subheader(
    "Enquiry & Enrollment Analytics System"
)

st.write(
    "Explore professional computer, technology, "
    "analytics and creative courses."
)

st.divider()

# =========================================================
# STUDENT ENQUIRY PAGE
# =========================================================

if st.session_state.page == "enquiry":

    st.header(
        "📝 Student Enquiry Form"
    )

    st.write(
        "Fill in your details and select the course "
        "you are interested in."
    )

    st.info(
        "Fields marked with * are required."
    )

    st.write("")

    # =====================================================
    # COURSE OPTIONS
    # =====================================================

    enquiry_course_options = [
        "Select Course"
    ] + list(courses.keys())

    default_course = st.session_state.get(
        "enquiry_course",
        "Select Course"
    )

    if default_course not in enquiry_course_options:

        default_course = "Select Course"

    default_course_index = enquiry_course_options.index(
        default_course
    )

    # =====================================================
    # ENQUIRY FORM
    # =====================================================

    with st.form(
        "student_enquiry_form"
    ):

        # =================================================
        # NAME + EMAIL
        # =================================================

        col1, col2 = st.columns(2)

        with col1:

            full_name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name"
            )

        with col2:

            email = st.text_input(
                "Email Address *",
                placeholder="example@gmail.com"
            )

        # =================================================
        # PHONE + CITY
        # =================================================

        col3, col4 = st.columns(2)

        with col3:

            phone = st.text_input(
                "Phone Number *",
                placeholder="Enter 10-digit mobile number"
            )

        with col4:

            city = st.text_input(
                "City",
                placeholder="Enter your city"
            )

        # =================================================
        # QUALIFICATION + AGE
        # =================================================

        col5, col6 = st.columns(2)

        with col5:

            qualification = st.selectbox(
                "Qualification",
                [
                    "Select Qualification",
                    "10th",
                    "12th",
                    "Diploma",
                    "Graduate",
                    "Post Graduate",
                    "Other"
                ],
                key="qualification_select"
            )

        with col6:

            age_group = st.selectbox(
                "Age Group",
                [
                    "Select Age Group",
                    "Below 18",
                    "18-21",
                    "22-25",
                    "26-30",
                    "31+"
                ],
                key="age_group_select"
            )

        # =================================================
        # INTERESTED COURSE
        # =================================================

        interested_course = st.selectbox(
            "Interested Course *",
            enquiry_course_options,
            index=default_course_index,
            key="interested_course_select"
        )

        # =================================================
        # MODE + BATCH
        # =================================================

        col7, col8 = st.columns(2)

        with col7:

            learning_mode = st.selectbox(
                "Preferred Learning Mode *",
                [
                    "Select Mode",
                    "Online",
                    "Offline",
                    "Hybrid"
                ],
                key="learning_mode_select"
            )

        with col8:

            preferred_batch = st.selectbox(
                "Preferred Batch",
                [
                    "Select Batch",
                    "Morning",
                    "Afternoon",
                    "Evening",
                    "Weekend"
                ],
                key="preferred_batch_select"
            )

        # =================================================
        # LEAD SOURCE
        # =================================================

        lead_source = st.selectbox(
            "How did you hear about us?",
            [
                "Select Source",
                "Google Search",
                "Instagram",
                "Facebook",
                "LinkedIn",
                "YouTube",
                "Referral",
                "Walk-in",
                "Other"
            ],
            key="lead_source_select"
        )

        # =================================================
        # MESSAGE
        # =================================================

        message = st.text_area(
            "Message",
            placeholder=(
                "Tell us if you have any questions "
                "about the course..."
            ),
            height=120
        )

        # =================================================
        # CONSENT
        # =================================================

        consent = st.checkbox(
            "I agree to be contacted regarding my course enquiry."
        )

        st.write("")

        # =================================================
        # SUBMIT
        # =================================================

        submit_enquiry = st.form_submit_button(
            "Submit Enquiry",
            use_container_width=True
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    if submit_enquiry:

        clean_name = full_name.strip()

        clean_email = email.strip()

        clean_phone = phone.strip()

        if not clean_name:

            st.error(
                "Please enter your full name."
            )

        elif not clean_email:

            st.error(
                "Please enter your email address."
            )

        elif (
            "@" not in clean_email
            or "." not in clean_email
        ):

            st.error(
                "Please enter a valid email address."
            )

        elif not clean_phone:

            st.error(
                "Please enter your phone number."
            )

        elif (
            not clean_phone.isdigit()
            or len(clean_phone) != 10
        ):

            st.error(
                "Phone number must contain exactly 10 digits."
            )

        elif interested_course == "Select Course":

            st.error(
                "Please select a course."
            )

        elif learning_mode == "Select Mode":

            st.error(
                "Please select your preferred learning mode."
            )

        elif not consent:

            st.error(
                "Please accept the contact consent."
            )

        else:

            # Get the course ID for the selected course
            selected_course_id = courses[
                interested_course
            ]["course_id"]

            # Save the validated enquiry in MySQL
            enquiry_saved = insert_enquiry(
                student_name=clean_name,
                email=clean_email,
                phone=clean_phone,
                city=city.strip(),
                qualification=qualification,
                age_group=age_group,
                course_id=selected_course_id,
                learning_mode=learning_mode,
                preferred_batch=preferred_batch,
                lead_source=lead_source,
                message=message.strip()
            )

            if enquiry_saved:

                st.session_state.enquiry_course = interested_course

                st.success(
                    "✅ Your enquiry has been submitted successfully!"
                )

            else:

                st.error(
                    "Unable to save your enquiry. "
                    "Please try again."
                )

# =========================================================
# ADMIN ENQUIRY MANAGEMENT PAGE
# =========================================================

elif st.session_state.page == "admin_enquiries":
    if not st.session_state.admin_logged_in:
        show_admin_login()
    else:
        show_admin_logout()


        st.header(
            "👩‍💼 Admin Enquiry Management"
        )

        st.write(
            "View student enquiries submitted through the "
            "Student Enquiry Form."
        )

        st.write("")

        enquiries = get_all_enquiries()

        if not enquiries:

            st.info(
                "No student enquiries found."
            )

        else:

            total_enquiries = len(enquiries)

            new_enquiries = sum(
                1
                for enquiry in enquiries
                if enquiry["enquiry_status"] == "New"
            )

            unique_courses = len(
                {
                    enquiry["course_id"]
                    for enquiry in enquiries
                }
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Total Enquiries",
                    total_enquiries
                )

            with col2:

                st.metric(
                    "New Enquiries",
                    new_enquiries
                )

            with col3:

                st.metric(
                    "Courses with Enquiries",
                    unique_courses
                )

            st.divider()

            st.subheader(
                "Student Enquiries"
            )

            display_data = []

            for enquiry in enquiries:

                enquiry_date = enquiry["enquiry_date"]

                if enquiry_date:
                    enquiry_date = enquiry_date.strftime(
                        "%d-%m-%Y %I:%M %p"
                    )

                display_data.append(
                    {
                        "Enquiry ID": enquiry["enquiry_id"],
                        "Date": enquiry_date,
                        "Student Name": enquiry["student_name"],
                        "Email": enquiry["email"],
                        "Phone": enquiry["phone"],
                        "City": enquiry["city"],
                        "Qualification": enquiry["qualification"],
                        "Age Group": enquiry["age_group"],
                        "Course": enquiry["course_name"],
                        "Learning Mode": enquiry["learning_mode"],
                        "Preferred Batch": enquiry["preferred_batch"],
                        "Lead Source": enquiry["lead_source"],
                        "Status": enquiry["enquiry_status"],
                        "Message": enquiry["message"]
                    }
                )

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # =================================================
            # ENQUIRY STATUS + FOLLOW-UP
            # =================================================

            st.subheader(
                "Update Enquiry Status"
            )

            st.write(
                "Select an enquiry, update its status and "
                "save follow-up notes."
            )

            enquiry_options = {
                (
                    f"#{enquiry['enquiry_id']} - "
                    f"{enquiry['student_name']} - "
                    f"{enquiry['course_name']}"
                ): enquiry
                for enquiry in enquiries
            }

            selected_enquiry_label = st.selectbox(
                "Select Enquiry",
                list(enquiry_options.keys()),
                key="admin_selected_enquiry"
            )

            selected_enquiry = enquiry_options[
                selected_enquiry_label
            ]

            st.write(
                f"**Current Status:** "
                f"{selected_enquiry['enquiry_status']}"
            )

            status_options = [
                "New",
                "Contacted",
                "Follow-up",
                "Interested",
                "Converted",
                "Lost"
            ]

            current_status = selected_enquiry[
                "enquiry_status"
            ]

            if current_status in status_options:
                status_index = status_options.index(
                    current_status
                )
            else:
                status_index = 0

            with st.form(
                "admin_status_update_form"
            ):

                new_status = st.selectbox(
                    "New Status",
                    status_options,
                    index=status_index,
                    key="admin_new_status"
                )

                followup_notes = st.text_area(
                    "Follow-up Notes",
                    placeholder=(
                        "Add call details, student response, "
                        "next action or other follow-up notes..."
                    ),
                    height=120
                )

                update_status_button = st.form_submit_button(
                    "Update Status",
                    use_container_width=True
                )

            if st.session_state.admin_status_success:
                st.success(
                    st.session_state.admin_status_success
                )
                st.session_state.admin_status_success = None

            if update_status_button:

                status_updated = update_enquiry_status(
                    enquiry_id=selected_enquiry[
                        "enquiry_id"
                    ],
                    new_status=new_status
                )

                if status_updated:

                    followup_saved = add_followup(
                        enquiry_id=selected_enquiry[
                            "enquiry_id"
                        ],
                        followup_status=new_status,
                        notes=followup_notes.strip()
                    )

                    if followup_saved:

                        st.session_state.admin_status_success = (
                            "✅ Enquiry status and follow-up "
                            "saved successfully!"
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "Enquiry status was updated, but "
                            "the follow-up record could not be saved."
                        )

                else:

                    st.error(
                        "Unable to update enquiry status. "
                        "Please try again."
                    )


            st.divider()

            # =================================================
            # FOLLOW-UP HISTORY
            # =================================================

            st.subheader("Follow-up History")

            followup_history = get_followup_history(
                selected_enquiry["enquiry_id"]
            )

            if not followup_history:
                st.info(
                    "No follow-up history available for this enquiry."
                )
            else:
                history_data = []

                for followup in followup_history:
                    followup_date = followup["followup_date"]

                    if followup_date:
                        followup_date = followup_date.strftime(
                            "%d-%m-%Y %I:%M %p"
                        )

                    history_data.append(
                        {
                            "Date & Time": followup_date,
                            "Status": followup["followup_status"],
                            "Follow-up Notes": followup["notes"]
                        }
                    )

                st.dataframe(
                    history_data,
                    use_container_width=True,
                    hide_index=True
                )


            # =================================================
            # STUDENT ENROLLMENT
            # =================================================

            if selected_enquiry["enquiry_status"] == "Converted":

                st.divider()

                st.subheader(
                    "Student Enrollment"
                )

                existing_enrollment = get_enrollment_by_enquiry(
                    selected_enquiry["enquiry_id"]
                )

                if existing_enrollment:

                    st.success(
                        "✅ This student is already enrolled."
                    )

                    enrollment_date_display = existing_enrollment[
                        "enrollment_date"
                    ]

                    if enrollment_date_display:
                        enrollment_date_display = (
                            enrollment_date_display.strftime(
                                "%d-%m-%Y"
                            )
                        )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Enrollment ID",
                            existing_enrollment["enrollment_id"]
                        )

                    with col2:
                        st.metric(
                            "Enrollment Date",
                            enrollment_date_display
                        )

                    with col3:
                        st.metric(
                            "Enrollment Status",
                            existing_enrollment["enrollment_status"]
                        )

                    col4, col5, col6 = st.columns(3)

                    with col4:
                        st.metric(
                            "Batch",
                            existing_enrollment["batch"]
                        )

                    with col5:
                        st.metric(
                            "Final Fee",
                            f"₹{float(existing_enrollment['final_fee']):,.2f}"
                        )

                    with col6:
                        st.metric(
                            "Course ID",
                            existing_enrollment["course_id"]
                        )

                    # =========================================
                    # PAYMENT MANAGEMENT
                    # =========================================

                    st.divider()

                    st.subheader(
                        "Payment Management"
                    )

                    st.markdown(
                        f"""
                        **Student:** {selected_enquiry["student_name"]}  
                        **Course:** {selected_enquiry["course_name"]}  
                        **Enrollment ID:** {existing_enrollment["enrollment_id"]}
                        """
                    )

                    payment_history = get_payment_history(
                        existing_enrollment["enrollment_id"]
                    )

                    total_paid = sum(
                        float(payment["amount_paid"])
                        for payment in payment_history
                        if payment["payment_status"] == "Paid"
                    )

                    final_fee_value = float(
                        existing_enrollment["final_fee"] or 0
                    )

                    remaining_fee = max(
                        final_fee_value - total_paid,
                        0
                    )

                    pay_col1, pay_col2, pay_col3 = st.columns(3)

                    with pay_col1:
                        st.metric(
                            "Final Fee",
                            f"₹{final_fee_value:,.2f}"
                        )

                    with pay_col2:
                        st.metric(
                            "Total Paid",
                            f"₹{total_paid:,.2f}"
                        )

                    with pay_col3:
                        st.metric(
                            "Remaining Fee",
                            f"₹{remaining_fee:,.2f}"
                        )

                    if remaining_fee > 0:

                        with st.form(
                            "student_payment_form"
                        ):

                            payment_date = st.date_input(
                                "Payment Date",
                                key="payment_date"
                            )

                            amount_paid = st.number_input(
                                "Amount Paid (₹)",
                                min_value=0.0,
                                max_value=float(remaining_fee),
                                step=500.0,
                                format="%.2f",
                                key="amount_paid"
                            )

                            payment_method = st.selectbox(
                                "Payment Method",
                                [
                                    "Cash",
                                    "UPI",
                                    "Bank Transfer",
                                    "Card",
                                    "Other"
                                ],
                                key="payment_method"
                            )

                            payment_status = st.selectbox(
                                "Payment Status",
                                [
                                    "Paid",
                                    "Pending",
                                    "Failed"
                                ],
                                key="payment_status"
                            )

                            save_payment_button = st.form_submit_button(
                                "Save Payment",
                                use_container_width=True
                            )

                        if save_payment_button:

                            if amount_paid <= 0:

                                st.error(
                                    "Please enter a valid payment amount."
                                )

                            elif amount_paid > remaining_fee:

                                st.error(
                                    "Payment amount cannot be greater "
                                    "than the remaining fee."
                                )

                            else:

                                payment_saved = add_payment(
                                    enrollment_id=existing_enrollment[
                                        "enrollment_id"
                                    ],
                                    payment_date=payment_date,
                                    amount_paid=amount_paid,
                                    payment_method=payment_method,
                                    payment_status=payment_status
                                )

                                if payment_saved:

                                    st.success(
                                        "✅ Payment saved successfully!"
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        "Payment could not be saved."
                                    )

                    else:

                        st.success(
                            "✅ Full fee has been paid."
                        )

                    st.markdown(
                        "#### Payment History"
                    )

                    if payment_history:

                        payment_rows = []

                        for payment in payment_history:

                            payment_date_display = payment[
                                "payment_date"
                            ]

                            if payment_date_display:
                                payment_date_display = (
                                    payment_date_display.strftime(
                                        "%d-%m-%Y"
                                    )
                                )

                            payment_rows.append(
                                {
                                    "Payment ID": payment["payment_id"],
                                    "Student Name": selected_enquiry["student_name"],
                                    "Course": selected_enquiry["course_name"],
                                    "Date": payment_date_display,
                                    "Amount Paid": (
                                        f"₹{float(payment['amount_paid']):,.2f}"
                                    ),
                                    "Method": payment["payment_method"],
                                    "Status": payment["payment_status"]
                                }
                            )

                        st.dataframe(
                            payment_rows,
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.info(
                            "No payment has been recorded yet."
                        )

                else:

                    st.write(
                        "This enquiry has been converted. "
                        "Complete the enrollment details below."
                    )

                    with st.form(
                        "student_enrollment_form"
                    ):

                        col1, col2 = st.columns(2)

                        with col1:

                            st.text_input(
                                "Student Name",
                                value=selected_enquiry["student_name"],
                                disabled=True
                            )

                        with col2:

                            st.text_input(
                                "Course",
                                value=selected_enquiry["course_name"],
                                disabled=True
                            )

                        col3, col4 = st.columns(2)

                        with col3:

                            enrollment_date = st.date_input(
                                "Enrollment Date"
                            )

                        with col4:

                            enrollment_batch = st.selectbox(
                                "Batch",
                                [
                                    "Morning",
                                    "Afternoon",
                                    "Evening",
                                    "Weekend"
                                ],
                                key="enrollment_batch"
                            )

                        final_fee = st.number_input(
                            "Final Fee (₹)",
                            min_value=0.0,
                            step=500.0,
                            format="%.2f"
                        )

                        enrollment_status = st.selectbox(
                            "Enrollment Status",
                            [
                                "Active",
                                "Completed",
                                "Cancelled"
                            ],
                            key="enrollment_status"
                        )

                        save_enrollment_button = st.form_submit_button(
                            "Save Enrollment",
                            use_container_width=True
                        )

                    if save_enrollment_button:

                        if final_fee <= 0:

                            st.error(
                                "Please enter a valid final fee."
                            )

                        else:

                            enrollment_saved = add_enrollment(
                                enquiry_id=selected_enquiry["enquiry_id"],
                                course_id=selected_enquiry["course_id"],
                                enrollment_date=enrollment_date,
                                batch=enrollment_batch,
                                final_fee=final_fee,
                                enrollment_status=enrollment_status
                            )

                            if enrollment_saved:

                                st.success(
                                    "✅ Student enrollment saved successfully!"
                                )

                                st.rerun()

                            else:

                                st.warning(
                                    "Enrollment could not be saved. "
                                    "This enquiry may already be enrolled."
                                )


    # =========================================================
    # COURSES PAGE
    # =========================================================

elif st.session_state.page == "courses":

    # =====================================================
    # NO COURSE SELECTED
    # =====================================================

    if selected_course == "Select Course":

        st.header(
            "Explore Our Courses"
        )

        st.write(
            "Choose a course from the left sidebar "
            "to view complete course information."
        )

        st.info(
            "👈 Select a course from the "
            "**Explore Courses** menu."
        )

        st.write("")

        # =================================================
        # HOME METRICS
        # =================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Available Courses",
                len(courses)
            )

        with col2:

            st.metric(
                "Learning Modes",
                "Online / Offline"
            )

        with col3:

            st.metric(
                "Learning Areas",
                "Multiple"
            )

    # =====================================================
    # COURSE SELECTED
    # =====================================================

    else:

        course = courses[
            selected_course
        ]

        # =================================================
        # IMAGE + DETAILS
        # =================================================

        image_column, detail_column = st.columns(
            [1, 2]
        )

        with image_column:

            image_path = (
                IMAGES_DIR
                / course["image"]
            )

            if image_path.exists():

                st.image(
                    str(image_path),
                    width=300
                )

            else:

                st.warning(
                    "Course image not found."
                )

                st.code(
                    str(image_path)
                )

        with detail_column:

            st.header(
                selected_course
            )

            st.write(
                course[
                    "short_description"
                ]
            )

            st.write(
                f"**Category:** "
                f"{course['category']}"
            )

            st.write(
                f"**Duration:** "
                f"{course['duration']}"
            )

            st.write(
                f"**Level:** "
                f"{course['level']}"
            )

            st.write(
                "**Learning Mode:** "
                + " / ".join(
                    course["mode"]
                )
            )

        st.divider()

        # =================================================
        # COURSE INFORMATION
        # =================================================

        st.subheader(
            "Course Information"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Course ID",
                course["course_id"]
            )

        with col2:

            st.metric(
                "Duration",
                course["duration"]
            )

        with col3:

            st.metric(
                "Level",
                course["level"]
            )

        with col4:

            st.metric(
                "Mode",
                " / ".join(
                    course["mode"]
                )
            )

        st.divider()

        # =================================================
        # COURSE OVERVIEW
        # =================================================

        st.subheader(
            "Course Overview"
        )

        st.write(
            course[
                "short_description"
            ]
        )

        st.write("")

        # =================================================
        # TOOLS + SKILLS
        # =================================================

        tools_column, skills_column = st.columns(
            2
        )

        with tools_column:

            st.subheader(
                "Tools & Technologies"
            )

            for tool in course[
                "tools"
            ]:

                st.write(
                    f"✓ {tool}"
                )

        with skills_column:

            st.subheader(
                "Skills You Will Learn"
            )

            for skill in course[
                "skills"
            ]:

                st.write(
                    f"✓ {skill}"
                )

        st.divider()

        # =================================================
        # COURSE CURRICULUM
        # =================================================

        st.subheader(
            "Course Curriculum"
        )

        for number, module in enumerate(
            course["modules"],
            start=1
        ):

            st.write(
                f"**{number}.** {module}"
            )

        st.divider()

        # =================================================
        # CAREER OPPORTUNITIES
        # =================================================

        st.subheader(
            "Career Opportunities"
        )

        for career in course[
            "career"
        ]:

            st.write(
                f"✓ {career}"
            )

        st.write("")

        # =================================================
        # ENQUIRY BUTTON
        # =================================================

        if st.button(
            "📝 Enquire About This Course",
            use_container_width=True,
            key="course_enquiry_button"
        ):

            st.session_state.enquiry_course = selected_course

            st.session_state.page = "enquiry"

            st.rerun()