__author__ = 'Alimohammad'

from wtforms import Form, StringField, PasswordField, validators, BooleanField

from flask import current_app

import urllib
import urllib2
import json

class LoginForm(Form):
    email = StringField('Email Address', [validators.email(message=u'Invalid email address')])
    password = PasswordField('Password', [validators.DataRequired(message=u'Password required')])
    remember = BooleanField('Remember Me')