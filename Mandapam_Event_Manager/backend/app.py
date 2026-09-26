from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
import sqlite3

from backend.database import get_db, init_db


# -------------------------------------------------
# CREATE FLASK APPLICATION
# -------------------------------------------------

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)


# Secret key used for sessions
app.secret_key = "mandapam-event-manager-secret-key"


# Create database and tables when application starts
init_db()


# -------------------------------------------------
# LOGIN REQUIRED DECORATOR
# -------------------------------------------------

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash("Please login first.")

            return redirect(
                url_for("login")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# -------------------------------------------------
# ADMIN REQUIRED DECORATOR
# -------------------------------------------------

def admin_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if session.get("role") != "admin":

            flash("Admin access required.")

            return redirect(
                url_for("login")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# -------------------------------------------------
# REGISTER
# -------------------------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # Validate fields
        if not name or not phone or not password:

            flash(
                "All fields are required."
            )

            return render_template(
                "register.html"
            )

        db = get_db()

        try:

            password_hash = generate_password_hash(
                password
            )

            db.execute(
                """
                INSERT INTO users
                (
                    name,
                    phone,
                    password_hash,
                    role
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    phone,
                    password_hash,
                    "customer"
                )
            )

            db.commit()

            flash(
                "Registration successful. Please login."
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "Phone number is already registered."
            )

        finally:

            db.close()

    return render_template(
        "register.html"
    )


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE phone = ?
            """,
            (phone,)
        ).fetchone()

        db.close()

        if user:

            try:

                password_correct = check_password_hash(
                    user["password_hash"],
                    password
                )

            except (
                ValueError,
                TypeError
            ):

                password_correct = False

        else:

            password_correct = False

        if password_correct:

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            session["role"] = user["role"]

            return redirect(
                url_for("services")
            )

        flash(
            "Invalid phone number or password."
        )

    return render_template(
        "login.html"
    )


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# -------------------------------------------------
# SERVICES
# -------------------------------------------------

@app.route("/services")
@login_required
def services():

    db = get_db()

    services_list = db.execute(
        """
        SELECT *
        FROM services
        ORDER BY id
        """
    ).fetchall()

    db.close()

    return render_template(
        "services.html",
        services=services_list
    )


# -------------------------------------------------
# BOOK SERVICE
# -------------------------------------------------

@app.route(
    "/book/<int:service_id>",
    methods=["GET", "POST"]
)
@login_required
def book(service_id):

    db = get_db()

    service = db.execute(
        """
        SELECT *
        FROM services
        WHERE id = ?
        """,
        (service_id,)
    ).fetchone()

    if service is None:

        db.close()

        flash(
            "Service not found."
        )

        return redirect(
            url_for("services")
        )

    if request.method == "POST":

        event_date = request.form.get(
            "event_date",
            ""
        ).strip()

        event_time = request.form.get(
            "event_time",
            ""
        ).strip()

        venue = request.form.get(
            "venue",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        guests_text = request.form.get(
            "guests",
            "0"
        )

        try:

            guests = int(
                guests_text
            )

            if guests < 0:

                raise ValueError

        except ValueError:

            db.close()

            flash(
                "Guests must be a valid number."
            )

            return render_template(
                "booking.html",
                service=service
            )

        if not event_date or not venue:

            flash(
                "Event date and venue are required."
            )

        else:

            db.execute(
                """
                INSERT INTO bookings
                (
                    user_id,
                    service_id,
                    event_date,
                    event_time,
                    venue,
                    guests,
                    notes,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    service_id,
                    event_date,
                    event_time,
                    venue,
                    guests,
                    notes,
                    "Pending"
                )
            )

            db.commit()

            db.close()

            flash(
                "Booking submitted successfully."
            )

            return redirect(
                url_for("my_bookings")
            )

    db.close()

    return render_template(
        "booking.html",
        service=service
    )


# -------------------------------------------------
# MY BOOKINGS
# -------------------------------------------------

@app.route("/my-bookings")
@login_required
def my_bookings():

    db = get_db()

    bookings = db.execute(
        """
        SELECT
            b.*,
            s.name AS service_name
        FROM bookings b

        JOIN services s
        ON s.id = b.service_id

        WHERE b.user_id = ?

        ORDER BY b.created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    db.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# -------------------------------------------------
# FEEDBACK
# -------------------------------------------------

@app.route(
    "/feedback",
    methods=["GET", "POST"]
)
@login_required
def feedback():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        rating = request.form.get(
            "rating",
            ""
        )

        features = ", ".join(
            request.form.getlist(
                "features"
            )
        )

        improvement = request.form.get(
            "improvement",
            ""
        ).strip()

        comments = request.form.get(
            "comments",
            ""
        ).strip()

        db = get_db()

        db.execute(
            """
            INSERT INTO feedback
            (
                user_id,
                name,
                email,
                rating,
                features,
                improvement,
                comments
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                session.get("name", ""),
                email,
                rating,
                features,
                improvement,
                comments
            )
        )

        db.commit()

        db.close()

        flash(
            "Thank you for your feedback."
        )

        return redirect(
            url_for("services")
        )

    return render_template(
        "feedback.html"
    )


# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------

@app.route("/admin")
@admin_required
def admin():

    db = get_db()

    bookings = db.execute(
        """
        SELECT
            b.*,
            u.name AS customer_name,
            u.phone,
            s.name AS service_name

        FROM bookings b

        JOIN users u
        ON u.id = b.user_id

        JOIN services s
        ON s.id = b.service_id

        ORDER BY b.created_at DESC
        """
    ).fetchall()

    feedback_rows = db.execute(
        """
        SELECT *
        FROM feedback
        ORDER BY created_at DESC
        """
    ).fetchall()

    users = db.execute(
        """
        SELECT
            id,
            name,
            phone,
            role,
            created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        feedback=feedback_rows,
        users=users
    )


# -------------------------------------------------
# UPDATE BOOKING STATUS
# -------------------------------------------------

@app.route(
    "/admin/booking/<int:booking_id>/status",
    methods=["POST"]
)
@admin_required
def update_status(booking_id):

    status = request.form.get(
        "status",
        "Pending"
    )

    allowed_statuses = {
        "Pending",
        "Confirmed",
        "Completed",
        "Cancelled"
    }

    if status not in allowed_statuses:

        flash(
            "Invalid status."
        )

        return redirect(
            url_for("admin")
        )

    db = get_db()

    db.execute(
        """
        UPDATE bookings
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            booking_id
        )
    )

    db.commit()

    db.close()

    flash(
        "Booking status updated."
    )

    return redirect(
        url_for("admin")
    )


# -------------------------------------------------
# SIMPLE API
# -------------------------------------------------

@app.route("/api/services")
def api_services():

    db = get_db()

    services_list = db.execute(
        """
        SELECT *
        FROM services
        ORDER BY id
        """
    ).fetchall()

    db.close()

    return jsonify(
        [
            dict(service)
            for service in services_list
        ]
    )


# -------------------------------------------------
# START APPLICATION
# -------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )