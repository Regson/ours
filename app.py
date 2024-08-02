from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_ckeditor import CKEditor

import uuid as uuid
import os

from blogforms import UsersForm, LoginForm, PostsForm, SearchForm


app = Flask(__name__)
#app.config.from_object('config.ProConfig')
app.config.from_object('config.DevConfig')
# app.config.from_pyfile('config.py')
# initialize ckeditor
ckeditor = CKEditor(app)

# initailize db
db = SQLAlchemy(app)
migrate = Migrate(app, db)



class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    author_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(), nullable=True)
    profile_pic = db.Column(db.String(600), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Posts', backref='author')

    @property
    def password(self):
        raise AttributeError("This password does not have a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password) 

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return '<name %r>' % self.name


# Blog post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topics = db.Column(db.String(200))
    slug = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    content =  db.Column(db.Text, nullable=False)
    post_image = db.Column(db.String(500), nullable=True)
    publish = db.Column(db.Integer, default=0)
    popular_view = db.Column(db.Integer)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)


# flask login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))    


"""routes"""
@app.route("/")
def index():
    blog_posts = Posts.query.order_by(Posts.date_created.desc()).limit(5).all()
    blog_views = Posts.query.order_by(Posts.popular_view.desc()).limit(5).all()
    return render_template("index.html", blog_posts=blog_posts, blog_views=blog_views)


@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form =  UsersForm()
    user_update = Users.query.get_or_404(id)
    old_pic=user_update.profile_pic
    if request.method == "POST":
        user_update.author_name = request.form['name']
        user_update.email = request.form['email']
        user_update.favorite_color = request.form['favorite_color']
        user_update.about_author = request.form['about_author']
        user_update.profile_pic = request.files['profile_pic'] 
        if form.profile_pic.data is not None: # check if user wants to change profile picture
            try:
                os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], old_pic))
            except IsADirectoryError:
                print("The given path is a directory")
            except FileNotFoundError:
                print("No such file or directory")
            except PermissionError:
                print("Permission denied")
            except:
                flash("Error! Something went wrong!")
            # Grab image name
            pic_filename = secure_filename(user_update.profile_pic.filename)
            # Set UUID
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            #save image to static folder
            user_update.profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            #save image name to db
            user_update.profile_pic = pic_name
            
        else:
            user_update.profile_pic = old_pic        
            
        try:
            db.session.commit()
            form.name.data = ""
            form.email.data = ""
            form.favorite_color.data = ""
            form.about_author.data = ""
            flash("User updated successfully!")
            return render_template('dashboard.html', form=form)
        except:
            flash("Error! Something went wrong....try again!")
            return render_template('add_user.html', form=form)
    else:
        return render_template('profile_update.html', form=form, user_update=user_update)


@app.route("/posts/editpost/<int:id>", methods = ['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostsForm()
    get_post = Posts.query.get_or_404(id)
    old_pic = get_post.post_image
    if request.method == 'POST':
        get_post.title = request.form['title']
        get_post.slug = request.form['slug']
        get_post.content = request.form['content']
        get_post.post_image = request.files['post_image']
        if form.post_image.data is not None:
            try:
                os.unlink(os.path.join(app.config['UPLOAD_PATH'], old_pic))
            except IsADirectoryError:
                print("The given path is a directory")
            except FileNotFoundError:
                print("No such file or directory")
            except PermissionError:
                print("Permission denied")
            except:
                flash("Error! Something went wrong!")
            image_name = secure_filename(get_post.post_image.filename)
            image_name_uuid = str(uuid.uuid1()) + "_" + image_name
            get_post.post_image.save(os.path.join(app.config['UPLOAD_PATH'], image_name_uuid))
            get_post.post_image = image_name_uuid
        else:
            get_post.post_image = old_pic
        try:
            db.session.commit()
            flash("Posts updated successfully!")
            return redirect(url_for('manage_post', id=get_post.id))
        except:
            flash("Error! Something went wrong....try again!")
            return render_template('editpost.html', form=form, get_post=get_post)
    if get_post.poster_id == current_user.id:
        form.title.data = get_post.title 
        form.slug.data = get_post.slug
        form.content.data = get_post.content
    else:
        flash("You're not authorized to edit the post!")
    return render_template('editpost.html', form=form, get_post=get_post)

@app.route("/posts/publish-post/<int:id>", methods = ['GET', 'POST'])
@login_required
def publish_post(id):
    get_post = Posts.query.get_or_404(id)
    if request.method == 'POST':
        get_post.publish = 1
        db.session.add(get_post)
        db.session.commit()
        flash("Your post has been published!")
        return redirect(url_for('manage_post', id=get_post.id))
    else:
        flash("Error: Failed to publish post! try again")
        return redirect(url_for('add_posts'))


@app.route("/posts/unpublish-post/<int:id>", methods = ['GET', 'POST'])
@login_required
def unpublish_post(id):
    get_post = Posts.query.get_or_404(id)
    if request.method == 'POST':
        get_post.publish = 0
        db.session.add(get_post)
        db.session.commit()
        flash("Your post has been unpublished!")
        return redirect(url_for('manage_post', id=get_post.id))
    else:
        flash("Error: Failed to unpublish post! try again")
        return redirect(url_for('add_posts'))
    

@app.route('/user/delete/<int:id>')
@login_required
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form=UsersForm()
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User deleted successfully!")
        user_list = Users.query.order_by(Users.date_created)
        return render_template('add_user.html', form=form, name=name, user_list=user_list, id=id)
    except:
        flash("Error! Something went wrong...could not delete user!")
        return render_template('add_user.html', form=form, name=name, user_list=user_list, id=id)

@app.route('/posts/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    post_to_del = Posts.query.get_or_404(id)
    if post_to_del.poster_id == current_user.id:
        try:
            os.unlink(os.path.join(app.config['UPLOAD_PATH'], post_to_del.post_image))
            db.session.delete(post_to_del)
            db.session.commit()
            flash("Post deleted successfully!")
            return redirect(url_for('manage_post'))
        except IsADirectoryError:
            print("No such file or directory")
        except FileNotFoundError:
            print("The given path is a directory")
        except PermissionError:
            print("Permission denied")
        except:
            flash("Error! Something went wrong!")
            return redirect(url_for('manage_post'))
    else:
        flash("Access denied!")
    return redirect(url_for('index'))


# Create Custom Error Pages
# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    form = UsersForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hash_pw = generate_password_hash(form.pw_hash.data, method="scrypt", salt_length= 16)
            user = Users(username=form.username.data,author_name=form.name.data, email=form.email.data, 
            favorite_color=form.favorite_color.data, about_author=form.about_author.data,
            password_hash=hash_pw)
            db.session.add(user)
            db.session.commit()
        form.name.data = ""
        form.username.data = ""
        form.email.data = ""
        form.favorite_color.data = ""
        form.about_author.data = ""
        form.pw_hash.data = ""
        flash('User added successfully!')
    return render_template('register.html', form=form)


@app.route("/add_posts", methods = ['GET', 'POST'])
@login_required
def add_posts():
    """This block of code will need to be REFRACTORED"""
    form = PostsForm()
    posts = None
    if form.validate_on_submit():
        poster_id = current_user.id
        add_image = request.files['post_image'] 
        image_name = secure_filename(add_image.filename) # Grab image name
        image_name_uuid = str(uuid.uuid1()) + "_" + image_name
        if image_name_uuid != '':
            file_ext = os.path.splitext(image_name_uuid)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return "Invalide image", 400
            add_image.save(os.path.join(app.config['UPLOAD_PATH'], image_name_uuid))
            if 'save' in request.form:
                publish = 0
                popular = 0
                flash("Post saved successfully!")
            elif 'preview' in request.form:
                posts = Posts(title=form.title.data, poster_id = poster_id, content=form.content.data, post_image=image_name_uuid)
                return render_template('fullpost.html', post=posts)
            else:
                publish=1
                popular=0
                flash("Post has been published!")
            posts = Posts(title=form.title.data, poster_id = poster_id, slug=form.slug.data, content=form.content.data, topics=form.topics.data, post_image=image_name_uuid, publish=publish, popular_view=popular)
            db.session.add(posts)
            db.session.commit()
            form.title.data = ''
            form.slug.data = ''
            form.content.data = ''
        else:
            if 'save' in request.form:
                publish = 0
                flash("Post saved successfully!")
            elif 'preview' in request.form:
                posts = Posts(title=form.title.data, poster_id = poster_id, content=form.content.data, post_image=image_name_uuid)
                return render_template('fullpost.html', post=posts)
            else:
                publish=1
                popular=0
                flash("publish!")
            posts = Posts(title=form.title.data, poster_id = poster_id, slug=form.slug.data, content=form.content.data, topics=form.topics.data, publish=publish, popular_view=popular)
            db.session.add(posts)
            db.session.commit()
            form.title.data = ''
            form.slug.data = ''
            form.content.data = ''
    return render_template('create_post.html', form=form, posts=posts)


@app.route("/user/manage-post")
@login_required
def manage_post():
    # Let's paginate the output
    ROWS_PER_PAGE = 3
    page = request.args.get('page', 1, type = int)
    
    blog_posts = Posts.query.order_by(Posts.date_created.desc()).paginate(
        page = page, 
        per_page = ROWS_PER_PAGE, 
        error_out=False
        )
    return render_template('user_posts.html', blog_posts=blog_posts, page=page)


@app.route("/readmore/<title>", methods = ['GET', 'POST'])
def fullpost(title):
    post = Posts.query.filter_by(title=title.replace('-'," ")).first_or_404()
    post.popular_view += 1
    db.session.add(post)
    db.session.commit()
    return render_template("fullpost.html", post=post)


@app.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # check the hash password
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login successfull")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong username or password! try again")
        else:
            flash("This user does not exist")
    return render_template("login.html", form=form)


@app.route("/dashboard", methods = ['GET', 'POST'])
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout", methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You're now logged out! Thanks for stopping by")
    return redirect(url_for('login'))


# Pass form to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        post_searched = form.searched.data
        posts = Posts.query.filter(Posts.content.like('%' + post_searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template('search.html', form=form, searched=post_searched, posts=posts)
    return render_template('search.html', form=form)

@app.route("/author/<author>/")
def about_author(author):
    user = Users.query.filter_by(author_name=author.replace("-"," ")).first_or_404()
    blog_posts = Posts.query.filter(Posts.author.has(author_name=author.replace('-', ' '))).all()
    return render_template('about_author.html', user=user, blog_posts=blog_posts)

@app.route("/admin")
@login_required
def admin():
    id = current_user.id
    if id == 17:
        return render_template("admin.html")
    else:
        flash("Access denied: You need to be an admin to access this page!!!")
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run()
