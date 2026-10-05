import random
from datetime import timedelta, datetime

import mysql.connector
from mysql.connector import Error


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "institute_analytics",
}

RANDOM_SEED = 42
TOTAL_SYNTHETIC_ENROLLMENTS = 160

# Synthetic/demo fee ranges only.
# These are NOT official institute fees.
COURSE_FEE_RANGES = {
    "CRS001": (25000, 45000),  # Data Analytics
    "CRS002": (35000, 60000),  # Data Science
    "CRS003": (12000, 25000),  # Python Programming
    "CRS004": (40000, 70000),  # AI & Machine Learning
    "CRS005": (35000, 65000),  # Full Stack Development
    "CRS006": (15000, 30000),  # Web Designing
    "CRS007": (15000, 30000),  # Digital Marketing
    "CRS008": (15000, 30000),  # Graphic Designing
    "CRS009": (12000, 25000),  # Video Editing
    "CRS010": (8000, 18000),   # Tally with GST
    "CRS011": (5000, 10000),   # Basic Computer Course
    "CRS012": (18000, 35000),  # DCA
    "CRS013": (4000, 8000),    # Computer Typing
    "CRS014": (8000, 18000),   # Advanced Excel
    "CRS015": (10000, 22000),  # Trading & Financial Market Basics
}

BATCHES = ["Morning", "Afternoon", "Evening", "Weekend"]


# =========================================================
# DATABASE CONNECTION
# =========================================================

def create_connection():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)

        if connection.is_connected():
            print("MySQL Database Connected Successfully!")

        return connection

    except Error as error:
        print(f"Database Connection Error: {error}")
        return None


# =========================================================
# HELPERS
# =========================================================

def generate_fee(course_id):
    minimum, maximum = COURSE_FEE_RANGES.get(
        course_id,
        (10000, 30000)
    )

    # Fees in ₹500 steps for cleaner demo data.
    possible_fees = list(range(minimum, maximum + 1, 500))
    return random.choice(possible_fees)


def choose_enrollment_status(enrollment_date):
    """
    Historical enrollments can be Active, Completed or Cancelled.
    Recent enrollments are more likely to remain Active.
    """

    cutoff = datetime(2026, 9, 22).date()
    age_days = (cutoff - enrollment_date).days

    if age_days >= 240:
        return random.choices(
            ["Completed", "Active", "Cancelled"],
            weights=[65, 30, 5],
            k=1,
        )[0]

    if age_days >= 120:
        return random.choices(
            ["Active", "Completed", "Cancelled"],
            weights=[60, 35, 5],
            k=1,
        )[0]

    return random.choices(
        ["Active", "Completed", "Cancelled"],
        weights=[90, 5, 5],
        k=1,
    )[0]


# =========================================================
# GENERATE SYNTHETIC ENROLLMENTS
# =========================================================

def generate_enrollments():
    random.seed(RANDOM_SEED)

    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor(dictionary=True)

    try:
        # -------------------------------------------------
        # Safety check
        # Count enrollments linked to Synthetic enquiries.
        # Live enrollments are ignored and never changed.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )

        existing_synthetic_enrollments = cursor.fetchone()["total"]

        if existing_synthetic_enrollments > 0:
            print(
                f"\nStopped: {existing_synthetic_enrollments} Synthetic "
                "enrollment record(s) already exist."
            )
            print("No enrollment data was inserted.")
            print("Existing Live and Synthetic data remain unchanged.")
            return

        # -------------------------------------------------
        # Read all Converted Synthetic enquiries.
        # Also get the last follow-up date for each enquiry.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT
                e.enquiry_id,
                e.enquiry_date,
                e.course_id,
                MAX(f.followup_date) AS last_followup_date
            FROM enquiries e
            LEFT JOIN followups f
                ON e.enquiry_id = f.enquiry_id
            WHERE e.data_source = 'Synthetic'
              AND e.enquiry_status = 'Converted'
            GROUP BY
                e.enquiry_id,
                e.enquiry_date,
                e.course_id
            ORDER BY e.enquiry_id
            """
        )

        converted_enquiries = cursor.fetchall()

        if len(converted_enquiries) < TOTAL_SYNTHETIC_ENROLLMENTS:
            print(
                f"\nOnly {len(converted_enquiries)} Converted Synthetic "
                f"enquiries are available."
            )
            print(
                f"{TOTAL_SYNTHETIC_ENROLLMENTS} enrollments cannot be generated."
            )
            return

        # Select exactly 160 of the 170 Converted enquiries.
        selected_enquiries = random.sample(
            converted_enquiries,
            TOTAL_SYNTHETIC_ENROLLMENTS,
        )

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

        enrollment_rows = []

        for enquiry in selected_enquiries:
            enquiry_id = enquiry["enquiry_id"]
            course_id = enquiry["course_id"]

            base_date = (
                enquiry["last_followup_date"]
                if enquiry["last_followup_date"] is not None
                else enquiry["enquiry_date"]
            )

            # Enrollment occurs 1-7 days after the last follow-up.
            enrollment_date = (
                base_date + timedelta(days=random.randint(1, 7))
            ).date()

            final_fee = generate_fee(course_id)
            enrollment_status = choose_enrollment_status(enrollment_date)

            enrollment_rows.append(
                (
                    enquiry_id,
                    course_id,
                    enrollment_date,
                    random.choice(BATCHES),
                    final_fee,
                    enrollment_status,
                )
            )

        cursor.executemany(insert_query, enrollment_rows)
        connection.commit()

        print(
            f"\n{len(enrollment_rows)} Synthetic enrollment records "
            "inserted successfully!"
        )

        # -------------------------------------------------
        # VERIFICATION
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM enquiries
            WHERE data_source = 'Synthetic'
              AND enquiry_status = 'Converted'
            """
        )
        total_converted = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )
        total_enrolled = cursor.fetchone()["total"]

        not_enrolled = total_converted - total_enrolled

        print(f"\nConverted Synthetic enquiries: {total_converted}")
        print(f"Synthetic enrollments: {total_enrolled}")
        print(f"Converted but not yet enrolled: {not_enrolled}")

        cursor.execute(
            """
            SELECT
                en.enrollment_status,
                COUNT(*) AS total
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            GROUP BY en.enrollment_status
            ORDER BY en.enrollment_status
            """
        )

        print("\nSynthetic Enrollment Status Summary:")

        for row in cursor.fetchall():
            print(f"{row['enrollment_status']}: {row['total']}")

        cursor.execute(
            """
            SELECT
                MIN(en.final_fee) AS minimum_fee,
                MAX(en.final_fee) AS maximum_fee,
                ROUND(AVG(en.final_fee), 2) AS average_fee
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )

        fee_summary = cursor.fetchone()

        print("\nSynthetic Fee Summary:")
        print(f"Minimum Fee: ₹{fee_summary['minimum_fee']}")
        print(f"Maximum Fee: ₹{fee_summary['maximum_fee']}")
        print(f"Average Fee: ₹{fee_summary['average_fee']}")

        print("\nExisting Live records were not updated or deleted.")

    except Error as error:
        connection.rollback()
        print(f"Enrollment Generation Error: {error}")

    finally:
        cursor.close()
        connection.close()
        print("\nDatabase Connection Closed.")


if __name__ == "__main__":
    generate_enrollments()
