# Importing the libraries

import math
import nsepy
import numpy
import pandas as pd
import sklearn
import importlib
import seaborn as sns
import matplotlib.pyplot as plt

from datetime import date
from scipy.stats import norm
from nsepy import get_history
from matplotlib.pyplot import figure

# Declaring neccessary global variables

global nifty500
global numberofsamples
global mean
global latest
global standard_deviation
global terminals
global confidence_intervals

# Determine Normal Distribution of Index

def normal_distribution_of_pe_ratio(symbol) :

    # Referencing global variables for using them in local scope

    global nifty500
    global numberofsamples
    global mean
    global latest
    global standard_deviation
    global terminals
    global confidence_intervals    

    # Downloading the most recent data from NSE

    print("")
    print('Wait while we download data starting from 2000 from NSE server...\n')
    nifty500 = nsepy.get_index_pe_history(symbol, date(2000, 1, 1), date.today())
    
    print("PE Based SIP Model Thesis : ")
    print("")
    print("1. Continue monthly SIP of Rs. 10,000 when NIFTY 500 PE < R2")
    print("2. Sell entire holdings when NIFTY 500 PE > R2")
    print("3. Buy stock back with all available cash as soon as NIFTY 500 PE < R2")
    print("")

    # Calculating the most critical data
    
    numberofsamples = len(nifty500)
    mean = nifty500['P/E'].mean()
    latest = nifty500['P/E'].iloc[-1]
    standard_deviation = nifty500['P/E'].std()
    terminals = numpy.array([nifty500['P/E'].min(), nifty500['P/E'].max()])
    
    confidence_intervals = numpy.array([mean - 3*standard_deviation, mean - 2*standard_deviation, mean - standard_deviation, mean + standard_deviation, mean + 2*standard_deviation, mean + 3*standard_deviation])

# PE Based SIP Model

def pe_based_sip_model (company) :
    
    # Referencing global variables for using them in local scope

    global nifty500
    global numberofsamples
    global mean
    global latest
    global standard_deviation
    global terminals
    global confidence_intervals

    # Downloading the most recent data from NSE
    
    stock = get_history(symbol = company, start = date(2000, 1, 1), end = date.today())

    # Declaring local variables

    row_num = 0 # Row Iterator
    
    current_profit = 0.00 # Current Profit
    cash_available = 0.00 # Initial balance
    total_num_of_stocks = 0 # Number of stocks
    total_invested_amount = 0.00 # Initial Invested Amount
    current_portfolio_value = 0.00 # Current Portfolio Value
    
    ledger = pd.DataFrame(columns = ['Type', 'Symbol', 'Price', 'Unit', 'Cash Available'])
    results = pd.DataFrame(columns = ['Total Investment', 'Cash in Hand', 'Current Portfolio Value', 'Net Profit'])
    
    while row_num < len(stock):
    
        # Add Rs. 10,000 Every Month and update cash available
    
        total_invested_amount += 10000.00
        
        if (row_num == 0) :
            
            cash_available = total_invested_amount
            
        else :
    
            cash_available = ledger['Cash Available'].iloc[-1] + 10000.00

        # Find current stock price
        
        stock_price = stock['Close'].iloc[row_num]

        # Buy stocks with available cash only if Nifty 500 PE is less than R2
        
        if (nifty500['P/E'].iloc[row_num] < confidence_intervals[4]) :
            
            # Buy stocks with available cash
            
            num_of_new_stocks = int (cash_available / stock_price)
            total_num_of_stocks += num_of_new_stocks
            
            # Update available cash
            
            cash_available -= (num_of_new_stocks * stock_price)
        
            # Add transaction in ledger and increment counter
            
            ledger = ledger.append(
                
                {
                 'Type' : 'Buy',
                 'Symbol' : stock['Symbol'].iloc[row_num],
                 'Price' : stock['Close'].iloc[row_num],
                 'Unit' : num_of_new_stocks,
                 'Cash Available' : cash_available
                },
                
                ignore_index = True)
        
        # Sell stocks when Nifty 500 PE is greater than R2
        
        elif ((nifty500['P/E'].iloc[row_num] > confidence_intervals[4])) :
            
            # Checking if I currently have a profit  
            
            current_profit = (total_num_of_stocks * stock_price) + ledger['Cash Available'].iloc[-1] + 10000.00 - total_invested_amount
            
            # Checking If I have profit
              
            if ((current_profit) > 0) :
              
                # I will sell all my holdings
              
                cash_available += (total_num_of_stocks * stock_price)
        
                # Add transaction in ledger and increment counter
                
                ledger = ledger.append(
                    
                    {
                     'Type' : 'Sell',
                     'Symbol' : stock['Symbol'].iloc[row_num],
                     'Price' : stock['Close'].iloc[row_num],
                     'Unit' : total_num_of_stocks,
                     'Cash Available' : cash_available
                    },
                    
                    ignore_index = True)
                
                # Reset total holdings
                
                total_num_of_stocks = 0.00
        
        row_num += 30
        
    # Return Calculation
    
    current_portfolio_value = (ledger['Unit'].iloc[-1] * stock['Close'].iloc[-1]) + ledger['Cash Available'].iloc[-1]
    
    # Storing Final Results To Print In Excel Later
    
    results = results.append(
            
            {
             'Total Investment' : total_invested_amount,
             'Cash in Hand' : cash_available,
             'Current Portfolio Value' : current_portfolio_value,
             'Net Profit' : (current_portfolio_value - total_invested_amount)
            },
            
            ignore_index = True)
    
    print("Result of PE Based SIP Model on %s :" %company)
    print("")
    
    print("Net profit = %.2f Lacs" % ((current_portfolio_value - total_invested_amount)/100000))
    print("Total investment = %.2f Lacs" % ((total_invested_amount)/100000))
    print("Current portfolio value = %.2f Lacs" % ((current_portfolio_value)//100000))
    print("Current portfolio value = %.2f times investment" % (current_portfolio_value / total_invested_amount))
    
    print("")
    print("Saving Everything Important Into an Excel File")
    
    # Print Stock History and Transaction Ledger
    
    writer = pd.ExcelWriter(company + ' (PE Based).xlsx', engine = 'xlsxwriter') # Create a Pandas Excel Writer using XLSXWriter as the engine.
    stock.to_excel(writer, sheet_name = 'HISTORY')
    ledger.to_excel(writer, sheet_name = 'LEDGER')
    results.to_excel(writer, sheet_name = 'RESULT')
    writer.save() # Close the Pandas Excel writer and output the Excel file.
    
def buy_and_hold (company) :

    # Downloading the most recent data from NSE

    stock = get_history(symbol = company, start = date(2000, 1, 1), end = date.today())

    # Declaring local variables
    
    row_num = 0 # Row Iterator
    
    current_profit = 0.00 # Current Profit
    cash_available = 0.00 # Initial balance
    total_num_of_stocks = 0 # Number of stocks
    total_invested_amount = 0.00 # Initial Invested Amount
    current_portfolio_value = 0.00 # Current Portfolio Value
    
    ledger = pd.DataFrame(columns = ['Type', 'Symbol', 'Price', 'Unit', 'Cash Available'])
    results = pd.DataFrame(columns = ['Total Investment', 'Cash in Hand', 'Current Portfolio Value', 'Net Profit'])
    
    while row_num < len(stock):
    
        # Add Rs. 10,000 Every Month and update cash available
    
        total_invested_amount += 10000.00
        
        if (row_num == 0) :
            
            cash_available = total_invested_amount
            
        else :
    
            cash_available = ledger['Cash Available'].iloc[-1] + 10000.00

        # Find current stock price
        
        stock_price = stock['Close'].iloc[row_num]    
        
        # Buy stocks worth Rs. 10,000 at day closing price
        
        num_of_new_stocks = int (cash_available / stock_price)
        total_num_of_stocks += num_of_new_stocks
        
        # Update cash available
        
        cash_available -= (stock_price * num_of_new_stocks)
        
        # Add transaction in ledger and increment counter
        
        ledger = ledger.append(
            
            {
             'Type' : 'Buy',
             'Symbol' : stock['Symbol'].iloc[row_num],
             'Price' : stock['Close'].iloc[row_num],
             'Unit' : num_of_new_stocks,
             'Cash Available' : cash_available
            },
            
            ignore_index = True)
        
        row_num += 30
    
    # Return Calculation
    
    for i in range (0, len(ledger) - 1):
        
        current_portfolio_value += (ledger['Unit'].iloc[i] * stock['Close'].iloc[-1])
    
    current_portfolio_value += ledger['Cash Available'].iloc[-1]
    
    # Storing Final Results To Print In Excel Later
    
    results = results.append(
            
            {
             'Total Investment' : total_invested_amount,
             'Cash in Hand' : cash_available,
             'Current Portfolio Value' : current_portfolio_value,
             'Net Profit' : (current_portfolio_value - total_invested_amount)
            },
            
            ignore_index = True)
    
    print("Result of Plain SIP Model on %s :" %company)
    print("")
    
    print("Net profit = %.2f Lacs" % ((current_portfolio_value - total_invested_amount)/100000))
    print("Total investment = %.2f Lacs" % ((total_invested_amount)/100000))
    print("Current portfolio value = %.2f Lacs" % ((current_portfolio_value)//100000))
    print("Current portfolio value = %.2f times investment" % (current_portfolio_value / total_invested_amount))

    print("")
    
    # Print Stock History and Transaction Ledger
    
    writer = pd.ExcelWriter(company + ' (Buy and Hold).xlsx', engine = 'xlsxwriter') # Create a Pandas Excel Writer using XLSXWriter as the engine.
    stock.to_excel(writer, sheet_name = 'HISTORY')
    ledger.to_excel(writer, sheet_name = 'LEDGER')
    results.to_excel(writer, sheet_name = 'RESULT')
    writer.save() # Close the Pandas Excel writer and output the Excel file.
    

# Test with stock

normal_distribution_of_pe_ratio('NIFTY 500')
# buy_and_hold('RELIANCE')
pe_based_sip_model('RELIANCE')