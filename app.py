import datetime
import json
import sqlite3

from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def initialise_database():
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                customer_name TEXT,
                items TEXT,
                addons TEXT,
                total REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) 
        ''')


def load_data():
    try:
        with open('data/flowers.json') as file:
            flowers = json.load(file)

        with open('data/addons.json') as file:
            addons = json.load(file)
        return flowers, addons
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}, {}

    


@app.route('/')
def index():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    total, discount_applied = calculate_total(cart, selected_addons)
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
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY date DESC")
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            orders.append({
                'order_id': row[0],
                'invoice_number': row[1],
                'customer_name': row[2],
                'items': json.loads(row[3]),
                'addons': json.loads(row[4]),
                'total': row[5],
                'date': row[6]
            })
    return render_template('order_history.html', orders=orders)

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
    
    if quantity > flowers[flower]['stock']:
        flash("Not enough stock")
        return redirect(url_for('index'))
    
    if flower in cart:
        potential_cart = cart[flower]['quantity'] + quantity
        if potential_cart > flowers[flower]['stock']:
            flash("Not enough stock 1")
            return redirect(url_for('index'))
        else:
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
    discount_applied = False
    if total > 180:
        discount_applied = True
    return total, discount_applied

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

@app.route('/cancel_saved_order/<int:order_id>', methods=['POST'])
def cancel_saved_order(order_id):
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit
    flash("Order cancelled")
    return redirect(url_for('order_history'))


@app.route('/checkout', methods=['POST'])
def checkout():
    # Validate customer name
    customer_name = request.form['customer_name'].strip().title()

    if not customer_name:
        flash("Customer name is required.")
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('index'))
    
    # Calculate Total
    total, applied_discount = calculate_total(cart, selected_addons)
    discount_amount = 0.0
    sub_total = total
    if applied_discount:
        sub_total = total
        discount_amount = (total * 0.1)
        total -= discount_amount
        print("discount applied")
    invoice_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"
    
    # Save order to SQLite Database
    with sqlite3.connect('flower_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (invoice_number, customer_name, items, addons, total)
            VALUES (?,?,?,?,?)
        ''', (invoice_number, customer_name, json.dumps(cart), json.dumps(selected_addons), total))
        conn.commit()
    print(f"Cart: {cart}")
    
    # Generate Invoice File
    invoice_filename = f"{invoice_number}.txt"

    try:
        with open(invoice_filename, 'w') as f:
            f.write(f"Invoice Number: {invoice_number}\n")
            f.write(f"Customer Name: {customer_name}\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Items:\n\n")
            for item, details in cart.items():
                f.write(f"- {item}: {details['quantity']} x ${details['price']} = ${details['quantity'] * details['price']:.2f}\n")
            f.write(f"\nAddons:\n")
            if selected_addons:
                for addon, price in selected_addons.items():
                    f.write(f"- {addon}: ${price:.2f}\n")
            else:
                f.write(f"- None\n")
            f.write(f"\nTotal: ${total:.2f}\n")
    except OSError as e:
        flash("Could not generate invoice file")
        print(f"Error writing invoice: {e}")


    # Update the stock in flowers.json

    try:
        with open('data/flowers.json', 'r') as file:
            flower_data = json.load(file)
        
        for flower_name, details in cart.items():
            if flower_name in flower_data:
                flower_data[flower_name]['stock'] -= details['quantity']
                if flower_data[flower_name]['stock'] < 0:
                    flower_data[flower_name]['stock'] = 0 # Prevents negative stock
        
        with open('data/flowers.json', 'w') as file:
            json.dump(flower_data, file, indent=4)
    except OSError as e:
        flash("Could not update stock file")
        print(f"Error updating stock: {e}")
    session.modified = True

    # Render the invoice html
    return render_template('invoices.html', customer_name = customer_name, invoice_date = invoice_date, invoice_number = invoice_number, cart = cart, selected_addons = selected_addons, total = total, applied_discount = applied_discount, discount_amount = discount_amount, sub_total = sub_total)


if __name__ == '__main__':
    initialise_database()
    app.run(debug=True, port=8000)
    # For some reason the browser says refused to connect. 
    # Gemini AI said to change the port from 5000 to 8000 for Mac.
    # This change works.

