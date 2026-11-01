
import os
import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE = os.environ.get("DATABASE_PATH", "jobs.db")

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create the jobs table if it does not exist
def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_table()


# Home page: search, filter, and dashboard statistics
@app.route("/")
def home():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_db_connection()

    # Calculate statistics for all applications
    stats = conn.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Interview' THEN 1 ELSE 0 END)
                AS interviews,
            SUM(CASE WHEN status = 'Selected' THEN 1 ELSE 0 END)
                AS selected,
            SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END)
                AS rejected
        FROM jobs
    """).fetchone()

    # Build the search and filter query
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search:
        query += " AND company LIKE ?"
        params.append("%" + search + "%")

    allowed_statuses = {
        "Applied", "Interview", "Selected", "Rejected"
    }

    if status in allowed_statuses:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC"

    jobs = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs,
        stats=stats
    )


# Add a new job application
@app.route("/add", methods=["POST"])
def add_job():
    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()
    date = request.form.get("date", "").strip()
    status = request.form.get("status", "").strip()

    allowed_statuses = {
        "Applied", "Interview", "Selected", "Rejected"
    }

    if not company or not role or not date:
        return "Company, job title, and date are required.", 400

    if status not in allowed_statuses:
        return "Invalid application status.", 400

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO jobs
            (company, role, application_date, status)
        VALUES (?, ?, ?, ?)
    """, (company, role, date, status))

    conn.commit()
    conn.close()

    return redirect("/")


# Update an application's status
@app.route("/update/<int:job_id>", methods=["POST"])
def update_job(job_id):
    status = request.form.get("status", "").strip()

    allowed_statuses = {
        "Applied", "Interview", "Selected", "Rejected"
    }

    if status not in allowed_statuses:
        return "Invalid application status.", 400

    conn = get_db_connection()

    conn.execute("""
        UPDATE jobs
        SET status = ?
        WHERE id = ?
    """, (status, job_id))

    conn.commit()
    conn.close()

    return redirect("/")


# Delete an application
@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# Start the Flask development server
if __name__ == "__main__":
    app.run(debug=True)


    


