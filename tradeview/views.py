from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.template import loader, Context
import requests
import pandas as pd
from .models import LocalBids, Pairs, Bots, Trades
import sqlite3 as db
import datetime as dt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import UserBids
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
import time
import math

#Helper functions

#Round to nearest non zero decimal
def myround(n, n_places=2):
    if n == 0:
        return 0
    sgn = -1 if n < 0 else 1
    scale = int(-math.floor(math.log10(abs(n))))
    if scale <= 0:
        scale = 1
    factor = 10**(scale+n_places)
    return sgn*math.floor(abs(n)*factor)/factor

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


    bids_dict = [{'price': float(x[0]), 'amount':float(x[1]), 'username':x[3], 'timestamp':x[2]} for x in bids.itertuples(index=False)][:10]
    asks_dict = [{'price': float(x[0]), 'amount':float(x[1]), 'username':x[3], 'timestamp':x[2]} for x in asks.itertuples(index=False)][:10]
    bidask = dict()
    bidask['asks'] = asks_dict
    bidask['bids'] = bids_dict
    return bidask

def portfolio_helper(df):
    if df[df.buy].volume.sum() >= df[~df.buy].volume.sum():
        vol = df[~df.buy].volume.sum()
        sell_p = df[~df.buy].profit.sum()
        x = df[df.buy]
        x['cum_vol'] = x.volume.cumsum()
        realized = x[x.cum_vol <= vol]
        buy_p = realized.profit.sum()
        if vol != round(realized.volume.sum(),10):
            p = (x[x.cum_vol > vol].cum_vol.iloc[0] - vol) * x[x.cum_vol > vol].price.iloc[0]
            buy_p += p
        else:
            p = 0
        unrealized = x[x.cum_vol > vol].profit.sum() - p
        un_vol = df[df.buy].volume.sum() - vol
    else:
        vol = df[df.buy].volume.sum()
        buy_p = df[df.buy].profit.sum()
        x = df[~df.buy]
        x['cum_vol'] = x.volume.cumsum()
        realized = x[x.cum_vol <= vol]
        sell_p = realized.profit.sum()
        if vol != round(realized.volume.sum(),10):
            p = (x[x.cum_vol > vol].cum_vol.iloc[0] - vol) * x[x.cum_vol > vol].price.iloc[0]
            sell_p += p
        else:
            p = 0
        unrealized = x[x.cum_vol > vol].profit.sum() - p
        un_vol = df[~df.buy].volume.sum() - vol

    return [sell_p+buy_p, unrealized, vol, un_vol, df.volume.sum()]

def update_session(request):
    # if not request.is_ajax() or not request.method=='POST':
    #     return HttpResponseNotAllowed(['POST'])

    request.session['coin_pair'] = max((request.session['coin_pair'] + 1) % (Pairs.objects.count() + 1),1)
    form=UserBids()
    print(request.session['coin_pair'])
    return render(request, 'trade_page.html',
                  {'orderbook': get_data_from_db(),
                   'bids': [(j['username'], myround(j['price'], 3), myround(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                   'asks': [(j['username'], myround(j['price'], 3), myround(j['amount'], 2), Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['asks'][:10])],
                   'form':form,
                   'username': request.user.username,
                   'pairs': [i[1]+'-'+i[2] for i in Pairs.objects.values_list()]
                   })

def index(request):
    request.session['coin_pair'] = 1
    return render(request, 'index.html', {'orderbook': get_data_from_db(request.session['coin_pair'])})

def refresh_orderbook(request):
    return render(request, 'refresh_orderbook.html', {'orderbook': get_data_from_db(request.session['coin_pair'])})

def refresh_table(request):
    return render(request, 'refresh_table.html',
                  {'bids': [(j['username'], myround(j['price'], 3), myround(j['amount'],2), Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                            for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                   'asks': [(j['username'], myround(j['price'], 3), myround(j['amount'],2), Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
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

    df = pd.DataFrame(list(Trades.objects.filter(user=request.user.id).all().values()))
    if not df.empty:
        df['profit'] = df.volume*df.price*(df.buy.apply(lambda x: 1 if x == 0 else -1))
        d = df.groupby('pair_id').apply(portfolio_helper)
        portfolio = [['_'.join(Pairs.objects.filter(id_pair=i.pair_id).values_list()[0][1:])]+[myround(x) for x in i[0]]
                     for j, i in d.reset_index().iterrows()]
    else:
        portfolio = []

    if request.method == 'POST':
        form = UserBids(request.POST)
        quantity = form.data['quantity']
        price = 0 if form.data['price'] == '' else form.data['price']
        pair = form.data['pair']
        buy = 'BUY' in form.data.keys()

        d = LocalBids(user=int(request.user.id), timestamp=str(dt.datetime.utcnow()),
                      volume=float(quantity), price=float(price),
                      pair=Pairs.objects.get(buy_pair=pair.split('-')[0], sell_pair=pair.split('-')[1]),
                      buy=buy
                      )
        d.save()
        print(request.POST)
        return HttpResponseRedirect('/tradeview/trade_page/')

    else:
        form = UserBids()
        return render(request, 'trade_page.html',
                      {'orderbook': get_data_from_db(),
                       'bids': [(j['username'], myround(j['price'], 3), myround(j['amount'], 3),
                                 Pairs.objects.get(id_pair=request.session['coin_pair']).buy_pair)
                                for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['bids'][:10])],
                       'asks': [(j['username'], myround(j['price'], 3), myround(j['amount'], 3),
                                 Pairs.objects.get(id_pair=request.session['coin_pair']).sell_pair)
                                for i, j in enumerate(get_data_from_db(request.session['coin_pair'])['asks'][:10])],
                       'form': form,
                       'username': request.user.username,
                       'pairs': [i[1] + '-' + i[2] for i in Pairs.objects.values_list()],
                       'portfolio': portfolio
                       })




