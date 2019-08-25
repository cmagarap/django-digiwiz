# Digiwiz: An Open-source Learning Platform
> The system’s goal is to provide free courses and class resources to students who are willing to learn.
![DigiWiz Homepage](https://raw.githubusercontent.com/seeej/digiwiz/master/static/images/digiwiz-home-screenshot.png)

## Built with
* [Django 2.2.2](https://www.djangoproject.com/)
* JavaScript
* [Python 3.6.8](https://www.python.org/)
* SQLite

## Instructions
1. Install [Python](https://www.python.org/) (v.3.6.8 is recommended).
1. Clone or download this repository.
1. Using a command prompt/terminal, go the project folder: `/digiwiz/`
1. Install the dependencies: 
`pip install -r requirements.txt`
1. Run the server:
`python manage.py runserver [port number, default=8000]`
1. Using a web browser, go to `http://127.0.0.1:[port]/`


##### To apply changes in the database:
`python manage.py makemigrations`

`python manage.py migrate`

## Authors
* [Chris John Agarap](https://github.com/seeej) - Lead Developer
* Rex Christian Baldonado - Front-end Developer
* Jeane Cabahug - QA Tester
* Beatrizce Anne Danao - Documentation
* Shayne Hazel Palafox - Assistant Lead & Front-end Developer
