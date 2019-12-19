from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from miniwalletapp import db, login_manager


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
	bankaccounts = db.relationship('BankAccounts', backref='user', lazy=True)


	@property
	def password(self):
		
		raise AttributeError("password is not a readable attribute")


	def set_password(self, password):

		self.password_hash = generate_password_hash(password)
	

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return "%s %s".format(self.first_name, self.last_name)

	@login_manager.user_loader
	def load_user(user_id):
		return User.query.get(int(user_id))

	def withdraw(self, bank_id, amount):
		if self.balance > ampunt:
			bankacc = BankAccount.query.filter_by(user=user).first()
			code = bankacc.recipient_code or  bankacc.create_recipient()
			response = Transfer.initiate(
				source='balance',
				reason = 'User Withdrawal',
				amount = amount,
				recipient = code)
			# check response
			'''
			{
				"status":true
				"message":"Transfer requires OTP to continue"
				"data":{
				"integration":100073
				"domain":"test"
				"amount":3794800
				"currency":"NGN"
				"source":"balance"
				"reason":"Calm down"
				"recipient":28
				"status":"otp"
				"transfer_code":"TRF_1ptvuv321ahaa7q"
				"id":14
				"createdAt":"2017-02-03T17:21:54.508Z"
				"updatedAt":"2017-02-03T17:21:54.508Z"
				}
			}			
			'''

			trf = TransactionLog(
			user = self,
			transaction_type = False,
			amount = amount,
			code = code
			)
			db.session.add(trf)
			db.session.commit()
			response =  Transfer.finalize(
				transfer_code = response.data.transfer_code)



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

	def check_tansaction(self):
		check = False
		if self.transaction_type == False:
			check = Transfer.verify(reference=self.code)
		elif self.transaction_type == True:
			check = Transaction.verify(reference = self.code)
		#parse check data to give result, true, false, pending
		return check

	def remit_pay(self):
		if not self.marked:
			user = User.query.get(user_id)
			if self.transaction_type == True:			
				user.balance += self.amount
			if self.transaction_type == False:		
				user.balance -= self.amount
			self.marked = True
			db.session.commit()

		

class BankAccounts(db.Model):
	__tablename__ = 'bankaccounts'

	id = db.Column(db.Integer, primary_key=True)
	bank_name = db.Column(db.String(60))
	account_name =  db.Column(db.String(60))
	account_number = db.Column(db.Integer)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	recipient_code = db.Column(db.String(60), default=None)

	def create_recipient(self):
		code = TransferRecipient.create(
            type="nuban",
            name="Zombie",
            description="Zombier",
            account_number="01000000010",
            bank_code="044",
        )
		self.recipient_code = code
		self.save()
		return self.recipient_code

	
	
