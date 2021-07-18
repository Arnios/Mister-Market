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
    global stock

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

    # Declaring Function variables

    row_num = 0 # Row Iterator
    
    liquid_fund = 0.00 # Liquid Fund
    current_profit = 0.00 # Current Profit
    cash_available = 0.00 # Initial Balance
    total_num_of_stocks = 0 # Number of Stocks
    total_invested_amount = 0.00 # Initial Invested Amount
    current_portfolio_value = 0.00 # Current Portfolio Value
    number_of_successive_sip = 0 # SIP counter
    
    ledger = pd.DataFrame(columns = ['Type', 'Symbol', 'Price', 'Unit', 'Cash Available', 'Liquid Fund'])
    results = pd.DataFrame(columns = ['Total Investment', 'Cash in Hand', 'Current Portfolio Value', 'Net Profit'])
    
    while row_num < len(stock):
    
        # Update cash available and liquid fund before we start the iteration  
    
        if (row_num == 0) :
            
            cash_available += installment # Function variable
            
        else :
    
            cash_available += installment
            liquid_fund += (liquid_fund * 0.06) / 12 # Add monthly interest at 6% Per annum

        # Find the stock price at the close of that particular day
        
        stock_price = stock['Close'].iloc[row_num] # Local variable
        
        
        #################################### BUY SIGNALS ####################################
        
        
        # SIP BUY : if Nifty 500 PE < R2
        # Rationale : To continue SIP at all times except the mere 5% time when market is beyond R2
        
        if (nifty500['P/E'].iloc[row_num] < confidence_intervals[4]) :
            
            # Buy stocks with available cash and adjust cash available afterwards
            
            num_of_new_stocks = math.floor(cash_available / stock_price) # Local variable
            total_num_of_stocks += num_of_new_stocks # Function variable
            cash_available -= (num_of_new_stocks * stock_price) # Function variable
            number_of_successive_sip += 1 # Function variable
        
            # Add transaction in ledger
            
            ledger = ledger.append(
                
                {
                     'Type' : 'SIP',
                     'Symbol' : stock['Symbol'].iloc[row_num],
                     'Price' : stock['Close'].iloc[row_num],
                     'Unit' : num_of_new_stocks, # Local variable
                     'Cash Available' : cash_available, # Global variable
                     'Liquid Fund' : liquid_fund # Global variable
                },
                
                ignore_index = True)
            
            
            ############################### EMERGENCY BUY ###############################
            
            
            # R(0.5) CROSSOVER : Use 50% liquid fund to buy stock when Nifty 500 PE < R(0.5)
            
            if ((nifty500['P/E'].iloc[row_num] < mean + (0.50 * standard_deviation)) and (liquid_fund > stock_price)) :
            
                # Buy stocks with liquid fund and Update liquid fund balance
                    
                num_of_new_stocks = math.floor((0.50 * liquid_fund) / stock_price) # Local variable
                total_num_of_stocks += num_of_new_stocks # Function variable
                liquid_fund -= (num_of_new_stocks * stock_price)
                
                # Add transaction in ledger
                    
                ledger = ledger.append(
                        
                    {
                        'Type' : 'Mean Buy',
                        'Symbol' : stock['Symbol'].iloc[row_num],
                        'Price' : stock['Close'].iloc[row_num],
                        'Unit' : num_of_new_stocks, # Local variable
                        'Cash Available' : cash_available, # Global variable
                        'Liquid Fund' : liquid_fund # Global variable
                    },
                        
                    ignore_index = True)
            
            # MEAN CROSSOVER : Use all liquid fund to buy stock when Nifty 500 PE < Mean
        
            elif ((nifty500['P/E'].iloc[row_num] < mean) and (liquid_fund > stock_price)) :
            
                # Buy stocks with liquid fund and Update liquid fund balance
                    
                num_of_new_stocks = math.floor(liquid_fund / stock_price) # Local variable
                total_num_of_stocks += num_of_new_stocks # Function variable
                liquid_fund -= (num_of_new_stocks * stock_price)
                
                # Add transaction in ledger
                    
                ledger = ledger.append(
                        
                    {
                        'Type' : 'Mean Buy',
                        'Symbol' : stock['Symbol'].iloc[row_num],
                        'Price' : stock['Close'].iloc[row_num],
                        'Unit' : num_of_new_stocks, # Local variable
                        'Cash Available' : cash_available, # Global variable
                        'Liquid Fund' : liquid_fund # Global variable
                    },
                        
                    ignore_index = True)
        
 
        #################################### SELL SIGNALS ####################################
        
    
        # PRECAUTIOUS SELL : Sell 30% of Portfolio on R1 crossover
        
        elif ((nifty500['P/E'].iloc[row_num] > confidence_intervals[3]) and (number_of_successive_sip >= 12)) :
            
            # Check if the Portfolio is in Profit that day
            # If I have Profit then I will sell 30% of the Porfolio value and transfer the proceeds into liquid fund
            
            current_profit = (total_num_of_stocks * stock_price) - total_invested_amount # Function variable
            
            if ((current_profit) > 0) :
              
                # Calculating 30% of the Current Portoflio Value
                
                current_num_of_stocks = 0 # Local variable
                
                for i in range (0, len(ledger) - 1):
        
                    current_num_of_stocks += ledger['Unit'].iloc[i]
              
                interim_portfolio_value = (current_num_of_stocks * stock['Close'].iloc[row_num]) # Local variable
                interim_no_of_stocks_to_sell = math.floor((0.30 * interim_portfolio_value) / stock['Close'].iloc[row_num]) # Local variable
                
                liquid_fund += (interim_no_of_stocks_to_sell * stock['Close'].iloc[row_num]) # Adding the proceeds to liquid fund
                total_num_of_stocks -= interim_no_of_stocks_to_sell # Function variable
        
                # Add transaction in ledger and increment counter
                
                ledger = ledger.append(
                    
                    {
                         'Type' : 'R-1 Sell',
                         'Symbol' : stock['Symbol'].iloc[row_num],
                         'Price' : stock['Close'].iloc[row_num],
                         'Unit' : (-1 * interim_no_of_stocks_to_sell), # Local variable
                         'Cash Available' : cash_available, # Function variable
                         'Liquid Fund' : liquid_fund # Function variable
                    },
                    
                    ignore_index = True)
                
                number_of_successive_sip = 0 # Reseting number of successive SIP streak
                
       # Add this month installment amount and update cash in hand and increment counter by 30 days
    
        total_invested_amount += installment
        row_num += 30
        
    # Final Portfolio Value Calculation
    
    for i in range (0, len(ledger) - 1):
        
        current_portfolio_value += (ledger['Unit'].iloc[i] * stock['Close'].iloc[-1]) # Global variable
    
    current_portfolio_value += cash_available # Adding the final cash in hand
    
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
    
    print("Net profit = ₹ %.2f Lacs" % (current_portfolio_value - total_invested_amount))
    print("Total investment = ₹ %.2f Lacs" % total_invested_amount)
    print("Current portfolio value = ₹ %.2f Lacs" % current_portfolio_value)
    print("Current portfolio value = ₹ %.2f times investment" % (current_portfolio_value / total_invested_amount))
    
    print("")
    print("Saving Everything Important Into an Excel File")
    
    # Print Stock History and Transaction Ledger
    
    writer = pd.ExcelWriter(company + ' (PE Based S-2).xlsx', engine = 'xlsxwriter') # Create a Pandas Excel Writer using XLSXWriter as the engine.
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
    
        # Update cash available
        
        cash_available += installment # Function variable
        
        # Find the stock price at the close of that particular day
        
        stock_price = stock['Close'].iloc[row_num] # Local variable

        # Buy stocks from available cash and update cash in hand afterwards
        
        num_of_new_stocks = math.floor(cash_available / stock_price) # Local variable
        total_num_of_stocks += num_of_new_stocks # Function variable
        cash_available -= (stock_price * num_of_new_stocks) # Function variable
        
        # Add transaction in ledger
        
        ledger = ledger.append(
            
            {
             'Type' : 'SIP',
             'Symbol' : stock['Symbol'].iloc[row_num],
             'Price' : stock['Close'].iloc[row_num],
             'Unit' : num_of_new_stocks,
             'Cash Available' : cash_available
            },
            
            ignore_index = True)
        
        # Add this month installment amount and increment counter by 30 days
    
        total_invested_amount += installment
        row_num += 30
    
    # Return Calculation
    
    for i in range (0, len(ledger) - 1):
        
        current_portfolio_value += (ledger['Unit'].iloc[i] * stock['Close'].iloc[-1]) # Global variable
    
    current_portfolio_value += cash_available # Adding the final cash in hand
    
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
    
    print("Net profit = ₹ %.2f Lacs" % (current_portfolio_value - total_invested_amount))
    print("Total investment = ₹ %.2f Lacs" % total_invested_amount)
    print("Current portfolio value = ₹ %.2f Lacs" % current_portfolio_value)
    print("Current portfolio value = ₹ %.2f times investment" % (current_portfolio_value / total_invested_amount))

    print("")
    
    # Print Stock History and Transaction Ledger
    
    writer = pd.ExcelWriter(company + ' (Plain SIP).xlsx', engine = 'xlsxwriter') # Create a Pandas Excel Writer using XLSXWriter as the engine.
    
    stock.to_excel(writer, sheet_name = 'HISTORY')
    ledger.to_excel(writer, sheet_name = 'LEDGER')
    results.to_excel(writer, sheet_name = 'RESULT')
    
    writer.save() # Close the Pandas Excel writer and output the Excel file.
    

# Test with stock

normal_distribution_of_pe_ratio('NIFTY 500', 2011)

# buy_and_hold('RELIANCE', 10000, 2011)
pe_based_sip_model('RELIANCE', 10000, 2011)