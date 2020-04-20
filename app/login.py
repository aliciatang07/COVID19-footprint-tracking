# coding=UTF-8

from app import webapp
from flask import render_template, session, request, redirect, url_for
from app import dynamo
from app.dynamo import  dynamodb
import hashlib
import os

LOGIN_ERROR_INVALID_CREDENTIALS = 1
LOGIN_ERROR_SUCCESSFUL_REGISTRATION = 2
LOGIN_ERROR_MANDATORY_FIELDS_MISSING = 3

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'


# Route for displaying login screen
@webapp.route('/login', methods=['GET', 'POST'])
def login():
    registration_success = False
    error = False
    error_text = ""
    # Find the login_error flag in session
    if "login_error" in session:
        error = True
        # Username not found or password not correct
        if session["login_error"] == LOGIN_ERROR_INVALID_CREDENTIALS:
            error_text = "Your user name or password does not match our records."
        # Page was redirected from a registration page
        elif session["login_error"] == LOGIN_ERROR_SUCCESSFUL_REGISTRATION:
            error_text = "Registration is complete. Please log in."
            registration_success = True
        # Not all fields have value
        elif session["login_error"] == LOGIN_ERROR_MANDATORY_FIELDS_MISSING:
            error_text = "All fields are required."

        # Delete the flag from session
        session.pop("login_error", None)

    # Prevent user from logging twice
    if "user" in session and "logged" in session:
        return redirect(url_for("main"))

    return render_template("login.html",
                           error=error,
                           error_text=error_text,
                           registration_success=registration_success)


# Route for submitting login information
@webapp.route('/login_submit', methods=['POST'])
def login_submit():
    username = request.form.get("username")
    password = request.form.get("password")
    # Validate if all fields have value
    if username == "" or password == "":
        # Save the error flag in cookies so an error message
        # can be displayed when page refreshes.
        session["login_error"] = LOGIN_ERROR_MANDATORY_FIELDS_MISSING
        return redirect(url_for("login"))


    table = dynamodb.Table('user')
    item = dynamo.get_item('user',{"user_id":username})

    # Retrieve hashed password of the entered user from database


    # By default the program assumes either user is not found
    # or password does not match the record
    authenticated = False

        # If the user is found in database
        # Append salt to password and perform SHA256
    print(item)
    if(item!=None):
        combined = password + item["salt"]
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        print(hashed)
        if hashed == item["password"]:
            authenticated = True
        # User is unique so there's no need to continue the loop

    if authenticated:
        # If identity is authenticated, save the username
        # and the flag showing a user has logged in to session cookie
        session['logged'] = True
        session['user'] = username
        session.permanent = True
        return redirect(url_for("main"))
    else:
        # Otherwise save the error message to session cookie.
        session['login_error'] = LOGIN_ERROR_INVALID_CREDENTIALS
        return redirect(url_for("login"))


# Route for logging out
@webapp.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session so that it clears all login information
    session.clear()
    return redirect(url_for("main"))
