import logging
import sys
import json
import hmac
import hashlib
# import miniwalletapp as app
from flask_login import current_user
from random import randint
from paystackapi.paystack import Paystack, Transfer
from paystackapi.transaction import Transaction
from miniwalletapp.models import User, TransactionLog, db
from miniwalletapp.config import PAYSTACK_SECRET_KEY as paystack_secret_key

paystack = Paystack(secret_key=paystack_secret_key)
ip_whitelist = ['52.31.139.75', '52.49.173.169', '52.214.14.220']

def gen_refcode():
    refcode = 'DPX%s' % (randint(500, 9000000000))
    if TransactionLog.query.filter_by(code=refcode).first():
        return gen_refcode()
    else:
        return refcode




class Transfer(Transfer):
  @classmethod
  def resend_otp(cls, **kwargs):
    return cls().requests.post('transfer/resend_otp', data=kwargs)



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
  logging.info('remmote address is', request.remote_addr)
  logging.info('remmote address is', request.remote_addr, file=sys.stdout)
  if request.remote_addr in ip_whitelist:  
    json_body = request.json
    srk = paystack_secret_key
    computed_hmac = hmac.new(
      bytes(srk, 'utf-8'),
      str.encode(request.data.decode('utf-8')),
        digestmod=hashlib.sha512
        ).hexdigest()
    logging.info('computed_hmac is', computed_hmac, file=sys.stdout)
    logging.info('computed_hmac is', computed_hmac)
    logging.info('request.headers is', request.headers)
    if ('HTTP_X_PAYSTACK_SIGNATURE' in request.headers) or ('HTTP-X-PAYSTACK-SIGNATURE' in request.headers ):
      if (request.headers['HTTP_X_PAYSTACK_SIGNATURE'] == computed_hmac) or ( request.headers['HTTP-X-PAYSTACK-SIGNATURE']  == computed_hmac):
        logger.info('passed hmac test')
        return True
  logging.info('failed hmac test')
  return True
  # return True


def initiate_bulk_withdrawals(trlist):
  transfers = [{"amount": trlog.amount, "recipient": trlog.get_recipient_code()} for trlog in trlist ]
  response = Transfer.initiate_bulk_transfer(
          currency="TRF_2x5j67tnnw1t98k",
          source="928783",
          transfers=[
              {
                  "amount": 50000,
                  "recipient": "RCP_db342dvqvz9qcrn"
              },
              {
                  "amount": 50000,
                  "recipient": "RCP_db342dvqvz9qcrn"
              }
          ]
      )


def resend_otp(ref_code):
    #   Resend OTP for Transfer
    # Generates a new OTP and sends to customer in the event they are having trouble receiving one.

     
    #  Try It
    # BODY PARAMS

    # transfer_code*
    # string
    # Transfer code

    # reason*
    # string
    # either resend_otp or transfer
    # curl https://api.paystack.co/transfer/resend_otp \
    # -H "Authorization: Bearer SECRET_KEY" \
    # -H "Content-Type: application/json" \
    # -d '{"transfer_code": "TRF_vsyqdmlzble3uii"}' \
    # -X POST

    import requests
    response =  requests.post("https://api.paystack.co/transfer/resend_otp",
      json={'reference': ref_code, "reason":'transfer'},
      headers={'Authorization': "Bearer %s" % paystack_secret_key, "Content-Type": "application/json"})
    return response.json()
  # return Transfer.resend_otp(reference=ref_code, reason='transfer')

def finalize_withdrawal(ref_code, otp):
  return Transfer.finalize(reference=ref_code, otp=otp)
