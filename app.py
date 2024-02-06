from matplotlib import pyplot as plt, ticker
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import datetime
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

st.set_page_config(page_title="AlgoTrade", page_icon="📈",
                   layout="wide", initial_sidebar_state="auto", menu_items=None)

st.title('Dual Moving Average Crossover Strategy')

tkr = st.sidebar.text_input("Please enter a ticker symbol","AAPL").upper()

sd = st.sidebar.date_input(
     "Enter a start date",
     datetime.date(2018, 7, 6))
ed = st.sidebar.date_input(
     "Enter an end date",
     datetime.date(2021, 7, 6))

sma_days = st.sidebar.number_input("Please enter a window for shorter average(days)",30)
lma_days = st.sidebar.number_input("Please enter a window for longer average",100)

ticker = yf.Ticker(tkr)

hist = ticker.history(start=sd, end=ed)
hist.reset_index(inplace=True)
#hist = hist.rename(columns={'Close': 'Close'})
st.markdown('Data')
st.write(hist)

start_date = pd.to_datetime(sd)
end_date = pd.to_datetime(ed)

if(end_date <= start_date):
    st.error('Invalid Date Input!')
    st.stop()

s_date = sd.strftime('%Y/%m/%d')
e_date = ed.strftime('%Y/%m/%d')
date_str = s_date + '-' + e_date

fig = plt.figure(figsize=(12.5, 4.5))
plt.plot(hist['Close'])
plt.title('Adj. Close Price History')
plt.xlabel(date_str)
plt.ylabel('Adj. Close Price USD ($)')
plt.legend(loc='upper left')
st.markdown('Adjusted Close Price history')
st.pyplot(fig)

sma = pd.DataFrame()
sma['Close'] = hist['Close'].rolling(window = sma_days).mean()

lma = pd.DataFrame()
lma['Close'] = hist['Close'].rolling(window = lma_days).mean()


fig2 = plt.figure(figsize=(12.5, 4.5))
plt.plot(hist['Close'], label = tkr)
plt.plot(sma['Close'], label = 'ShortAvg')
plt.plot(lma['Close'], label = 'LongAvg')
plt.title('Adj. Close Price History')
plt.xlabel(date_str)
plt.ylabel('Adj. Close Price USD ($)')
plt.legend(loc='upper left')
#st.pyplot(fig2)


data = pd.DataFrame()
data['tkr'] = hist['Close']
data['sma'] = sma['Close']
data['lma'] = lma['Close']
st.markdown('Moving Averages for ' + tkr + ' Data')
st.write(data)

def buyNsell(data):
    sigPriceBuy = []
    sigPriceSell = []
    flag = -1

    for i in range(len(data)):
        if(data['sma'][i] > data['lma'][i]):
            if flag != 1:
                sigPriceBuy.append(data['tkr'][i])
                sigPriceSell.append(np.nan)
                flag = 1
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)
        elif (data['sma'][i] < data['lma'][i]):
            if flag != 0:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(data['tkr'][i])
                flag = 0
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)
        else:
            sigPriceBuy.append(np.nan)
            sigPriceSell.append(np.nan)

    return (sigPriceBuy, sigPriceSell)

buyNsell = buyNsell(data)
data['Buy Signal Price'] = buyNsell[0]
data['Sell Signal Price'] = buyNsell[1]


fig3 = plt.figure(figsize=(12, 4.6))
plt.plot(data['tkr'], label = tkr, alpha = 0.35)
plt.plot(data['sma'], label = 'ShortAvg', alpha = 0.35)
plt.plot(data['lma'], label = 'LongAvg', alpha = 0.35)
plt.scatter(data.index, data['Buy Signal Price'], label = 'Buy', marker = '^', color = 'green')
plt.scatter(data.index, data['Sell Signal Price'], label = 'Sell', marker = 'v', color = 'red')
plt.title('Adj. Close Price History Buy and Sell Signals')
plt.xlabel(date_str)
plt.ylabel('Adj. Close Price USD ($)')
plt.legend(loc = 'upper left')
st.markdown('Buy and Sell Signals')
st.pyplot(fig3)



class DualMACrossover(Strategy):

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(SMA, close, sma_days)
        self.sma2 = self.I(SMA, close, lma_days)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

bt = Backtest(hist, DualMACrossover,
              exclusive_orders=True)

btdf = bt.run().head(27)
st.write('Viability of the Trading Strategy: ')
st.table(btdf)
