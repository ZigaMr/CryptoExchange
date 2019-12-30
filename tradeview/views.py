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
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
import time

def get_data_from_db(pair_id=2):
    con = db.connect('db.sqlite3')

    for i in range(4):
        bids = pd.read_sql("""select * from
                        (
                        select Price price, Volume volume, TimeStamp timestamp,'API' as username
                        from tradeview_bids where id_pair = {}
                        union
                        select price, volume, timestamp, username
                        from (select a.*, b.username from tradeview_localbids as a join auth_user as b on a.user = b.id)
                        where pair_id = {} and buy = 1
                        )
                        order by cast(price as decimal) desc""".format(pair_id, pair_id), con=con)
        if len(bids) >= 10:
            break
        time.sleep(0.01)
    for i in range(4):
        asks = pd.read_sql("""select * from
                            (
                            select Price price, Volume volume, TimeStamp timestamp,'API' as username
                            from tradeview_asks where id_pair = {}
                            union
                            select price, volume, timestamp, username
                            from (select a.*, b.username from tradeview_localbids as a join auth_user as b on a.user = b.id)
                            where pair_id = {} and buy = 0
                            )
                            order by cast(price as decimal)""".format(pair_id, pair_id), con=con)
        if len(asks) >= 10:
            break
        time.sleep(0.01)

    # if pd.to_datetime(bids['TimeStamp']).max() < dt.datetime.utcnow() - dt.timedelta(seconds=10):
    #     print('Update orderbook')
    #     get_data()
    bids_dict = [{'price': float(x[0]), 'amount':float(x[1]), 'username':x[3], 'timestamp':x[2]} for x in bids.itertuples(index=False)][:10]
    asks_dict = [{'price': float(x[0]), 'amount':float(x[1]), 'username':x[3], 'timestamp':x[2]} for x in asks.itertuples(index=False)][:10]
    bidask = dict()
    bidask['asks'] = asks_dict
    bidask['bids'] = bids_dict
    return bidask


def update_session(request):
    # if not request.is_ajax() or not request.method=='POST':
    #     return HttpResponseNotAllowed(['POST'])

    request.session['coin_pair'] = max((request.session['coin_pair'] + 1) % (Pairs.objects.count(                                                                                                                            ) + 1),1)
    form=UserBids()
    print(request.session['coin_pair'])
    return render(request, 'trade_page.html',
                  {'orderbook': get_data_from_db(),
                   'bids': [(j['username'], round(j['price'], 7), round(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                   'asks': [(j['username'], round(j['price'], 7), round(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['asks'][:10])],
                   'form':form,
                   'username': request.user.username
                   })

def index(request):
    request.session['coin_pair'] = 1
    return render(request, 'index.html', {'orderbook': get_data_from_db(request.session['coin_pair'])})

def refresh_orderbook(request):
    return render(request, 'refresh_orderbook.html', {'orderbook': get_data_from_db(request.session['coin_pair'])})

def refresh_table(request):
    return render(request, 'refresh_table.html',
                  {'bids': [(j['username'], round(j['price'], 7), round(j['amount'],2), Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                   'asks': [(j['username'], round(j['price'], 7), round(j['amount'],2), Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['asks'][:10])]
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
            return redirect('trade_page')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def trade_page(request):
    if request.method == 'POST':
        form = UserBids(request.POST)
        quantity = form.data['quantity']
        price = form.data['price']
        pair = form.data['pair']
        buy = 'BUY' in form.data.keys()

        d = LocalBids(user=int(request.user.id), timestamp=str(dt.datetime.utcnow()),
                      volume=float(quantity), price=float(price),
                      pair=Pairs.objects.get(buy_pair=pair.split('-')[0], sell_pair=pair.split('-')[1]),
                      buy=buy
                      )
        d.save()
    else:
        form = UserBids()
    print(request.POST)
    return render(request, 'trade_page.html',
                  {'orderbook': get_data_from_db(),
                   'bids': [(j['username'], round(j['price'], 7), round(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                   'asks': [(j['username'], round(j['price'], 7), round(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['asks'][:10])],
                   'form':form,
                   'username': request.user.username
                   })


