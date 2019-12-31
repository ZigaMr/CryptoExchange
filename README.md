# CryptoExchange

Virtual crypto exchange, based on real market data scraped from Bitstamp API.
Installed libraries used in venv:
asgiref==3.2.3
certifi==2019.11.28
chardet==3.0.4
Django==3.0
django-background-tasks==1.2.0
django-compat==1.0.15
idna==2.8
numpy==1.17.4
pandas==0.25.3
python-dateutil==2.8.1
pytz==2019.3
requests==2.22.0
six==1.13.0
sqlparse==0.3.0
urllib3==1.25.7

To start, first run data_pull.py(python data_pull.py).
Then run python manage.py("runserver" already contained in script for debugging purpouses).

Site is still under development so there will be bugs, I still have to add bots traffic, so only API data is used. 
I'm not good at front-end so it doesn't look good yet.
