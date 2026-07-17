import os
from datetime import datetime
from functools import wraps

import pyodbc
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook

app = Flask(__name__)

app.secret_key = "OfficeWorkAnalysisSecretKey2026"

# ==========================================
# SQL SERVER CONNECTION
# ==========================================

def get_conn():

    return pyodbc.connect(

        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=OfficeWorkDB;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;",
        timeout=5

    )
# ==========================================
# UPLOAD SETTINGS
# ==========================================

UPLOAD_FOLDER = os.path.join("static", "uploads", "employees")

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS
    )

# ==========================================
# LOGIN REQUIRED DECORATOR
# ==========================================

def login_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        if "user_id" not in session:

            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated

@app.route("/")
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/save", methods=["POST"])
def save():

    username = request.form["username"].strip()

    password = request.form["password"]

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT user_id FROM users WHERE username=?",

        (username,)

    )

    if cursor.fetchone():

        flash("Username already exists.")

        cursor.close()

        conn.close()

        return redirect("/register")

    password_hash = generate_password_hash(password)

    cursor.execute(

        """
        INSERT INTO users
        (
            username,
            password
        )
        VALUES
        (?,?)
        """,

        (
            username,
            password_hash
        )

    )

    conn.commit()

    cursor.close()

    conn.close()

    flash("Registration Successful")

    return redirect("/")

@app.route("/check", methods=["POST"])
def check():

    username = request.form["username"].strip()
    password = request.form["password"]

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, username
        FROM users
        WHERE username=? AND password=?
        """,
        (username, password)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["username"] = user[1]
        return redirect(url_for("home"))

    return render_template(
        "login.html",
        error="Invalid Username or Password"
    )
from datetime import datetime

from datetime import datetime

from datetime import datetime

@app.route("/home")
def home():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cursor = conn.cursor()

    # Employees
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]

    # Attendance
    cursor.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cursor.fetchone()[0]

    # Letters
    cursor.execute("SELECT COUNT(*) FROM letters")
    letter_count = cursor.fetchone()[0]

    # Tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]

    # Pending Tasks
    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='Pending'
    """)
    pending_tasks = cursor.fetchone()[0]

    # Recent Tasks
    cursor.execute("""
        SELECT TOP 5
            task_name,
            priority,
            status
        FROM tasks
        ORDER BY task_id DESC
    """)

    rows = cursor.fetchall()

    recent_tasks = []

    for row in rows:

        recent_tasks.append({

            "task_name": row.task_name,
            "priority": row.priority,
            "status": row.status

        })

    current_date = datetime.now().strftime("%d-%m-%Y")

    cursor.close()
    conn.close()

    return render_template(

        "dashboard.html",

        employee_count=employee_count,
        attendance_count=attendance_count,
        letter_count=letter_count,
        task_count=task_count,
        pending_tasks=pending_tasks,
        recent_tasks=recent_tasks,
        current_date=current_date

    )

@app.route("/employees")
@login_required
def employees():

    search = request.args.get("search", "").strip()

    conn = get_conn()
    cursor = conn.cursor()

    sql = """
    SELECT
        employee_id,
        employee_code,
        employee_name,
        organization,
        designation,
        qualification,
        email,
        mobile_no,
        date_of_birth,
        joining_date,
        blood_group,
        address,
        photo,
        status
    FROM employees
    """

    if search:

        sql += """
        WHERE
            employee_name LIKE ?
            OR employee_code LIKE ?
            OR organization LIKE ?
            OR designation LIKE ?
            OR mobile_no LIKE ?
        """

        value = "%" + search + "%"

        cursor.execute(
            sql,
            (value, value, value, value, value)
        )

    else:

        cursor.execute(sql)

    rows = cursor.fetchall()

    employee_list = []

    for row in rows:

        employee_list.append({

    "employee_id": row.employee_id,
    "employee_code": row.employee_code,
    "employee_name": row.employee_name,

    # Map database columns to the names used in your HTML
    "department": row.organization,

    "designation": row.designation,
    "qualification": row.qualification,
    "email": row.email,

    "mobile": row.mobile_no,

    "date_of_birth": row.date_of_birth,

    "date_of_joining": row.joining_date,

    "blood_group": row.blood_group,
    "address": row.address,

    "profile_picture": row.photo,

    "status": row.status

})

    cursor.close()
    conn.close()

    return render_template(
        "employees.html",
        employees=employee_list,
        search=search
    )


@app.route("/addemployee")
@login_required
def addemployee():

    return render_template("addemployee.html")

@app.route("/saveemployee", methods=["POST"])
@login_required
def saveemployee():

    employee_code = request.form["employee_code"].strip()
    employee_name = request.form["employee_name"].strip()

    # HTML field -> Database column
    organization = request.form["department"]
    designation = request.form["designation"]
    qualification = request.form["qualification"]
    email = request.form["email"]
    mobile_no = request.form["mobile"]
    date_of_birth = request.form["date_of_birth"] or None
    joining_date = request.form["date_of_joining"] or None
    blood_group = request.form["blood_group"]
    address = request.form["address"]
    status = request.form["status"]

    photo = None

    file = request.files.get("profile_picture")

    if file and file.filename != "":

        if allowed_file(file.filename):

            photo = secure_filename(
                employee_code + "_" + file.filename
            )

            file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    photo
                )
            )

    conn = get_conn()
    cursor = conn.cursor()

    # Check duplicate employee code
    cursor.execute(
        "SELECT employee_id FROM employees WHERE employee_code=?",
        (employee_code,)
    )

    if cursor.fetchone():

        cursor.close()
        conn.close()

        flash("Employee Code already exists.")

        return redirect("/addemployee")

    cursor.execute("""
        INSERT INTO employees
        (
            employee_code,
            employee_name,
            organization,
            designation,
            qualification,
            email,
            mobile_no,
            date_of_birth,
            joining_date,
            blood_group,
            address,
            photo,
            status
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,
    (
        employee_code,
        employee_name,
        organization,
        designation,
        qualification,
        email,
        mobile_no,
        date_of_birth,
        joining_date,
        blood_group,
        address,
        photo,
        status
    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Employee Added Successfully")

    return redirect("/employees")

@app.route("/viewemployee/<int:id>")
@login_required
def viewemployee(id):

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM employees WHERE employee_id=?",
        id
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:

        return redirect("/employees")

    return render_template(
        "viewemployee.html",
        employee=row
    )

@app.route("/editemployee/<int:id>")
@login_required
def editemployee(id):

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            employee_id,
            employee_code,
            employee_name,
            organization,
            designation,
            qualification,
            email,
            mobile_no,
            date_of_birth,
            joining_date,
            blood_group,
            address,
            photo,
            status
        FROM employees
        WHERE employee_id = ?
    """, (id,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return redirect("/employees")

    employee = {

        "employee_id": row[0],
        "employee_code": row[1],
        "employee_name": row[2],

        # Convert DB names to HTML names
        "department": row[3],

        "designation": row[4],
        "qualification": row[5],
        "email": row[6],

        "mobile": row[7],

        "date_of_birth": row[8],

        "date_of_joining": row[9],

        "blood_group": row[10],
        "address": row[11],

        "profile_picture": row[12],

        "status": row[13]

    }

    return render_template(
        "editemployee.html",
        employee=employee
    )

@app.route("/updateemployee", methods=["POST"])
@login_required
def updateemployee():

    employee_id = request.form["employee_id"]

    employee_code = request.form["employee_code"]
    employee_name = request.form["employee_name"]
    organization = request.form["department"]
    designation = request.form["designation"]
    qualification = request.form["qualification"]
    email = request.form["email"]
    mobile_no = request.form["mobile"]
    date_of_birth = request.form["date_of_birth"] or None
    joining_date = request.form["date_of_joining"] or None
    blood_group = request.form["blood_group"]
    address = request.form["address"]
    status = request.form["status"]

    conn = get_conn()
    cursor = conn.cursor()

    picture = request.files.get("profile_picture")

    if picture and picture.filename != "":

        filename = secure_filename(
            employee_code + "_" + picture.filename
        )

        picture.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        cursor.execute("""
            UPDATE employees
            SET
                employee_code=?,
                employee_name=?,
                organization=?,
                designation=?,
                qualification=?,
                email=?,
                mobile_no=?,
                date_of_birth=?,
                joining_date=?,
                blood_group=?,
                address=?,
                photo=?,
                status=?
            WHERE employee_id=?
        """,
        (
            employee_code,
            employee_name,
            organization,
            designation,
            qualification,
            email,
            mobile_no,
            date_of_birth,
            joining_date,
            blood_group,
            address,
            filename,
            status,
            employee_id
        ))

    else:

        cursor.execute("""
            UPDATE employees
            SET
                employee_code=?,
                employee_name=?,
                organization=?,
                designation=?,
                qualification=?,
                email=?,
                mobile_no=?,
                date_of_birth=?,
                joining_date=?,
                blood_group=?,
                address=?,
                status=?
            WHERE employee_id=?
        """,
        (
            employee_code,
            employee_name,
            organization,
            designation,
            qualification,
            email,
            mobile_no,
            date_of_birth,
            joining_date,
            blood_group,
            address,
            status,
            employee_id
        ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Employee Updated Successfully")

    return redirect("/employees")

@app.route("/deleteemployee/<int:id>")
@login_required
def deleteemployee(id):

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute(

        "UPDATE employees SET status='Inactive' WHERE employee_id=?",

        id

    )

    conn.commit()

    cursor.close()

    conn.close()

    flash("Employee Deactivated")

    return redirect("/employees")

@app.route("/deleteemployeepermanent/<int:id>")
@login_required
def deleteemployeepermanent(id):

    conn = get_conn()

    cursor = conn.cursor()

    try:

        cursor.execute(

            "DELETE FROM employees WHERE employee_id=?",

            id

        )

        conn.commit()

        flash("Employee Deleted")

    except Exception:

        conn.rollback()

        flash("Employee cannot be deleted because related records exist.")

    finally:

        cursor.close()

        conn.close()

    return redirect("/employees")

@app.route("/tasks")
@login_required
def tasks():

    search = request.args.get("search", "").strip()

    conn = get_conn()
    cursor = conn.cursor()

    sql = """
    SELECT
        t.task_id,
        e.employee_name,
        t.employee_id,
        t.task_name,
        t.description,
        t.assigned_date,
        t.due_date,
        t.priority,
        t.status,
        t.remarks
    FROM tasks t
    INNER JOIN employees e
        ON t.employee_id = e.employee_id
    """

    if search:

        sql += """
        WHERE
            t.task_name LIKE ?
            OR e.employee_name LIKE ?
            OR t.status LIKE ?
            OR t.priority LIKE ?
        """

        value = "%" + search + "%"

        cursor.execute(
            sql,
            value,
            value,
            value,
            value
        )

    else:

        cursor.execute(sql)

    rows = cursor.fetchall()

    task_list = []

    for row in rows:

        task_list.append({

            "task_id": row[0],
            "employee_name": row[1],
            "employee_id": row[2],
            "task_name": row[3],
            "description": row[4],
            "assigned_date": row[5],
            "due_date": row[6],
            "priority": row[7],
            "status": row[8],
            "remarks": row[9]

        })

    cursor.close()
    conn.close()

    return render_template(
        "tasks.html",
        tasks=task_list,
        search=search
    )

@app.route("/addtask")
@login_required
def addtask():

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        employee_id,
        employee_name

    FROM employees

    WHERE status='Active'

    ORDER BY employee_name

    """)

    employees = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template(
        "addtask.html",
        employees=employees
    )

@app.route("/savetask", methods=["POST"])
@login_required
def savetask():

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO tasks
    (
        employee_id,
        task_name,
        description,
        assigned_date,
        due_date,
        priority,
        status,
        remarks
    )

    VALUES
    (?,?,?,?,?,?,?,?)

    """,

    (

        request.form["employee_id"],
        request.form["task_name"],
        request.form["description"],
        request.form["assigned_date"],
        request.form["due_date"],
        request.form["priority"],
        request.form["status"],
        request.form["remarks"]

    ))

    conn.commit()

    cursor.close()

    conn.close()

    flash("Task Added Successfully")

    return redirect("/tasks")

@app.route("/edittask/<int:id>")
@login_required
def edittask(id):

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM tasks WHERE task_id=?",

        id

    )

    task = cursor.fetchone()

    cursor.execute("""

    SELECT

        employee_id,
        employee_name

    FROM employees

    WHERE status='Active'

    ORDER BY employee_name

    """)

    employees = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template(

        "edittask.html",

        task=task,

        employees=employees

    )

@app.route("/updatetask", methods=["POST"])
@login_required
def updatetask():

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE tasks

    SET

        employee_id=?,
        task_name=?,
        description=?,
        assigned_date=?,
        due_date=?,
        priority=?,
        status=?,
        remarks=?

    WHERE task_id=?

    """,

    (

        request.form["employee_id"],
        request.form["task_name"],
        request.form["description"],
        request.form["assigned_date"],
        request.form["due_date"],
        request.form["priority"],
        request.form["status"],
        request.form["remarks"],
        request.form["task_id"]

    ))

    conn.commit()

    cursor.close()

    conn.close()

    flash("Task Updated Successfully")

    return redirect("/tasks")

@app.route("/deletetask/<int:id>")
@login_required
def deletetask(id):

    conn = get_conn()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM tasks WHERE task_id=?",

        id

    )

    conn.commit()

    cursor.close()

    conn.close()

    flash("Task Deleted Successfully")

    return redirect("/tasks")

@app.route("/attendance")
@login_required
def attendance():

    search = request.args.get("search", "").strip()

    conn = get_conn()
    cursor = conn.cursor()

    # ---------- Summary ----------
    cursor.execute("SELECT COUNT(*) FROM attendance")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE attendance_status='Present'")
    present = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE attendance_status='Leave'")
    leave = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE attendance_status='Half Day'")
    half_day = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE attendance_status='On Duty'")
    on_duty = cursor.fetchone()[0]

    # ---------- Attendance List ----------

    sql = """
    SELECT
        a.attendance_id,
        e.employee_name,
        a.attendance_date,
        a.attendance_status,
        a.leave_type,
        a.purpose,
        a.remarks

    FROM attendance a

    INNER JOIN employees e

        ON a.employee_id = e.employee_id
    """

    if search:

        sql += """
        WHERE
            e.employee_name LIKE ?
            OR a.attendance_status LIKE ?
            OR a.leave_type LIKE ?
        """

        value = "%" + search + "%"

        cursor.execute(sql, (value, value, value))

    else:

        cursor.execute(sql)

    attendance = []

    for row in cursor.fetchall():

        attendance.append({

            "attendance_id": row[0],
            "employee_name": row[1],
            "attendance_date": row[2],
            "attendance_status": row[3],
            "leave_type": row[4],
            "purpose": row[5],
            "remarks": row[6]

        })

    cursor.close()
    conn.close()

    return render_template(

        "attendance.html",

        attendance=attendance,

        search=search,

        total=total,

        present=present,

        leave=leave,

        half_day=half_day,

        on_duty=on_duty

    )

@app.route("/addattendance")
@login_required
def addattendance():

    conn=get_conn()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT

        employee_id,
        employee_name

    FROM employees

    WHERE status='Active'

    ORDER BY employee_name

    """)

    employees=[]

    for row in cursor.fetchall():

        employees.append({

            "employee_id":row[0],
            "employee_name":row[1]

        })

    cursor.close()
    conn.close()

    return render_template(

        "addattendance.html",

        employees=employees

    )

@app.route("/saveattendance",methods=["POST"])
@login_required
def saveattendance():

    employee_id=request.form["employee_id"]

    attendance_date=request.form["attendance_date"]

    attendance_status=request.form["attendance_status"]

    leave_type=request.form["leave_type"]

    purpose=request.form["purpose"]

    remarks=request.form["remarks"]

    conn=get_conn()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT attendance_id

    FROM attendance

    WHERE employee_id=?

    AND attendance_date=?

    """,

    (

        employee_id,

        attendance_date

    ))

    if cursor.fetchone():

        cursor.close()

        conn.close()

        flash("Attendance already entered for this employee.")

        return redirect("/addattendance")

    cursor.execute("""

    INSERT INTO attendance

    (

        employee_id,
        attendance_date,
        attendance_status,
        leave_type,
        purpose,
        remarks

    )

    VALUES

    (?,?,?,?,?,?)

    """,

    (

        employee_id,
        attendance_date,
        attendance_status,
        leave_type,
        purpose,
        remarks

    ))

    conn.commit()

    cursor.close()

    conn.close()

    flash("Attendance Saved Successfully")

    return redirect("/attendance")

@app.route("/letters")
@login_required
def letters():

    search = request.args.get("search", "").strip()

    conn = get_conn()
    cursor = conn.cursor()

    sql = """
    SELECT
        l.letter_id,
        l.letter_no,
        l.subject,
        l.received_from,
        l.received_date,
        l.priority,
        l.status,
        e.employee_name

    FROM letters l

    LEFT JOIN employees e

        ON l.assigned_to=e.employee_id
    """

    if search:

        sql += """

        WHERE

            l.letter_no LIKE ?

            OR l.subject LIKE ?

            OR l.received_from LIKE ?

            OR e.employee_name LIKE ?

        """

        value="%" + search + "%"

        cursor.execute(

            sql,

            value,
            value,
            value,
            value

        )

    else:

        cursor.execute(sql)

    rows=cursor.fetchall()

    letters=[]

    for row in rows:

        letters.append({

            "letter_id":row[0],
            "letter_no":row[1],
            "subject":row[2],
            "received_from":row[3],
            "received_date":row[4],
            "priority":row[5],
            "status":row[6],
            "employee_name":row[7]

        })

    cursor.close()
    conn.close()

    return render_template(

        "letters.html",

        letters=letters,

        search=search

    )

@app.route("/addletter")
@login_required
def addletter():

    print(">>> addletter() started")

    conn = get_conn()
    cursor = conn.cursor()

    print(">>> Connected to database")

    cursor.execute("""
        SELECT employee_id, employee_name
        FROM employees
        WHERE status='Active'
        ORDER BY employee_name
    """)

    print(">>> Query executed")

    employees = []

    for row in cursor.fetchall():
        employees.append({
            "employee_id": row[0],
            "employee_name": row[1]
        })

    print(">>> Employees:", employees)

    cursor.close()
    conn.close()

    return render_template(
        "addletter.html",
        employees=employees
    )


@app.route("/saveletter",methods=["POST"])
@login_required
def saveletter():

    conn=get_conn()

    cursor=conn.cursor()

    letter_no=request.form["letter_no"].strip()

    cursor.execute(

        "SELECT letter_id FROM letters WHERE letter_no=?",

        letter_no

    )

    if cursor.fetchone():

        cursor.close()

        conn.close()

        flash("Letter Number already exists.")

        return redirect("/addletter")

    cursor.execute("""

    INSERT INTO letters

    (

        letter_no,
        subject,
        received_from,
        received_date,
        assigned_to,
        priority,
        status,
        remarks

    )

    VALUES

    (?,?,?,?,?,?,?,?)

    """,

    (

        letter_no,
        request.form["subject"],
        request.form["received_from"],
        request.form["received_date"],
        request.form["assigned_to"],
        request.form["priority"],
        request.form["status"],
        request.form["remarks"]

    ))

    conn.commit()

    cursor.close()

    conn.close()

    flash("Letter Saved Successfully")

    return redirect("/letters")
@app.route("/editletterstatus/<int:id>")
@login_required
def editletterstatus(id):

    conn=get_conn()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT

        letter_id,
        letter_no,
        subject,
        received_from,
        received_date,
        assigned_to,
        priority,
        status,
        remarks

    FROM letters

    WHERE letter_id=?

    """,

    id

    )

    row=cursor.fetchone()

    cursor.close()

    conn.close()

    if row is None:

        return redirect("/letters")

    letter={

        "letter_id":row[0],
        "letter_no":row[1],
        "subject":row[2],
        "received_from":row[3],
        "received_date":row[4],
        "assigned_to":row[5],
        "priority":row[6],
        "status":row[7],
        "remarks":row[8]

    }

    return render_template(

        "editletterstatus.html",

        letter=letter

    )
@app.route("/updateletterstatus", methods=["POST"])
@login_required
def updateletterstatus():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE letters
        SET status=?
        WHERE letter_id=?
    """,
    (
        request.form["status"],
        request.form["letter_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Letter Status Updated Successfully")

    return redirect("/letters")

@app.route("/reports")
@login_required
def reports():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cursor.fetchone()[0]

    try:
        cursor.execute("SELECT COUNT(*) FROM letters")
        letter_count = cursor.fetchone()[0]
    except:
        letter_count = 0

    cursor.close()
    conn.close()

    return render_template(
        "reports.html",
        employee_count=employee_count,
        task_count=task_count,
        attendance_count=attendance_count,
        letter_count=letter_count
    )


@app.route("/employee_report")
@login_required
def employee_report():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            employee_id,
            employee_name,
            organization,
            designation,
            email,
            mobile_no
        FROM employees
        ORDER BY employee_name
    """)

    employees = []

    for row in cursor.fetchall():

        employees.append({

    "employee_id": row[0],
    "employee_name": row[1],
    "department": row[2],
    "designation": row[3],
    "email": row[4],
    "mobile": row[5]

})

    cursor.close()
    conn.close()

    return render_template(
        "employee_report.html",
        employees=employees
    )

@app.route("/task_report")
@login_required
def task_report():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        e.employee_name,
        t.task_name,
        t.priority,
        t.status,
        t.assigned_date,
        t.due_date

    FROM tasks t

    INNER JOIN employees e

    ON t.employee_id=e.employee_id

    ORDER BY t.assigned_date DESC

    """)

    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "task_report.html",
        tasks=tasks
    )

@app.route("/attendance_report")
@login_required
def attendance_report():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.employee_name,

            SUM(CASE WHEN a.attendance_status='Present' THEN 1 ELSE 0 END) AS Present,

            SUM(CASE WHEN a.attendance_status='Half Day' THEN 1 ELSE 0 END) AS HalfDay,

            SUM(CASE WHEN a.attendance_status='Leave' THEN 1 ELSE 0 END) AS LeaveCount,

            SUM(CASE WHEN a.attendance_status='On Duty' THEN 1 ELSE 0 END) AS OnDuty,

            COUNT(*) AS TotalDays

        FROM attendance a

        INNER JOIN employees e
            ON a.employee_id = e.employee_id

        GROUP BY e.employee_name

        ORDER BY e.employee_name
    """)

    attendance = []

    for row in cursor.fetchall():

        attendance.append({

            "employee_name": row[0],
            "present": row[1],
            "half_day": row[2],
            "leave": row[3],
            "on_duty": row[4],
            "total_days": row[5]

        })

    cursor.close()
    conn.close()

    return render_template(
        "attendance_report.html",
        attendance=attendance
    )

@app.route("/letter_report")
@login_required
def letter_report():

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            l.letter_no,
            l.subject,
            l.received_from,
            l.received_date,
            e.employee_name,
            l.priority,
            l.status
        FROM letters l
        LEFT JOIN employees e
            ON l.assigned_to = e.employee_id
        ORDER BY l.received_date DESC
    """)

    letters = []

    for row in cursor.fetchall():

        letters.append({

            "letter_no": row[0],
            "subject": row[1],
            "received_from": row[2],
            "received_date": row[3],
            "employee_name": row[4],   # <-- This is important
            "priority": row[5],
            "status": row[6]

        })

    cursor.close()
    conn.close()

    return render_template(
        "letter_report.html",
        letters=letters
    )
@app.route("/export_excel")
@login_required
def export_excel():

    wb = Workbook()

    ws = wb.active

    ws.title = "Employees"

    ws.append([
        "Employee Code",
        "Employee Name",
        "Department",
        "Designation",
        "Mobile",
        "Email",
        "Status"
    ])

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT

    employee_code,
    employee_name,
    department,
    designation,
    mobile,
    email,
    status

    FROM employees

    ORDER BY employee_name

    """)

    for row in cursor.fetchall():

        ws.append(row)

    cursor.close()
    conn.close()

    filename = "Employee_Report.xlsx"

    wb.save(filename)

    return send_file(
        filename,
        as_attachment=True
    )

@app.route("/monthly_report")
@login_required
def monthly_report():

    conn = get_conn()
    cursor = conn.cursor()

    # Employee list
    cursor.execute("""
        SELECT employee_id, employee_name
        FROM employees
        WHERE status='Active'
        ORDER BY employee_name
    """)

    all_employees = []

    for row in cursor.fetchall():

        all_employees.append({

            "employee_id": row[0],
            "employee_name": row[1]

        })

    employee = None
    attendance_summary = {}
    attendance_records = []
    tasks = []
    letters = []

    employee_id = request.args.get("employee_id")
    selected_month = request.args.get("month")

    if employee_id and selected_month:

        year, month = selected_month.split("-")

        # Employee details
        cursor.execute("""
            SELECT
                employee_id,
                employee_name,
                organization,
                designation,
                photo
            FROM employees
            WHERE employee_id=?
        """, (employee_id,))

        row = cursor.fetchone()

        if row:

            employee = {

                "employee_id": row[0],
                "employee_name": row[1],
                "department": row[2],
                "designation": row[3],
                "profile_picture": row[4]

            }

        # Attendance
        cursor.execute("""
            SELECT
                attendance_date,
                attendance_status,
                leave_type,
                purpose,
                remarks
            FROM attendance
            WHERE employee_id=?
              AND YEAR(attendance_date)=?
              AND MONTH(attendance_date)=?
            ORDER BY attendance_date
        """,
        (
            employee_id,
            year,
            month
        ))

        rows = cursor.fetchall()

        for r in rows:

            attendance_records.append({

                "attendance_date": r[0],
                "attendance_status": r[1],
                "leave_type": r[2],
                "purpose": r[3],
                "remarks": r[4]

            })

            attendance_summary[r[1]] = attendance_summary.get(r[1], 0) + 1

        # Tasks
        cursor.execute("""
            SELECT
                task_name,
                priority,
                status,
                assigned_date,
                due_date
            FROM tasks
            WHERE employee_id=?
              AND YEAR(assigned_date)=?
              AND MONTH(assigned_date)=?
            ORDER BY assigned_date
        """,
        (
            employee_id,
            year,
            month
        ))

        for r in cursor.fetchall():

            tasks.append({

                "task_name": r[0],
                "priority": r[1],
                "status": r[2],
                "assigned_date": r[3],
                "due_date": r[4]

            })

        # Letters
        cursor.execute("""
            SELECT
                letter_no,
                subject,
                priority,
                status,
                received_date
            FROM letters
            WHERE assigned_to=?
              AND YEAR(received_date)=?
              AND MONTH(received_date)=?
            ORDER BY received_date
        """,
        (
            employee_id,
            year,
            month
        ))

        for r in cursor.fetchall():

            letters.append({

                "letter_no": r[0],
                "subject": r[1],
                "priority": r[2],
                "status": r[3],
                "received_date": r[4]

            })

    cursor.close()
    conn.close()

    return render_template(

        "Monthly_report.html",

        all_employees=all_employees,
        employee=employee,
        selected_month=selected_month,
        attendance_summary=attendance_summary,
        attendance_records=attendance_records,
        tasks=tasks,
        letters=letters

    )
@app.route("/dailywork")
@login_required
def dailywork():

    return render_template("dailywork.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )