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

def normal_distribution_of_pe_ratio(symbol, start_year) :

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
    print("Wait while we download data from NSE server...\n")
    nifty500 = nsepy.get_index_pe_history(symbol, date(start_year, 1, 1), date.today())

    # Calculating the most critical data
    
    numberofsamples = len(nifty500)
    mean = nifty500['P/E'].mean()
    latest = nifty500['P/E'].iloc[-1]
    standard_deviation = nifty500['P/E'].std()
    terminals = numpy.array([nifty500['P/E'].min(), nifty500['P/E'].max()])
    
    confidence_intervals = numpy.array([mean - 3*standard_deviation, mean - 2*standard_deviation, mean - standard_deviation, mean + standard_deviation, mean + 2*standard_deviation, mean + 3*standard_deviation])

# PE Based SIP Model

def pe_based_sip_model (company, installment, start_year) :
    
    # Referencing global variables for using them in local scope

    global nifty500
    global numberofsamples
    global mean
    global latest
    global standard_deviation
    global terminals
    global confidence_intervals

    # Downloading the most recent data from NSE
    
    stock = get_history(symbol = company, start = date(start_year, 1, 1), end = date.today())

    # Declaring local variables

    row_num = 0 # Row Iterator
    
    liquid_fund = 0.00 # Liquid Fund
    current_profit = 0.00 # Current Profit
    cash_available = 0.00 # Initial Balance
    total_num_of_stocks = 0 # Number of Stocks
    total_invested_amount = 0.00 # Initial Invested Amount
    current_portfolio_value = 0.00 # Current Portfolio Value
    
    ledger = pd.DataFrame(columns = ['Type', 'Symbol', 'Price', 'Unit', 'Cash Available', 'Liquid Fund'])
    results = pd.DataFrame(columns = ['Total Investment', 'Cash in Hand', 'Current Portfolio Value', 'Net Profit'])
    
    while row_num < len(stock):
    
        # Add monthly installment amount and update cash in hand
    
        total_invested_amount += installment
        
        if (row_num == 0) :
            
            cash_available = total_invested_amount
            
        else :
    
            cash_available = ledger['Cash Available'].iloc[-1] + installment
            liquid_fund += (liquid_fund * 0.06) / 12 # Add monthly interest at 6% Per annum

        # Find current stock price
        
        stock_price = stock['Close'].iloc[row_num]
        
        # BUY SIGNALS
        
        # Continue SIP if Nifty 500 PE < R2
        
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
                 'Cash Available' : cash_available,
                 'Liquid Fund' : liquid_fund
                },
                
                ignore_index = True)
            
            # EMERGENCY BUY : Use all liquid fund to buy stock when Nifty 500 PE < Mean
        
            if ((nifty500['P/E'].iloc[row_num] < mean) and (liquid_fund > stock_price)) :
            
                # Buy stocks with cash reserved in liquid fund
                    
                num_of_new_stocks = int (liquid_fund / stock_price)
                total_num_of_stocks += num_of_new_stocks
                    
                # Update liquid fund balance
                    
                liquid_fund -= (num_of_new_stocks * stock_price)
                
                # Add transaction in ledger and increment counter
                    
                ledger = ledger.append(
                        
                    {
                        'Type' : 'Emergency Buy',
                        'Symbol' : stock['Symbol'].iloc[row_num],
                        'Price' : stock['Close'].iloc[row_num],
                        'Unit' : num_of_new_stocks,
                        'Cash Available' : cash_available,
                        'Liquid Fund' : liquid_fund
                    },
                        
                    ignore_index = True)
        
        # SELL SIGNALS
        
        # EMERGENCY SELL : Sell all holdings on R2 crossover
        
        elif ((nifty500['P/E'].iloc[row_num] > confidence_intervals[4])) :
            
            # Checking if I have a profit on my current holdings
            
            current_profit = (total_num_of_stocks * stock_price) + ledger['Cash Available'].iloc[-1] + installment - total_invested_amount
            
            # Checking If I have profit
              
            if ((current_profit) > 0) :
              
                # I sell all my current holdings and transfer the proceeds into liquid fund
              
                no_of_stocks_to_sell = total_num_of_stocks
                liquid_fund += (no_of_stocks_to_sell * stock_price)
        
                # Add transaction in ledger and increment counter
                
                ledger = ledger.append(
                    
                    {
                     'Type' : 'Emergency Sell',
                     'Symbol' : stock['Symbol'].iloc[row_num],
                     'Price' : stock['Close'].iloc[row_num],
                     'Unit' : (-1 * no_of_stocks_to_sell),
                     'Cash Available' : cash_available,
                     'Liquid Fund' : liquid_fund
                    },
                    
                    ignore_index = True)
                
                # Reset total holdings
                
                total_num_of_stocks -= no_of_stocks_to_sell
        
        # EMERGENCY SELL : Sell 60% holdings on R1 Crossover 
        
        elif ((nifty500['P/E'].iloc[row_num] > confidence_intervals[3])) :
            
            # Checking if I have a profit on my current holdings
            
            current_profit = (total_num_of_stocks * stock_price) + ledger['Cash Available'].iloc[-1] + installment - total_invested_amount
            
            # Checking If I have profit
              
            if ((current_profit) > 0) :
              
                # I sell all my current holdings and transfer the proceeds into liquid fund
              
                no_of_stocks_to_sell = (0.60 * total_num_of_stocks)
                liquid_fund += (no_of_stocks_to_sell * stock_price)
        
                # Add transaction in ledger and increment counter
                
                ledger = ledger.append(
                    
                    {
                     'Type' : 'Precautionary Sell',
                     'Symbol' : stock['Symbol'].iloc[row_num],
                     'Price' : stock['Close'].iloc[row_num],
                     'Unit' : (-1 * no_of_stocks_to_sell),
                     'Cash Available' : cash_available,
                     'Liquid Fund' : liquid_fund
                    },
                    
                    ignore_index = True)
                
                # Reset total holdings
                
                total_num_of_stocks -= no_of_stocks_to_sell
        
        # Check after 30 Days
        
        row_num += 30
        
    # Return Calculation
    
    for i in range (0, len(ledger) - 1):
        
        current_portfolio_value += (ledger['Unit'].iloc[i] * stock['Close'].iloc[-1])
    
    current_portfolio_value += ledger['Cash Available'].iloc[-1] # Adding the final cash in hand
    
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
    
def buy_and_hold (company, installment, start_year) :

    # Downloading the most recent data from NSE

    stock = get_history(symbol = company, start = date(start_year, 1, 1), end = date.today())

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
    
        # Add installment amount every week and update cash available
    
        total_invested_amount += installment
        
        if (row_num == 0) :
            
            cash_available = total_invested_amount
            
        else :
    
            cash_available = ledger['Cash Available'].iloc[-1] + installment

        # Find current stock price
        
        stock_price = stock['Close'].iloc[row_num]    
        
        # Buy stocks from available cash
        
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
    
    current_portfolio_value += ledger['Cash Available'].iloc[-1] # ERROR AREA : Adding the final cash in hand
    
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

normal_distribution_of_pe_ratio('NIFTY 500', 2011)

buy_and_hold('NTPC', 10000, 2011)
pe_based_sip_model('NTPC', 10000, 2011)