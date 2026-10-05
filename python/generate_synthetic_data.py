import random
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "institute_analytics",
}

TOTAL_SYNTHETIC_ENQUIRIES = 500
RANDOM_SEED = 42
START_DATE = datetime(2025, 1, 1, 9, 0, 0)
END_DATE = datetime(2026, 9, 22, 18, 0, 0)

STATUS_COUNTS = {
    "New": 60,
    "Contacted": 70,
    "Follow-up": 80,
    "Interested": 90,
    "Converted": 170,
    "Lost": 30,
}

FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Ananya", "Anjali", "Arjun", "Ayush",
    "Deepak", "Diya", "Gaurav", "Isha", "Kajal", "Karan", "Khushi",
    "Manish", "Mehak", "Mohit", "Muskan", "Neha", "Nikhil", "Nisha",
    "Pooja", "Prachi", "Rahul", "Riya", "Rohit", "Sahil", "Saksham",
    "Shivani", "Simran", "Sneha", "Sonam", "Tanya", "Varun", "Yash"
]
LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Gupta", "Yadav", "Jain",
    "Malik", "Dahiya", "Panchal", "Bansal", "Mehta", "Khatri",
    "Chauhan", "Saini"
]
CITIES = [
    "Delhi", "Sonipat", "Panipat", "Rohtak", "Gurugram",
    "Faridabad", "Karnal", "Bahadurgarh", "Noida", "Ghaziabad"
]
AGE_GROUPS = ["Below 18", "18-21", "22-25", "26-30", "31+"]
BATCHES = ["Morning", "Afternoon", "Evening", "Weekend"]
LEAD_SOURCES = [
    "Google Search", "Instagram", "Facebook", "LinkedIn",
    "YouTube", "Referral", "Walk-in", "Other"
]
MESSAGES = [
    "Please share course details and fee information.",
    "I would like to know about the next available batch.",
    "Please contact me regarding admission and course timings.",
    "I am interested in this course and want more information.",
    "Please share the syllabus and learning mode details.",
    "I would like to know about enrollment and batch options.",
    "Please provide complete course information.",
    "I am interested in joining the upcoming batch.",
    ""
]

def create_connection():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        if connection.is_connected():
            print("MySQL Database Connected Successfully!")
        return connection
    except Error as error:
        print(f"Database Connection Error: {error}")
        return None

def random_datetime(start_date, end_date):
    seconds = int((end_date - start_date).total_seconds())
    return start_date + timedelta(seconds=random.randint(0, seconds))

def build_statuses():
    statuses = []
    for status, count in STATUS_COUNTS.items():
        statuses.extend([status] * count)
    random.shuffle(statuses)
    return statuses

def choose_qualification(age_group):
    choices = {
        "Below 18": (["10th", "12th", "Diploma"], [55, 35, 10]),
        "18-21": (["12th", "Diploma", "Graduate"], [45, 25, 30]),
        "22-25": (["12th", "Diploma", "Graduate", "Post Graduate"], [10, 15, 50, 25]),
        "26-30": (["Diploma", "Graduate", "Post Graduate", "Other"], [15, 50, 30, 5]),
        "31+": (["12th", "Diploma", "Graduate", "Post Graduate", "Other"], [10, 15, 40, 25, 10]),
    }
    values, weights = choices[age_group]
    return random.choices(values, weights=weights, k=1)[0]

def choose_learning_mode(course_mode):
    modes = [m.strip() for m in course_mode.replace("/", ",").split(",") if m.strip()]
    return random.choice(modes) if modes else "Offline"

def generate_synthetic_enquiries():
    random.seed(RANDOM_SEED)
    connection = create_connection()
    if connection is None:
        return

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM enquiries
            WHERE data_source = 'Synthetic'
        """)
        existing_synthetic = cursor.fetchone()["total"]

        if existing_synthetic > 0:
            print(f"Stopped: {existing_synthetic} Synthetic enquiry record(s) already exist.")
            print("No data was inserted. Existing data remains unchanged.")
            return

        cursor.execute("""
            SELECT course_id, course_name, learning_mode
            FROM courses
            WHERE course_status = 'Active'
            ORDER BY course_id
        """)
        courses = cursor.fetchall()

        if not courses:
            print("No active courses found. Nothing was inserted.")
            return

        statuses = build_statuses()

        insert_query = """
            INSERT INTO enquiries
            (
                enquiry_date, student_name, email, phone, city,
                qualification, age_group, course_id, learning_mode,
                preferred_batch, lead_source, message,
                enquiry_status, data_source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s)
        """

        rows = []

        for number in range(1, TOTAL_SYNTHETIC_ENQUIRIES + 1):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            age_group = random.choices(
                AGE_GROUPS, weights=[8, 30, 32, 20, 10], k=1
            )[0]
            course = random.choice(courses)

            rows.append((
                random_datetime(START_DATE, END_DATE),
                f"{first_name} {last_name}",
                f"demo.student{number:03d}.{first_name.lower()}{last_name.lower()}@example.com",
                f"9000{number:06d}",
                random.choice(CITIES),
                choose_qualification(age_group),
                age_group,
                course["course_id"],
                choose_learning_mode(course["learning_mode"]),
                random.choice(BATCHES),
                random.choices(
                    LEAD_SOURCES,
                    weights=[25, 20, 8, 5, 8, 15, 14, 5],
                    k=1
                )[0],
                random.choice(MESSAGES),
                statuses[number - 1],
                "Synthetic"
            ))

        cursor.executemany(insert_query, rows)
        connection.commit()

        print("\n500 Synthetic enquiries inserted successfully!")

        cursor.execute("""
            SELECT data_source, COUNT(*) AS total
            FROM enquiries
            GROUP BY data_source
            ORDER BY data_source
        """)
        print("\nData Source Summary:")
        for row in cursor.fetchall():
            print(f"{row['data_source']}: {row['total']}")

        cursor.execute("""
            SELECT enquiry_status, COUNT(*) AS total
            FROM enquiries
            WHERE data_source = 'Synthetic'
            GROUP BY enquiry_status
            ORDER BY enquiry_status
        """)
        print("\nSynthetic Status Summary:")
        for row in cursor.fetchall():
            print(f"{row['enquiry_status']}: {row['total']}")

        print("\nExisting Live enquiries were not updated or deleted.")

    except Error as error:
        connection.rollback()
        print(f"Synthetic Data Insert Error: {error}")

    finally:
        cursor.close()
        connection.close()
        print("\nDatabase Connection Closed.")

if __name__ == "__main__":
    generate_synthetic_enquiries()
