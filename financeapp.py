import sqlite3
import hashlib
import datetime

class FinanceApp:
    def __init__(self):
        self.conn = sqlite3.connect('finance.db')
        self.cur = self.conn.cursor()
        self.create_tables()
        self.current_user = None

    def create_tables(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = self.cur.fetchone()
        if user:
            self.current_user = user[0]
            return True
        return False

    def add_transaction(self, type, category, amount, date):
        self.cur.execute('''
            INSERT INTO transactions (user_id, type, category, amount, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.current_user, type, category, amount, date))
        self.conn.commit()

    def get_transactions(self, start_date, end_date):
        self.cur.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (self.current_user, start_date, end_date))
        return self.cur.fetchall()

    def generate_report(self, start_date, end_date):
        transactions = self.get_transactions(start_date, end_date)
        total_income = sum(t[4] for t in transactions if t[2] == 'income')
        total_expenses = sum(t[4] for t in transactions if t[2] == 'expense')
        savings = total_income - total_expenses
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'savings': savings
        }

    def set_budget(self, category, amount):
        self.cur.execute('''
            INSERT OR REPLACE INTO budgets (user_id, category, amount)
            VALUES (?, ?, ?)
        ''', (self.current_user, category, amount))
        self.conn.commit()

    def check_budget(self, category):
        self.cur.execute('''
            SELECT budgets.amount, SUM(transactions.amount) as spent
            FROM budgets
            LEFT JOIN transactions ON budgets.user_id = transactions.user_id
                AND budgets.category = transactions.category
                AND transactions.type = 'expense'
                AND transactions.date LIKE ?
            WHERE budgets.user_id = ? AND budgets.category = ?
            GROUP BY budgets.category
        ''', (f"{datetime.date.today().strftime('%Y-%m')}%", self.current_user, category))
        result = self.cur.fetchone()
        if result:
            budget, spent = result
            return budget, spent if spent else 0
        return None, None

    def close(self):
        self.conn.close()

def main():
    app = FinanceApp()
    
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            if app.register_user(username, password):
                print("Registration successful!")
            else:
                print("Username already exists.")
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            if app.login_user(username, password):
                print("Login successful!")
                user_menu(app)
            else:
                print("Invalid credentials.")
        elif choice == '3':
            app.close()
            break
        else:
            print("Invalid choice. Please try again.")

def user_menu(app):
    while True:
        print("\n1. Add Transaction")
        print("2. View Transactions")
        print("3. Generate Report")
        print("4. Set Budget")
        print("5. Check Budget")
        print("6. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            type = input("Enter transaction type (income/expense): ")
            category = input("Enter category: ")
            amount = float(input("Enter amount: "))
            date = input("Enter date (YYYY-MM-DD): ")
            app.add_transaction(type, category, amount, date)
            print("Transaction added successfully!")
        elif choice == '2':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            transactions = app.get_transactions(start_date, end_date)
            for t in transactions:
                print(f"ID: {t[0]}, Type: {t[2]}, Category: {t[3]}, Amount: {t[4]}, Date: {t[5]}")
        elif choice == '3':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            report = app.generate_report(start_date, end_date)
            print(f"Total Income: {report['total_income']}")
            print(f"Total Expenses: {report['total_expenses']}")
            print(f"Savings: {report['savings']}")
        elif choice == '4':
            category = input("Enter category: ")
            amount = float(input("Enter budget amount: "))
            app.set_budget(category, amount)
            print("Budget set successfully!")
        elif choice == '5':
            category = input("Enter category to check: ")
            budget, spent = app.check_budget(category)
            if budget is not None:
                print(f"Budget: {budget}, Spent: {spent}")
                if spent > budget:
                    print("You have exceeded your budget!")
            else:
                print("No budget set for this category.")
        elif choice == '6':
            app.current_user = None
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()