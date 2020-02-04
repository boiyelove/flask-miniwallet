import sys
import json
import logging
from flask import render_template, abort, request, Response, redirect, flash, url_for, g, Markup
from flask_login import login_required, current_user
import miniwalletapp as app
from miniwalletapp.config import PAYSTACK_SECRET_KEY as srk
from miniwalletapp.models import User, TransactionLog, BankAccount, WithdrawalRequest

from .utils import init_transaction, verify_hook, resend_otp, finalize_withdrawal
from .forms import BankForm
from . import dashboard as dbp
from ..models import BankAccount, Bank, OTPLog

login_manager = app.login_manager
data = None

@login_manager.user_loader
def load_user(user_id):
	try: 
		user = User.query.filter(User.id == int(user_id)).first()
		return user
	except:
		return None


@dbp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(*args, **kwargs):

	trlogs = TransactionLog.query.filter_by(marked=True).order_by(TransactionLog.timestamp.desc()).paginate(1,10,error_out=False)
	
	return render_template('dashboard.html', title="Dashboard", trlogs = trlogs)



@dbp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdrawal():
	if current_user.validate_bank_account():
		if request.method == 'POST':
			amount = int(request.form['amount'])
			if amount is not None and amount > 100:
				if current_user.balance >  amount:
					withdrawal = current_user.withdraw(amount)
					if withdrawal['status']:
						flash('Your withdrawal was successful, Your acccount will be credited shortly')
					else:
						flash(withdrawal['message'])
					return redirect(url_for('dashboard.dashboard'))
	else:
		message = Markup('<a href="' + url_for('dashboard.bank_settings') + '">Please, provide bank account details before continuing to withdrawals</a>')
		flash(message)



	return render_template('withdrawal.html', title="withdraw")


@dbp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
	data = {}
	if request.method == 'GET':
		logging.error('deposit get request')
		refcode = request.args.get('ref', None)
		if refcode:
			trlog = TransactionLog.query.filter_by(code=refcode).first()
			logging.error('trlog is', trlog)
			logging.error('type trlog is', type(trlog))
			logging.error('trlog marked is', trlog.marked)
			if trlog:
				if not trlog.marked:
					trlog = trlog.remit_pay()
				if trlog.marked:
					flash("You deposit has been completed successfully")
					data['url'] = url_for('dashboard.dashboard')
					do_json = request.args.get('json', False)
					if do_json:return Response(json.dumps(data), mimetype='application/json', status=201)
			else:
				flash("Opps! something went wrong with your transaction reference")
	elif (request.method == 'POST'):

		form = request.get_json(force=True) 
		if form:
			amount = int(form['amount'])
			if amount >= 100:
				ref = init_transaction((amount * 100), current_user.email)
				
				
				data['reference'] = ref
				data['amount'] = amount * 100
				data['email'] = current_user.email 
				return Response(json.dumps(data), mimetype='application/json', status=201)
		else:
			return Response(json.dumps(data), mimetype='application/json', status=406)



	# if request.method== 'POST':
	# 	if amount_form.validate():



	return render_template("deposit.html", title="deposit", data=data)



@dbp.route('/settings')
@login_required
def account_settings():
			

	return render_template("settings.html", title="Settings", data=data)



@dbp.route('/settings/bank_account', methods=['GET', 'POST'])
@login_required
def bank_settings():
	bnk_acc = current_user.get_bank_account()
	form = BankForm(request.form)	
	if request.method == 'GET' and bnk_acc:
	
		form = BankForm(bank = bnk_acc.bank_id,
			account_name = bnk_acc.account_name,
			account_number = bnk_acc.account_number)
		form.bank.data = bnk_acc.bank_id
	
	if request.method == 'POST':
		if form.validate_on_submit():
			bank = Bank.query.filter_by(id=form.bank.data).first()
			uid = current_user.get_id()
			if bnk_acc is not None:
				bnk_acc.bank_id = form.bank.data
				bnk_acc.account_name = form.account_name.data
				bnk_acc.account_number = (form.account_number.data).strip()
				flash("Your bank account details have been updated successfully")
			else:
				bnk_acc = BankAccount(bank_id = form.bank.data,
					account_name = form.account_name.data,
					account_number = form.account_number.data,
					user_id = uid )
				app.db.session.add(bnk_acc)
				flash("Your bank account details have been save successfully")
			app.db.session.commit()
	return render_template("bank_settings.html", title="Bank Accounts", data=data, form=form)



@dbp.route('/webhook/' + srk, methods=['POST'])
def webhook():
	if verify_hook(request):
		logging.error('passed hooktest')
		data = request.json
		resp_data = data['data']
		logging.error('data is', data)
		if data['event'] == 'transfer.success':
			logging.error('passed transfer success')
			trlog = TransactionLog.query.filter_by(code=resp_data['transfer_code']).first()
			if trlog is not None:
				trlog = trlog.remit_pay()
			return Response({}, status=200)
		elif data['event'] == 'transfer.failed':
			trlog = TransactionLog.query.filter_by(code=resp_data['transfer_code']).first()
			if trlog is not None:
				trlog = trlog.reverse_pay()
			return Response({}, status=200)

		elif data['event'] == 'charge.success':
			trlog = TransactionLog.query.filter_by(code=resp_data['reference']).first()
			if trlog is not None:
				trlog.amount = data['data']['amount']
				trlog = trlog.remit_pay()

			return Response({}, status=200)
		# return Response({}, status=200)
	return Response({}, status=400) #non 200


@dbp.route('/otp_setting/', methods=['GET', 'POST'])
def otp_setting():
	otplogs = OTPLog.query.order_by(OTPLog.timestamp.desc()).paginate(1,10,error_out=False)
	mode = OTPLog.get_mode()
	if request.method == 'POST':
		logging.error('submit_button is', request.form['submit_button'])
		if request.form['submit_button'] == 'disable-otp':
			message = OTPLog.disable_otp()
			flash(message)

		elif request.form['submit_button'] == 'enable-otp':
			message = OTPLog.enable_otp()
			flash(message)
			mode = OTPLog.get_mode()

		elif request.form['submit_button'] == 'submit-otp':
			if int(request.form['otp-code']):
				message = OTPLog.disable_otp(code = int(request.form['otp-code']))
				flash(message)
				mode = OTPLog.get_mode()
	return render_template("otp_setting.html", otpstatus = mode, title="OTP Settings", otplogs = otplogs)


@dbp.route('/withdrawal_setting/', methods=['GET', 'POST'])
def confirm_withdrawals():
	data = {}
	otp_mode = True #OTPLog.get_mode()
	submit_button = None
	trlog = None
	if request.method == 'POST':
		# withdrawals = request.form.getlist('withdrawals', None)
		# print('Request.forms is', request.form, file=sys.stderr)
		trlog = request.form.get('trlog', None)
		submit_button = request.form.get('submit_button', None)
		# if submit_button == 'resend-otp':
		# 	if trlog:
		# 		response = resend_otp(trlog)
		# 		print('response is', response, file=sys.stderr)
		# 		submit_button =  'resent-otp'
		# 		flash(response['message'])
		# 	else:
		# 		flash("Oops! something went wrong, pleae select a valid withdrawal")
		if trlog:
			wreq = WithdrawalRequest.query.filter_by(id=trlog).first()

			if  submit_button == 'confim-withdrawal':
				response = wreq.accept()
				flash(response['message'])
			elif  submit_button == 'deny-withdrawal':
				print('wreq is ', wreq, file=sys.stderr)
				if wreq.deny():
					flash("The withdrawal has been denied and the funds credited back to user's balance")
				else:
					flash('Oops! an error occured')

		# elif  submit_button == 'submit-otp':
		# 	otp_code = request.form.get('otp_code', None)

		# 	if otp_code:
		# 		# trlog_item = trlog.query.filter_by(code=trlog)
		# 		# response = trlog_item.confirm_withdrawal(otp_code)
		# 		response = finalize_withdrawal(trlog, int(otp_code))
		# 		if response:
		# 			flash(response['message'])
		# 		else:
		# 			flash('an error occured!')
		# 	submit_button = None

	# otplogs = OTPLog.query.order_by(OTPLog.timestamp.desc()).paginate(1,10,error_out=False)
	# mode = OTPLog.get_mode()
	# if request.method == 'POST':
	# 	logging.error('submit_button is', request.form['submit_button'])
	# 	if request.form['submit_button'] == 'disable-otp':
	# 		message = OTPLog.disable_otp()
	# 		flash(message)

	# 	elif request.form['submit_button'] == 'enable-otp':
	# 		message = OTPLog.enable_otp()
	# 		flash(message)
	# 		mode = OTPLog.get_mode()

	# 	elif request.form['submit_button'] == 'submit-otp':
	# 		if int(request.form['otp-code']):
	# 			message = OTPLog.disable_otp(code = int(request.form['otp-code']))
	# 			flash(message)
	# 			mode = OTPLog.get_mode()
	trlogs = WithdrawalRequest.query.all()
	print('Withdrawal requests is', trlogs, file=sys.stderr)

	return render_template("confirm_withdrawal.html",
		title="Withdrawal Settings",
		trlogs = trlogs, 
		otp_mode = otp_mode,
		trlog = trlog,
		submit_button=submit_button)