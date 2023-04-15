import csv
import pandas as pd
import os.path
from datetime import datetime
import numpy as np

def readMetaTraderCsv(csvPath):
    stockDataFrame = pd.read_csv(csvPath, sep=',')

    if 'Time' in stockDataFrame.columns:
        stockDataFrame = stockDataFrame.rename(columns={
            'Time': 'time',
        })

    else:
        stockDataFrame['time'] = "00:00:00"

    stockDataFrame = stockDataFrame.rename(columns={
        'Date': 'Date',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    })

    stockDataFrame.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
    stockDataFrame['Date'] = stockDataFrame['Date'] + ' ' + stockDataFrame['time']
    return stockDataFrame


# When you want the intersection points of 2 graphs in same dataframe
# Extended is when you
# BUY at MACD Signal + 200 EMA UP
# SELL at MACD Signal + 200 EMA DOWN
def getCrossingPoints(graph1, graph2, ema200, actualStock, action="sell", extendedStrategy=True):
    previous1 = graph1.shift(1)
    previous2 = graph2.shift(1)
    previous_ema200 = ema200.shift(1)
    previous_ema200_2 = ema200.shift(2)
    previousStock = actualStock.shift(1)

    crossing = []
    ema_diffs = previous_ema200 - previous_ema200_2

    pd.set_option('display.max_rows', ema_diffs.shape[0] + 1)
    ema_diffs = ema_diffs.dropna(how='all', axis='rows')

    mean = ema_diffs.mean()

    if action == "sell":
        if extendedStrategy:
            crossing = (
                    ((graph1 <= graph2) & (previous1 >= previous2) & (graph1 > 0) & (previous_ema200 > ema200) & (
                            ema_diffs < -mean))
                    | ((ema_diffs.shift(1) > 0) & (ema_diffs < 0))
                    | ((actualStock <= ema200) & (previousStock >= previous_ema200))
            )

        else:
            crossing = ((graph1 <= graph2) & (previous1 >= previous2) & (graph1 > 0))

    elif action == "buy":
        if extendedStrategy:
            crossing = (((graph1 >= graph2) & (previous1 <= previous2) & (graph1 < 0) & (previous_ema200 < ema200) & (
                    ema_diffs > mean)) | ((ema_diffs.shift(1) < 0) & (ema_diffs > 0))
                        | ((actualStock >= ema200) & (previousStock <= previous_ema200))
                        )

        else:
            crossing = ((graph1 >= graph2) & (previous1 <= previous2) & (graph1 < 0))

    pd.set_option('display.max_rows', crossing.shape[0] + 1)

    return crossing


def simulateTrades(allTicks, buyMoments, sellMoments, path, spentForPositionPercent=0.1,
                   takeProfitLong=1.1,
                   stopLossLong=0.9,
                   takeProfitShort=1.1,
                   stopLossShort=0.9, col='close'):
    columns = ['price', 'spent']

    buyPositions = pd.DataFrame(columns=columns)
    sellPositions = pd.DataFrame(columns=columns)
    wholeAccount = 10000
    accountBegin = wholeAccount
    tradeCounter = 0
    profitableTradeCounter = 0

    # START SIMULATION OF TRADING BY CURRENT STRATEGY
    for index, row in allTicks.iterrows():

        # CURRENT PRICE OF STOCK
        currentPrice = row[col]

        # OPEN POSITION
        # IF BUY SIGNAL
        if index in buyMoments.index:
            openCost = spentForPositionPercent * wholeAccount
            newRow = pd.json_normalize({'price': currentPrice, 'spent': openCost})
            buyPositions = pd.concat([buyPositions, newRow])
            wholeAccount = wholeAccount - openCost
            tradeCounter = tradeCounter + 1

        # IF SELL SIGNAL
        if index in sellMoments.index:
            openCost = spentForPositionPercent * wholeAccount
            newRow = pd.json_normalize({'price': currentPrice, 'spent': openCost})
            sellPositions = pd.concat([sellPositions, newRow])
            wholeAccount = wholeAccount - openCost
            tradeCounter = tradeCounter + 1

        # CLOSE POSITION
        # IF WE HAVE SOME OPEN BUY POSITIONS
        for buyIndex, position in buyPositions.iterrows():
            positionGainPercent = currentPrice / position.price
            # CLOSE POSITION CONDITIONS
            if (positionGainPercent >= takeProfitLong) or (positionGainPercent <= stopLossLong):
                # CLOSE POSITION AT TAKE PROFIT OR STOP LOSS VALUE (LONG)
                spentForPosition = position.spent * positionGainPercent

                # FOR STATISTICS OUTPUT
                # IF 'WON'
                if positionGainPercent > 1:
                    profitableTradeCounter = profitableTradeCounter + 1

                # DELETE TRADE FROM DATAFRAME
                buyPositions = buyPositions[buyPositions.price != position.price]
                wholeAccount = wholeAccount + spentForPosition

        # IF WE HAVE SOME OPEN SELL POSITIONS
        for sellIndex, position in sellPositions.iterrows():
            positionGainPercent = currentPrice / position.price
            positionGainPercent = (1 - positionGainPercent) + 1

            # CLOSE POSITIONS IF STOP LOS OR TAKE PROFIT (SHORT)
            if (positionGainPercent >= takeProfitShort) or (positionGainPercent <= stopLossShort):
                spentForPosition = position.spent * positionGainPercent

                # FOR STATISTICS OUTPUT
                if positionGainPercent > 1:
                    profitableTradeCounter = profitableTradeCounter + 1

                # DELETE TRADE FROM DATAFRAME
                sellPositions = sellPositions[sellPositions.price != position.price]
                wholeAccount = wholeAccount + spentForPosition

    gain = ((wholeAccount / accountBegin) * 100) - 100
    if tradeCounter == 0:
        win_rate = 0
    else:
        win_rate = (profitableTradeCounter / tradeCounter) * 100
    latestBuy = buyMoments.tail(1).date.values
    try:
        latestBuy = latestBuy[0]
    except:
        latestBuy = 0
    latestSell = sellMoments.tail(1).date.values
    try:
        latestSell = latestSell[0]
    except:
        latestSell = 0

    today = datetime.today()

    diffSell = 999999
    diffBuy = 99999

    if latestBuy != 0:
        lastBuyDatetime = datetime.strptime(latestBuy, '%Y-%m-%d %H:%M:%S')
        diffBuy = today - lastBuyDatetime
        diffBuy = diffBuy.days
    if latestSell != 0:
        lastSellDatetime = datetime.strptime(latestSell, '%Y-%m-%d %H:%M:%S')
        diffSell = today - lastSellDatetime
        diffSell = diffSell.days

    if (diffSell < 5 or diffBuy < 5) and win_rate > 50:
        print("------------------")
        print("STOCK: " + str(path))
        print("ACCOUNT BEGIN: " + str(accountBegin))
        print("ACCOUNT END: " + str(wholeAccount))
        print("GAIN %: " + str(gain))
        print("TRADES: " + str(tradeCounter))
        print("PROFITABLE TRADES: " + str(profitableTradeCounter))
        print("WIN RATE % : " + str(win_rate))

        print("LATEST BUY SIGNAL : " + str(latestBuy))
        print("LATEST SELL SIGNAL : " + str(latestSell))

        print("TP-Long: " + str(takeProfitLong))
        print("SL-Long: " + str(stopLossLong))
        print("TP-Short: " + str(takeProfitShort))
        print("SL-Short: " + str(stopLossShort))

        createCsv('results_soon_action.csv',
                  [str(wholeAccount).replace('.', ','), str(gain).replace('.', ','), str(tradeCounter),
                   str(profitableTradeCounter), str(win_rate).replace('.', ','),
                   str(takeProfitLong), str(stopLossLong), str(takeProfitShort), str(stopLossShort), str(path),
                   str(latestBuy), str(latestSell)],
                  ['ACCOUNT END', 'GAIN %', 'TRADES AMOUNT', 'PROFITABLE TRADES', 'TRADE WIN-RATE', 'TP-Long',
                   'SL-Long',
                   'TP-Short', 'SL-Short', 'Stock', 'LatestBuy', 'LatestSell'])
    # data as array e.g. data = [x,y,z]


def createCsv(file_path, data, header):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(header)  # file doesn't exist yet, write a header

        writer.writerow(data)

def calculate_pivot_points(df):
    # Calculate pivot points
    pivot_points = pd.DataFrame(columns=['P', 'R1', 'S1', 'R2', 'S2', 'R3', 'S3'])
    pivot_points['P'] = (df['High'] + df['Low'] + df['Close']) / 3
    pivot_points['R1'] = (2 * pivot_points['P']) - df['Low']
    pivot_points['S1'] = (2 * pivot_points['P']) - df['High']
    pivot_points['R2'] = pivot_points['P'] + (df['High'] - df['Low'])
    pivot_points['S2'] = pivot_points['P'] - (df['High'] - df['Low'])
    pivot_points['R3'] = pivot_points['R1'] + (df['High'] - df['Low'])
    pivot_points['S3'] = pivot_points['S1'] - (df['High'] - df['Low'])
    return pivot_points


# Define function to calculate SuperTrend
def SuperTrend(df,  n, multiplier):
    # Calculate ATR
    df['H-L'] = abs(df['High'] - df['Low'])
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(n).mean()

    # Calculate SuperTrend
    pivot_points = calculate_pivot_points(df)

    df['Upper Basic'] = pivot_points['R1'] + (multiplier * df['ATR'])
    df['Lower Basic'] = pivot_points['S1'] - (multiplier * df['ATR'])
    df['Upper Band'] = None
    df['Lower Band'] = None
    for i in range(df.shape[0]):
        if i < n:
            df.loc[i, 'Upper Band'] = df.loc[i, 'Upper Basic']
            df.loc[i, 'Lower Band'] = df.loc[i, 'Lower Basic']
        else:
            if (df.loc[i - 1, 'Upper Band'] is not None) and (df.loc[i - 1, 'Lower Band'] is not None):
                df.loc[i, 'Upper Band'] = min(df.loc[i, 'Upper Basic'], df.loc[i - 1, 'Upper Band'])
                df.loc[i, 'Lower Band'] = max(df.loc[i, 'Lower Basic'], df.loc[i - 1, 'Lower Band'])
            else:
                df.loc[i, 'Upper Band'] = df.loc[i, 'Upper Basic']
                df.loc[i, 'Lower Band'] = df.loc[i, 'Lower Basic']

    df['SuperTrend'] = None
    for i in range(df.shape[0]):
        if i < n:
            pass
        else:
            if df.loc[i - 1, 'SuperTrend'] is not None:
                if df.loc[i - 1, 'SuperTrend'] == df.loc[i - 1, 'Upper Band']:
                    df.loc[i, 'SuperTrend'] = df.loc[i, 'Upper Band'] if df['Close'][i] > df['Upper Band'][i] else \
                    df.loc[i, 'Lower Band']
                else:
                    df.loc[i, 'SuperTrend'] = df.loc[i, 'Lower Band'] if df['Close'][i] < df['Lower Band'][i] else \
                    df.loc[i, 'Upper Band']

    return df