# MFA Secured Website
<a href="http://dev.bandwidth.com"><img src="https://s3.amazonaws.com/bwdemos/BW-VMP.png"/></a>

 # Table of Contents

<!-- TOC -->

* [MFA Secured Website](#mfa-secured-website)
* [Description](#description)
* [Pre-Requisites](#pre-requisites)
* [Environmental Variables](#environmental-variables)
* [Running the Application](#running-the-application)
  * [Run](#run)

<!-- /TOC -->

# Description

Example of a website with an admin page that is secured by MFA.

## What You Can Do

- Go to http://localhost:5000 and you will see user login
- Enter a username, anything will do; Note that it will be referenced in the message sent with the MFA Code
- Select your preference for delivery of the Code, either voice or sms (this will persist for this session)
- Click login, then you'll be presented with a page where you enter the MFA code; this is the "login" scope
- Enter the code you receive on your phone
- You can click the link to the "secure area", which is another area that is protected by a different scope
- again you enter a MFA code that will be sent to your phone. This will be delivered via the same as your already selected preference. To change this you will need to log out.

## Read through the Code

The code for this example is fairly well documented, so please take a look through it to understand how it works. But here are a few pointers on flow

### General Flow

The path that you take for verification via MFA is as follows:

1. Determine the user's phone number.
1. Request a MFA be sent to them via voice (`create_voice_two_factor`) or sms (`create_messaging_two_factor`) the body which is required is detailed in the app.
1. Request that the user provide the code which arrives on their device back to you.
1. Verify the code via the `create_verify_two_factor` call, it returns True or False in `response.body.valid`.

This application makes use of 2 Scopes, one for Login and one for Admin. This allows for the separation of these MFAs, a code for one cannot be used for the other.

# Pre-Requisites

Python 3.7.6+ installed with pip.

In order to use the Bandwidth API, users need to set up the appropriate application in their [Bandwidth Dashboard](https://dashboard.bandwidth.com/) and create [API credentials](https://dev.bandwidth.com/guides/accountCredentials.html#top).

To create an application, log into the [Bandwidth Dashboard](https://dashboard.bandwidth.com/) and navigate to the `Applications` tab.  Fill out the **New Application** form, selecting the service (Messaging or Voice) that the application will be used for.

For more information about API credentials see [here](https://dev.bandwidth.com/guides/accountCredentials.html#top).

# Environmental Variables

The sample app uses the below environmental variables.
```sh
BW_ACCOUNT_ID                        # Your Bandwidth Account Id
BW_USERNAME                          # Your Bandwidth API Username
BW_PASSWORD                          # Your Bandwidth API Password
BW_VOICE_APPLICATION_ID              # Your Voice Application Id created in the dashboard
BW_MESSAGING_APPLICATION_ID          # Your Messaging Application Id created in the dashboard
BW_NUMBER                            # The Bandwidth phone number involved with this application
USER_NUMBER                          # The user's phone number involved with this application
BASE_CALLBACK_URL                    # Your public base url to receive Bandwidth Webhooks. No trailing '/'
```

# Running the Application
## Run
Use the following commands to run the application:

```sh
pip install -r requirements.txt
python app.py
```
