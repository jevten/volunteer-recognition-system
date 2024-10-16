# Flask modules
from flask import Blueprint, redirect, url_for, render_template, flash, abort
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from flask_mail import Message


# Local modules
from app.models import User
from app.extensions import db, bcrypt, login_manager
from app.forms import LoginForm, RegistrationForm
from app.extensions import mail
routes_bp = Blueprint('routes', __name__, url_prefix="/")


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).one_or_none()


@routes_bp.route("/")
@login_required
def home():
    return render_template('index.html')


@routes_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.home"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = User.query.filter_by(email=email).one_or_none()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember_me)
            flash(f"Logged in successfully as {user.name}", 'success')
            return redirect(url_for("routes.home"))
        else:
            flash("Invalid email or password", 'danger')

    return render_template('auth/login.html', form=form)


@routes_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("routes.home"))

    form = RegistrationForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.generate_password_hash(password)

        # Add user to database
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Login user
        login_user(new_user)

        flash(f'Account created successfully! You are now logged in as {new_user.name}.', 'success')
        return redirect(url_for("routes.home"))

    return render_template('auth/register.html', form=form)

@routes_bp.route("/user/<name>")
@login_required
def user_profile(name):
    user = User.query.filter_by(name=name).one_or_none()
    return render_template('user.html', user=user)

@routes_bp.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.login"))

#role restricted route decorator
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role):
                abort(403)  # Forbidden if not role
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

#skeleton for admin dashboard
@routes_bp.route("/admin")
@role_required("admin")
def admin_dashboard():
    return "Admin Dashboard"

def send_email(subject, recipient, body):
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)