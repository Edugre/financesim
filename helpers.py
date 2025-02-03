import requests

from flask import redirect, render_template, session
from functools import wraps
import sqlite3


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    url = f"https://finance.cs50.io/quote?symbol={symbol.upper()}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP error responses
        quote_data = response.json()
        return {
            "name": quote_data["companyName"],
            "price": quote_data["latestPrice"],
            "symbol": symbol.upper()
        }
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {e}")
    return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def get_user_row(user_id):
    try:
        with sqlite3.connect("finance.db") as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE id = :id", 
                {"id": user_id}
            )

            user_row = cursor.fetchone()
            return user_row
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def get_user_shares(user_id):
    try:
        with sqlite3.connect("finance.db") as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROMT stocks WHERE userId = :id", 
                {"id": user_id}
            )

            shares = cursor.fetchone()
            return shares
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None 
    finally:
        if cursor:
            cursor.close()  