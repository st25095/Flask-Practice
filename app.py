import json

from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)

    with open('data/addons.json') as file:
        addons = json.load(file)

    return flowers, addons


@app.route('/')
def index():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    return render_template("index.html", flowers=flowers, addons=addons, cart=cart)

@app.route("/remove_from_cart/<item>")
def remove_from_cart(item):
    cart = session.get('cart', {})

    if item in cart:
        del cart[item]
        session['cart'] = cart
        session.modified = True
        flash(f"{item} removed from cart.")
    else:
        flash("Item not found in cart.")
    return redirect(url_for('index'))


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    quantity = int(request.form['quantity'])
    flowers, addons = load_data()
    cart = session.get('cart', {})

    if flower not in flowers:
        flash("Invalid flower selected")
        return redirect(url_for('index'))
    
    if flower in cart:
        cart[flower]['quantity'] += quantity
    else:
        cart[flower] = {
            'price': flowers[flower]['price'],
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} {flower}(s) added to your!!!! cart.")
    print(f"SUCCESS: {quantity} {flower}(s) added to cart.") # Added myself to confirm the quantity
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)
    # For some reason the browser says refused to connect. 
    # Gemini AI said to change the port from 5000 to 8000 for Mac.
    # This change works.

