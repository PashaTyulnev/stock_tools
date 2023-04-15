import plotly.express as px
import helperFunctions
import plotly.graph_objects as go
import glob


def testMacdStrategy(csvPath, extendedStrategy=True, takeProfitLong=1.2,
                     stopLossLong=0.95,
                     takeProfitShort=1.1,
                     stopLossShort=0.97,
                     graph=False,
                     col = 'close'):
    # Gets data from CSV and reformat columns names
    stockDataFrame = helperFunctions.readMetaTraderCsv(csvPath)

    # EMA 12 Days
    stockDataFrame['ema12'] = stockDataFrame[col].ewm(span=12, adjust=False).mean()

    # EMA 26 Days
    stockDataFrame['ema26'] = stockDataFrame[col].ewm(span=26, adjust=False).mean()

    # stockDataFrame['ema26vol'] = stockDataFrame['tickvol'].ewm(span=200, adjust=False).mean()

    stockDataFrame['ema200'] = stockDataFrame[col].ewm(span=200, adjust=False).mean()

    # MACD LINE
    stockDataFrame['macd'] = stockDataFrame['ema26'] - stockDataFrame['ema12']

    # SIGNAL LINE
    stockDataFrame['signal'] = stockDataFrame['macd'].ewm(span=9, adjust=False).mean()

    crossingDatesSell = helperFunctions.getCrossingPoints(stockDataFrame['macd'], stockDataFrame['signal'],
                                                          stockDataFrame['ema200'],stockDataFrame[col], 'sell', extendedStrategy)
    crossingDatesBuy = helperFunctions.getCrossingPoints(stockDataFrame['macd'], stockDataFrame['signal'],
                                                         stockDataFrame['ema200'], stockDataFrame[col], 'buy', extendedStrategy)

    # Define Sell Dates
    sellDates = stockDataFrame.loc[crossingDatesSell]

    # Define Buy Dates
    buyDates = stockDataFrame.loc[crossingDatesBuy]

    # Simulate trade strategy
    helperFunctions.simulateTrades(
        stockDataFrame,
        buyDates,
        sellDates,
        path=csvPath,
        spentForPositionPercent=0.1,
        takeProfitLong=takeProfitLong,
        stopLossLong=stopLossLong,
        takeProfitShort=takeProfitShort,
        stopLossShort=stopLossShort,
        col=col
    )

    # DRAW GRAPHS
    if graph:
        fig = px.line(x=stockDataFrame.date, y=stockDataFrame[col], title=csvPath)
        fig.add_scatter(x=stockDataFrame.date, y=stockDataFrame.signal, name="Signal")
        fig.add_scatter(x=stockDataFrame.date, y=stockDataFrame.macd, name="MCD")
        fig.add_scatter(x=stockDataFrame.date, y=stockDataFrame.ema200, name="EMA200")
        # fig.add_scatter(x=stockDataFrame.date, y=stockDataFrame.volema, name="vol")

        fig.add_trace(go.Scatter(
            x=sellDates.date,
            y=sellDates[col],
            marker=dict(color="red", size=12),
            mode="markers",
            name="SELL",
        ))

        fig.add_trace(go.Scatter(
            x=buyDates.date,
            y=buyDates[col],
            marker=dict(color="green", size=12),
            mode="markers",
            name="BUY",
        ))

        fig.update_layout(hovermode="x unified")
        # fig.add_scatter(x=stockTimePeriod.date,y=ema3)
        fig.show()


# Go trough all csvs in directory
# for file in glob.glob("data\stocks\*.csv"):
# # stoppedAt = False
# # for file in glob.glob("data\stocks\*.csv"):
# #     if file == "data\stocks\SPGM1d.csv":
# #         stoppedAt = True
# #
# #     if stoppedAt:
#     testMacdStrategy(file,
#                      takeProfitLong=1.1,
#                      stopLossLong=0.95,
#                      takeProfitShort=1.1,
#                      stopLossShort=0.98,
#                      graph=False)

file = "data/stocks/ENOB1d.csv"
testMacdStrategy(file, takeProfitLong=1.1,
                 stopLossLong=0.95,
                 takeProfitShort=1.1,
                 stopLossShort=0.98,
                 graph=True,
                 col='close',
                 extendedStrategy=True
                 )
