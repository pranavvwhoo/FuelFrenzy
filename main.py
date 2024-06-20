from flask import Flask, jsonify, request, redirect, url_for, render_template
import mysql.connector
import random

app = Flask(__name__)

# Database Connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='',
        database='fuel_frenzy'
    )
    return conn

def update_prices(price_per_barrel):
    rounded_price = round(price_per_barrel, 1)  # Round the price to one decimal place
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE prices SET prices = %s WHERE assets="barrels"', (rounded_price,))
    conn.commit()
    conn.close()

def get_price_per_barrel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT prices FROM prices WHERE assets="barrels"')
    price_per_barrel = cursor.fetchone()[0]  # Fetching the price from the first row of the 'prices' table
    conn.close()
    return price_per_barrel

def update_capital(country_name, new_capital):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE consuming_countries SET ccapital = %s WHERE ccname = %s', (new_capital, country_name))
    cursor.execute('UPDATE producing_countries SET wcapital = %s WHERE pcname = %s', (new_capital, country_name))
    conn.commit()
    conn.close()

def update_investment(country_name, investments):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Determine the total cost of the investment
    total_investment_cost = 0
    for investment_type, quantity in investments.items():
        cursor.execute('SELECT prices FROM prices WHERE assets = %s', (investment_type,))
        price = cursor.fetchone()
        if price:
            total_investment_cost += quantity * price['prices']

    # Check if the country has enough capital for the investment
    cursor.execute('SELECT ccapital FROM consuming_countries WHERE ccname = %s UNION SELECT wcapital FROM producing_countries WHERE pcname = %s', (country_name, country_name))
    country_capital_info = cursor.fetchone()

    if country_capital_info:
        country_capital = country_capital_info['ccapital'] if 'ccapital' in country_capital_info else country_capital_info['wcapital']
        if country_capital < total_investment_cost:
            # Country does not have enough capital for the investment
            conn.close()
            return False  # Indicate that the investment could not be processed due to insufficient funds

    # Proceed with investment as the country has enough capital
    # Deduct the investment cost from the country's capital
    new_capital = country_capital - total_investment_cost

    # Update country's capital
    cursor.execute('UPDATE consuming_countries SET ccapital = %s WHERE ccname = %s', (new_capital, country_name))
    cursor.execute('UPDATE producing_countries SET wcapital = %s WHERE pcname = %s', (new_capital, country_name))

    # Update investments
    for investment_type, quantity in investments.items():
        cursor.execute(f'UPDATE country_data SET {investment_type} = {investment_type} + %s WHERE cname = %s', (quantity, country_name))

    conn.commit()
    conn.close()
    return True  # Indicate successful investment process


@app.route('/')
def index():
    return 'Welcome to Oil Sheikhs! Navigate to /buy, /sell, or /invest to interact.'

@app.route('/confirmation')
def confirmation():
    message = "Your transaction was successful."
    return render_template('confirmation.html', message=message)

@app.route('/error')
def error():
    message = "There was an error processing your request."
    return render_template('error.html', message=message)

def record_transaction(country_name, transaction_type, quantity, amount):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO transactions (country_name, transaction_type, quantity, amount) VALUES (%s, %s, %s, %s)',
                   (country_name, transaction_type, quantity, amount))

    conn.commit()
    conn.close()

@app.route('/buy', methods=['GET', 'POST'])
@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        country_name = request.form['country_name']
        barrels = int(request.form['barrels'])
        price_per_barrel = get_price_per_barrel()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch country's information
        cursor.execute('SELECT cbarrels, ccapital FROM consuming_countries WHERE ccname = %s', (country_name,))
        country_info = cursor.fetchone()

        if not country_info:
            cursor.execute('SELECT barrels, wcapital FROM producing_countries WHERE pcname = %s', (country_name,))
            country_info = cursor.fetchone()

        if country_info:
            current_barrels = country_info.get('cbarrels', 0) if 'cbarrels' in country_info else country_info.get('barrels', 0)
            current_capital = country_info['ccapital'] if 'ccapital' in country_info else country_info['wcapital']

            # Validate if the transaction is valid
            if current_capital - (barrels * price_per_barrel) < 0:
                return redirect(url_for('error'))  # Redirect to error page
            
            # Update barrels
            new_barrels = current_barrels + barrels
            
            # Calculate total cost
            total_cost = barrels * price_per_barrel

            # Update capital for buyer
            new_capital = current_capital - total_cost

            # Update database with fixed price
            if 'cbarrels' in country_info:
                cursor.execute('UPDATE consuming_countries SET cbarrels = %s, ccapital = %s WHERE ccname = %s', (new_barrels, new_capital, country_name,))
            else:
                cursor.execute('UPDATE producing_countries SET barrels = %s, wcapital = %s WHERE pcname = %s', (new_barrels, new_capital, country_name,))
            conn.commit()

            # Record the transaction
            record_transaction(country_name, 'buy', barrels, total_cost)

            # Generate random percentage change in price
            price_percentage_change = random.uniform(-5, 5)  # Random percentage change between -5% and 5%
            new_price_per_barrel = price_per_barrel + (price_per_barrel * price_percentage_change / 100)  # Adjusted price based on percentage change
            update_prices(new_price_per_barrel)

            # Redirect to confirmation page
            transaction_summary = f"Bought {barrels} barrels at ${price_per_barrel} per barrel"
            return redirect(url_for('confirmation', transaction_summary=transaction_summary))

        else:
            return redirect(url_for('error'))  # Redirect to error page

    return render_template('buy.html')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        country_name = request.form['country_name']
        barrels = int(request.form['barrels'])
        price_per_barrel = get_price_per_barrel()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch country's information
        cursor.execute('SELECT cbarrels, ccapital FROM consuming_countries WHERE ccname = %s', (country_name,))
        country_info = cursor.fetchone()

        if not country_info:
            cursor.execute('SELECT barrels, wcapital FROM producing_countries WHERE pcname = %s', (country_name,))
            country_info = cursor.fetchone()

        if country_info:
            current_barrels = country_info.get('cbarrels', 0) if 'cbarrels' in country_info else country_info.get('barrels', 0)
            current_capital = country_info['ccapital'] if 'ccapital' in country_info else country_info['wcapital']

            # Validate if the transaction is valid
            if current_barrels - barrels < 0:
                return redirect(url_for('error'))  # Redirect to error page
            
            # Update barrels
            new_barrels = current_barrels - barrels
            
            # Calculate total revenue
            total_revenue = barrels * price_per_barrel

            # Update capital for seller
            new_capital = current_capital + total_revenue

            # Update database with fixed price
            if 'cbarrels' in country_info:
                cursor.execute('UPDATE consuming_countries SET cbarrels = %s, ccapital = %s WHERE ccname = %s', (new_barrels, new_capital, country_name,))
            else:
                cursor.execute('UPDATE producing_countries SET barrels = %s, wcapital = %s WHERE pcname = %s', (new_barrels, new_capital, country_name,))
            conn.commit()

            # Record the transaction
            record_transaction(country_name, 'sell', barrels, total_revenue)

            # Generate random percentage change in price
            price_percentage_change = random.uniform(-5, 5)  # Random percentage change between -5% and 5%
            new_price_per_barrel = price_per_barrel + (price_per_barrel * price_percentage_change / 100)  # Adjusted price based on percentage change
            update_prices(new_price_per_barrel)

            # Redirect to confirmation page
            transaction_summary = f"Sold {barrels} barrels at ${price_per_barrel} per barrel"
            return redirect(url_for('confirmation', transaction_summary=transaction_summary))

        else:
            return redirect(url_for('error'))  # Redirect to error page

    return render_template('sell.html')


@app.route('/invest', methods=['GET', 'POST'])
def invest():
    if request.method == 'POST':
        country_name = request.form['country_name']
        investments = {
            'ai': int(request.form['ai']),
            'gold': int(request.form['gold']),
            'lithium': int(request.form['lithium']),
            'manufacturing': int(request.form['manufacturing']),
            'tourism': int(request.form['tourism'])
        }

        # Update investments
        update_investment(country_name, investments)

        # Redirect to confirmation page
        return redirect(url_for('confirmation'))

    return render_template('investment.html')

@app.route('/winners')
def winners():
    top_3_winners = get_top_3_winners()
    return render_template('winners.html', winners=top_3_winners)
def get_top_3_winners():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch data for producing countries
    cursor.execute('SELECT pcname AS country_name, wcapital AS capital, barrels AS barrel_count FROM producing_countries')
    producing_countries_data = cursor.fetchall()

    # Fetch data for consuming countries
    cursor.execute('SELECT ccname AS country_name, ccapital AS capital, cbarrels AS barrel_count FROM consuming_countries')
    consuming_countries_data = cursor.fetchall()

    # Combine data from both types of countries
    country_data = producing_countries_data + consuming_countries_data

    top_3 = []

    # Calculate total value for each country
    for country in country_data:
        capital = country['capital']
        barrel_count = country['barrel_count']
        price_per_barrel = get_price_per_barrel()

        # Calculate the amount generated by barrels
        barrel_amount = barrel_count * price_per_barrel

        # Fetch the amount of assets from the country_data table
        cursor.execute('SELECT amount FROM country_data WHERE cname = %s', (country['country_name'],))
        assets_amount = cursor.fetchone()['amount']

        # Calculate the total value
        total_value = capital + barrel_amount + assets_amount

        country['total_value'] = total_value

    # Sort the countries based on their total value
    sorted_countries = sorted(country_data, key=lambda x: x['total_value'], reverse=True)

    # Get the top 3 winners
    top_3 = sorted_countries[:3]

    conn.close()

    return top_3

# Example usage
top_3_winners = get_top_3_winners()
for i, winner in enumerate(top_3_winners, 1):
    print(f"Winner {i}: {winner['country_name']} - Total Value: {winner['total_value']}")
    
    
def get_asset_prices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT assets,prices FROM prices')
    asset_prices = cursor.fetchall()
    conn.close()
    return asset_prices

@app.route('/prices')
def prices():
    asset_prices = get_asset_prices()
    return render_template('prices.html', asset_prices=asset_prices)


if __name__ == '__main__':
    app.run(debug=True)
