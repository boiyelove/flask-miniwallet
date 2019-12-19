from flask import flash, redirect, render_template, url_for, request, session
from flask_login import login_required, login_user, logout_user
from . import auth
from .forms import LoginForm, RegistrationForm
from .. import db
from ..models import User

@auth.route('/register', methods=['GET', 'POST'])
def register():

	form = RegistrationForm(request.form)
	if form.validate_on_submit():
		user = User(
			email = form.email.data,
			first_name = form.first_name.data,
			last_name = form.last_name.data)
		user.set_password(form.password.data)

		db.session.add(user)
		db.session.commit()
		print('user saved')

		flash("You have successfully registered! You may now login")
		return redirect(url_for('auth.login'))
	else:
		flash("Oops! something went wrong")
		return render_template('register.html', form=form, title="Regsiter")

@auth.route('/', methods=['GET'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	if form.validate_on_submit():
		print('email is ' + form.email.data)
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user)
			session['xid'] = user.id
			return redirect(url_for('dashboard.dashboard'))
		else:
			flash("Invalid email or password")

	return render_template("login.html", form=form, title='Login')

@auth.route('/logout')
def logout():
	logout_user()
	session.pop('xid', None)
	flash("you have been successfully logged out")
	return redirect(url_for('auth.login'))