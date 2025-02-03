import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from sqlhelpers import get_user_row, get_user_shares, substract_user_cash, create_transaction_record, update_user_shares, register_user, remove_stocks, add_user_cash, change_user_password

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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
    userRow = get_user_row(session["user_id"])
    if userRow:
        user = {
            "username": userRow["username"],
            "cash": userRow["cash"],
            "total": userRow["cash"] # Total amount of capital that the user has distributed
        }
        sharesDB = get_user_shares(session["user_id"])
        shares = [{}]
        if sharesDB:
            for shareDB in sharesDB:
                stock = lookup(shareDB["symbol"])
                shares.append({"price": stock["price"], "total": usd(stock["price"]* shareDB["numbShares"])})
                user["total"] += (stock["price"]* shareDB["numbShares"])
        else: 
            apology("user not found", 404)

        user["total"] = usd(user["total"])
        user["cash"] = usd(user["cash"])

        return render_template("index.html", user=user, shares=shares)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get("shares"):
            return apology("must enter number of shares", 400)
        elif not request.form.get("shares").isdigit():
            return apology("must enter a valid number of shares", 400)
        elif int(request.form.get("shares")) < 1:
            return apology("must enter a valid number of shares", 400)
        elif not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        stock = lookup(request.form.get("symbol"))
        if stock is None:
            return apology("invalid stock symbol", 400)

        userRow = get_user_row(session["user_id"])
        cash = userRow["cash"]
        total_cost = int(request.form.get("shares")) * stock["price"]
        if total_cost > cash:
            return apology("not enough cash", 403)

        substract_user_cash(session["user_id"], total_cost)

        create_transaction_record(session["user_id"], int(request.form.get("shares")), stock["price"], request.form.get("symbol"), "purchase")

        update_user_shares(session["user_id"], request.form.get("symbol"), int(request.form.get("shares")))
        
        flash("Bought!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    transactions = db.execute("SELECT * FROM transactions WHERE userId = (?)", session["user_id"])
    for transaction in transactions:
        transaction["price"] = usd(transaction["price"])
    return render_template("history.html", transactions=transactions)


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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("stock symbol not valid", 400)

        stock["price"]=usd(stock["price"])
        return render_template("quote.html", stock=stock)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)
        if not request.form.get("password"):
            return apology("must provide password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)
        try:
            password = generate_password_hash(request.form.get("password"))
            register_user(username, password)
            return redirect("/login")
        except Exception as e:
            print(e)
            return apology("username already exists", 400)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must select a stock to sell", 400)
        elif not request.form.get("shares"):
            return apology("must input number of shares", 400)
        elif not int(request.form.get("shares").isdigit()):
            return apology("invalid number of shares", 400)
        elif int(request.form.get("shares")) < 1:
            return apology("invalid number of shares", 400)

        for share in get_user_shares(session["user_id"]):
            if share["symbol"] == request.form.get("symbol"):
                row = share
                break

        numbShares = row["numbShares"]

        if numbShares < int(request.form.get("shares")):
            return apology("you dont have enough shares to sell", 400)


        remove_stocks(session["user_id"], request.form.get("symbol"), int(request.form.get("shares")))

        stock = lookup(request.form.get("symbol"))
        cash = int(request.form.get("shares")) * stock["price"]

        add_user_cash(session["user_id"], cash)
       
        create_transaction_record(session["user_id"], int(request.form.get("shares")), stock["price"], request.form.get("symbol"), "sell")
    
        flash("Sold!")
        return redirect("/")

    else:
        stocks = get_user_shares(session["user_id"])
        return render_template("sell.html", stocks=stocks)


@app.route("/change_password", methods=["GET", "POST"])
def passwordChange():
    if request.method == "POST":
        if not request.form.get("name"):
            return apology("must provide username", 403)
        if not request.form.get("password"):
            return apology("must provide password", 403)

        rows = get_user_row(session["user_id"])

        if len(rows) != 1 or not check_password_hash(
            rows["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        if request.form.get("new_password") != request.form.get("confirm"):
            return apology("passwords don't match", 403)

        change_user_password(request.form.get("name"), generate_password_hash(request.form.get("new_password")))
        
        flash("Password changed!")

        return redirect("/")
    else:
        return render_template("password.html")
