import sqlite3

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
            cursor.close()
            return user_row
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

def get_user_shares(user_id):
    try:
        with sqlite3.connect("finance.db") as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM stocks WHERE userId = :id", 
                {"id": user_id}
            )

            shares = cursor.fetchall()
            cursor.close()
            return shares
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None 
    
def substract_user_cash(user_id, amount):
    try:
        with sqlite3.connect("fiannce.db") as conn: 
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET cash = cash - :amount WHERE id = :id",
                {"amount": amount, "id": user_id}
            )
            conn.commit()
            cursor.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    
def create_transaction_record(user_id, shares, price, symbol):
    try:
        with sqlite3.connect("finance.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (userId, numbShares, price, date, symbol, type) VALUES (:userId, :shares, :price, CURRENT_TIMESTAMP, :symbol, 'purchase')",
                {"userId": user_id, "shares": shares, "price": price, "symbol": symbol}
            )
            conn.commit()
            cursor.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    
def update_user_shares(user_id, symbol, shares):
    try:
        with sqlite3.connect("finance.db") as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO stocks (userId, numbShares, symbol) VALUES (:userId, :shares, :symbol)",
                    {"userId": user_id, "shares": shares, "symbol": symbol}
                )
                conn.commit()
            except sqlite3.IntegrityError:
                cursor.execute(
                    "UPDATE stocks SET numbShares = numbShares + :shares WHERE userId = :userId AND symbol = :symbol",
                    {"shares": shares, "userId": user_id, "symbol": symbol}
                )
                conn.commit()
            cursor.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None