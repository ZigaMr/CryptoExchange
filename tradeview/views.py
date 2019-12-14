from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.template import loader, Context
import requests
import pandas as pd
from .models import tradeview_asks, tradeview_bids, tradeview_pairs
import sqlite3 as db
import datetime as dt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate

def get_data():
    con = db.connect('db.sqlite3')
    for id, buy, sell in tradeview_pairs.objects.values_list():
        data = requests.get(r'https://www.bitstamp.net/api/v2/order_book/{}{}'.format(buy.lower(), sell.lower()))
        data = data.json()

        bids = pd.DataFrame()
        bids['Volume'] = [i[1] for i in data['bids']]
        bids['Price'] = [i[0] for i in data['bids']]
        asks = pd.DataFrame()
        asks['Price'] = [i[0] for i in data['asks']]
        asks['Volume'] = [i[1] for i in data['asks']]

        # asks.price = asks.Price.apply(float)
        # asks.quantity = asks.Volume.apply(float)
        asks['TimeStamp'] = dt.datetime.utcnow()
        asks['ID_pair_id'] = id
        # bids.price = bids.Price.apply(float)
        # bids.quantity = bids.Volume.apply(float)
        bids['TimeStamp'] = dt.datetime.utcnow()
        bids['ID_pair_id'] = id

        asks.to_sql(name='tradeview_tradeview_asks', con=con, if_exists='replace', index=False)
        bids.to_sql(name='tradeview_tradeview_bids', con=con, if_exists='replace', index=False)
    return

def get_data_from_db():
    con = db.connect('db.sqlite3')

    bids = pd.read_sql('select Price, Volume, TimeStamp from tradeview_tradeview_bids', con=con)
    asks = pd.read_sql(' select Price, Volume, TimeStamp from tradeview_tradeview_asks', con=con)

    if pd.to_datetime(bids['TimeStamp']).max() < dt.datetime.utcnow() - dt.timedelta(seconds=10):
        print('Update orderbook')
        get_data()
    bids_dict = [{'price': float(x[0]), 'amount':float(x[1])} for x in bids.itertuples(index=False)][:10]
    asks_dict = [{'price': float(x[0]), 'amount':float(x[1])} for x in asks.itertuples(index=False)][:10]
    bidask = dict()
    bidask['asks'] = asks_dict
    bidask['bids'] = bids_dict
    return bidask

def index(request):
    get_data()
    return render(request, 'index.html', {'orderbook': get_data_from_db()})

def refresh_orderbook(request):
    return render(request, 'refresh_orderbook.html', {'orderbook': get_data_from_db()})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
