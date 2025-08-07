from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os 
from models import db, User, Media, UserMedia 
from datetime import date
from datetime import datetime
from recommend_engine.embeddings_util import recommend_media  # Adjust import path if needed




app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Ensure the 'database' folder exists
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FOLDER = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_FOLDER, exist_ok=True)

# Use os.path.join to set database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(DB_FOLDER, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return User.query.get(username)

from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = 'user'

        if User.query.get(username):
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.get(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

from flask_login import login_required, current_user
from flask import request, render_template

@app.route('/view', methods=['GET', 'POST'])
@login_required
def view_user_media():
    query = UserMedia.query.join(Media).filter(UserMedia.user_id == current_user.username)

    status = request.args.get('status') or request.form.get('status') or ''
    genre = request.args.get('genre') or request.form.get('genre') or ''
    title = request.args.get('title') or request.form.get('title') or ''

    if status:
        query = query.filter(UserMedia.status == status)
    if genre:
        query = query.filter(Media.genre.ilike(f"%{genre}%"))
    if title:
        query = query.filter(Media.title.ilike(f"%{title}%"))

    user_media = query.all()
    return render_template('view.html', user_media=user_media, status=status, genre=genre, title=title)



@app.route('/browse', methods=['GET', 'POST'])
@login_required
def browse_media():
    if request.method == 'POST' and 'status' in request.form:
        # Handle status update from dropdown
        media_title = request.form.get('media_title')
        status = request.form.get('status')
        if media_title and status:
            user_media = UserMedia.query.filter_by(user_id=current_user.username, media_title=media_title).first()
            if user_media:
                user_media.status = status
            else:
                user_media = UserMedia(user_id=current_user.username, media_title=media_title, status=status)
                db.session.add(user_media)
            db.session.commit()
            flash(f'Status for "{media_title}" set to "{status}".', 'success')
        else:
            flash('Invalid data submitted.', 'danger')
        return redirect(url_for('browse_media'))

    # GET or POST without status means search/filter
    title = request.args.get('title', '').strip()
    genre = request.args.get('genre', '').strip()

    query = Media.query
    if title:
        query = query.filter(Media.title.ilike(f"%{title}%"))
    if genre:
        query = query.filter(Media.genre.ilike(f"%{genre}%"))

    media_list = query.all()
    return render_template('browse.html', media_list=media_list, title=title, genre=genre)


    # GET request - show all media
    media_list = Media.query.all()
    return render_template('browse.html', media_list=media_list)



@app.route('/admin/media', methods=['GET'])
@login_required
@admin_required
def admin_media_list():
    # List media entries created by the admin user
    user_media = UserMedia.query.filter_by(user_id=current_user.username).all()
    return render_template('admin_media_list.html', user_media=user_media)

from datetime import datetime
from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user

from flask import (
    render_template, request, redirect, url_for, flash
)
from flask_login import login_required, current_user
from datetime import datetime


@app.route('/admin/media/add', methods=['GET', 'POST'])
@app.route('/admin/media/edit/<string:title>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_edit_media(title=None):
    media = None
    user_media = None
    action = "Add"

    if title:
        media = Media.query.get_or_404(title)
        user_media = UserMedia.query.filter_by(user_id=current_user.username, media_title=title).first()
        action = "Edit"

    if request.method == 'POST':
        form_title = request.form.get('title')
        creator = request.form.get('creator')
        genre = request.form.get('genre')
        release_date_str = request.form.get('release_date')
        media_tags = request.form.get('media_tags')
        status = request.form.get('status')

        # Validate required fields
        if not (form_title and creator and genre and release_date_str and status):
            flash('Please fill all required fields.', 'warning')
            # Re-render the form with current inputs
            return render_template(
                'admin_add_edit_media.html',
                action=action,
                media=media or Media(
                    title=form_title,
                    creator=creator,
                    genre=genre,
                    release_date=None,
                    media_tags=media_tags
                ),
                user_media=user_media or UserMedia(status=status)
            )

        # Parse release_date
        try:
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return render_template(
                'admin_add_edit_media.html',
                action=action,
                media=media or Media(
                    title=form_title,
                    creator=creator,
                    genre=genre,
                    release_date=None,
                    media_tags=media_tags
                ),
                user_media=user_media or UserMedia(status=status)
            )

        if action == "Add":
            # Prevent duplicate media title
            if Media.query.get(form_title):
                flash(f'Media with title "{form_title}" already exists.', 'warning')
                return render_template(
                    'admin_add_edit_media.html',
                    action=action,
                    media=media or Media(
                        title=form_title,
                        creator=creator,
                        genre=genre,
                        release_date=release_date,
                        media_tags=media_tags
                    ),
                    user_media=user_media or UserMedia(status=status)
                )

            media = Media(
                title=form_title,
                creator=creator,
                genre=genre,
                release_date=release_date
            )
            if media_tags:
                media.set_metadata_list(media_tags.split(','))
            db.session.add(media)

            user_media = UserMedia(user_id=current_user.username, media_title=form_title, status=status)
            db.session.add(user_media)

        else:  # Edit
            media.creator = creator
            media.genre = genre
            media.release_date = release_date
            if media_tags:
                media.set_metadata_list(media_tags.split(','))
            else:
                media.media_tags = None

            if user_media:
                user_media.status = status
            else:
                user_media = UserMedia(user_id=current_user.username, media_title=media.title, status=status)
                db.session.add(user_media)

        db.session.commit()
        flash(f'Media "{form_title}" {action.lower()}ed successfully.', 'success')
        return redirect(url_for('admin_media_list'))

    # GET request: Render form with existing data if editing
    return render_template('admin_add_edit_media.html', action=action, media=media, user_media=user_media)


# @app.route('/admin/media/edit/<string:title>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def admin_edit_media(title):
#     media = Media.query.get_or_404(title)
#     user_media = UserMedia.query.filter_by(user_id=current_user.username, media_title=title).first()
#     if not user_media:
#         flash("You don't have permission to edit this media", 'danger')
#         return redirect(url_for('admin_media_list'))

#     if request.method == 'POST':
#         media.creator = request.form.get('creator')
#         media.genre = request.form.get('genre')
#         media.release_date = request.form.get('release_date')
#         media_tags = request.form.get('media_tags')
#         media.set_metadata_list(media_tags.split(',')) if media_tags else media.media_tags

#         user_media.status = request.form.get('status')

#         db.session.commit()
#         flash(f'Media "{title}" updated successfully', 'success')
#         return redirect(url_for('admin_media_list'))

#     return render_template('admin_add_edit_media.html', action="Edit", media=media, user_media=user_media)

@app.route('/admin/media/delete/<string:title>', methods=['POST'])
@login_required
@admin_required
def admin_delete_media(title):
    media = Media.query.get_or_404(title)
    user_media = UserMedia.query.filter_by(user_id=current_user.username, media_title=title).first()

    if not user_media:
        flash("You don't have permission to delete this media", 'danger')
        return redirect(url_for('admin_media_list'))

    # Delete user-media association first
    db.session.delete(user_media)
    db.session.commit()

    # If no other users are linked to this media, delete media itself
    others = UserMedia.query.filter_by(media_title=title).first()
    if not others:
        db.session.delete(media)
        db.session.commit()

    flash(f'Media "{title}" deleted successfully', 'success')
    return redirect(url_for('admin_media_list'))

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    recommendations = None
    query = ""

    if request.method == 'POST':
        query = request.form.get('query', '')
        if query:
            recommendations = recommend_media(query)

    return render_template('recommend.html', query=query, recommendations=recommendations)

def create_dummy_admin():
    existing = db.session.get(User, 'admin')
    if existing:
        print("Admin user already exists.")
        return

    admin_user = User(
        username='admin',
        role='admin'
    )
    admin_user.password = generate_password_hash('admin')  # hash the password
    db.session.add(admin_user)
    db.session.commit()
    print("Dummy admin user created.")


if __name__ == '__main__':
    DB_PATH = os.path.join(DB_FOLDER, 'site.db')

    with app.app_context():

        if not os.path.exists(DB_PATH):
            db.create_all()

            # Add dummy Media data (public media library)
            dummy_media = [
                Media(
                    title="Inception",
                    creator="Christopher Nolan",
                    genre="Sci-Fi",
                    release_date=date(2010, 7, 16),
                    metadata="HDR,4K,Dolby"
                ),
                Media(
                    title="The Matrix",
                    creator="The Wachowskis",
                    genre="Action",
                    release_date=date(1999, 3, 31),
                    metadata="HDR,Neo,Red Pill"
                ),
                Media(
                    title="Interstellar",
                    creator="Christopher Nolan",
                    genre="Sci-Fi",
                    release_date=date(2014, 11, 7),
                    metadata="Space,Black Hole,Time"
                ),
                Media(
                    title="Pulp Fiction",
                    creator="Quentin Tarantino",
                    genre="Crime",
                    release_date=date(1994, 10, 14),
                    metadata="Nonlinear,Classic,Cult"
                ),
                Media(
                    title="The Shawshank Redemption",
                    creator="Frank Darabont",
                    genre="Drama",
                    release_date=date(1994, 9, 23),
                    metadata="Prison,Hope,Friendship"
                ),
                Media(
                    title="The Godfather",
                    creator="Francis Ford Coppola",
                    genre="Crime",
                    release_date=date(1972, 3, 24),
                    metadata="Mafia,Classic,Family"
                ),
                Media(
                    title="Avengers: Endgame",
                    creator="Anthony and Joe Russo",
                    genre="Action",
                    release_date=date(2019, 4, 26),
                    metadata="Superheroes,Marvel,Time Travel"
                ),
                Media(
                    title="The Dark Knight",
                    creator="Christopher Nolan",
                    genre="Action",
                    release_date=date(2008, 7, 18),
                    metadata="Batman,Joker,DC"
                ),
                Media(
                    title="Forrest Gump",
                    creator="Robert Zemeckis",
                    genre="Drama",
                    release_date=date(1994, 7, 6),
                    metadata="Life,History,Inspirational"
                ),
                Media(
                    title="The Lion King",
                    creator="Roger Allers and Rob Minkoff",
                    genre="Animation",
                    release_date=date(1994, 6, 24),
                    metadata="Disney,Family,Musical"
                ),
            ]


            db.session.bulk_save_objects(dummy_media)
            db.session.commit()
            print("✅ Dummy media added.")
            create_dummy_admin()

        else:
            print("📂 Database already exists.")

    app.run(debug=True)