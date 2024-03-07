import os
from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app.models import UserProfile
from app.forms import LoginForm
from app.forms import UploadForm 
from werkzeug.security import check_password_hash
from flask import send_from_directory

###
# Routing for your application.
###
# Define the allowed_file function
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")

def get_uploaded_images():
    rootdir = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
    uploaded_images = []

    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            uploaded_images.append(file)

    return uploaded_images

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    form = UploadForm()

    # Validate file upload on submit
    if form.validate_on_submit():
        # Get file data and save to your uploads folder
        file = form.file.data

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            flash('File Saved', 'success')
            return redirect(url_for('home'))  # Redirect to the home page

        else:
            flash('Invalid file format. Please upload only jpg or png files.', 'danger')
    return render_template('upload.html', form=form)  # Pass the form to the template

@app.route('/uploads/<filename>')
def get_image(filename):
    uploads_folder = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads_folder, filename)

@app.route('/files')
@login_required
def files():
    image_filenames = get_uploaded_images()
    image_urls = [url_for('get_image', filename=filename) for filename in image_filenames]

    return render_template('files.html', image_urls=image_urls)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Query the database for a user based on the username
        user = UserProfile.query.filter_by(username=username).first()

        # change this to actually validate the entire form submission
        # and not just one field
        if user and check_password_hash(user.password_hash, password):
            # If the user exists and the password is correct, log in the user
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for("home"))  # Redirect to the home page
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template("login.html", form=form)


        

# user_loader callback. This callback is used to reload the user object from
# the user ID stored in the session
@login_manager.user_loader
def load_user(id):
    return db.session.execute(db.select(UserProfile).filter_by(id=id)).scalar()

###
# The functions below should be applicable to all Flask apps.
###

# Flash errors from the form if validation fails
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
), 'danger')

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404
