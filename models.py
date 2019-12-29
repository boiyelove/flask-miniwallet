import logging
import requests
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from paystackapi.paystack import Transfer
from paystackapi.trecipient import TransferRecipient
from paystackapi.transaction import Transaction
from miniwalletapp import db, login_manager
from miniwalletapp.config import paystack_secret_key

# bankaccounts = db.Table('bankaccount',
# 	db.Column('bankaccount_id', db.Integer, db.ForeignKey('bankaccounts.id'), primary_key=True),
# 	db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
# 	)


class Bank(db.Model):

	__tablename__ = 'banks'
	

	id = db.Column(db.Integer, primary_key=True)
	bank_name  = db.Column(db.String(100), index=True)
	code = db.Column(db.String(3), unique=True)
	slug = db.Column(db.String(25), unique=True)
	active = db.Column(db.Boolean, default=True)


	@classmethod
	def get_banklist(cls):
		bank_list = Bank.query.filter(Bank.active == True).all()
		bank_tuple = []
		if bank_list:
			bank_tuple = [(item.id, item.bank_name) for item in bank_list]
		else:
			cls.update_bank_list()
		return bank_tuple

	@classmethod
	def update_bank_list(cls):
		response = requests.get('https://api.paystack.co/bank', headers={"Authorization": paystack_secret_key},
		params= {'currency': 'NGN', 'country':'Nigeria'})
		res_data = response.json()
		if res_data['status'] and (res_data['message'] == "Banks retrieved"):
			for item in res_data["data"]:
				bank = Bank.query.filter_by(slug = item['slug']).first()
				if bank is not None and  item['active'] != bank.active:
					bank.active = item['active']
					if item['is_deleted']: bank.active = False
				if bank is None:
					bank = cls(bank_name = item['name'],
					  slug = item['slug'],
					  code = item['code'],
					  active = item['active'])
					db.session.add(bank)

		db.session.commit()


class User(UserMixin, db.Model):

	__tablename__  = 'users'

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(60), index=True, unique=True)
	first_name = db.Column(db.String(60))
	last_name = db.Column(db.String(60))
	balance = db.Column(db.Integer, default=0)
	is_admin = db.Column(db.Boolean, default=False)
	password_hash = db.Column(db.String(100))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	transactions = db.relationship('TransactionLog', backref='user', lazy=True)
	bankaccounts = db.relationship('BankAccount',  backref='user', lazy=True)


	@property
	def password(self):
		raise AttributeError("password is not a readable attribute")


	def set_password(self, password):

		self.password_hash = generate_password_hash(password)
	

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return "%s %s".format(self.first_name, self.last_name)

	def validate_bank_account(self):
		bnkacc = BankAccount.query.filter_by(user=self).first()
		if bnkacc:
			if bnkacc.bank_id and bnkacc.account_name and bnkacc.account_number:
				return True
		return False

	def get_bank_account(self):
		return BankAccount.query.filter_by(user=self).first()

	@login_manager.user_loader
	def load_user(user_id):
		return User.query.get(int(user_id))

	def withdraw(self, amount):
		reply={'status': False, 'message': "An error occured from withdrawal"}
		#if user has the right amount
		if self.balance > amount:
			bankacc = BankAccount.query.filter_by(user_id=self.id).first()
			rcode_reply = bankacc.create_recipient()

			# if paystack recipient was created successfully
			if rcode_reply['status']:
				response = Transfer.initiate(
					source='balance',
					reason = 'User %s Withdrawal: %s' % (self.id, self.email),
					amount = amount * 100,
					recipient = rcode_reply['recipient_code'])
				logging.error('response is', response)

				# if transfer was initiated successfully
				if response['status']:
					trf = TransactionLog(
					user_id = self.id,
					transaction_type = False,
					amount = amount * 100,
					code = response['data']['transfer_code']
					)
					db.session.add(trf)
					db.session.commit()
					trf = trf.remit_pay()
					response =  Transfer.finalize(
						transfer_code = response['data']['transfer_code'])
					logging.error('YXE response after transfer is ', response)
					logging.error('response status ', response['status'])
				reply['status'] = response['status']
				reply['message'] = response['message']
			else:
				reply = rcode_reply

		return reply




class TransactionLog(db.Model):
	__tablename__ = 'transactionlogs'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	#transaction_type - False: Withdrawal, True: Deposit
	transaction_type = db.Column(db.Boolean, default=True)
	amount = db.Column(db.Integer, default=0)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	code = db.Column(db.String(30), unique=True) 
	marked = db.Column(db.Boolean, default=False)

	def check_transaction(self):
		if self.transaction_type == False:
			response = Transfer.verify(reference=self.code)
			if response['status']:
				if response['data']['status'] == "success":
					return True
		elif self.transaction_type == True:
			check = Transaction.verify(reference = self.code)
			if response['status']:
				if response['data']['status'] == "success":
					return True
		#parse check data to give result, true, false, pending
		return False

	def remit_pay(self):
		if not self.marked:
			user = User.query.get(self.user_id)
			if self.transaction_type == True:
				if self.check_transaction():			
					user.balance = user.balance + self.get_amount()
					self.marked = True
			elif self.transaction_type == False:	
				user.balance = user.balance - self.get_amount()
				self.marked = True
			db.session.commit()
		return db.session.refresh(self)

	def reverse_pay(self):
		user = User.query.get(self.user_id)
		if self.marked == True and self.transaction_type == True:
			user.balance = user.balance - self.get_amount()
		if self.marked == False and self.transaction_type == False:
			user.balance = user.balance - self.get_amount()
		db.session.commit()
		return db.session.refresh(self)

	def set_amount(self, amount):
		self.amount = amount * 100
		return self.amount

	def get_amount(self):
		return (self.amount / 100)

		

class BankAccount(db.Model):

	__tablename__ = 'bankaccounts'

	id = db.Column(db.Integer, primary_key=True)
	bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'))
	bank = db.relationship('Bank', backref='bankaccount')
	account_name =  db.Column(db.String(60))
	account_number = db.Column(db.String(20))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	recipient_code = db.Column(db.String(60), default=None)

	def create_recipient(self):
		
		bnk = Bank.query.filter_by(id=self.bank_id).first()
		response = TransferRecipient.create(
			type="nuban",
			name=self.account_name,
			account_number= self.account_number,
			bank_code=bnk.code,
			)
		reply={'status': response['status'], 'message': response['message']}
		logging.error('response is ', response)
		logging.error('response status is ', response['status'])
		logging.error('response message is ', response['message'])
		reply['message'] = response['message']
		if response['status']:
			self.recipient_code = response['data']['recipient_code']
			reply['recipient_code']  = response['data']['recipient_code']
			db.session.commit()
			

		return reply


class OTPLog(db.Model):

	__tablename__ = 'otplogs'

	id = db.Column(db.Integer, primary_key=True)
	mode = db.Column(db.Boolean, default=True)
	message = db.Column(db.String(30))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

	@classmethod
	def get_mode(cls):
		otplog =  cls.query.order_by(cls.timestamp.desc()).first()
		if otplog is not None:
			return otplog.mode
		return True

	@classmethod
	def enable_otp(cls):
		url = 'https://api.paystack.co/transfer/enable_otp'
		resp= requests.post(url, data={}, headers={'Authorization': 'Bearer ' + paystack_secret_key})
		if resp.status_code == 200:
			resp = resp.json()
			otplog = cls(mode = True,
				message = resp['message'])
			db.session.add(otplog)
			db.session.commit()
			return resp['message']
		return "Opp! something went wrong"

	@classmethod
	def disable_otp(cls, code=None):
		if code and type(code) is not int: raise TypeError('OTP code must be in Integer format')
		logging.error('code is', code)
		logging.error('code string is', str(code))
		logging.error('code formated is ', "%s" % code )
		url = url = 'https://api.paystack.co/transfer/disable_otp'
		if code:
			code = {'otp': "%s" % code}
			url = 'https://api.paystack.co/transfer/disable_otp_finalize'
		resp = requests.post(url, json=code, headers={'Authorization': 'Bearer ' +  paystack_secret_key,
			'Content-Type': 'application/json'})
		logging.error('text is', resp.text)
		logging.error('status_code is', resp.status_code)
		if resp.status_code == 200:
			resp = resp.json()
			mode = OTPLog.get_mode()
			if resp['message'] == 'OTP already disabled for transfers': mode = False
			otplog = cls(mode =mode,
					message = resp['message'])
			if code: otplog.mode = False
			db.session.add(otplog)
			db.session.commit()
			return resp['message']
		return "Opp! something went wrong"



