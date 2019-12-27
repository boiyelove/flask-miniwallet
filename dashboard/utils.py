import sys
import json
import hmac
import hashlib
import requests
from flask_login import current_user
from random import randint
from paystackapi.paystack import Paystack, Transfer
from paystackapi.transaction import Transaction
from miniwalletapp.models import User, TransactionLog, db
from miniwalletapp.config import paystack_secret_key

paystack = Paystack(secret_key=paystack_secret_key)
ip_whitelist = ['52.31.139.75', '52.49.173.169', '52.214.14.220']

def gen_refcode():
    refcode = 'DPX%s' % (randint(500, 9000000000))
    if TransactionLog.query.filter_by(code=refcode).first():
        return gen_refcode()
    else:
        return refcode








def init_transaction(amount, email):
    trl = TransactionLog(transaction_type = True,
        amount = amount,
        user_id = current_user.get_id(),
        code = gen_refcode())
    db.session.add(trl)
    db.session.commit()
    # response = Transaction.initialize(
    #       reference= trl.code,
    #       amount= amount,
    #       email= current_user.email)
    return trl.code #(or false)

def verify_hook(request):
  # print('remmote address is', request.remote_addr)
  # print('remmote address is', request.remote_addr, file=sys.stdout)
  # if request.remote_addr in ip_whitelist:  
  #   json_body = request.json
  #   srk = paystack_secret_key
  #   computed_hmac = hmac.new(
  #     bytes(srk, 'utf-8'),
  #     str.encode(request.data.decode('utf-8')),
  #       digestmod=hashlib.sha512
  #       ).hexdigest()
  #   print('computed_hmac is', computed_hmac, file=sys.stdout)
  #   print('computed_hmac is', computed_hmac)
  #   print('request.headers is', request.headers)
  #   if ('HTTP_X_PAYSTACK_SIGNATURE' in request.headers) or ('HTTP-X-PAYSTACK-SIGNATURE' in request.headers ):
  #     if (request.headers['HTTP_X_PAYSTACK_SIGNATURE'] == computed_hmac) or ( request.headers['HTTP-X-PAYSTACK-SIGNATURE']  == computed_hmac):
  #       print('passed hmac test')
  #       return True
  # return False
  return True