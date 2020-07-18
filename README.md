# Django Impersonate Permissions

Add ability to control impersonate permissions.

Impersonate is a powerful Django app that allow site admins to log in to a user's account, and take
actions on their behalf. This can be invalulable in providing technical support. However, with great
power comes great responsiblity, and operationally you should **never** impersonate a user without
their explicit consent.

This app provides a mechanism for recording user consent, and enforcing it.
