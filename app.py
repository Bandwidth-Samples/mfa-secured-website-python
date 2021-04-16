"""
app.py

A simple MFA application that shows how to integrate with a login and administrative page
 that are both protected via Multi Factor Authentication, with different Scopes

@copyright Bandwidth INC
"""

import os
from user import User
from flask import Flask, request, Response, render_template, redirect, url_for
from bandwidth.bandwidth_client import BandwidthClient
from bandwidth.exceptions.api_exception import APIException

try:
    os.environ["BW_USERNAME"]
    os.environ["BW_PASSWORD"]
except error:
    print("Please set the environment variables defined in the README", error)
    exit(-1)

bandwidth_client = BandwidthClient(
    two_factor_auth_basic_auth_user_name=os.environ["BW_USERNAME"],
    two_factor_auth_basic_auth_password=os.environ["BW_PASSWORD"],
)

app = Flask(__name__)

# track our username
#  - if not a demo, these would be stored in persistant storage
globalUser = User("Name Not Set")
globalUser.security_level = 0


@app.route("/", methods=["GET"])
def show_login_page():
    # show the login page
    return render_template('home_page.html')


@app.route("/appPage", methods=["GET"])
def show_app_page():
    '''
    This should have precautions that only allow access after granting auth, this page will require 'login' scope
    '''
    user = get_user()
    if(user.security_level >= 1):
        # show the main app page
        return render_template('app_page.html', username=user.username)
    else:
        return render_template('error_page.html', username=user.username)


@ app.route("/securePage", methods=["GET"])
def show_secure_page():
    '''
    This should have precautions that only allow access after granting auth, this page will require 'admin' scope
    '''
    user = get_user()
    if(user.security_level >= 2):
        # show the secure app page
        return render_template('secure_page.html', username=user.username)
    else:
        return render_template('error_page.html', username=user.username)


@ app.route("/submitLogin", methods=["POST"])
def validateLogin():
    '''validate login info, and then send a MFA and prompt for a MFA'''
    # we would normally validate here, but we aren't in this simple example
    username = request.form['username']
    myUser = User(username)
    myUser.delivery_pref = request.form['delivery_preference']
    set_user(myUser)

    # throw up the MFA login page
    return show_mfa("login")


@ app.route("/goSecure", methods=["GET"])
def goSecure():
    user = get_user()
    print(f"Username '{user.username}' accessing secure site")
    return show_mfa("admin")


def show_mfa(scope):
    '''
    A function that will send a MFA code and then 
    show a MFA page; supports different SCOPEs
    :param the scope to show this for
    '''
    # obtain user info
    user = get_user()

    # send out MFA code
    sendMFA(os.environ["BW_ACCOUNT_ID"],
            user, scope)

    # then show MFA request
    # we'll pass the scope in the html for simplification of the demo, but it should be somewhere non-user accessible
    message = "We just sent you a MFA code for '" + scope + "', please enter it here"
    return render_template('mfa_form.html', username=user.username, scope=scope, message=message)


@ app.route("/MFASubmit", methods=["POST"])
def twofa_submit():
    user = get_user()
    # validate the MFA code
    code = request.form['code']
    scope = request.form['scope']

    if(validateMFA(os.environ["BW_ACCOUNT_ID"], user, scope, code) != True):
        return render_template('mfa_form.html', username=user.username, scope=scope, message="Sorry, wrong code, please try again")

    # update their security level
    # proceed on to protected area of the website
    if (scope == "login"):
        user.security_level = 1
        return redirect(url_for('show_app_page'))
    elif(scope == "admin"):
        user.security_level = 2
        return redirect(url_for('show_secure_page'))


@ app.route("/logOut", methods=["GET"])
def log_out():
    '''Clear the user info so you can try again'''
    user = get_user()
    print(f"Logging out ", user.username)
    user.security_level = 0  # just to be sure
    set_user(User("Invalid"))
    return redirect(url_for('show_login_page'))

#  ------------------------------------------------------------------------------------------
#  All the functions for interacting with Bandwidth MFA services below here
#


def set_user(this_user):
    global globalUser
    globalUser = this_user


def get_user():
    '''
    Return the user if it has already been created,
        this should be replaced with your own logic to get the username from a session
    :return: user
    :rtype: object
    '''
    global globalUser
    # simplifying things here, we would normally pull this data from a database
    if (globalUser.username != "Invalid"):
        globalUser.number = os.environ["USER_NUMBER"]

    return globalUser


def sendMFA(account_id, user, scope):
    '''
    Send out a MFA Code
    :param account_id your BAND account id
    :param user who is receiving this code, object has their number and username
    :param scope the scope for this request, e.g. login, secure action, etc
    :return None
    '''
    # FYI, printing the to_number in prod could violate PII
    print(
        f"For {user.username} sending MFA to {user.number} from {os.environ['BW_NUMBER']} for Scope '{scope}'")

    # determine if the user has a preference for voice or sms, for use below
    if(user.delivery_pref == "sms"):
        application_id = os.environ["BW_MESSAGING_APPLICATION_ID"]
    else:
        application_id = os.environ["BW_VOICE_APPLICATION_ID"]

    # These three variables are available for expansion by our MFA service
    # {NAME} (optional) is the name of your Application within the Bandwidth dashboard
    # {SCOPE} (optional) is the scope defined by this call, e.g. login, admin, verify
    # {CODE} (required) is the code created by the system
    message = user.username + ", your {NAME} {SCOPE} code is {CODE}"

    try:
        body = {
            # from is any number in the location referenced by your Bandwidth Messaging Application
            "from": os.environ["BW_NUMBER"],
            "to": user.number,  # the recipient of the message
            "applicationId": application_id,
            "scope": scope,
            "digits": 6,  # 4-8
            "message": message
        }
        auth_client = bandwidth_client.two_factor_auth_client.mfa
        if(user.delivery_pref == "sms"):
            auth_client.create_messaging_two_factor(account_id, body)
        else:
            auth_client.create_voice_two_factor(account_id, body)

        return None

    except APIException as e:
        print("sendMFA> Failed to send MFA: %s" %
              e.response.text)
        return None


def validateMFA(account_id, user, scope, code):
    '''
    Validate the MFA Code you sent out before
    :param account_id your BAND account id
    :param user who is receiving this code
    :param scope the scope for this request, e.g. login, secure action, etc
    :param code The code that was given back to you by the End User
    :return True or False
    '''
    # FYI, printing the to_number in prod could violate PII
    print(
        f"verifying MFA for {user.number} for Scope '{scope}''")
    # determine if the user has a preference for voice or sms, for use below
    if(user.delivery_pref == "sms"):
        application_id = os.environ["BW_MESSAGING_APPLICATION_ID"]
    else:
        application_id = os.environ["BW_VOICE_APPLICATION_ID"]

    try:
        body = {
            # Should be the same as your request
            "from": os.environ["BW_NUMBER"],
            "to": user.number,
            "applicationId": application_id,
            "scope": scope,
            "code": code,
            "digits": 6,
            "expirationTimeInMinutes": 3
        }
        auth_client = bandwidth_client.two_factor_auth_client.mfa
        response = auth_client.create_verify_two_factor(account_id, body)

        return response.body.valid

    except APIException as e:
        print("validateMFA> Failed to validate MFA: %s" %
              e.response.text)
        return None


if __name__ == '__main__':
    app.run(debug=True)
