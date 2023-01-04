import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    #Query for logged in users username
    userName = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    name = userName[0]["username"]

    # Query for the logged in users cash amount
    userCash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

    # Store cash as an integer as 'grandTotal', this variable will be used as the grand sum of the users portfolio
    grandTotal = userCash[0]["cash"]

    # Update userCash to be a string of the cash amount, formated with usd()
    userCash = usd(userCash[0]["cash"])


    # Query for all transactions that the logged in user has made, sum their quanity per stock.
    # userStocks is a JSON where each object contains a stock and the quantity of that stock the user has.
    userStocks = db.execute("SELECT stock, SUM(quantity) as quantity FROM transactions WHERE userID = ? GROUP BY stock", session["user_id"])

    # Loop through the userStocks JSON, for each 'row' (stock), we loopkup and store the API data for said stock using lookup().
    # Then we append each object in the JSON with a 'name' and a 'price' using values from the API data.
    # Get the 'total' value from the price and quantity, append this as a formatted string to the object, and sum it to the 'grandTotal' as a number
    for row in userStocks:
        stockAPIInfo = lookup(row["stock"])
        row["name"] = stockAPIInfo["name"]
        row["price"] = usd(stockAPIInfo["price"])
        total = stockAPIInfo["price"] * row["quantity"]
        row["total"] = usd(total)
        grandTotal += total

    # Format the grandTotal using usd()
    grandTotal = usd(grandTotal)

    #Render index.html, sending through the userStocks JSON with all the data we need in it, as well as name, userCash and grandTotal.
    return render_template("index.html", userStocks=userStocks, userCash=userCash, grandTotal=grandTotal, name=name)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock was entered
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Store the stock symbol as symbol
        symbol = request.form.get("symbol")

        # Check if the symbol entered corresponds to a stock
        if not lookup(symbol):
            return apology("stock not found", 403)

        # Store the dictionary of the stock data as varibale
        stockDict = lookup(symbol)

        # Ensure a quantity was entered
        if not request.form.get("shares"):
            return apology("must provide number of shares", 403)

        # Store quantity as varibale 'shares', store as an int.
        shares = int(request.form.get("shares"))

        # Ensure a quantity greater than 0 was entered
        if shares < 1:
            return apology("must provide a positive number of shares", 403)

        # Calculate the cost using the stock dictionary we saved above.
        price = stockDict["price"]*shares

        # Find the user in the database, by their session ID
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Find how much cash the user has, stoe this as userCash
        userCash = user[0]["cash"]

        # If the user has less cash than needed for the transaction, render an apology message
        if price > userCash:
            return apology("you don't have enough cash", 403)

        # Subtract the cost from the userCash variable, to get the users cash after the transaction
        userCash -= price

        # Update cash varibale in 'users' database for current user
        db.execute("UPDATE users SET cash = ? where id = ?", userCash, session["user_id"])

        # Insert a new row into 'transactions' database, logging the user's ID, the stock name, price and number of shares
        db.execute("INSERT INTO transactions (userID, stock, price, quantity) VALUES (?, ?, ?, ?)", session["user_id"], stockDict["symbol"], stockDict["price"], shares)

        # Redirect user to homepage
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Retrieve the users transaction from the transaction table
    userTransactions = db.execute("SELECT * FROM transactions WHERE userID = ?", session["user_id"])

    return render_template("history.html", userTransactions=userTransactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock was entered
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Store the stock symbol as symbol
        symbol = request.form.get("symbol")

        # Check if the symbol entered corresponds to a stock
        if not lookup(symbol):
            return apology("stock not found", 403)

        # Store the disctionary of the stock data as varibale
        stockDict = lookup(symbol)

        # Redirect user to /quoted
        return render_template("/quoted.html", stockDict=stockDict)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Store the username and check if it's already taken
        username = request.form.get("username")
        if db.execute("SELECT * FROM users WHERE username = ?", username):
            return apology("username is already taken", 409)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 403)

        # Ensure passwords match.
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 403)

        # Store the hashed password in variable hashPassword
        hashPassword = generate_password_hash(request.form.get("password"))

        # Store the new users information on the database,
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashPassword)

        # Redirect user to a page that says "You are registered!"
        return render_template("registered.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query for all transactions that the logged in user has made, sum their quanity per stock.
        # userStocks is a JSON where each object contains a stock and the quantity of that stock the user has.
        userStocks = db.execute("SELECT stock, SUM(quantity) as quantity FROM transactions WHERE userID = ? GROUP BY stock", session["user_id"])

        # Ensure stock was chosen
        if not request.form.get("symbol"):
            return apology("must select stock", 403)

        # Store the stock symbol as symbol
        symbol = request.form.get("symbol")

        # Check if the symbol entered corresponds to a stock
        if not lookup(symbol):
            return apology("stock not found", 403)

        # Find the data for the stock chosen, from userStocks
        for stock in userStocks:
            if stock["stock"] == symbol:
                stockSelected = stock

        # Store the dictionary of the stock data as varibale
        stockDict = lookup(symbol)

        # Ensure a quantity was entered
        if not request.form.get("shares"):
            return apology("must provide number of shares", 403)

        # Store quantity as varibale 'shares', store as an int.
        shares = int(request.form.get("shares"))

        # Ensure a quantity greater than 0 was entered
        if shares < 1:
            return apology("must provide a positive number of shares", 403)

        # Check that the user has enough of the selected stock to sell the specified amount of shares
        if stockSelected["quantity"] < shares:
            return apology("You do not have enough shares to make this transaction", 403)

        # Calculate the cost using the stock dictionary we saved above.
        price = stockDict["price"]*shares

        # Find the user in the database, by their session ID
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Find how much cash the user has, stoe this as userCash
        userCash = user[0]["cash"]

        # Add the price to the userCash variable, to get the users cash after the transaction
        userCash += price

        # Update cash varibale in 'users' database for current user
        db.execute("UPDATE users SET cash = ? where id = ?", userCash, session["user_id"])

        # Set shares to negative to reflect a sale in the database
        shares = -shares

        # Insert a new row into 'transactions' database, logging the user's ID, the stock name, price and number of shares sold
        db.execute("INSERT INTO transactions (userID, stock, price, quantity) VALUES (?, ?, ?, ?)", session["user_id"], stockDict["symbol"], stockDict["price"], shares)

        # Redirect user to homepage
        return redirect("/")

    else:

        # Query for all transactions that the logged in user has made, sum their quanity per stock.
        # userStocks is a JSON where each object contains a stock and the quantity of that stock the user has.
        userStocks = db.execute("SELECT stock, SUM(quantity) as quantity FROM transactions WHERE userID = ? GROUP BY stock", session["user_id"])

        # stocks is an empty list which we will fill with the names of the stocks that the user has more than 0 of.
        userStocksHas = []
        for stock in userStocks:
            if stock["quantity"] > 0:
                userStocksHas.append(stock["stock"])

        # Render sell.html, sending this list of the stocks the user has, it will be used to generate a drop-down menu.
        return render_template("sell.html", userStocks=userStocksHas)
