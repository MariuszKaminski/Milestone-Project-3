import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_food_items")
def get_food_items():
    food_items = mongo.db.food_items.find()
    return render_template("food_items.html", food_items=food_items)

@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    food_items = list(mongo.db.food_items.find({"$text": {"$search": query}}))
    if food_items == []:
        flash("No Food Items Found !!!")
    return render_template("food_items.html", food_items=food_items)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/add_food_item", methods=["GET", "POST"])
def add_food_item():
    if request.method == "POST":
        stock = request.form.get("in_stock")
        stock_int = int(stock)
        low_stock = False
        if stock_int <= 10:
            low_stock = True

        food_item = {
            "item_name": request.form.get("item_name"),
            "category_name": request.form.get("category_name"),
            "in_stock": stock_int,
            "weight_or_quantity": request.form.get("weight_or_quantity"),
            "unit": request.form.get("unit"),
            "low_stock": low_stock,
            "created_by": session["user"]
        }
        mongo.db.food_items.insert_one(food_item)
        flash("Food Item Successfully Added")
        return redirect(url_for("get_food_items"))

    food_categories = mongo.db.food_categories.find().sort("category_name", 1)
    units = mongo.db.units.find().sort("unit_name", 1)
    return render_template("add_food_item.html", food_categories=food_categories, units=units)


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

@app.route("/edit_food_item/<food_item_id>", methods=["GET", "POST"])
def edit_food_item(food_item_id):    
    if request.method == "POST":
        stock = request.form.get("in_stock")
        stock_int = int(stock)
        low_stock = False
        if stock_int <= 10:
            low_stock = True

        submit = {
            "item_name": request.form.get("item_name"),
            "category_name": request.form.get("category_name"),
            "in_stock": stock_int,
            "weight_or_quantity": request.form.get("weight_or_quantity"),
            "unit": request.form.get("unit"),
            "low_stock": low_stock,
            "created_by": session["user"]
        }
        mongo.db.food_items.replace_one({"_id": ObjectId(food_item_id)}, submit)
        flash("Food Item Successfully Edited")

    food_item = mongo.db.food_items.find_one({"_id": ObjectId(food_item_id)})
    food_categories = mongo.db.food_categories.find().sort("category_name", 1)
    units = mongo.db.units.find().sort("unit_name", 1)    
    return render_template("edit_food_item.html", food_item=food_item, food_categories=food_categories, units=units)


@app.route("/delete_food_item/<food_item_id>")
def delete_food_item(food_item_id):
    mongo.db.food_items.delete_one({"_id": ObjectId(food_item_id)})
    flash("Food Item Successfully Deleted")
    return redirect(url_for("get_food_items"))


@app.route("/get_categories")
def get_food_categories():
    food_categories = list(mongo.db.food_categories.find().sort("category_name", 1))
    return render_template("food_categories.html", food_categories=food_categories)


@app.route("/add_food_category", methods=["GET", "POST"])
def add_food_category():
    if request.method == "POST":
        food_category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.food_categories.insert_one(food_category)
        flash("New Food Category Added")
        return redirect(url_for("get_food_categories"))

    return render_template("add_food_category.html")


@app.route("/edit_food_category/<food_category_id>", methods=["GET", "POST"])
def edit_food_category(food_category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("food_category_name")
        }
        mongo.db.food_categories.replace_one({"_id": ObjectId(food_category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_food_categories"))

    food_category = mongo.db.food_categories.find_one({"_id": ObjectId(food_category_id)})
    return render_template("edit_food_category.html", food_category=food_category)



# Due to unspecified syntax error occuring here. This space has been intentionally left empty.




@app.route("/delete_food_category/<food_category_id>")
def delete_food_category(food_category_id):
    mongo.db.food_categories.delete_one({"_id": ObjectId(food_category_id)})
    flash("Food Category Successfully Deleted")
    return redirect(url_for("get_food_categories"))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True
    )
