qqc
===

QQC! is a very simple web UI for reporting errors in visual novel translations.


Installation intro
------------------

You will need to be root (at least for Postgres).

For the sake of this example, the DB and username is `qqc_quartett`. Substitute in your own names.

We also assume you have a mechanism for putting game scripts into the DB. The tools aren't online right now, but it's probably something like VASTT or TInEE, coupled with some decent python utilities for doing the dirty work of Postgres interfacing.


Setup a DB
----------

1. Create the user from the shell (you can do this in psql as well):
    ```
    createuser -SDR -PE qqc_quartett
    UD7kfuhliauwefhlauhe <- some password here
    createdb -T template0 -E UTF8 -O qqc_quartett qqc_quartett
    ```

2. Pipe the dump to psql shell for import:
    ```
    zcat qqc_quartett.sql.gz | psql qqc_quartett
    ```


Setup the app environment
-------------------------

You'll want to run QQC! in a virtualenv.

1. Install necessary distro packages, this is a Debian example:
    ```
    aptitude install python-virtualenv
    aptitude install libpq-dev python-dev
    ```

2. Create the virtualenv:
    ```
    virtualenv my_qqc
    cd my_qqc
    source bin/activate
    pip install pgdb
    pip install paste
    ```


Run it
------

The plan was to run it via gunicorn, but it's too hard and doesn't work. So
just use Apache with mod_wsgi instead. I've tried modernising but it just won't
work without a proper rewrite.

Your `.htaccess` file should ensure proper running of the scripts. This is
what's in the included sample htaccess:

```
AddHandler      wsgi-script     .py
AddHandler      wsgi-script     .pyc
```
