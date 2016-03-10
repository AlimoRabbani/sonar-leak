__author__ = 'Alimohammad'
from flask import redirect, url_for, request, render_template, abort
from flask_login import login_user, login_required, current_user, logout_user
from flask import current_app

from data_model import User
from forms import LoginForm

from flask import Blueprint

common_views = Blueprint('common_views', __name__, template_folder='templates')

@common_views.route('/', methods=["GET", "POST"])
def index():
    form = LoginForm(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        user = User.get(email=form.email.data)
        if user is not None:
            if user.authenticate(form.password.data):
                if login_user(user, remember=True):
                    current_app.logger.debug(url_for("user_views.devices_view"))
                    return redirect(request.args.get("next") or url_for("user_views.devices_view"))
            else:
                error = "Email and password do not match!"
        else:
            error = "A user with this email does not exist!"
    return render_template("index.html", form=form, error=error)

@common_views.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("common_views.index"))
