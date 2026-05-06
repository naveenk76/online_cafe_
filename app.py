
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(200))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    food_id = db.Column(db.Integer)
    qty = db.Column(db.Integer)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    total = db.Column(db.Float)
    status = db.Column(db.String(100), default="Preparing")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    foods = Food.query.all()
    return render_template("index.html", foods=foods)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u = request.form["username"]
        p = generate_password_hash(request.form["password"])
        user = User(username=u,password=p)
        db.session.add(user)
        db.session.commit()
        flash("Account created")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password,p):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid login")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/add_to_cart/<int:id>")
@login_required
def add_to_cart(id):
    item = Cart.query.filter_by(user_id=current_user.id, food_id=id).first()
    if item:
        item.qty += 1
    else:
        item = Cart(user_id=current_user.id, food_id=id, qty=1)
        db.session.add(item)
    db.session.commit()
    return redirect(url_for("cart"))

@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    foods = []
    total = 0
    for i in items:
        food = Food.query.get(i.food_id)
        subtotal = food.price * i.qty
        foods.append({"name":food.name,"qty":i.qty,"subtotal":subtotal})
        total += subtotal
    return render_template("cart.html", foods=foods, total=total)

@app.route("/checkout")
@login_required
def checkout():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = 0
    for i in items:
        food = Food.query.get(i.food_id)
        total += food.price * i.qty
        db.session.delete(i)
    order = Order(user_id=current_user.id,total=total)
    db.session.add(order)
    db.session.commit()
    flash("Payment simulated successfully")
    return redirect(url_for("orders"))

@app.route("/orders")
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("orders.html", orders=orders)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if Food.query.count()==0:
            sample=[
            ("Pizza",299,"pizza.png"),
            ("Burger",199,"burger.png"),
            ("Cold Coffee",149,"coffee.png"),
            ("Pasta",249,"Pasta.png"),
            ("Sandwich",129,"Sandwich.png"),
            ("Garlic Bread", 119, "garlic_bread.png"),
            ("Chicken Burger", 229, "c_b.png"),
            ("Veg Momos", 139, "v_m.png"),
            ("Chicken Momos", 169, "c_m.png"),
            ("Chocolate Brownie", 149, "b.png")
            ]
            for n,p,i in sample:
                db.session.add(Food(name=n,price=p,image=i))
            db.session.commit()
    app.run(debug=True)
