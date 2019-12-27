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
    tim = dt.datetime.utcnow()
    asks_final = pd.DataFrame(columns=['Volume', 'Price', 'TimeStamp', 'ID_pair_id'])
    bids_final = pd.DataFrame(columns=['Volume', 'Price', 'TimeStamp', 'ID_pair_id'])
    d = pd.read_sql('select * from tradeview_pairs', con)
    if d.empty:
        time.sleep(60)
        print('No Pairs in table')
    for ind, id, buy, sell in d.itertuples():
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
        asks['TimeStamp'] = tim
        asks['id_pair'] = id
        # bids.price = bids.Price.apply(float)
        # bids.quantity = bids.Volume.apply(float)
        bids['TimeStamp'] = tim
        bids['id_pair'] = id
        print(buy, sell, len(data))
        asks_final = asks_final.append(asks)
        bids_final = bids_final.append(bids)
        time.sleep(int(sys.argv[1]))
    asks_final.to_sql(name='tradeview_asks', con=con, if_exists='replace', index=False)
    bids_final.to_sql(name='tradeview_bids', con=con, if_exists='replace', index=False)
    return

if __name__ == '__main__':
    while True:
        print(sys.argv)
        try:
            get_data()
        except Exception as e:
            print(e)
            print("Can't access Bitstamp API, sleeping 60s")
            time.sleep(60)