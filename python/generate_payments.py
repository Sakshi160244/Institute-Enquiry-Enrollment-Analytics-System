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

PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Bank Transfer",
    "Card",
]


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

def split_amount(total_amount, installments):
    """
    Split a fee into 1, 2 or 3 installments.
    Every installment is in whole rupees and the final total
    always equals total_amount.
    """

    total_amount = int(total_amount)

    if installments == 1:
        return [total_amount]

    if installments == 2:
        first = int(round(total_amount * random.uniform(0.40, 0.65)))
        second = total_amount - first
        return [first, second]

    first = int(round(total_amount * random.uniform(0.25, 0.40)))
    remaining = total_amount - first

    second = int(round(remaining * random.uniform(0.40, 0.60)))
    third = total_amount - first - second

    return [first, second, third]


# =========================================================
# GENERATE SYNTHETIC PAYMENTS
# =========================================================

def generate_payments():
    random.seed(RANDOM_SEED)

    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor(dictionary=True)

    try:
        # -------------------------------------------------
        # Safety check
        # Count payments belonging to Synthetic enquiries.
        # Existing Live payments are ignored.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM payments p
            INNER JOIN enrollments en
                ON p.enrollment_id = en.enrollment_id
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            """
        )

        existing_synthetic_payments = cursor.fetchone()["total"]

        if existing_synthetic_payments > 0:
            print(
                f"\nStopped: {existing_synthetic_payments} Synthetic "
                "payment record(s) already exist."
            )
            print("No payment data was inserted.")
            print("Existing Live and Synthetic data remain unchanged.")
            return

        # -------------------------------------------------
        # Read only Synthetic enrollments.
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT
                en.enrollment_id,
                en.enrollment_date,
                en.final_fee,
                en.enrollment_status
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            ORDER BY en.enrollment_id
            """
        )

        enrollments = cursor.fetchall()

        if not enrollments:
            print("\nNo Synthetic enrollments found. Nothing was inserted.")
            return

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

        payment_rows = []

        for enrollment in enrollments:
            enrollment_id = enrollment["enrollment_id"]
            enrollment_date = enrollment["enrollment_date"]
            final_fee = int(enrollment["final_fee"])
            enrollment_status = enrollment["enrollment_status"]

            # ---------------------------------------------
            # Decide how much of the fee has actually been paid.
            #
            # Completed -> always fully paid
            # Active    -> mostly full, sometimes partial
            # Cancelled -> usually partial, sometimes no payment
            # ---------------------------------------------

            if enrollment_status == "Completed":
                payment_fraction = 1.0

            elif enrollment_status == "Active":
                payment_fraction = random.choices(
                    [1.0, 0.75, 0.50],
                    weights=[55, 30, 15],
                    k=1,
                )[0]

            else:  # Cancelled
                payment_fraction = random.choices(
                    [0.0, 0.25, 0.50],
                    weights=[35, 40, 25],
                    k=1,
                )[0]

            target_paid = int(round(final_fee * payment_fraction))

            # Keep amount clean for analytics.
            target_paid = int(round(target_paid / 500.0) * 500)

            if target_paid > final_fee:
                target_paid = final_fee

            # No payment record for cancelled enrollments
            # where nothing was paid.
            if target_paid <= 0:
                continue

            # ---------------------------------------------
            # Decide installment count.
            # Larger paid amounts are more likely to have
            # multiple installments.
            # ---------------------------------------------

            if target_paid <= 10000:
                installment_count = random.choices(
                    [1, 2],
                    weights=[80, 20],
                    k=1,
                )[0]

            elif target_paid <= 25000:
                installment_count = random.choices(
                    [1, 2, 3],
                    weights=[45, 45, 10],
                    k=1,
                )[0]

            else:
                installment_count = random.choices(
                    [1, 2, 3],
                    weights=[25, 50, 25],
                    k=1,
                )[0]

            amounts = split_amount(target_paid, installment_count)

            # First payment is on enrollment date or within 3 days.
            payment_date = enrollment_date + timedelta(
                days=random.randint(0, 3)
            )

            for index, amount in enumerate(amounts):
                if index > 0:
                    # Next installment 15-45 days later.
                    payment_date += timedelta(
                        days=random.randint(15, 45)
                    )

                payment_rows.append(
                    (
                        enrollment_id,
                        payment_date,
                        amount,
                        random.choices(
                            PAYMENT_METHODS,
                            weights=[45, 25, 20, 10],
                            k=1,
                        )[0],
                        "Paid",
                    )
                )

        cursor.executemany(insert_query, payment_rows)
        connection.commit()

        print(
            f"\n{len(payment_rows)} Synthetic payment records "
            "inserted successfully!"
        )

        # -------------------------------------------------
        # VERIFICATION
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
        synthetic_enrollments = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(DISTINCT p.enrollment_id) AS total
            FROM payments p
            INNER JOIN enrollments en
                ON p.enrollment_id = en.enrollment_id
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
              AND p.payment_status = 'Paid'
            """
        )
        enrollments_with_payments = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT
                COUNT(*) AS payment_records,
                ROUND(SUM(p.amount_paid), 2) AS total_collected
            FROM payments p
            INNER JOIN enrollments en
                ON p.enrollment_id = en.enrollment_id
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
              AND p.payment_status = 'Paid'
            """
        )
        payment_summary = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                ROUND(SUM(en.final_fee), 2) AS total_final_fee,
                ROUND(
                    SUM(en.final_fee) -
                    COALESCE(SUM(payment_totals.total_paid), 0),
                    2
                ) AS total_outstanding
            FROM enrollments en
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            LEFT JOIN (
                SELECT
                    enrollment_id,
                    SUM(
                        CASE
                            WHEN payment_status = 'Paid'
                            THEN amount_paid
                            ELSE 0
                        END
                    ) AS total_paid
                FROM payments
                GROUP BY enrollment_id
            ) payment_totals
                ON en.enrollment_id = payment_totals.enrollment_id
            WHERE e.data_source = 'Synthetic'
            """
        )
        fee_summary = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                p.payment_method,
                COUNT(*) AS total
            FROM payments p
            INNER JOIN enrollments en
                ON p.enrollment_id = en.enrollment_id
            INNER JOIN enquiries e
                ON en.enquiry_id = e.enquiry_id
            WHERE e.data_source = 'Synthetic'
            GROUP BY p.payment_method
            ORDER BY total DESC
            """
        )
        methods = cursor.fetchall()

        print(f"\nSynthetic enrollments: {synthetic_enrollments}")
        print(
            "Enrollments with at least one payment: "
            f"{enrollments_with_payments}"
        )
        print(
            "Enrollments with no payment yet: "
            f"{synthetic_enrollments - enrollments_with_payments}"
        )

        print("\nSynthetic Payment Summary:")
        print(
            f"Payment Records: "
            f"{payment_summary['payment_records']}"
        )
        print(
            f"Total Final Fee: ₹{fee_summary['total_final_fee']}"
        )
        print(
            f"Total Collected: ₹{payment_summary['total_collected']}"
        )
        print(
            f"Total Outstanding: ₹{fee_summary['total_outstanding']}"
        )

        print("\nPayment Method Summary:")
        for row in methods:
            print(f"{row['payment_method']}: {row['total']}")

        # Important integrity check:
        # no enrollment should have paid more than its final fee.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM (
                SELECT
                    en.enrollment_id,
                    en.final_fee,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN p.payment_status = 'Paid'
                                THEN p.amount_paid
                                ELSE 0
                            END
                        ),
                        0
                    ) AS total_paid
                FROM enrollments en
                INNER JOIN enquiries e
                    ON en.enquiry_id = e.enquiry_id
                LEFT JOIN payments p
                    ON en.enrollment_id = p.enrollment_id
                WHERE e.data_source = 'Synthetic'
                GROUP BY
                    en.enrollment_id,
                    en.final_fee
                HAVING total_paid > en.final_fee
            ) AS invalid_payments
            """
        )

        overpaid = cursor.fetchone()["total"]

        print(f"\nOverpaid Synthetic enrollments: {overpaid}")

        if overpaid == 0:
            print("Payment integrity check passed.")

        print("\nExisting Live records were not updated or deleted.")

    except Error as error:
        connection.rollback()
        print(f"Payment Generation Error: {error}")

    finally:
        cursor.close()
        connection.close()
        print("\nDatabase Connection Closed.")


if __name__ == "__main__":
    generate_payments()
