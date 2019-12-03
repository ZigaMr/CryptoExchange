from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader, Context
import requests
import pandas as pd

def get_data():
    data = requests.get(r'https://www.bitstamp.net/api/v2/order_book/ethbtc')
    data = data.json()

    bids = pd.DataFrame()
    bids['quantity'] = [i[1] for i in data['bids']]
    bids['price'] = [i[0] for i in data['bids']]
    asks = pd.DataFrame()
    asks['price'] = [i[0] for i in data['asks']]
    asks['quantity'] = [i[1] for i in data['asks']]

    asks.price = asks.price.apply(float)
    asks.quantity = asks.quantity.apply(float)

    bids.price = bids.price.apply(float)
    bids.quantity = bids.quantity.apply(float)

    bids_dict = {x[1]:x[0] for x in bids.itertuples(index=False)}
    asks_dict = {x[0]:x[1] for x in asks.itertuples(index=False)}
    bidask = dict()
    bidask['asks'] = asks_dict
    bidask['bids'] = bids_dict

    data['asks'] = [{'price':float(i[0]), 'amount':float(i[1])} for i in data['asks']][:10]
    data['bids'] = [{'price':float(i[0]), 'amount':float(i[1])} for i in data['bids']][:10]
    return data

def index(request):
    template = loader.get_template('index.html')
    context = {}
    # return template('glavni.html', mail=None, geslo=None,ime=None,priimek=None, napaka_registriraj=None,napaka_prijava=None, orderbook=data)
    return render(request, 'index.html', {'orderbook': get_data()})
    # return HttpResponse(template.render({'orderbook': get_data()}, request))

def refresh_orderbook(request):
    template = loader.get_template('refresh_orderbook.html')
    # results = get_data()
    # return render(request, 'refresh_orderbook.html', {'orderbook': get_data()})
    return HttpResponse(template.render({'orderbook': get_data()}, request))
