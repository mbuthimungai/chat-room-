from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base


from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user


import os
import uuid

from form import RegisterForm, LoginForm, AddGroupForm, PostForm

##load all the .env files
load_dotenv()

app = Flask(__name__)

#configurations

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", str(os.urandom(30)))

## Login manager to handle user session management
login_manager = LoginManager()
login_manager.init_app(app=app)

bootstrap = Bootstrap5(app)

db = SQLAlchemy(app)
Base =  declarative_base()

## Users class is an orm representation of the users
## table in sqlalchemy
class Users(UserMixin, Base, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.Text, nullable=False)
    f_name = db.Column(db.String(30), nullable=False)
    l_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)
    owner_of_group = db.relationship("Groups", backref="owner", cascade="all,delete",)
    groups = db.relationship("Members", backref="member", cascade="all,delete",)
    texts = db.relationship("Conversation", backref="text_owner", cascade="all,delete",)

class Groups(Base, db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(30), nullable=False)
    created_on = db.Column(db.DateTime, default=func.now())
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    members = db.relationship("Members", backref="group",  cascade="all,delete",)
    posts = db.relationship("Conversation", backref="group_text",  cascade="all,delete",)

class Members(Base, db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    

class Conversation(Base, db.Model):
    __tablename__ = "conversation"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, )
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))

@app.route("/")
def home():
    all_groups = db.session.query(Groups).all()
    current_user_group = []
    member_in = Members.query.filter_by(member_id=current_user.id).all()
    for mem in member_in:
        current_user_group.append(mem.group_id)
    return render_template("index.html", groups=all_groups, curr_u_groups=current_user_group)


@app.route("/register", methods=["POST", "GET"])
def register():
    ## This route handles registering of users into the database
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            flash("User Already Exists Login Rather", "warning")
            return redirect(url_for("login"))
        admin = os.getenv("ADMINISTRATORS").split("*")
        if form.email.data in admin:
            admin = True
        else:
            admin = False
        new_user = Users(f_name=form.f_name.data.title(), l_name=form.l_name.data.title(),
         email=form.email.data, password=generate_password_hash(method="pbkdf2:sha256",password=form.password.data, salt_length=16), public_id=str(uuid.uuid4()),
         admin=admin)
        db.session.add(new_user)
        db.session.commit()
        flash("Account Created Successfully")
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form)

@app.route("/login", methods=["POST", "GET"])
def login():
    ## This routes handles login
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if not user:
            flash("User Doest Not Exist, regsiter rather", "warning")
            return redirect(url_for("register"))
        if check_password_hash(pwhash=user.password, password=form.password.data):
            flash("login successful", "success")
            login_user(user=user)
            return redirect(url_for("home"))
        flash("Incorrect Password", "error")
    return render_template("login.html", form=form)

@app.route("/add-groups", methods=["POST","GET"])
@login_required
def add_group():
    form = AddGroupForm()    
    if form.validate_on_submit():
        public_id = str(uuid.uuid4())
        new_group = Groups(title=form.title.data.title(), public_id=public_id,
        owner=current_user)        
        db.session.add(new_group)
        db.session.commit()
        new_member = Members(member=current_user, group=Groups.query.filter_by(public_id=public_id).first())
        db.session.add(new_member)
        db.session.commit()
        flash("Group added successfully", "success")
        return redirect(url_for("group", group=public_id))
    return render_template("add_groups.html", form=form)
@app.route("/group", methods=["POST" ,"GET"])
@login_required
def group():
    group_id = request.args.get("group")    
    group = Groups.query.filter_by(public_id=group_id).first()
    form = PostForm()    
    in_group_arr = []
    for member in group.members:
        in_group_arr.append(member.member_id)
    if form.validate_on_submit():        
        new_conversation = Conversation(text=form.text.data, text_owner=current_user, group_text=group)
        db.session.add(new_conversation)
        db.session.commit()
        redirect(url_for("group", group=group.public_id))
    all_conversations = group.posts
    return render_template("group.html", group=group, form=form, 
    members=group.members, conversations=all_conversations, 
    users=db.session.query(Users).all(), ids=in_group_arr)
@app.route("/join")
def join_group():
    group_id = request.args.get("group")    
    group = Groups.query.filter_by(public_id=group_id).first()
    new_member = Members(member=current_user, group=group)
    db.session.add(new_member)
    db.session.commit()
    flash(f"Your are now a member to {group.title} group", "success")
    return redirect(url_for("group", group=group.public_id))
@app.route("/add-member")
def add_member():
    group_id = request.args.get("group")  
    user = Users.query.filter_by(public_id=request.args.get("user")).first() 
    group = Groups.query.filter_by(public_id=group_id).first()
    new_member = Members(member=user, group=group)
    db.session.add(new_member)
    db.session.commit()
    flash(f"Your are now a member to {group.title} group", "success")
    return redirect(url_for("group", group=group.public_id))
@app.route("/remove-member")
@login_required
def remove_member():
    group_id = request.args.get("group")  
    user = Users.query.filter_by(public_id=request.args.get("user")).first() 
    group = Groups.query.filter_by(public_id=group_id).first()
    delete_member = Members.query.filter_by(member=user).first()    
    db.session.delete(delete_member)
    db.session.commit()    
    flash("The member has been remove successfully", "success")
    return redirect(url_for("group", group=group.public_id))
@app.route("/delete-text")
@login_required
def delete_text():
    group_id = request.args.get("group")  
    group = Groups.query.filter_by(public_id=group_id).first()    
    text = Conversation.query.get(request.args.get("text"))
    db.session.delete(text)
    db.session.commit()
    flash("conversaton deleted successfully", "success")
    return redirect(url_for("group", group=group.public_id))
@app.route("/delete-group")
@login_required
def delete_group():
    group = Groups.query.filter_by(public_id=request.args.get("group")).first()
    db.session.delete(group)
    db.session.commit()
    flash("The group has been deleted successfully", "success")
    return redirect(url_for("user_profile"))
@app.route("/profile")
@login_required
def user_profile():
    groups_in = current_user.groups    
    return render_template("profile.html", groups=groups_in)
@app.route("/logout")
def logout():
    logout_user()
    flash("logged out successfully", "success")
    return redirect(url_for("login"))