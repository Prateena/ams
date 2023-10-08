# Artist Management System
## Table of Contents
* [Development Setup](#development-setup)
    * [Prerequisites](#prerequisites)
    * [Initial Setup](#initial-setup)
    * [Running Project](#running-project)

## Development Setup

### Prerequisites
---------------------
- python >= 3.8
- Git
- Virtualenv

### Initial Setup
---------------------
- Clone main repository locally.
```
    $ git clone git@github.com:Prateena/ams.git
    $ cd ams
```

- Create a virtualenv
```
    $ virtualenv venv --python=python3.8
    $ source venv/bin/activate
```

on Windows,
```
    > env\Scripts\activate
```

- install development dependencies.
```
   $ pip install -r requirements.txt
```

- Copy settings.py.example to settings.py located in the project's main directory.
```
    $ cp settings.py.example settings.py
```

- Copy .env.example to .env in root directory of the project.
```
    $ cp .env.example .env
```
 > Note: Make sure you have required values in .env file before development.


## Running project
### Running migrations
```
    $ python manage.py makemigrations 
    $ python manage.py migrate
```

### Running project
```
    $ python manage.py runserver
```