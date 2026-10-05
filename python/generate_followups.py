import random
from datetime import timedelta

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


# =========================================================
# FOLLOW-UP RULES
# =========================================================

FOLLOWUP_COUNTS = {
    "New": (0, 0),
    "Contacted": (1, 1),
    "Follow-up": (2, 3),
    "Interested": (2, 3),
    "Converted": (2, 4),
    "Lost": (1, 3),
}

NOTES = {
    "Contacted": [
        "Called student and shared course details. Student will review the information.",
        "Spoke with student regarding course duration and learning mode. Follow-up may be required.",
        "Course details and batch options were explained over call.",
        "Student responded to the call and requested additional course information.",
    ],
    "Follow-up": [
        "Follow-up call completed. Student requested time to discuss the course with family.",
        "Student asked about batch timings and fee details. Next follow-up planned.",
        "Student is considering the course and requested another call after a few days.",
        "Follow-up completed. Student requested information about the upcoming batch.",
    ],
    "Interested": [
        "Student showed interest in joining and asked about the admission process.",
        "Student is interested in the course and requested fee and batch information.",
        "Student confirmed interest and asked for enrollment details.",
        "Student is interested but needs time before completing enrollment.",
    ],
    "Converted": [
        "Student confirmed interest and agreed to proceed with enrollment.",
        "Admission process explained. Student confirmed course selection.",
        "Student agreed to enroll after discussion of batch and fee details.",
        "Student confirmed enrollment decision. Admission details were shared.",
    ],
    "Lost": [
        "Student is currently not interested in proceeding with the course.",
        "Student decided not to enroll at this time.",
        "Student could not proceed due to schedule or personal constraints.",
        "Student selected another option and does not wish to continue the enquiry.",
    ],
}


def create_connection():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)

        if connection.is_connected():
            print("MySQL Database Connected Successfully!")

        return connection

    except Error as error:
        print(f"Database Connection Error: {error}")
        return None


def generate_followups():
    random.seed(RANDOM_SEED)

    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor(dictionary=True)

    try:
        # -------------------------------------------------
        # Safety check
        # Only checks follow-ups belonging to Synthetic enquiries.
        # Live follow-ups are ignored and never changed.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM followups f
            INNER JOIN enquiries e
                ON f.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )

        existing_synthetic_followups = cursor.fetchone()["total"]

        if existing_synthetic_followups > 0:
            print(
                f"\nStopped: {existing_synthetic_followups} Synthetic "
                "follow-up record(s) already exist."
            )
            print("No follow-up data was inserted.")
            print("Existing Live and Synthetic data remain unchanged.")
            return

        # -------------------------------------------------
        # Read only Synthetic enquiries.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT
                enquiry_id,
                enquiry_date,
                enquiry_status
            FROM enquiries
            WHERE data_source = 'Synthetic'
            ORDER BY enquiry_id
            """
        )

        enquiries = cursor.fetchall()

        if not enquiries:
            print("\nNo Synthetic enquiries found. Nothing was inserted.")
            return

        insert_query = """
            INSERT INTO followups
            (
                enquiry_id,
                followup_date,
                followup_status,
                notes
            )
            VALUES (%s, %s, %s, %s)
        """

        followup_rows = []

        for enquiry in enquiries:
            enquiry_id = enquiry["enquiry_id"]
            enquiry_date = enquiry["enquiry_date"]
            final_status = enquiry["enquiry_status"]

            minimum, maximum = FOLLOWUP_COUNTS.get(final_status, (0, 0))

            if maximum == 0:
                continue

            number_of_followups = random.randint(minimum, maximum)

            # First follow-up happens 1-4 days after enquiry.
            current_date = enquiry_date + timedelta(
                days=random.randint(1, 4),
                hours=random.randint(0, 5),
                minutes=random.randint(0, 59),
            )

            for followup_number in range(number_of_followups):

                # Earlier follow-ups use sensible intermediate statuses.
                if final_status == "Contacted":
                    followup_status = "Contacted"

                elif final_status == "Follow-up":
                    followup_status = (
                        "Contacted"
                        if followup_number == 0
                        else "Follow-up"
                    )

                elif final_status == "Interested":
                    if followup_number == 0:
                        followup_status = "Contacted"
                    elif followup_number == number_of_followups - 1:
                        followup_status = "Interested"
                    else:
                        followup_status = "Follow-up"

                elif final_status == "Converted":
                    if followup_number == 0:
                        followup_status = "Contacted"
                    elif followup_number == number_of_followups - 1:
                        followup_status = "Converted"
                    else:
                        followup_status = random.choice(
                            ["Follow-up", "Interested"]
                        )

                elif final_status == "Lost":
                    if followup_number == number_of_followups - 1:
                        followup_status = "Lost"
                    elif followup_number == 0:
                        followup_status = "Contacted"
                    else:
                        followup_status = "Follow-up"

                else:
                    followup_status = final_status

                note_key = (
                    followup_status
                    if followup_status in NOTES
                    else final_status
                )

                followup_rows.append(
                    (
                        enquiry_id,
                        current_date,
                        followup_status,
                        random.choice(NOTES[note_key]),
                    )
                )

                # Next contact is 2-8 days later.
                current_date += timedelta(
                    days=random.randint(2, 8),
                    hours=random.randint(0, 4),
                    minutes=random.randint(0, 59),
                )

        cursor.executemany(insert_query, followup_rows)
        connection.commit()

        print(
            f"\n{len(followup_rows)} Synthetic follow-up records "
            "inserted successfully!"
        )

        # -------------------------------------------------
        # Verification
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT
                f.followup_status,
                COUNT(*) AS total
            FROM followups f
            INNER JOIN enquiries e
                ON f.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            GROUP BY f.followup_status
            ORDER BY f.followup_status
            """
        )

        print("\nSynthetic Follow-up Status Summary:")

        for row in cursor.fetchall():
            print(f"{row['followup_status']}: {row['total']}")

        cursor.execute(
            """
            SELECT COUNT(DISTINCT f.enquiry_id) AS total
            FROM followups f
            INNER JOIN enquiries e
                ON f.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )

        enquiries_with_followups = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM enquiries
            WHERE data_source = 'Synthetic'
              AND enquiry_status = 'New'
            """
        )

        new_enquiries = cursor.fetchone()["total"]

        print(
            f"\nSynthetic enquiries with follow-ups: "
            f"{enquiries_with_followups}"
        )
        print(
            f"New Synthetic enquiries without generated follow-ups: "
            f"{new_enquiries}"
        )
        print("\nExisting Live records were not updated or deleted.")

    except Error as error:
        connection.rollback()
        print(f"Follow-up Generation Error: {error}")

    finally:
        cursor.close()
        connection.close()
        print("\nDatabase Connection Closed.")


if __name__ == "__main__":
    generate_followups()
