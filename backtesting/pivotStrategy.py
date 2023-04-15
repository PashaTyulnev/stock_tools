import plotly.express as px
import helperFunctions
import plotly.graph_objects as go
import glob
import pandas as pd
import numpy as np


def buildPivotPoints(csvPath):

    # Gets data from CSV and reformat columns names
    stockDataFrame = helperFunctions.readMetaTraderCsv(csvPath)

    # Calculate pivot point and SuperTrend
    stockDataFrame['Pivot Point'], stockDataFrame['S1'], stockDataFrame['S2'], stockDataFrame['R1'], stockDataFrame[
        'R2'] = helperFunctions.SuperTrend(stockDataFrame,7,3)
    stockDataFrame['SuperTrend'] = None

    stockDataFrame = helperFunctions.SuperTrend(stockDataFrame)

    fig = go.Figure(data=[go.Candlestick(x=stockDataFrame['Date'],
                                         open=stockDataFrame['Open'],
                                         high=stockDataFrame['High'],
                                         low=stockDataFrame['Low'],
                                         close=stockDataFrame['Close'])])
    fig.add_trace(go.Scatter(
        x=stockDataFrame['Date'],
        y=stockDataFrame['SuperTrend'],
        marker=dict(color="green", size=3),
        mode="markers",
        name="SELL",
    ))

    # fig.add_trace(go.Scatter(
    #     x=stockDataFrame['date'],
    #     y=stockDataFrame['ATR'],
    #     marker=dict(color="red", size=3),
    #     mode="markers",
    #     name="SELL",
    # ))
    fig.show()

    print(stockDataFrame)

# Print result
buildPivotPoints("data/stocks/TSLA1d.csv")

