import json
from flask import render_template, abort, request, session, Response, redirect
from flask_login import login_required
import miniwalletapp as app

from .utils import init_transaction, paystack_secret_key as srk
from . import dashboard as dbp

User = app.models.User
login_manager = app.login_manager
data = None

@login_manager.user_loader
def load_user(user_id):
	try: 
		session['xid'] 
		user = User.query.filter(User.id == int(user_id)).first()
		session['xid'] = user.id
		return user
	except:
		return None


@dbp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(*args, **kwargs):
	print('session guy is', session['xid'])
	return render_template('dashboard.html', title="Dashboard")



@dbp.route('/withdraw')
@login_required
def withdrawal():
	# user = User.query.filter_by(id = user_id)
	# if request.method == 'POST':
	# 	amount = int(request.form)
	# 	user.withdraw(amount)
	return render_template('withdrawal.html', title="withdraw")


@dbp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
	data = None
	if (request.method == 'POST'):
		refcode = request.args.get('ref', None)
		if refcode:
			trlog = TransactionLog.query.filter_by(code=refcode)
			if not trlog.marked:
				trlog = trlog.remit_pay()
			if trlog.marked:
				flash("You deposit has been completed successfully")
				return redirect(url_for('dashboard.dashboard'))
		else:

			amount = int(request.form['amount'])
			if amount > 100:
				user = User.query.get(session['xid'])
				response = init_transaction(amount, user.email)
				print('paystack response is', response)
				if response['status']:
					data = response['data']
					data['amount'] = amount
					data['email'] = user.email 
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



@dbp.route('/settings/bank_account')
@login_required
def bank_settings():
			

	return render_template("bank_settings.html", title="Bank Accounts", data=data)



@dbp.route('/webhook/' + srk)
def webhook():
	ip_whitelist = ['52.31.139.75', '52.49.173.169', '52.214.14.220']
	if request.method == 'POST':
		if request.remote_addr in ip_whitelist:  
			data = json.loads(request.response)
			trf = TransactionLog.query.filter_by(code=data.data['reference'])
			if data['event'] == 'charge.success':
				data = data['data']
				deposit = Transaction.query.filter_by(refcode = data['reference'])
				if not deposit.marked:
					deposit.user.balance +=  (data['amount'] / 100)
					deposit.user.save()
					deposit.marked = True
					deposit.save()
	
			elif data['event'] == 'transfer.success':
				Transaction.marked = True
				# if failed, refund the money
		return 200
	else:
		return abort(404)


'''
Transaction Successful
{  
   "event":"charge.success",
   "data":{  
      "id":302961,
      "domain":"live",
      "status":"success",
      "reference":"qTPrJoy9Bx",
      "amount":10000,
      "message":null,
      "gateway_response":"Approved by Financial Institution",
      "paid_at":"2016-09-30T21:10:19.000Z",
      "created_at":"2016-09-30T21:09:56.000Z",
      "channel":"card",
      "currency":"NGN",
      "ip_address":"41.242.49.37",
      "metadata":0,
      "log":{  
         "time_spent":16,
         "attempts":1,
         "authentication":"pin",
         "errors":0,
         "success":false,
         "mobile":false,
         "input":[  

         ],
         "channel":null,
         "history":[  
            {  
               "type":"input",
               "message":"Filled these fields: card number, card expiry, card cvv",
               "time":15
            },
            {  
               "type":"action",
               "message":"Attempted to pay",
               "time":15
            },
            {  
               "type":"auth",
               "message":"Authentication Required: pin",
               "time":16
            }
         ]
      },
      "fees":null,
      "customer":{  
         "id":68324,
         "first_name":"BoJack",
         "last_name":"Horseman",
         "email":"bojack@horseman.com",
         "customer_code":"CUS_qo38as2hpsgk2r0",
         "phone":null,
         "metadata":null,
         "risk_action":"default"
      },
      "authorization":{  
         "authorization_code":"AUTH_f5rnfq9p",
         "bin":"539999",
         "last4":"8877",
         "exp_month":"08",
         "exp_year":"2020",
         "card_type":"mastercard DEBIT",
         "bank":"Guaranty Trust Bank",
         "country_code":"NG",
         "brand":"mastercard"
      },
      "plan":{}
   }
}		

'''

'''
Withdrawal Successful
{
  event: "transfer.success",
  data: {
    domain: "live",
    amount: 10000,
    currency: "NGN",
    source: "balance",
    source_details: null,
    reason: "Bless you",
    recipient: {
      domain: "live",
      type: "nuban",
      currency: "NGN",
      name: "Someone",
      details: {
        account_number: "0123456789",
        account_name: null,
        bank_code: "058",
        bank_name: "Guaranty Trust Bank"
      },
      description: null,
      metadata: null,
      recipient_code: "RCP_xoosxcjojnvronx",
      active: true
    },
    status: "success",
    transfer_code: "TRF_zy6w214r4aw9971",
    transferred_at: "2017-03-25T17:51:24.000Z",
    created_at: "2017-03-25T17:48:54.000Z"
  }
}
'''