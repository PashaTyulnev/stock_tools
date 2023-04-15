import yfinance as yf
from pyfinviz.screener import Screener

page = 1000

screener = Screener(pages=[x for x in range(1, page)])

list_ticker = []
for i in range(0, page):
    if i == 1:
        pass
    else:
        for j in range(len(screener.data_frames[i])):

            tickerName = screener.data_frames[i].Ticker[j]
            print("DOWNLOADING: " + screener.data_frames[i].Ticker[j])
            data = yf.download(tickerName, period="500d", interval="1d")

            size = data.size

            # If ticket not exists don't save
            if size > 0:
                data.to_csv('data/stocks/' + tickerName + '1d.csv', index=True)


