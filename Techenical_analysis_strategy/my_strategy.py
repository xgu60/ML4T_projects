import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import math


"""MLT: Utility code."""
# the following two functions are copied from util.py
def symbol_to_path(symbol, base_dir=os.path.join("..", "data")):
    """Return CSV file path given ticker symbol."""
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))


def get_data(symbols, dates, addSPX=True):
    """Read stock data (adjusted close) for given symbols from CSV files."""
    df = pd.DataFrame(index=dates)
    if addSPX and '$SPX' not in symbols:  # add SPX for reference, if absent
        symbols = ['$SPX'] + symbols

    for symbol in symbols:
        df_temp = pd.read_csv(symbol_to_path(symbol), index_col='Date',
                parse_dates=True, usecols=['Date', 'Adj Close'], na_values=['nan'])
        df_temp = df_temp.rename(columns={'Adj Close': symbol})
        df = df.join(df_temp)
        if symbol == '$SPX':  # drop dates SPX did not trade
            df = df.dropna(subset=["$SPX"])

    return df


# calculate bollinger bands of IBM and $SPX
def bollinger(sd = dt.datetime(2007,12,31), ed = dt.datetime(2009,12,31), \
    syms = ['IBM']):

    # Read in adjusted closing prices for given symbols, date range
    dates = pd.date_range(sd, ed)
    prices_all = get_data(syms, dates)  # automatically adds SPX
    prices = prices_all[syms]  # only portfolio symbols
    prices_SPX = prices_all[['$SPX']]  # only SPX, for comparison later
    
    
    # Calculate rollinger band of IBM
    ave = pd.rolling_mean(prices, window = 20)
    std = pd.rolling_std(prices, window = 20)
    prices['SMA'] = ave
    prices['upper'] = ave + 2 * std
    prices['lower'] = ave - 2 * std

    # Calculate rollinger band of SPX
    ave = pd.rolling_mean(prices_SPX, window = 20)
    std = pd.rolling_std(prices_SPX, window = 20)
    prices_SPX['SMA'] = ave
    prices_SPX['upper'] = ave + 2 * std
    prices_SPX['lower'] = ave - 2 * std 

    return prices, prices_SPX


# trader uses bollinger band information to trade
# return a dataframe of trades
# return lists of dates of long entry, short entry, and exit
def operations(bollinger):
    prices = bollinger['IBM']
    trades = prices * 0.0
    
    longStock = False
    shortStock = False
    lenter = []
    senter = []
    exit = []

    for i in range(1, len(bollinger.index)):
        if longStock:
            if bollinger.ix[i]['IBM'] >= bollinger.ix[i]['SMA']:
                longStock = False
                trades.ix[i] = -100
                exit.append(bollinger.index[i])
            else:
                continue

        elif shortStock:
            if bollinger.ix[i]['IBM'] <= bollinger.ix[i]['SMA']:
                shortStock = False
                trades.ix[i] = 100
                exit.append(bollinger.index[i])
            else:
                continue

        elif bollinger.ix[i-1]['IBM'] > bollinger.ix[i-1]['upper'] and bollinger.ix[i]['IBM'] < bollinger.ix[i]['upper']:
            shortStock = True
            trades.ix[i] = -100
            senter.append(bollinger.index[i])

        elif bollinger.ix[i-1]['IBM'] < bollinger.ix[i-1]['lower'] and bollinger.ix[i]['IBM'] > bollinger.ix[i]['lower']:
            longStock = True
            trades.ix[i] = 100
            lenter.append(bollinger.index[i])

    return trades, lenter, senter, exit

# This is my trading strategy 
# return a dataframe of trades, and csv file of orders
# return lists of dates of long entry, short entry, and exit
def myOperations(bollinger, bollinger_SPX):
    out = csv.writer(open("orders.csv", "w"), delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(['Date', 'Symbol', 'Order', 'Shares'])

    prices = bollinger['IBM']
    trades = prices * 0.0
    
   
    longStock = False
    shortStock = False
    current_price = 0.0
    lenter = []
    senter = []
    exit = []

    for i in range(1, len(bollinger.index)):
        if longStock:
            if bollinger.ix[i]['IBM'] >= bollinger.ix[i]['SMA'] or bollinger_SPX.ix[i]['$SPX'] >= bollinger_SPX.ix[i]['SMA']: 
                longStock = False
                trades.ix[i] = -100
		out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'SELL', '100'])
                exit.append(bollinger.index[i])
            
        elif shortStock:
            if bollinger.ix[i]['IBM'] <= bollinger.ix[i]['SMA'] or bollinger.ix[i]['IBM'] < current_price * 0.98: 
                shortStock = False
                trades.ix[i] = 100
                out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'BUY', '100'])
                exit.append(bollinger.index[i])
                    
        
        

        elif bollinger.ix[i-1]['IBM'] > bollinger.ix[i-1]['upper'] and  bollinger.ix[i]['IBM'] < bollinger.ix[i]['upper']:
            
            shortStock = True
            trades.ix[i] = -100
	    out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'SELL', '100'])
            senter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']
            

        elif bollinger.ix[i-1]['IBM'] < bollinger.ix[i-1]['lower'] and bollinger.ix[i]['IBM'] > bollinger.ix[i]['lower']:
            
            longStock = True
            trades.ix[i] = 100
            out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'BUY', '100'])
            lenter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']

        elif bollinger.ix[i]['IBM'] < bollinger.ix[i]['lower'] and bollinger_SPX.ix[i]['$SPX'] > bollinger_SPX.ix[i]['SMA'] :
            
            longStock = True
            trades.ix[i] = 100
            out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'BUY', '100'])
            lenter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']

        elif bollinger.ix[i]['IBM'] > bollinger.ix[i]['upper'] and bollinger_SPX.ix[i]['$SPX'] < bollinger_SPX.ix[i]['SMA']:
            
            shortStock = True
            trades.ix[i] = -100
            out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'SELL', '100'])
            senter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']

        elif bollinger_SPX.ix[i-1]['$SPX'] > bollinger_SPX.ix[i-1]['upper'] and  bollinger_SPX.ix[i]['$SPX'] < bollinger_SPX.ix[i]['upper']:
            if bollinger.ix[i]['IBM'] < bollinger.ix[i]['SMA']:
                continue
            shortStock = True
            trades.ix[i] = -100
            out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'SELL', '100'])
            senter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']
            

        elif bollinger_SPX.ix[i-1]['$SPX'] < bollinger_SPX.ix[i-1]['lower'] and bollinger_SPX.ix[i]['$SPX'] > bollinger_SPX.ix[i]['lower']:
            if bollinger.ix[i]['IBM'] > bollinger.ix[i]['SMA']:
                continue
            longStock = True
            trades.ix[i] = 100
            out.writerow([bollinger.index[i].strftime("%Y-%m-%d"),'IBM', 'BUY', '100'])
            lenter.append(bollinger.index[i])
            current_price = bollinger.ix[i]['IBM']

            
        


    return trades, lenter, senter, exit
        
# use dataframe of trade, and start value to calculate portvalues
def portfolioVals(prices, trades, sv):
    
    cash = trades * 0.0
    cash.ix[0] = sv
    cash = cash - prices * trades
    holdings = trades.copy(deep = True)
    for i in range(1, len(holdings.index)):
        holdings.ix[i] += holdings.ix[i-1]
        cash.ix[i] += cash.ix[i-1]
        
    return cash + prices * holdings

# calculate sharp ratio, cum return, standard deviation and averaged daily return of given portvals      
def analysis(portvals):
    dr = portvals/portvals.shift(1) - 1
    dr = dr.ix[1:]
    cr = portvals.ix[-1] / portvals[0] - 1
    adr = dr.mean()
    sddr = dr.std()
    sr = math.sqrt(252) * adr /sddr
    return sr, cr, sddr, adr

    


if __name__ == "__main__":
   
    start_date = dt.datetime(2009,12,31)
    end_date = dt.datetime(2011,12,31)
    symbols = ['IBM']
    
    # df1 is a datframe keeping bollinger band info of IBM
    # df2 is a datframe keeping bollinger band info of $SPX
    df1 , df2 = bollinger(start_date, end_date, symbols)
    

    # df3 is a dataframe keeping trades of IBM using my own strategy
    # le is a list for long entries dates
    # se is a list for short entries dates
    # exit is a list for exit dates
    df3, le, se, exit = myOperations(df1, df2)
    

    # df4 is a dataframe keeping trades of IBM using bollinger band strategy
    df4, le2, se2, exit2 = operations(df1)
       
    
    
    # calculate portvals of IBM using different strategies
    prices = df1['IBM']
    
    portvals = portfolioVals(prices, df3, 10000)
    portvals2 = portfolioVals(prices, df4, 10000)

    # only present results between 2007-02-28 to 2009-12-29
    sd = dt.datetime(2010,02,1)
    ed = dt.datetime(2011,12,30)
    portvals = portvals.ix[sd:ed]
    portvals2 = portvals2.ix[sd:ed]
    
    # normalization of portvals of IBM and $SPX
    norm_portvals = portvals / portvals.ix[0]
    norm_portvals2 = portvals2 / portvals2.ix[0]

    # plot chart for IBM bollinger bandS and different entries
    plt.plot(df1['IBM'], color = 'blue', label = 'IBM')
    plt.plot(df1['SMA'], color = 'orange', label = 'SMA')
    plt.plot(df1['upper'], color = 'cyan', label = 'Bollinger Bands')
    plt.plot(df1['lower'], color = 'cyan', label = '')
    plt.legend(loc = 2)
    for date in le:
        plt.axvline(x = date, color = 'green')
    for date in se:
        plt.axvline(x = date, color = 'red')
    for date in exit:
        plt.axvline(x = date, color = 'black')
    plt.show()
    
    # plot daily portfolio valus my strategy vs bollinger strategy
    plt.plot(norm_portvals, color = 'blue', label = 'my_strategy' )
    plt.plot(norm_portvals2, color = 'green', label = 'Bollinger_strategy')
    plt.title ('Daily portfolio value')
    plt.xlabel ('Date')
    plt.ylabel ('Normalized price')
    plt.legend(loc = 2)
    plt.show()


    # analyze the portfolio
    sr, cr, sddr, adr = analysis(portvals)
    sr2, cr2, sddr2, adr2 = analysis(portvals2)
    
    print 'Data Range:', sd, 'to', ed, ':', '\n'
    print 'Sharpe Ratio of Fund (my_strategy):', sr
    print 'Sharpe Ratio of Fund (Bollinger_strategy):', sr2, '\n'
    print 'Cumulative Return of Fund (my_strategy):', cr
    print 'Cumulative Return of Fund (Bollinger_strategy):', cr2, '\n'
    print 'Standard Deviation of Fund (my_strategy):' , sddr
    print 'Standard Deviation of Fund (Bollinger_strategy):', sddr2, '\n'
    print 'Average Daily Return of Fund (my_strategy):', adr
    print 'Average Daily Return of Fund (Bollinger_strategy):', adr2, '\n'
    print 'Final Portfolio Value (my_strategy):', portvals.ix[-1]
    print 'Final Portfolio Value (Bollinger_strategy):', portvals2.ix[-1], '\n'
    print 'Cumulative Return ratio', cr/cr2

