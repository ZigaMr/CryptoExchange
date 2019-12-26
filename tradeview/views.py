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

def get_data_from_db(pair_id=1):
    con = db.connect('db.sqlite3')

    bids = pd.read_sql('select Price, Volume, TimeStamp from tradeview_tradeview_bids where ID_pair_id = {}'.format(pair_id), con=con)
    asks = pd.read_sql('select Price, Volume, TimeStamp from tradeview_tradeview_asks where ID_pair_id = {}'.format(pair_id), con=con)

    # if pd.to_datetime(bids['TimeStamp']).max() < dt.datetime.utcnow() - dt.timedelta(seconds=10):
    #     print('Update orderbook')
    #     get_data()
    bids_dict = [{'price': float(x[0]), 'amount':float(x[1])} for x in bids.itertuples(index=False)][:10]
    asks_dict = [{'price': float(x[0]), 'amount':float(x[1])} for x in asks.itertuples(index=False)][:10]
    bidask = dict()
    bidask['asks'] = asks_dict
    bidask['bids'] = bids_dict
    return bidask

def index(request):
    return render(request, 'index.html', {'orderbook': get_data_from_db()})

def refresh_orderbook(request):
    return render(request, 'refresh_orderbook.html', {'orderbook': get_data_from_db()})

def refresh_table(request):
    return render(request, 'refresh_table.html',
                  {'bids': [(i, round(j['price'], 7), round(j['amount'],2), 1)
                            for i,j in enumerate(get_data_from_db()['bids'][:10])],
                   'asks': [(i, round(j['price'], 7), round(j['amount'],2), 1)
                            for i, j in enumerate(get_data_from_db()['asks'][:10])]
                   })

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

def trade_page(request):
    return render(request, 'trade_page.html',
                  {'orderbook': get_data_from_db(),
                   'bids': [(i, round(j['price'], 7), round(j['amount'], 2), 1)
                            for i, j in enumerate(get_data_from_db()['bids'][:10])],
                   'asks': [(i, round(j['price'], 7), round(j['amount'], 2), 1)
                            for i, j in enumerate(get_data_from_db()['asks'][:10])]
                   })

