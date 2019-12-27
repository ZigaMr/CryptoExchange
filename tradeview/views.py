from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.template import loader, Context
import requests
import pandas as pd
from .models import LocalBids, Pairs, Bots
import sqlite3 as db
import datetime as dt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import UserBids
from django.http import HttpResponseRedirect


def get_data_from_db(pair_id=1):
    con = db.connect('db.sqlite3')

    bids = pd.read_sql('select Price, Volume, TimeStamp from tradeview_bids where id_pair = {}'.format(pair_id), con=con)
    asks = pd.read_sql('select Price, Volume, TimeStamp from tradeview_asks where id_pair = {}'.format(pair_id), con=con)

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
                  {'bids': [('API', round(j['price'], 7), round(j['amount'],2), 1)
                            for i,j in enumerate(get_data_from_db()['bids'][:10])],
                   'asks': [('API', round(j['price'], 7), round(j['amount'],2), 1)
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
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UserBids(request.POST)
        quantity = form.data['quantity']
        price = form.data['price']
        pair = form.data['pair']
        buy = 'BUY' in form.data.keys()

        d = LocalBids(user=int(request.user.id), timestamp=str(dt.datetime.utcnow()),
                      volume=float(quantity), price=float(price),
                      pair=Pairs.objects.get(buy_pair=pair.split('-')[0], sell_pair=pair.split('-')[1])
                      )
        d.save()
        # check whether it's valid:
        # if form.is_valid():
        #     # process the data in form.cleaned_data as required
        #     # ...
        #     # redirect to a new URL:
        #     return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserBids()
    print(request.POST)
    d = Bots(2, True, 3, 4)
    d.save()
    return render(request, 'trade_page.html',
                  {'orderbook': get_data_from_db(),
                   'bids': [('API', round(j['price'], 7), round(j['amount'], 2), 1)
                            for i, j in enumerate(get_data_from_db()['bids'][:10])],
                   'asks': [('API', round(j['price'], 7), round(j['amount'], 2), 1)
                            for i, j in enumerate(get_data_from_db()['asks'][:10])],
                   'form':form
                   })


