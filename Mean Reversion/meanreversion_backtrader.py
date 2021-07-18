# Import Libraries

import math
import numpy
import nsepy
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers

from datetime import date
from scipy.stats import norm
from backtrader.feeds import GenericCSVData

# Downloading the data  

print('Downloading Data From National Stock Exchange (NSE)')
nifty500 = nsepy.get_history('NIFTY 500', date(2016, 1, 1), date.today(), index = True)
peratio = nsepy.get_index_pe_history('NIFTY 500', date(2016, 1, 1), date.today())
nifty500['PE'] = peratio['P/E']
nifty500.to_csv('NIFTY 500.csv')

# Calculating the most critical data

numberofsamples = len(nifty500)
mean = nifty500['PE'].mean()
latest = nifty500['PE'].iloc[-1]
standard_deviation = nifty500['PE'].std()
terminals = numpy.array([nifty500['PE'].min(), nifty500['PE'].max()])
confidence_intervals = numpy.array([mean - 3*standard_deviation, mean - 2*standard_deviation, mean - standard_deviation, mean + standard_deviation, mean + 2*standard_deviation, mean + 3*standard_deviation])

# Function to calculate confidence intervals

def statistical_confidence(data, num, lowerbound, upperbound): 
      
    occurance = 0 
    
    for i in range (0, num-1):
        
        if (data[i] > lowerbound and data[i] < upperbound):
            occurance += 1
        else :
            continue
              
    return "{:.2f} %".format(((occurance/num)*100))

# Load the data in backtrader and run the strategy

"""
By default downloaded data only has datetime, Open, High, Low, Close, Volume and Turnover.
As we are adding one more parameter "PE", we can no longer use GenericCSVData reader provided
by backtrader library without modification to base class.

"""

# Define the new parameter

class GenericCSV_PE(GenericCSVData):
    
    lines = ('pe',) # Add a 'PE' line to the inherited ones from the base class
    params = (('pe', 8),) # Add the parameter to the parameters inherited from the base class


# Declare position of each column in csv file

data = GenericCSV_PE(dataname='NIFTY 500.csv', dtformat=('%Y-%m-%d'), datetime=0, high=1, low=2, open=3, close=4, volume=5, pe=7, openinterest=-1)

# Strategy : Buy and Hold

class BuyAndHold(bt.Strategy):
        
    params = dict(
        
        monthly_cash = 10000.0,  # amount of cash to buy every month
        when = bt.timer.SESSION_START, # when to buy
        timer = True,
        monthdays = [1], # on what day of the month to buy
        investment = 0
        
    )
    
    # Constructor for this class
    
    def __init__(self):
        
        self.add_timer(when = self.p.when, monthdays = self.p.monthdays,)
    
    # Logging function fot this strategy
    
    def log(self, txt, dt = None):
        
        dt = dt or self.data.datetime[0]
        print('%s, %s' % (dt.isoformat(), txt))
        
        if isinstance(dt, float):
            
            dt = bt.num2date(dt)
   
    # Start    
    
    def start(self):
        
        self.cash_start = self.broker.get_cash()
        self.val_start = 0

        # Add a timer which will be called on the 1st trading day of the month
        
        self.add_timer(
            
            bt.timer.SESSION_END,  # when it will be called
            monthdays = [1],  # called on the 1st day of the month
            monthcarry = True,  # called on the 2nd day if the 1st is holiday
            
        )

    # Add the influx of monthly cash to the broker account

    def notify_timer(self, timer, when, *args, **kwargs):
        
        self.broker.add_cash(self.p.monthly_cash)
        self.p.investment = self.p.investment + 10000
    
    # calculate the actual returns

    def stop(self):
        
        print('Final Portfolio Value of Buy and Hold : %.2f' % self.broker.getvalue())
    
# Running Buy and Hold Strategy

cerebro = bt.Cerebro()

cerebro.adddata(data) # Adding dataset created above to our universe before we can test our strategy on it
cerebro.addstrategy(BuyAndHold) # Adding our strategy created above
cerebro.run()

# PE Based Strategy : Buy when PE < L1 | Sell when PE > R1

class PEInvesting(bt.SignalStrategy):
    
    params = dict(
        
        monthly_cash = 10000.0,  # amount of cash to buy every month
        when = bt.timer.SESSION_START, # when to buy
        timer = True,
        monthdays = [1], # on what day of the month to buy
        investment = 0
        
    )
    
    # Constructor for this class
    
    def __init__(self):
        
        self.add_timer(when = self.p.when, monthdays = self.p.monthdays,)
        
        # Keep a reference to the "close" line in the data[0] dataseries
        
        self.dataclose = self.datas[0].close
        self.pe = self.datas[0].pe
    
    # Logging function fot this strategy
    
    def log(self, txt, dt=None):
        
        pass
     
    def start(self):
        
        self.cash_start = self.broker.get_cash()
        self.val_start = 0

        # Add a timer which will be called on the 1st trading day of the month
        
        self.add_timer(
            
            bt.timer.SESSION_END,  # when it will be called
            monthdays = [1],  # called on the 1st day of the month
            monthcarry = True,  # called on the 2nd day if the 1st is holiday
            
        )

    # Add the influx of monthly cash to the broker account

    def notify_timer(self, timer, when, *args, **kwargs):
        
        self.broker.add_cash(self.p.monthly_cash)
        self.p.investment = self.p.investment + 10000
     
    # Buying Decisions    
     
    def next(self):
            
        # Sell Points
        
        if self.pe[0] > confidence_intervals[4]:
            
            self.order_target_percent(target=0.80) # Retain 80% of Portfolio Value - Convert 20% To Cash
        
        elif self.pe[0] > confidence_intervals[3]:
            
            self.order_target_percent(target=0.80) # Retain 80% of Portfolio Value - Convert 20% To Cash

    # calculate the actual returns

    def stop(self):
        
        print('Final Portfolio Value of PE Based Strategy : %.2f' % self.broker.getvalue())
       
# Running Alternate Strategy

cerebro = bt.Cerebro()
cerebro.adddata(data) # Adding dataset created above to our universe before we can test our strategy on it
cerebro.addstrategy(PEInvesting) # Adding our strategy created above

cerebro.run()










