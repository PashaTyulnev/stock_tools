import csv
import pandas as pd
import os.path
import datetime as dt

def readMetaTraderCsv(csvPath):
    stockDataFrame = pd.read_csv(csvPath, sep=',')

    stockDataFrame = stockDataFrame.rename(columns={
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

    stockDataFrame.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

    return stockDataFrame
