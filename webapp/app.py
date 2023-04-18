from flask import Flask, request, jsonify
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import boto3
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import json
import bcrypt
import re
from functools import wraps
from sqlalchemy_utils import create_database, database_exists
from botocore.exceptions import NoCredentialsError
from werkzeug.utils import secure_filename
import uuid
import logging
from statsd import StatsClient

load_dotenv()

# S3 bucket details
BUCKET_NAME = os.getenv("s3")

# Initialize Flask app
app = Flask(__name__)

# RDS MySQL database details
if not os.getenv('DISABLE_DATABASE'):
    DB_HOST = os.getenv("host")
    DB_USERNAME = os.getenv("username")
    DB_PASSWORD = os.getenv("password")
    DB_NAME = 'dbcsye6225'
    # Initialize SQLAlchemy engine and session
    db = create_engine(f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

else:
    db = None

#cluoudwatch metrics using statsd
statsd = StatsClient(host='localhost', port=8125)

namespace = 'API counts'

logging.basicConfig(filename='flask.log', level=logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')

Base = declarative_base()

if db is not None and not database_exists(db.url):
    create_database(db.url)

# Define image table schema using SQLAlchemy
class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    s3_bucket_path = Column(String(255), nullable=False)

    def __init__(self, product_id,file_name, date_created, s3_bucket_path):
        self.product_id = product_id
        self.file_name = file_name
        self.date_created = date_created
        self.s3_bucket_path = s3_bucket_path

    def __repr__(self):
        return f"Image(image_id={self.image_id},product_id={self.product_id}, file_name='{self.file_name}', date_created='{self.date_created}', s3_bucket_path='{self.s3_bucket_path}')"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    username = Column(String(80), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    account_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    account_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, first_name, last_name, username, email, password, account_created, account_updated):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.password = password
        self.account_created = account_created
        self.account_updated = account_updated


    def __repr__(self):
        return f"User(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', username='{self.username}', email='{self.email}', password='{self.password}', account_created='{self.account_created}', account_updated='{self.account_updated}')"


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False)
    description = Column(String(200), nullable=False)
    sku = Column(String(80), nullable=False)
    manufacturer = Column(String(80), nullable=False)
    quantity = Column(Integer, nullable=False)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    owner_user_id = Column(Integer, nullable=False)

    def __init__(self, name, description, sku, manufacturer, quantity, owner_user_id, date_last_updated, date_added):
        self.name = name
        self.description = description
        self.sku = sku
        self.manufacturer = manufacturer
        self.quantity = quantity
        self.owner_user_id = owner_user_id
        self.date_added = datetime.utcnow
        self.date_last_updated = datetime.utcnow

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', description='{self.description}', sku='{self.sku}', manufacturer='{self.manufacturer}', quantity='{self.quantity}', date_added='{self.date_added}', date_last_updated='{self.date_last_updated}', owner_user_id='{self.owner_user_id}')"


# Create table in database if it doesn't exist
if db is not None:
    Base.metadata.create_all(db)
session = sessionmaker(bind=db)
session=session()

  #function to check authentication of user
def authentication(username, password):
    #to check if the username given exists in the database
    # create a session object
    Session = sessionmaker(bind=db)
    session = Session()
    user_check = session.query(User).filter_by(username=username).first()
    if user_check is not None:
        #if true - it then encodes the given password
        password = password.encode('utf-8')
        #User is authenticated - if the encoded password matches the hashed password in the database
        if bcrypt.checkpw(password, user_check.password.encode('utf-8')):
            return True
    return False

#it provides access to user if authorized else returns appropriate status code
def authentication_required(f):
    statsd.incr(f'{namespace}.api_calls.authentication')
    #used to wrap other functions together
    @wraps(f)
    def check(*args, **kwargs):
        req = request.authorization
        if not req or not authentication(req.username, req.password):
            app.logger.error('authentication failed')
            return 'Unauthorized user or invalid credentials', 401
        return f(*args, **kwargs)
    return check
#this endpoint check if the localhost is working correctly.
@app.route('/healthz', methods=['GET'])
def get_healthz():
    statsd.incr(f'{namespace}.api_calls.healthz')
    app.logger.info('health check')
    return "Ok",200


#this endpoint is used for adding new users to the user table
#when POST request is sent, this function is executed
@app.route('/v1/user', methods=['POST'])
def new_user():
    statsd.incr(f'{namespace}.api_calls.postuser')
    app.logger.info('to add user')
    #values are added in the json format
    value= request.get_json()
    first_name = value['first_name']
    last_name = value['last_name']
    username = value['username']
    email = value['email']
    #password is encoded and stored as using bcrypt encryption
    password = value['password'].encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    #current timestamp is added
    account_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    account_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #returns appropriate status codes when email is invalid
    email_regex = re.compile(f'{username}@.+\\.com')
    if not email_regex.match(email):
        app.logger.error('invalid email')
        return 'Email address is invalid. Please enter againn', 400
    #finally new user is added to the database
    new_user = User(first_name, last_name, username, email, hashed_password, account_created, account_updated)
    session.add(new_user)
    session.commit()
    return 'User added successfully', 200

@app.route('/v1/product', methods=['POST'])
@authentication_required
def new_prod():
    statsd.incr(f'{namespace}.api_calls.postproduct')
    app.logger.info('to add product')
    #values are added in the json format
    value= request.get_json()
    name = value['name']
    description = value['description']
    sku = value['sku']
    manufacturer = value['manufacturer']
    quantity = value['quantity']

    #current timestamp is added
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    owner_user_id = value['owner_user_id']

    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    # check if owner_user_id exists and matches the user id from user table
    user_check = session.query(User).filter_by(id=owner_user_id).first()
    if user_check is None:
        app.logger.error('invalid user id')
        return "Please enter a valid owner_user_id", 400

    # if any of the required fields is None or "", it'll throw an error
    if name is None or name == '' or description is None or description == '' or sku is None or sku == '' or manufacturer is None or manufacturer == '':
        app.logger.error('incomplete data')
        return "Please enter all fields", 400

    # if the quantity of product is less than 0, it'll throw an error
    if type(quantity) != int or quantity <= 0:
        app.logger.error('quality is less than 0')
        return "quality cannot be lesser than 0", 400

    # Check if the product SKU is unique
    prod_sku = session.query(Product).filter_by(sku=sku).first()
    if prod_sku is not None:
        app.logger.error('sku exists')
        return "SKU already exists", 400

    #finally new product is added to the table
    new_prod = Product(name, description, sku, manufacturer, quantity, date_added, date_last_updated,owner_user_id)
    session.add(new_prod)               
    session.commit()
    return 'product added successfully', 200

#this endpoint is used for updating the user details
#when put request is sent, this function is executed
@app.route('/v1/user/<id>', methods=['PUT'], endpoint='update_user')
@authentication_required
def update_user(id):
    statsd.incr(f'{namespace}.api_calls.putuser')
    app.logger.info('to update user')
    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    user_update = session.query(User).get(id)
    if user_update is None:
        app.logger.error('invalid user')
        return 'Requested User does not exist', 404
    value = request.get_json()
    user_update.first_name = value['first_name']
    user_update.last_name = value['last_name']
    password = value['password']
    if password is None or password == '':
        app.logger.error('incomplete data')
        return "Please enter all fields", 400
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    user_update.password = hashed_password
    if user_update.first_name is None or user_update.first_name == '' or user_update.last_name is None or user_update.last_name == '':
        app.logger.error('incomplete data')
        return "Please enter all fields", 400

    #updated time is added
    user_update.account_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    return 'Successfully updated the user details', 200

#endpoint to update product details using put (all fields are required)
@app.route('/v1/product/<id>', methods=['PUT'], endpoint='update_prod')
#only the authorized user can update the product
@authentication_required
def update_prod(id):
    statsd.incr(f'{namespace}.api_calls.putproduct')
    app.logger.info('to update product')
    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    # Check if the requested product exists in the database

    prod_update = session.query(Product).filter_by(id=id).first()
    if prod_update is None:
        app.logger.error('invalid product id')
        return "product id doesn't exist. Please provide a valid product id", 400

    # Get the updated values from the request
    value = request.get_json()
    name = value['name']
    description = value['description']
    sku = value['sku']
    manufacturer = value['manufacturer']
    quantity = value['quantity']
    owner_user_id = value['owner_user_id']

    # Check if the user who is trying to update the product is the same user who created it
    user_check = session.query(User).filter_by(id=owner_user_id).first()
    if user_check is None:
        app.logger.error('invalid user')
        return "user id doesn't exist. Please provide a valid owner_user_id", 400

    # if any of the required fields is None or "", it'll throw an error
    if name is None or name == '' or description is None or description == '' or sku is None or sku == '' or manufacturer is None or manufacturer == '':
        app.logger.error('incomplete data')
        return "Please enter all fields", 400

    # if the quantity of product is less than 0, it'll throw an error
    if type(quantity) != int or quantity <= 0:
        app.logger.error('quality less than 0')
        return "quality cannot be lesser than 0", 400
    # Check if the product SKU is unique
    product_sku = session.query(Product).filter_by(sku=sku).first()
    if product_sku is not None:
        app.logger.error('sku exists')
        return "SKU already exists", 400

    # Update the product in the database
    prod_update.name = name
    prod_update.description = description
    prod_update.sku = sku
    prod_update.manufacturer = manufacturer
    prod_update.quantity = quantity
    prod_update.owner_user_id = owner_user_id
    prod_update.date_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    return 'product updated successfully', 200

#this endpoint is used to update product details using patch. all details are not required to be entered
@app.route('/v1/product/<id>', methods=['PATCH'], endpoint='update_prod_patch')
#only the authorized user can update the product
@authentication_required
def update_prod_patch(id):
    statsd.incr(f'{namespace}.api_calls.patchproduct')
    app.logger.info('to update product')
    # Check if the requested product exists in the database

    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    prod_update = session.query(Product).filter_by(id=id).first()
    if prod_update is None:
        app.logger.error('invalid product id')
        return "product id doesn't exist. Please provide a valid product id", 400

    # Get the updated values from the request
    value = request.get_json()
    name = value.get('name')
    description = value.get('description')
    sku = value.get('sku')
    manufacturer = value.get('manufacturer')
    quantity = value.get('quantity')
    owner_user_id = value.get('owner_user_id')

    # Check if the user who is trying to update the product is the same user who created it
    user_check = session.query(User).filter_by(id=owner_user_id).first()
    if user_check is None:
        app.logger.error('invalid user id')
        return "user id doesn't exist. Please provide a valid owner_user_id", 400

    # Update the values that were provided in the request
    if name is not None:
        prod_update.name = name
    if description is not None:
        prod_update.description = description
    if sku is not None:
        prod_update.sku = sku
    if manufacturer is not None:
        prod_update.manufacturer = manufacturer
    if quantity is not None:
        prod_update.quantity = quantity
    if owner_user_id is not None:
        prod_update.owner_user_id = owner_user_id
    prod_update.date_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    return 'product updated successfully', 200

#this endpoint is used for getting the user details
#when get request is sent, this function is executed
@app.route('/v1/user/<id>', methods=['GET'], endpoint='get_user')
#first the authentication of the user is done
@authentication_required
def get_user(id):
    statsd.incr(f'{namespace}.api_calls.getuser')
    app.logger.info('to get user')
    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    #if the requested user doesn't exist, it'll return 404
    user = session.query(User).get(id)
    account_created = user.account_created.strftime('%Y-%m-%d %H:%M:%S')
    account_updated = user.account_updated.strftime('%Y-%m-%d %H:%M:%S')
    if user is None:
        app.logger.error('invalid user')
        return 'User not found', 404
    #if user exists, their details are pulled from the database
    return json.dumps({'user': {'id': user.id,'first_name': user.first_name,'last_name': user.last_name,'username': user.username,'email': user.email,'account_created': account_created,'account_updated': account_updated}})

#this endpoint is used for getting the product details
#when get request is sent, this function is executed
@app.route('/v1/product/<id>', methods=['GET'], endpoint='get_prod')
def get_prod(id):
    #if the requested product doesn't exist, it'll return 404
    statsd.incr(f'{namespace}.api_calls.getproduct')
    app.logger.info('to get product')
   # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    prod = session.query(Product).get(id)
    date_added = datetime.strptime(prod.date_added,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    date_last_updated = datetime.strptime(prod.date_last_updated,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    if prod is None:
        app.logger.error('invalid product')
        return 'Product not found', 404
    #if product exists, their details are pulled from the database
    return json.dumps({'prod': {'id': prod.id,'name': prod.name,'description': prod.description,'sku': prod.sku,'manufacturer': prod.manufacturer,'quantity': prod.quantity, 'date_added': date_added,'date_last_updated': date_last_updated}})

@app.route('/v1/product/<id>', methods=['DELETE'], endpoint='delete_prod')
@authentication_required
def delete_prod(id):
    #if the requested product doesn't exist, it'll return 404
    statsd.incr(f'{namespace}.api_calls.deleteproduct')
    app.logger.info('to delete product')
    # create a new session object
    Session = sessionmaker(bind=db)
    session = Session()

    prod = session.query(Product).get(id)
    if prod is None:
        app.logger.error('invalid product')
        return 'Product cannot be deleted because it does not exist', 404
    # delete the product
    session.delete(prod)
    session.commit()
    return 'Product successfully deleted', 200

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/v1/product/<product_id>/image', methods=['POST'])
@authentication_required
def upload_image(product_id):
    statsd.incr(f'{namespace}.api_calls.postimage')
    app.logger.info('to upload an image')
    # Check if the product exists
    Session = sessionmaker(bind=db)
    session = Session()
    product = session.query(Product).get(product_id)
    if not product:
        app.logger.error('invalid product id')
        return 'Invalid product ID', 400

    image_file = request.files['image']
    if not image_file or not allowed_file(image_file.filename):
        app.logger.error('invalid file type')
        return 'Invalid file type', 400

    # Generate a unique filename for the image
    filename = secure_filename(image_file.filename)
    unique_filename = f"{str(uuid.uuid4())}.{filename.split('.')[-1]}"

    # Upload the file to S3
    s3 = boto3.client('s3')
    s3.upload_fileobj(image_file, BUCKET_NAME, unique_filename)

    # Save the image details to the database
    image = Image(
        product_id = product_id,
        file_name=unique_filename,
        date_created=datetime.utcnow,
        s3_bucket_path=f's3://{BUCKET_NAME}/{unique_filename}'
    )
    session.add(image)
    session.commit()

    return f'File {unique_filename} uploaded successfully to S3 and details saved to database', 200

@app.route('/v1/product/<product_id>/image/<image_id>', methods=['GET'])
@authentication_required
def get_image(product_id, image_id):
    statsd.incr(f'{namespace}.api_calls.getimage')
    app.logger.info('to get image details')
    # Check if the product exists
    Session = sessionmaker(bind=db)
    session = Session()
    product = session.query(Product).get(product_id)
    if not product:
        app.logger.error('invalid product id')
        return 'Invalid product ID', 400

    # Check if the image exists and belongs to the product
    image = session.query(Image).filter_by(image_id=image_id, product_id=product_id).first()
    if not image:
        app.logger.error('invalid image id')
        return 'Invalid image ID', 400

    # Get the details of the image
    image_details = {
        'image_id': image.image_id,
        'product_id':product_id,
        'file_name': image.file_name,
        'date_created': image.date_created,
        's3_bucket_path': image.s3_bucket_path
    }

    return jsonify(image_details), 200

@app.route('/v1/product/<product_id>/images', methods=['GET'])
@authentication_required
def get_images(product_id):
    statsd.incr(f'{namespace}.api_calls.getimages')
    app.logger.info('to get all images details')
    # Check if the product exists
    Session = sessionmaker(bind=db)
    session = Session()
    product = session.query(Product).filter_by(id=product_id).one()
    if not product:
        app.logger.error('invalid product id')
        return 'Invalid product ID', 400

    # Get all images for the product
    images = session.query(Image).filter_by(product_id=product_id).all()
    if not images:
        app.logger.error('invalid image id')
        return 'No images found for the product', 404

    # Create a list of image details
    image_list = []
    for image in images:
        image_details = {
            'image_id': image.image_id,
            'file_name': image.file_name,
            'date_created': image.date_created,
            's3_bucket_path': image.s3_bucket_path
        }
        image_list.append(image_details)

    return jsonify(image_list), 200

@app.route('/v1/product/<product_id>/image/<image_id>', methods=['DELETE'])
@authentication_required
def delete_image(product_id, image_id):
    statsd.incr(f'{namespace}.api_calls.deleteimage')
    app.logger.info('to delete image')
    # Check if the product exists
    Session = sessionmaker(bind=db)
    session = Session()
    product = session.query(Product).get(product_id)
    if not product:
        app.logger.error('invalid product id')
        return 'Invalid product ID', 400

    # Check if the image exists and belongs to the product
    image = session.query(Image).filter_by(image_id=image_id).first()
    if not image:
        app.logger.error('invalid image id')
        return 'Invalid image ID', 400
    elif image.product_id != int(product_id):
        app.logger.error('image doesnt belong to this product id')
        return 'Image does not belong to this product', 400

    # Delete the image from S3
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=BUCKET_NAME, Key=image.file_name)

    # Delete the image from the database
    session.delete(image)
    session.commit()

    return 'Image deleted successfully', 200

# Run app
if __name__ == '__main__':

    app.run(host='0.0.0.0',port=8765,debug=True)
