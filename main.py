### JUST FOR LEARNING PURPOSE USE AT YOUR OWN RISK !!!!! ####

# import neccessary package

import ccxt
import json
import pandas as pd
import time
import decimal
from datetime import datetime
import pytz
import csv

def read_config():
    with open('real_config.json') as json_file:
        return json.load(json_file)

config = read_config()

# Api and secret
api_key = config["apiKey"]
api_secret = config["secret"]
subaccount = config["sub_account"]
account_name = config["account_name"]  # Set your account name (ตั้งชื่อ Account ที่ต้องการให้แสดงผล)
pair = config["pair"]
token_name = config["token_name"]
fix_value = config["rebalance_value"]


# Exchange Details
exchange = ccxt.ftx({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True}
)
exchange.headers = {'FTX-SUBACCOUNT': subaccount,}
post_only = True  # Maker or Taker (วางโพซิชั่นเป็น MAKER เท่านั้นหรือไม่ True = ใช่)

# Global Varibale Setting
token_name_lst =[token_name]  # Name of Rebalancing Token (ใส่ชื่อเหรียญที่ต้องการ Rebalance)
pair_lst = [pair]  # Rebalancing Pair (ใส่ชื่อคู่ที่ต้องการ Rebalance เช่น XRP จะเป็น XRP/USD)
fix_value_lst = [fix_value]  # Rebalancing Ratio (ใส่สัดส่วนที่ต้องการ Rebalance หน่วยเป็น $)

# file system
tradelog_file = "tradinglog_{}.csv".format(subaccount)
trading_call_back = 5

# Rebalance Condition
min_reb_size = 1.5  # Minimum Rebalance Size ($)
time_sequence = [2, 5, 0, 2, 9, 0, 7, 8, 7, 5, 0, 9, 5, 8]  # Rebalancing Time Sequence (เวลาที่จะใช้ในการ Rebalance ใส่เป็นเวลาเดี่ยว หรือชุดตัวเลขก็ได้)
time_multiplier = 1

# List to Dict Setting
token_fix_value = {token_name_lst[i]: fix_value_lst[i] for i in range(len(token_name_lst))}
pair_dict = {token_name_lst[i]: pair_lst[i] for i in range(len(token_name_lst))}



### Function Part ###

def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return Time

def get_price():
    price = float(exchange.fetch_ticker(pair)['last'])
    return price

def get_ask_price():
    ask_price = float(exchange.fetch_ticker(pair)['ask'])
    return ask_price

def get_bid_price():
    bid_price = float(exchange.fetch_ticker(pair)['bid'])
    return bid_price

def get_pending_buy():
    pending_buy = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'buy':
            pending_buy.append(i['info'])
    return pending_buy

def get_pending_sell():
    pending_sell = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'sell':
            pending_sell.append(i['info'])
    return pending_sell

def create_buy_order():
    # Order Parameter
    types = 'limit'
    side = 'buy'
    size = buy_size
    price = buy_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    print("{} Buy Order Created".format(asset_name))
    
def create_sell_order():
    # Order Parameter
    types = 'limit'
    side = 'sell'
    size = sell_size
    price = sell_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    print("{} Sell Order Created".format(asset_name))
    
def cancel_order(order_id):
    order_id = order_id
    exchange.cancel_order(order_id)
    print("Order ID : {} Successfully Canceled".format(order_id))

def get_minimum_size():
    minimum_size = float(exchange.fetch_ticker(pair)['info']['minProvideSize'])
    return minimum_size

def get_step_size():
    step_size = float(exchange.fetch_ticker(pair)['info']['sizeIncrement'])
    return step_size

def get_step_price():
    step_price = float(exchange.fetch_ticker(pair)['info']['priceIncrement'])
    return step_price

def get_min_trade_value():
    min_trade_value = float(exchange.fetch_ticker(pair)['info']['sizeIncrement']) * price
    return min_trade_value

def get_wallet_details():
    wallet = exchange.privateGetWalletBalances()['result']
    return wallet

def get_cash():
    wallet = exchange.privateGetWalletBalances()['result']
    for t in wallet:
        if t['coin'] == 'USD':
            cash = float(t['availableWithoutBorrow'] )
    return cash

def buy_execute():
    pending_buy = get_pending_buy()
    if pending_buy == []:
        print('Buying {} Size = {}'.format(asset_name, buy_size))
        create_buy_order()
        time.sleep(2)
        pending_buy = get_pending_buy()

        if pending_buy != []:
            pending_buy_id = get_pending_buy()[0]['id']
            print('Buy Order Created Success, Order ID: {}'.format(pending_buy_id))
            print('Waiting For Buy Order To be Filled')
            print("------------------------------")
            time.sleep(10)
            pending_buy = get_pending_buy()

        if pending_buy == []:
            print("Buy order Matched or Cancelled")
            print("Updating Trade Log")
            update_trade_log(pair)
            print("------------------------------")
        else:
            print('Buy Order is not match, Resending...')
            pending_buy_id = get_pending_buy()[0]['id']
            order_id = pending_buy_id
            cancel_order(order_id)  
    else:
        pending_buy_id = get_pending_buy()[0]['id']
        print("Pending BUY Order Found")
        print('Waiting For BUY Order To be filled')
        print("------------------------------")
        time.sleep(10)
        print("Canceling pending Order")
        order_id = pending_buy_id
        cancel_order(order_id)
        time.sleep(2)
        pending_buy = get_pending_buy()

        if pending_buy == []:
            print('Buy Order Matched or Cancelled')
        else:
            print('Buy Order is not Matched or Cancelled, Retrying')
    print("------------------------------")

def sell_execute():
    pending_sell = get_pending_sell()

    if pending_sell == []:
        print('Selling {} Size = {}'.format(asset_name, sell_size))
        create_sell_order()
        time.sleep(2)
        pending_sell = get_pending_sell()

        if pending_sell != []:
            pending_sell_id = get_pending_sell()[0]['id']
            print('Sell Order Created Success, Order ID: {}'.format(pending_sell_id))
            print('Waiting For Sell Order To be filled')
            time.sleep(10)
            pending_sell = get_pending_sell()

        if pending_sell == []:
            print("Sell order Matched or Cancelled")
            print("Updating Trade Log")
            update_trade_log(pair)
        else:
            print('Sell Order is not match, Resending...')
            pending_sell_id = get_pending_sell()[0]['id']
            order_id = pending_sell_id
            cancel_order(order_id)

    else:
        pending_sell_id = get_pending_sell()[0]['id']
        print("Pending SELL Order Found")
        print('Waiting For SELL Order To be filled')
        time.sleep(10)
        print("Canceling pending Order")
        order_id = pending_sell_id
        cancel_order(order_id)
        time.sleep(1)
        pending_sell = get_pending_sell()

        if pending_sell == []:
            print('Sell Order Matched or Cancelled')
        else:
            print('Sell Order is not Matched or Cancelled, Retrying')
    print("------------------------------")

def get_last_trade_price(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = 1),
                            columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    last_trade_price = trade_history['price']
    
    return float(last_trade_price)

# Database Function Part

def checkDB():
    try:
        tradinglog = pd.read_csv(tradelog_file)
        print('DataBase Exist Loading DataBase....')
    except:
        tradinglog = pd.DataFrame(columns=['id', 'timestamp', 'time', 'pair', 'side', 'price', 'qty', 'fee','bot_name', 'subaccount', 'cost'])
        tradinglog.to_csv(tradelog_file, index=False)
        print("Database Created")
        
        
    return tradinglog

# Database Setup
print('Checking Database file.....')
tradinglog = checkDB()

def get_trade_history(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = trading_call_back),
                              columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'fee'])
    
    cost=[]
    for i in range(len(trade_history)):
        fee = trade_history['fee'].iloc[i]['cost'] if trade_history['fee'].iloc[i]['currency'] == 'USD' else trade_history['fee'].iloc[i]['cost'] * trade_history['price'].iloc[i]
        cost.append(fee)  # ใน fee เอาแค่ cost
    
    trade_history['fee'] = cost
    
    return trade_history

def get_last_id(pair):
    pair = pair
    trade_history = get_trade_history(pair)
    last_trade_id = (trade_history.iloc[:trading_call_back]['id'])
    
    return last_trade_id

def update_trade_log(pair):
    pair = pair
    tradinglog = pd.read_csv(tradelog_file)
    last_trade_id = get_last_id(pair)
    trade_history = get_trade_history(pair)
    
    for i in last_trade_id:
        tradinglog = pd.read_csv(tradelog_file)
        trade_history = get_trade_history(pair)
    
        if int(i) not in tradinglog.values:
            print("New Trade Founded")
            last_trade = trade_history.loc[trade_history['id'] == i]
            list_last_trade = last_trade.values.tolist()[0]

            # แปลงวันที่ใน record
            d = datetime.strptime(list_last_trade[2], "%Y-%m-%dT%H:%M:%S.%fZ")
            d = pytz.timezone('Etc/GMT+7').localize(d)
            d = d.astimezone(pytz.utc)
            Date = d.strftime("%Y-%m-%d")
            Time = d.strftime("%H:%M:%S")
            time_serie = (d.weekday()*1440)+(d.hour*60)+d.minute

            cost = float(list_last_trade[5] * list_last_trade[6])

            # edit & append ข้อมูลก่อน add เข้า database
            list_last_trade[1] = Date
            list_last_trade[2] = Time
            list_last_trade.append(account_name)
            list_last_trade.append(subaccount)
            list_last_trade.append(cost)

            ## list_last_trade.append(cost)

            with open(tradelog_file, "a+", newline='') as fp:
                wr = csv.writer(fp, dialect='excel')
                wr.writerow(list_last_trade)
            print('Recording Trade ID : {}'.format(i))
        else:
            print('Trade Already record')


# Status Report
while True:
    try:
        # Trade history Checking
        print('Validating Trading History')
        update_trade_log(pair)
        print("------------------------------")

        wallet = get_wallet_details()
        cash = get_cash()
        Time = get_time()

        print('Time : {}'.format(Time))
        print('Account : {}'.format(account_name))
        print('Your Remaining Balance : {}'.format(cash))
        print('Checking Your Asset')

        total_asset = 0

        for item in wallet:
            asset_value = round(float(item['usdValue']),2)
            total_asset += asset_value
            
        print('Your Total Asset Value is : {}'.format(total_asset))
        print("------------------------------")

        # Checking Initial Balance Loop
        while len(wallet) < len(token_name_lst) + 1:

            print('Entering Initial Loop')
            print("------------------------------")
            
            wallet = get_wallet_details()
            asset_in_wallet = [item['coin'] for item in wallet]
            print("Wallet Asset < Setting")

            for asset_name in token_fix_value:
                if asset_name not in asset_in_wallet:
                    print('{} is missing'.format(asset_name))
                    print('Checking {} Buy Condition ......'.format(format(asset_name)))

                    # Get price params
                    pair = pair_dict[asset_name]
                    price = get_price()
                    ask_price = get_ask_price()
                    bid_price = get_bid_price()

                    # Innitial asset BUY params
                    pair = pair_dict[asset_name]
                    bid_price = get_bid_price()
                    min_size = get_minimum_size()
                    step_price = get_step_price()
                    min_trade_value = get_min_trade_value()
                    cash = get_cash()
                    pending_buy = get_pending_buy()

                    # Create BUY params
                    initial_diff = token_fix_value[asset_name]
                    buy_size = initial_diff / price
                    buy_price = bid_price

                    if cash > min_trade_value and buy_size > min_size:
                        buy_execute()
                    else:
                        print("Not Enough Balance to buy {}".format(asset_name))
                        print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                        print("------------------------------")
                else:
                    print('{} is Already in Wallet'.format(asset_name))
                    print("------------------------------")
                    time.sleep(1)      
        
        # Rebalancing Loop
        for t in time_sequence:
            cash = get_cash()
            Time = get_time()

            print("------------------------------")
            print('Time : {}'.format(Time))
            print('Checking Your Asset')
            print('Your Total Asset Value is : {}'.format(total_asset))
            

            if cash > 0 and len(wallet) == len(token_name_lst) + 1:
                print('Entering Rebalance Loop')
                print("------------------------------")
                wallet = get_wallet_details()

                for item in wallet:
                    asset_name = item['coin']
                    
                    if asset_name != 'USD':
                    
                        asset_value = round(float(item['usdValue']),2)
                        fixed_value = token_fix_value[asset_name]
                        diff = abs(fixed_value - asset_value)
                        asset_amt = float(item['total'])
                        pair = pair_dict[asset_name]
                        price = get_price()
                        last_trade_price = get_last_trade_price(pair)
                    
                        if asset_name in token_fix_value.keys():
                            # check coin price and value
                            print('{} Price is {}'.format(asset_name, price))
                            print('{} Value is {}'.format(asset_name, asset_value))
                            
                            # Check rebalance BUY trigger
                            if asset_value < fixed_value - min_reb_size and price < last_trade_price:
                                print("Current {} Value less than fix value : Rebalancing -- Buy".format(asset_name))
                                        
                                # Create trading params
                                price = get_price()
                                bid_price = get_bid_price()
                                min_size = get_minimum_size()
                                step_price = get_step_price()
                                min_trade_value = get_min_trade_value()
                                cash = get_cash()
                                pending_buy = get_pending_buy()
                                
                                # Create BUY params
                                buy_size = diff / price
                                buy_price = bid_price


                                # BUY order execution
                                if cash > min_trade_value and buy_size > min_size:
                                   buy_execute()
                                else:
                                    print("Not Enough Balance to buy {}".format(asset_name))
                                    print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                                    print("------------------------------")
                                    
                            # Check rebalance SELL trigger        
                            elif asset_value > fixed_value + min_reb_size and price > last_trade_price:
                                print("Current {} Value more than fix value : Rebalancing -- Sell".format(asset_name))
                                
                                # Create trading params
                                bid_price = get_bid_price()
                                ask_price = get_ask_price()
                                min_size = get_minimum_size()
                                step_price = get_step_price()
                                min_trade_value = get_min_trade_value()
                                pending_sell = get_pending_sell()
                                        
                                # Create SELL params
                                sell_size = diff / price
                                sell_price = ask_price
                                
                                # SELL order execution
                                if diff > min_trade_value and sell_size > min_size:
                                    sell_execute()
                                else:
                                    print("Not Enough Balance to sell {}".format(asset_name))
                                    print('You have {} {} // Minimum Trade Value is {}'.format(asset_name, asset_value, min_trade_value))
                                    print("------------------------------")
                                
                            else:
                                print("Current {} Value is not reach fix value yet : Waiting".format(asset_name))
                                print("------------------------------")
                                time.sleep(5)
        
        # Rebalancing Time Sequence
            print('Current Time Sequence is : {}'.format(t))
            time.sleep(t * time_multiplier)

    except Exception as e:
        print('Error : {}'.format(str(e)))
        time.sleep(10)                    