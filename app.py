```python
import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "development-secret-change-this"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    food_id = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(
        db.String(100),
        default="Preparing",
        nullable=False
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    foods = Food.query.all()
    return render_template("index.html", foods=foods)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)
            return redirect(url_for("index"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/add_to_cart/<int:id>")
@login_required
def add_to_cart(id):
    food = db.session.get(Food, id)

    if not food:
        flash("Food item not found.", "danger")
        return redirect(url_for("index"))

    item = Cart.query.filter_by(
        user_id=current_user.id,
        food_id=id
    ).first()

    if item:
        item.qty += 1
    else:
        item = Cart(
            user_id=current_user.id,
            food_id=id,
            qty=1
        )
        db.session.add(item)

    db.session.commit()

    return redirect(url_for("cart"))


@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(
        user_id=current_user.id
    ).all()

    foods = []
    total = 0

    for item in items:
        food = db.session.get(Food, item.food_id)

        if not food:
            continue

        subtotal = food.price * item.qty

        foods.append({
            "name": food.name,
            "qty": item.qty,
            "subtotal": subtotal
        })

        total += subtotal

    return render_template(
        "cart.html",
        foods=foods,
        total=total
    )


@app.route("/checkout")
@login_required
def checkout():
    items = Cart.query.filter_by(
        user_id=current_user.id
    ).all()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    total = 0

    for item in items:
        food = db.session.get(Food, item.food_id)

        if food:
            total += food.price * item.qty

        db.session.delete(item)

    order = Order(
        user_id=current_user.id,
        total=total
    )

    db.session.add(order)
    db.session.commit()

    flash("Payment simulated successfully.", "success")

    return redirect(url_for("orders"))


@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "orders.html",
        orders=user_orders
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Food.query.count() == 0:
            sample = [
                ("Pizza", 299, "pizza.png"),
                ("Burger", 199, "burger.png"),
                ("Cold Coffee", 149, "coffee.png"),
                ("Pasta", 249, "Pasta.png"),
                ("Sandwich", 129, "Sandwich.png"),
                ("Garlic Bread", 119, "garlic_bread.png"),
                ("Chicken Burger", 229, "c_b.png"),
                ("Veg Momos", 139, "v_m.png"),
                ("Chicken Momos", 169, "c_m.png"),
                ("Chocolate Brownie", 149, "b.png")
            ]

            for name, price, image in sample:
                db.session.add(
                    Food(
                        name=name,
                        price=price,
                        image=image
                    )
                )

            db.session.commit()

    app.run(debug=True)
```
