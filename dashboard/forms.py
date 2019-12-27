from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, ValidationError, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from ..models import BankAccount, Bank
# from .utils import get_bank_list

class PaymentForm(FlaskForm):
	pass

class BankForm(FlaskForm):

	bank = SelectField('Bank Name',
	coerce=int,
	 validators=[DataRequired()])
	account_name = StringField('Account Name', validators=[DataRequired()])
	account_number = StringField('Account Number', validators=[DataRequired(), Length(min=10)])

	def __init__(self, *args, **kwargs):
		super(BankForm, self).__init__(*args, **kwargs)
		self.bank.choices = Bank.get_banklist()

	def validate_account_number(self, field):
		# if BankAccount.query.filter_by(account_number = field.data).first():
		# 	raise ValidationError('Bank Account already exists')
		if type(int(field.data)) is not int:
			raise ValidationError('Please provide a valid account number')
