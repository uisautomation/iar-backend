Administrator's Guide
=====================

This section has some notes on how to perform some administration tasks.

Data migration from initial data
--------------------------------

The [iar-migration](https://github.com/uisautomation/iar-migration) repository
has a set of scripts which are used to migrate asset entries from the old
spreadsheet list into the new database.

The repository contains an ``upload.py`` script which takes a series of YAML
documents describing the asset entries to add and a token for a user to add them
as.

By default, users do not have the ability to create or edit assets outside of
their own institution. However, the Django add, change and delete permissions
are respected so to grant a user powers to perform a migration:

1. Log into the app as the desired admin user. For example, ``spqr2``.

2. Create a superuser user, e.g. ``mug99`` via ``./migrate.py createsuperuser``.

3. Navigate to http://iar-backend.invalid/accounts/login and log in as the super
   user.

4. Navigate to http://iar-backend.invalid/admin and locate the ``crsid+spqr2``
   user.

5. Give that user permissions to add and edit assets.

The OAuth2 token from the frontend app may now be used to upload assets.
