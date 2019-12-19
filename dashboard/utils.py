from flask import session
from random import randint
from paystackapi.paystack import Paystack, Transfer
from paystackapi.transaction import Transaction
from paystackapi.trecipient import TransferRecipient
from miniwalletapp.models import User, TransactionLog, db
paystack_secret_key = "sk_test_98ed509224c4c328448657dee0c17641f69a55a9"
paystack = Paystack(secret_key=paystack_secret_key)

# # to use transaction class
# paystack.transaction.list()

# # to use customer class
# paystack.customer.get(transaction_id)

# # to use plan class
# paystack.plan.get(plan_id)

# # to use subscription class
# paystack.subscription.list()


# response = Transaction.initialize(reference='reference',
#                                   amount='amount', email='email')

# response = Transaction.charge(reference='reference',
#                               authorization_code='authorization_code',
#                               email='email',
#                               amount='amount')

# response = Transaction.charge_token(reference='reference',
#                                     token='token', email='email',
#                                     amount='amount')

# response = Transaction.get(transaction_id=23)

# response = Transaction.totals()

def gen_refcode():
	refcode = 'DP%s' % (randint(500, 9000000000))
	if TransactionLog.query.filter_by(code=refcode).first():
		return gen_refcode()
	else:
		return refcode

def init_transaction(amount, email):
  user = User.query.get(session['xid'])
  if user:
    trl = TransactionLog(
      transaction_type = True,
      amount = amount,
      user_id = session['xid'],
      code = gen_refcode())
    db.session.add(trl)
    db.session.commit()
    response = Transaction.initialize(
          reference= trl.code,
          amount= amount,
          email= user.email)
    return response


 


# response = TransferRecipient.create(
#             type="nuban",
#             name="Zombie",
#             description="Zombier",
#             account_number="01000000010",
#             bank_code="044",
#         )


# response = Transfer.initiate(
#             source="balance",
#             reason="Calm down",
#             amount="3794800",
#             recipient="RCP_gx2wn530m0i3w3m",
#         )


# response = Transfer.finalize(
#             transfer_code="TRF_2x5j67tnnw1t98k",
#             otp="928783"
#         )


# response = Transfer.verify(
#             reference="ref_demo",
#         )