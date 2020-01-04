import requests
import pandas as pd
import sqlite3 as db
import traceback
import time
import sys
import datetime as dt
import numpy as np
con = db.connect('db.sqlite3')

def get_data(orders_local):
    print(dt.datetime.utcnow())
    tim = dt.datetime.utcnow()
    asks_final = pd.DataFrame(columns=['Volume', 'Price', 'TimeStamp', 'ID_pair_id'])
    bids_final = pd.DataFrame(columns=['Volume', 'Price', 'TimeStamp', 'ID_pair_id'])
    d = pd.read_sql('select * from tradeview_pairs', con)

    if d.empty:
        time.sleep(60)
        print('No Pairs in table')

    modify_orders, delete_orders = dict(), []
    trades = pd.DataFrame(columns=['user', 'TimeStamp', 'Volume', 'Price', 'id_pair'])
    for ind, id, buy, sell in d.itertuples():
        data = requests.get(r'https://www.bitstamp.net/api/v2/order_book/{}{}'.format(buy.lower(), sell.lower()))
        data = data.json()

        bids = pd.DataFrame()
        bids['Volume'] = [float(i[1]) for i in data['bids']]
        bids['Price'] = [float(i[0]) for i in data['bids']]
        asks = pd.DataFrame()
        asks['Price'] = [float(i[0]) for i in data['asks']]
        asks['Volume'] = [float(i[1]) for i in data['asks']]

        asks['TimeStamp'] = tim
        asks['id_pair'] = id

        bids['TimeStamp'] = tim
        bids['id_pair'] = id
        print('Matching Bitstamp orders')


        #Using cumulative sum to calculate trades for local orders
        asks['cum_vol'] = asks.Volume.astype(float).cumsum()
        bids['cum_vol'] = bids.Volume.astype(float).cumsum()

        for ind, order in orders_local[orders_local.pair_id == id].iterrows():
            if order.buy == 1 and order.price >= asks.Price.astype(float).min():
                asks['cum_vol'] = np.where(asks.Price.astype(float) <= order.price,
                                           asks.cum_vol-order.volume,
                                           asks.cum_vol)
                if asks[asks.Price.astype(float) <= order.price].Volume.sum() >= order.volume:
                    delete_orders.append(order.id)
                    print('Deleting buy order: ', order.id)
                    pr = asks[asks.cum_vol <= 0].Volume.sum()
                    tr = asks[asks.cum_vol <= 0][['TimeStamp', 'Volume', 'Price', 'id_pair']]
                    asks = asks[asks.cum_vol > 0].reset_index(drop=True)
                    asks.Volume.iloc[0] -= (order.volume - pr)
                    tr = tr.append(asks.loc[:0, :][['TimeStamp', 'Volume', 'Price', 'id_pair']])
                    tr.Volume.iloc[-1] = (order.volume - pr)
                else:
                    modify_orders[order.id] = order.volume - asks[asks.Price.astype(float) <= order.price].Volume.sum()
                    print('Modifying buy order: ', order.id)
                    tr = asks[asks.cum_vol <= 0][['TimeStamp', 'Volume', 'Price', 'id_pair']]
                    asks = asks[asks.cum_vol > 0].reset_index(drop=True)


                tr['user'] = order.user
                tr['buy'] = 1
                trades = trades.append(tr[['user', 'TimeStamp', 'Volume', 'Price', 'id_pair', 'buy']])
                asks['cum_vol'] = asks.Volume.astype(float).cumsum()

            elif order.buy == 0 and order.price <= bids.Price.astype(float).max():
                bids['cum_vol'] = np.where(bids.Price.astype(float) >= order.price, bids.cum_vol-order.volume, bids.cum_vol)
                if bids[bids.Price.astype(float) >= order.price].Volume.sum() >= order.volume:
                    delete_orders.append(order.id)
                    print('Deleting ask order: ', order.id)
                    pr = bids[bids.cum_vol <= 0].Volume.sum()
                    tr = bids[bids.cum_vol <= 0][['TimeStamp', 'Volume', 'Price', 'id_pair']]
                    bids = bids[bids.cum_vol > 0].reset_index(drop=True)
                    bids.Volume.iloc[0] -= (order.volume - pr)
                    tr = tr.append(bids.loc[:0, :][['TimeStamp', 'Volume', 'Price', 'id_pair']])
                    tr.Volume.iloc[-1] = (order.volume - pr)
                else:
                    modify_orders[order.id] = order.volume - bids[bids.Price.astype(float) >= order.price].Volume.sum()
                    print('Modifying ask order: ', order.id)
                    tr = asks[asks.cum_vol <= 0][['TimeStamp', 'Volume', 'Price', 'id_pair']]
                    bids = bids[bids.cum_vol > 0].reset_index(drop=True)

                tr['user'] = order.user
                tr['buy'] = 0
                trades = trades.append(tr[['user', 'TimeStamp', 'Volume', 'Price', 'id_pair', 'buy']])
                bids['cum_vol'] = bids.Volume.astype(float).cumsum()

        asks = asks[asks.cum_vol > 0].drop('cum_vol', 1)
        bids = bids[bids.cum_vol > 0].drop('cum_vol', 1)
        print(buy, sell)
        asks_final = asks_final.append(asks)
        bids_final = bids_final.append(bids)
        time.sleep(1)#int(sys.argv[1]))
    if not trades.empty:
        trades = trades.rename(columns={'id_pair': 'pair_id'})
        trades.columns = [i.lower() for i in trades.columns]
        trades.to_sql('tradeview_trades', con, if_exists='append', index=False)
    cursor = con.cursor()
    if len(delete_orders) > 0:
        cursor.execute('delete from tradeview_localbids where id in {}'.format('(' + str(delete_orders[0]) +')' if len(delete_orders) == 1 else tuple(delete_orders)))
    if len(modify_orders) > 0:
        for i, j in modify_orders.items():
            cursor.execute('update tradeview_localbids set volume = {} where id = {}'.format(j, i))
    con.commit()
    cursor.close()

    asks_final.to_sql(name='tradeview_asks', con=con, if_exists='replace', index=False)
    bids_final.to_sql(name='tradeview_bids', con=con, if_exists='replace', index=False)
    return

def internal_matching(df):
    if df.empty:
        return df
    modify_orders, delete_orders = dict(), []
    trades = pd.DataFrame(columns=['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id'])


    for pair in df.pair_id.unique():
        asks = df[(~df.buy) & (df.pair_id == pair)].sort_values('price', ascending=True)
        # bids = df[df.buy & (df.pair_id == pair) & (df.price >= asks.price.min())].sort_values('price', ascending=False)
        bids = df[df.buy & (df.pair_id == pair)].sort_values('price', ascending=False)
        asks_final = pd.DataFrame(columns=['id', 'user', 'timestamp', 'volume', 'price', 'buy', 'pair_id'])

        #Using cumulative sum to calculate trades for local orders
        asks['cum_vol'] = asks.volume.cumsum()
        bids['cum_vol'] = bids.volume.cumsum()
        # if asks.empty or bids.empty:
        #     continue
        for ind, order in bids.iterrows():
            asks['cum_vol'] = np.where(asks.price <= order.price,
                                       asks.cum_vol - order.volume,
                                       asks.cum_vol)
            if order.price >= asks.price.min():
                if asks[asks.price <= order.price].volume.sum() >= order.volume:
                    delete_orders.append(order.id)
                    print('Deleting buy order: ', order.id)
                    pr = asks[asks.cum_vol <= 0].volume.sum()
                    tr = asks[asks.cum_vol <= 0][['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id']]
                    asks = asks[asks.cum_vol > 0].reset_index(drop=True)
                    if order.volume != pr:
                        asks.volume.iloc[0] -= (order.volume - pr)
                        tr = tr.append(asks.loc[:0, :][['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id']])
                        tr.volume.iloc[-1] = (order.volume - pr)
                else:
                    modify_orders[order.id] = order.volume - asks[asks.price <= order.price].volume.sum()
                    print('Modifying buy order: ', order.id)
                    tr = asks[asks.cum_vol <= 0][['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id']]
                    asks = asks[asks.cum_vol > 0].reset_index(drop=True)

                trades = trades.append(tr[['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id']])
                tr['user'] = order.user
                tr.buy = (tr.buy +1)%2
                trades = trades.append(tr[['user', 'timestamp', 'volume', 'price', 'buy', 'pair_id']])
                asks['cum_vol'] = asks.volume.cumsum()
            else:
                break
        asks = asks[asks.cum_vol > 0].drop('cum_vol', 1)
        asks_final = asks_final.append(asks)
    if not trades.empty:
        trades = trades.rename(columns={'id_pair': 'pair_id'})
        trades.columns = [i.lower() for i in trades.columns]
        trades.to_sql('tradeview_trades', con, if_exists='append', index=False)
    #Adding sell orders to delete
    delete_orders += list(df[(df.buy == 0) & (~df.id.isin(asks.id))].id)
    a = df[(df.buy == 0)][['id', 'volume']].merge(asks[['id', 'volume']], on=['id'])
    modify_orders.update({x.id: x.volume_y for i, x in a[a.volume_x != a.volume_y].iterrows()})
    cursor = con.cursor()
    if len(delete_orders) > 0:
        cursor.execute('delete from tradeview_localbids where id in {}'.format('(' + str(delete_orders[0]) +')' if len(delete_orders) == 1 else tuple(delete_orders)))
    if len(modify_orders) > 0:
        for i, j in modify_orders.items():
            cursor.execute('update tradeview_localbids set volume = {} where id = {}'.format(j, i))
    con.commit()
    cursor.close()
    df = df[~df.id.isin(delete_orders)]
    df.volume = [modify_orders[i.id] if i.id in modify_orders.keys() else i.volume for ind, i in df.iterrows()]
    return df

def api_matching():
    modify_orders, delete_orders = dict(), []
    pass

if __name__ == '__main__':
    while True:
        print(sys.argv)
        orders_local = pd.read_sql('select * from tradeview_localbids', con)
        try:
            get_data(internal_matching(orders_local))
        except Exception as e:
            print(traceback.print_exc())
            print("Can't access Bitstamp API, sleeping 60s")
            time.sleep(60)