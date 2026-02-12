# Prebuilt payment page with subscriptions

Explore a full, working code sample of an integration with Stripe Checkout and the customer portal. The client- and server-side code redirects to a prebuilt payment page hosted on Stripe. Included are some basic build and run scripts you can use to start up the application.

## Running the sample

1. Build the server

~~~
pip3 install -r requirements.txt
~~~

2. Run the server

~~~
export FLASK_APP=server.py
python3 -m flask run --port=4242
~~~

3. Go to [http://localhost:4242/checkout.html](http://localhost:4242/checkout.html)
