import os
import stripe
import json

from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, jsonify

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = os.getenv('API_VERSION')
app = Flask(__name__,
  static_url_path='',
  template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "views"),
  static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"))


products_data = {"1": {"name": "The Art of Doing Science and Engineering", "amount": 2300, "images": "https://storage.googleapis.com/cf_cache_samples/art-science-eng.jpg", "stripe_product_id": "prod_LK5ceHC4vZrihZ", "stripe_price_id": "price_1KdRQzKTHHGmVV8PI0IQhZ6t"}, "2": {"name": "The Making of Prince of Persia: Journals 1985-1993", "amount": 2500, "images": "https://storage.googleapis.com/cf_cache_samples/prince-of-persia.jpg", "stripe_product_id": "prod_LK5c2MfmoSkoYY", "stripe_price_id": "price_1KdRR0KTHHGmVV8PykwvHhuW"}, "3": {"name": "Working in Public: The Making and Maintenance of Open Source", "amount": 2800, "images": "https://storage.googleapis.com/cf_cache_samples/working-in-public.jpg", "stripe_product_id": "prod_LK5c36ZSb5CdLF", "stripe_price_id": "price_1KdRR1KTHHGmVV8PHKDQsoLK"}}

# Home route
@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')

# Checkout route
@app.route('/checkout', methods=['POST'])
def checkout():
  try:
    inputs = request.form
    book_id = inputs.get('item')
    if book_id not in ["1", "2", "3"]:
      return "No valid item selected"
    return render_template('checkout.html', items={'id':book_id},name=products_data[book_id]['name'],images=products_data[book_id]['images'],amount=products_data[book_id]['amount']/100)

  except Exception as e:
    return jsonify(error=str(e)), 403

# create paymentIntent based on selected item return clientSecret
@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
  try:
    print(request.data)
    data = json.loads(request.data.decode("utf-8"))
    product_id = data.get('id')
    if product_id in ['1','2','3']:
      amount = products_data[product_id]['amount']
      intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='sgd',
        automatic_payment_methods={
          'enabled': True,
        },
        metadata={"book_id":product_id}
        )
      return jsonify({'clientSecret':intent['client_secret'],'paymentIntentId':intent['id']})
  except Exception as e:
    return jsonify(error=str(e)), 403

#update paymentIntent with shipping info and email info
@app.route('/update_payment_intent', methods=['POST'])
def update_payment_intent():
  try:
    print(request.data)
    data = json.loads(request.data.decode("utf-8"))
    intent = stripe.PaymentIntent.modify(
      data['paymentIntentInfo']['paymentIntentId'],
      shipping=data['shipping'],
      receipt_email=data['customer']['email']
    )
    return jsonify(success=True), 200
  except Exception as e:
    return jsonify(error=str(e)), 403

# Confirmation return
@app.route('/confirmation', methods=['GET'])
def confirmation():
  try:
    payment_intent_id = request.args.get('payment_intent', default=None)
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    book_id = payment_intent['metadata']['book_id']
    item = products_data[book_id]
    status = payment_intent['status']
    if(status=='succeeded'):
      message='Payment succeeded!'
    elif(status=='processing'):
      message = 'Your payment is processing.'
    elif(status=='requires_payment_method'):
      message = 'Your payment was not successful, please try again.'
    else:
      message = 'Something went wrong'
    return render_template('confirmation.html', message=message, reference_id=payment_intent_id,
                           amount=payment_intent['amount']/100, name=item['name'], images=item['images'])
  except Exception as e:
    return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    endpoint_secret = os.getenv("WEBHOOK_SECRET")
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'payment_intent.payment_failed':
      payment_intent = event['data']['object']
      print('Webhook received! Payment for PaymentIntent ' + payment_intent['id'] + ' failed.')
      # update order with payment failed,
      # rollback stock information and put items back to shopping cart
      # send out notification to seller
    elif event['type'] == 'payment_intent.succeeded':
      payment_intent = event['data']['object']
      print('Webhook received! Payment for PaymentIntent ' +
            payment_intent['id'] + ' succeeded')
      #update order/shopping cart/stock information
      #kickoff order fullfillment
      #send out notification to seller
    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

if __name__ == '__main__':
  app.run(port=5000, host='127.0.0.1', debug=True)