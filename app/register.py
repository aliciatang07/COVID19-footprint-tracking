# coding=UTF-8

from app import webapp
from flask import render_template, session, request, redirect, url_for
from app import dynamo
from app.dynamo import dynamodb

import binascii
import hashlib
import os

REGISTER_ERROR_USER_EXISTS = 1
REGISTER_ERROR_MANDATORY_FIELDS_MISSING = 2
REGISTER_ERROR_PASSWORD_MISMATCH = 3
REGISTER_ERROR_USERNAME_LENGTH_ERROR = 4
REGISTER_ERROR_USERNAME_CONTAIN_WHITESPACE_ERROR = 5
REGISTER_ERROR_PASSWORD_LENGTH_ERROR = 6
REGISTER_ERROR_USERNAME_CONTAIN_UNDERSCORE_ERROR = 7

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'


# Function for closing the database connection first before redirecting in case of error
def safe_redirect(cursor, inst, target):
    cursor.close()
    inst.close()
    return redirect(target)


# Route for displaying sign up page
@webapp.route("/registration", methods=["GET", "POST"])
def register_form():
    error = False
    error_text = ""
    # Find the register_error flag in session
    if "register_error" in session:
        error = True
        # User name already exists in database records
        if session["register_error"] == REGISTER_ERROR_USER_EXISTS:
            error_text = "Sorry! This user already exists in our records."
        # Not all fields have value
        elif session["register_error"] == REGISTER_ERROR_MANDATORY_FIELDS_MISSING:
            error_text = "All fields are required."
        # Password and re-entered password do not match
        elif session["register_error"] == REGISTER_ERROR_PASSWORD_MISMATCH:
            error_text = "Passwords you entered do not match."
        # Username length is not in the requred range
        elif session["register_error"] == REGISTER_ERROR_USERNAME_LENGTH_ERROR:
            error_text = "Sorry! The username should be in 6-30 characters"
        # Username contains whitespace
        elif session["register_error"] == REGISTER_ERROR_USERNAME_CONTAIN_WHITESPACE_ERROR:
            error_text = "Sorry! No whitespace is allowed in username"
        elif session["register_error"] == REGISTER_ERROR_USERNAME_CONTAIN_UNDERSCORE_ERROR:
            error_text = "Sorry! No underscore is allowed in username"
        # Password length is not in the requred range
        elif session["register_error"] == REGISTER_ERROR_PASSWORD_LENGTH_ERROR:
            error_text = "Sorry! The password should be in 6-30 characters"
        session.pop("register_error", None)

    return render_template("register.html", error=error, error_text=error_text)


# Route for accepting registration request
@webapp.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    # Validate if all fields have value
    if username == "" or password == "" or confirm_password == "":
        # Save the error flag in cookies so an error message
        # can be displayed when page refreshes.
        session["register_error"] = REGISTER_ERROR_MANDATORY_FIELDS_MISSING
        return redirect(url_for("register_form"))
    # Validate if username length is within right range
    if len(username) > 30 or len(username) < 6:
        session["register_error"] = REGISTER_ERROR_USERNAME_LENGTH_ERROR
        return redirect(url_for("register_form"))
    # Validate if username contains whitespace
    if (' ' in username):
        session["register_error"] = REGISTER_ERROR_USERNAME_CONTAIN_WHITESPACE_ERROR
        return redirect(url_for("register_form"))
    if ('_' in username):
        session["register_error"] = REGISTER_ERROR_USERNAME_CONTAIN_UNDERSCORE_ERROR
        return redirect(url_for("register_form"))
    # Validate if password password is within right range
    if len(password) > 30 or len(password) < 6:
        session["register_error"] = REGISTER_ERROR_PASSWORD_LENGTH_ERROR
        return redirect(url_for("register_form"))
    # Validate if password entered match
    if password != confirm_password:
        session["register_error"] = REGISTER_ERROR_PASSWORD_MISMATCH
        return redirect(url_for("register_form"))

    # connect dynamodb
    table = dynamodb.Table('user')
    item = dynamo.get_item('user',{"user_id":username})
    user_exists = False
    if item != None:
        user_exists = True


    # # Retrieve user by the name entered
    # query = "SELECT * FROM users WHERE username=%s"
    # cursor.execute(query, (username,))

    # user_exists = False
    # # If a record is successfully retrieved, then the user exists
    # for _ in cursor:
    #     user_exists = True
    #     break

    # If user exists, abort the registration and give error message.
    if user_exists:
        session['register_error'] = REGISTER_ERROR_USER_EXISTS
        return redirect(url_for("register_form"))
        # return safe_redirect(cursor, inst, '/registration')

    # Insert user into database with hashed password and salt

    # query = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    # Generate salt from a random value and convert it to hexadecimal representation
    salt = binascii.b2a_hex(os.urandom(8)).decode("utf-8")
    # Append salt to password
    combined = password + salt
    # Hash the combined password
    hashed = hashlib.sha256(combined.encode()).hexdigest()
    data = {"user_id":username, "password":hashed, "salt":salt}
    dynamo.insert_data('user',data)

    # cursor.execute(query, (username, hashed, salt))
    # inst.commit()
    #
    # cursor.close()
    # inst.close()

    # Set the login error flag to "Successful registration"
    session["login_error"] = 2
    return redirect(url_for("login"))
