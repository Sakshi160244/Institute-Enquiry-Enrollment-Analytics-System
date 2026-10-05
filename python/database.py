import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error

from courses import courses


# =========================================================
# DATABASE CONNECTION
# =========================================================

def _get_secret(name, default=None):
    """
    Read value from Streamlit secrets first.
    If not available, read from environment variables.
    """

    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]

    except Exception:
        pass

    return os.getenv(name, default)


def create_connection():

    try:

        project_dir = Path(__file__).resolve().parent.parent

        ca_path = project_dir / "certs" / "ca.pem"

        connection = mysql.connector.connect(
            host=_get_secret("DB_HOST"),
            port=int(_get_secret("DB_PORT", 3306)),
            user=_get_secret("DB_USER"),
            password=_get_secret("DB_PASSWORD"),
            database=_get_secret(
                "DB_NAME",
                "institute_analytics"
            ),
            ssl_ca=str(ca_path),
            ssl_verify_cert=True,
            connection_timeout=15
        )

        if connection.is_connected():

            print(
                "Aiven MySQL Database Connected Successfully!"
            )

        return connection

    except Error as e:

        print(
            f"Database Connection Error: {e}"
        )

        return None


# =========================================================
# INSERT COURSES
# =========================================================

def insert_courses():

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    insert_query = """
        INSERT INTO courses
        (
            course_id,
            course_name,
            category,
            duration,
            learning_mode,
            level,
            course_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:

        inserted_count = 0

        for course_name, course in courses.items():

            learning_mode = " / ".join(
                course["mode"]
            )

            values = (
                course["course_id"],
                course_name,
                course["category"],
                course["duration"],
                learning_mode,
                course["level"],
                "Active"
            )

            cursor.execute(
                insert_query,
                values
            )

            inserted_count += 1

        connection.commit()

        print(
            f"{inserted_count} course(s) inserted successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Course Insert Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# INSERT STUDENT ENQUIRY
# =========================================================

def insert_enquiry(
    student_name,
    email,
    phone,
    city,
    qualification,
    age_group,
    course_id,
    learning_mode,
    preferred_batch,
    lead_source,
    message
):

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    insert_query = """
        INSERT INTO enquiries
        (
            student_name,
            email,
            phone,
            city,
            qualification,
            age_group,
            course_id,
            learning_mode,
            preferred_batch,
            lead_source,
            message
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    values = (
        student_name,
        email,
        phone,
        city,
        qualification,
        age_group,
        course_id,
        learning_mode,
        preferred_batch,
        lead_source,
        message
    )

    try:

        cursor.execute(
            insert_query,
            values
        )

        connection.commit()

        print(
            "Student enquiry inserted successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Enquiry Insert Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# GET ALL STUDENT ENQUIRIES
# =========================================================

def get_all_enquiries():

    connection = create_connection()

    if connection is None:
        return []

    cursor = connection.cursor(
        dictionary=True
    )

    select_query = """
        SELECT
            e.enquiry_id,
            e.enquiry_date,
            e.student_name,
            e.email,
            e.phone,
            e.city,
            e.qualification,
            e.age_group,
            e.course_id,
            c.course_name,
            e.learning_mode,
            e.preferred_batch,
            e.lead_source,
            e.message,
            e.enquiry_status
        FROM enquiries e

        LEFT JOIN courses c
            ON e.course_id = c.course_id

        ORDER BY e.enquiry_date DESC
    """

    try:

        cursor.execute(
            select_query
        )

        enquiries = cursor.fetchall()

        return enquiries

    except Error as e:

        print(
            f"Enquiry Fetch Error: {e}"
        )

        return []

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# UPDATE ENQUIRY STATUS
# =========================================================

def update_enquiry_status(
    enquiry_id,
    new_status
):

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    update_query = """
        UPDATE enquiries
        SET enquiry_status = %s
        WHERE enquiry_id = %s
    """

    values = (
        new_status,
        enquiry_id
    )

    try:

        cursor.execute(
            update_query,
            values
        )

        connection.commit()

        print(
            "Enquiry status updated successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Status Update Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# ADD FOLLOW-UP
# =========================================================

def add_followup(
    enquiry_id,
    followup_status,
    notes
):

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    insert_query = """
        INSERT INTO followups
        (
            enquiry_id,
            followup_status,
            notes
        )
        VALUES (%s, %s, %s)
    """

    values = (
        enquiry_id,
        followup_status,
        notes
    )

    try:

        cursor.execute(
            insert_query,
            values
        )

        connection.commit()

        print(
            "Follow-up added successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Follow-up Insert Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# GET FOLLOW-UP HISTORY
# =========================================================

def get_followup_history(
    enquiry_id
):

    connection = create_connection()

    if connection is None:
        return []

    cursor = connection.cursor(
        dictionary=True
    )

    select_query = """
        SELECT
            followup_id,
            enquiry_id,
            followup_date,
            followup_status,
            notes
        FROM followups

        WHERE enquiry_id = %s

        ORDER BY followup_date DESC
    """

    try:

        cursor.execute(
            select_query,
            (enquiry_id,)
        )

        followups = cursor.fetchall()

        return followups

    except Error as e:

        print(
            f"Follow-up Fetch Error: {e}"
        )

        return []

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# CHECK EXISTING ENROLLMENT
# =========================================================

def get_enrollment_by_enquiry(
    enquiry_id
):

    connection = create_connection()

    if connection is None:
        return None

    cursor = connection.cursor(
        dictionary=True
    )

    select_query = """
        SELECT
            enrollment_id,
            enquiry_id,
            course_id,
            enrollment_date,
            batch,
            final_fee,
            enrollment_status
        FROM enrollments
        WHERE enquiry_id = %s
        LIMIT 1
    """

    try:

        cursor.execute(
            select_query,
            (enquiry_id,)
        )

        enrollment = cursor.fetchone()

        return enrollment

    except Error as e:

        print(
            f"Enrollment Fetch Error: {e}"
        )

        return None

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# ADD STUDENT ENROLLMENT
# =========================================================

def add_enrollment(
    enquiry_id,
    course_id,
    enrollment_date,
    batch,
    final_fee,
    enrollment_status="Active"
):

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    check_query = """
        SELECT enrollment_id
        FROM enrollments
        WHERE enquiry_id = %s
        LIMIT 1
    """

    insert_query = """
        INSERT INTO enrollments
        (
            enquiry_id,
            course_id,
            enrollment_date,
            batch,
            final_fee,
            enrollment_status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        enquiry_id,
        course_id,
        enrollment_date,
        batch,
        final_fee,
        enrollment_status
    )

    try:

        cursor.execute(
            check_query,
            (enquiry_id,)
        )

        existing_enrollment = cursor.fetchone()

        if existing_enrollment:

            print(
                "Enrollment already exists for this enquiry."
            )

            return False

        cursor.execute(
            insert_query,
            values
        )

        connection.commit()

        print(
            "Student enrollment added successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Enrollment Insert Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# ADD STUDENT PAYMENT
# =========================================================

def add_payment(
    enrollment_id,
    payment_date,
    amount_paid,
    payment_method,
    payment_status="Paid"
):

    connection = create_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    insert_query = """
        INSERT INTO payments
        (
            enrollment_id,
            payment_date,
            amount_paid,
            payment_method,
            payment_status
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        enrollment_id,
        payment_date,
        amount_paid,
        payment_method,
        payment_status
    )

    try:

        cursor.execute(
            insert_query,
            values
        )

        connection.commit()

        print(
            "Student payment added successfully!"
        )

        return True

    except Error as e:

        connection.rollback()

        print(
            f"Payment Insert Error: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# GET PAYMENT HISTORY
# =========================================================

def get_payment_history(
    enrollment_id
):

    connection = create_connection()

    if connection is None:
        return []

    cursor = connection.cursor(
        dictionary=True
    )

    select_query = """
        SELECT
            payment_id,
            enrollment_id,
            payment_date,
            amount_paid,
            payment_method,
            payment_status
        FROM payments
        WHERE enrollment_id = %s
        ORDER BY payment_date DESC, payment_id DESC
    """

    try:

        cursor.execute(
            select_query,
            (enrollment_id,)
        )

        payments = cursor.fetchall()

        return payments

    except Error as e:

        print(
            f"Payment Fetch Error: {e}"
        )

        return []

    finally:

        cursor.close()
        connection.close()

        print(
            "Database Connection Closed."
        )


# =========================================================
# TEST DATABASE CONNECTION
# =========================================================

if __name__ == "__main__":

    connection = create_connection()

    if connection:

        connection.close()

        print(
            "Database Connection Closed."
        )