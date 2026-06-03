import datetime
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
    selected_addons = session.get('selected_addons', {})
    total = calculate_total(cart, selected_addons)
    return render_template("index.html", flowers=flowers, addons=addons, cart=cart, total=total, selected_addons = selected_addons)

@app.route('/index1')
def index1():
    flowers, addons = load_data()
    return render_template('index1.html', flowers = flowers, addons=addons)

@app.route('/about')
def about ():
    return render_template('about.html')

@app.route('/order')
def order_history():
    return render_template('order_history.html')

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

@app.route("/remove_from_cart/<item>")
def remove_from_cart(item):
    cart = session.get('cart', {})

    if item in cart:
        del cart[item]
        session['cart'] = cart
        session.modified = True
        flash(f"Removed all {item} from the cart.")
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
    flash(f"{quantity} {flower}(s) added to your cart!")
    print(f"SUCCESS: {quantity} {flower}(s) added to cart.") # Added myself to confirm the quantity
    return redirect(url_for('index'))

def calculate_total(cart, selected_addons):
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    addons_total = sum(item for item in selected_addons.values())
    total += addons_total
    return total

@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()

    selected_keys = request.form.getlist('addons')

    for addon in selected_keys:
        if addon in addons:
            selected_addons[addon] = float(addons[addon]['price'])
    
    session['selected_addons'] = selected_addons
    session.modified = True
    return redirect(url_for('index'))

@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True

    return redirect(url_for('index'))

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form['customer_name'].strip().title()

    if not customer_name:
        flash("Customer name is required.")
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('index'))
    
    total = calculate_total(cart, selected_addons)
    invoice_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"

    return render_template('invoices.html', customer_name = customer_name, invoice_date = invoice_date, invoice_number = invoice_number, cart = cart, selected_addons = selected_addons, total = total)


if __name__ == '__main__':
    app.run(debug=True, port=8000)
    # For some reason the browser says refused to connect. 
    # Gemini AI said to change the port from 5000 to 8000 for Mac.
    # This change works.

