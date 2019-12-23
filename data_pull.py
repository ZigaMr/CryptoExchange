import requests
import pandas as pd
import sqlite3 as db
import datetime as dt
import time
import sys
import datetime as dt

def get_data():
    print(dt.datetime.utcnow())
    con = db.connect('db.sqlite3')
    for ind, id, buy, sell in pd.read_sql('select * from tradeview_tradeview_pairs', con).itertuples():
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
        print(buy, sell,len(data))
    return

if __name__ == '__main__':
    while True:
        print(sys.argv)
        get_data()
        time.sleep(int(sys.argv[1]))