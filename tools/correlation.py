import glob
import pandas as pd
import helperFunctions
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
counter = 0

for file in glob.glob("data\stocks\*.csv"):

    stockDataFrame = helperFunctions.readMetaTraderCsv(file)
    symbol = file.replace('data\stocks\\', '')
    symbol = symbol.replace('1d.csv', '')

    if counter == 0:
        allTickers = pd.DataFrame()
        allTickers['symbol'] = symbol
        stockDataFrame['symbol'] = symbol
        allTickers = stockDataFrame[['date','close','symbol']]
        allTickers = allTickers.pivot('date', 'symbol', 'close').reset_index()
    else:
        allTickers[symbol] = stockDataFrame.close
    if counter > 10:
        break
    counter += 1


corr_df = allTickers.corr(method='pearson')
corr_df.head().reset_index()
corr_df=corr_df.dropna(how='all',axis='columns')
corr_df=corr_df.dropna(how='all',axis='rows')
corr_df=corr_df.round(decimals=2)


fig = px.imshow(corr_df,text_auto=True,color_continuous_scale= [
    [0, 'red'],
    [0.5, 'black'],
    [1, 'green'],
])
fig.update_xaxes(side="top")
fig.show()
