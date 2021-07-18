# Importing the libraries

import math
import nsepy
import numpy
import sklearn
import pandas as pd
import matplotlib.pyplot as plt

from datetime import date
from scipy.stats import norm
from matplotlib.pyplot import figure

############################# Calculation of statistical confidence in specific intervals ############################

def statistical_confidence(data, num, lowerbound, upperbound) : 
      
    occurance = 0 
    
    for i in range (0, num-1):
        
        if (data[i] > lowerbound and data[i] < upperbound):
            
            occurance += 1
            
        else :
            
            continue
              
    return "{:.2f} %".format(((occurance/num)*100))


################################ Calculation of Normal Distribution of Index Div Yield Ratio ################################

def normal_distribution_of_div_yield (symbol, start_year) :

    # Downloading the most recent data from NSE

    print('Wait while we download data from NSE server \n')
    dataset = nsepy.get_index_pe_history(symbol, date(start_year, 1, 1), date.today())

    # Calculating the most critical data
    
    mean = dataset['Div Yield'].mean() # Determine mean of the Div Yield Ratio
    numberofsamples = len(dataset) # Determine number of sample in dataset fetched from NSE
    latest = dataset['Div Yield'].iloc[-1] # Find out the most recent Div Yield Ratio
    standard_deviation = dataset['Div Yield'].std() # Find out the standard deviation of the Div Yield
    terminals = numpy.array([dataset['Div Yield'].min(), dataset['Div Yield'].max()]) # Find out the terminal values in the Div Yield data
    
    # Determining the individual confidence intervals
    
    confidence_intervals = numpy.array([mean - 3*standard_deviation, mean - 2*standard_deviation, mean - standard_deviation, mean + standard_deviation, mean + 2*standard_deviation, mean + 3*standard_deviation])
    
    # Console Logging Granular Confidence Intervals and their statistical confidence
    
    print("Confidence intervals of {s} Div Yield \n".format(s = symbol))
    
    # Confidence intervals left of mean
    
    print("The confidence between L2-L3 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, confidence_intervals[0], confidence_intervals[1]))
    print("The confidence between L(1.5)-L2 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, confidence_intervals[1], mean - (1.50 * standard_deviation)))
    print("The confidence between L1-L(1.5) = ", statistical_confidence(dataset['Div Yield'], numberofsamples, mean - (1.50 * standard_deviation), confidence_intervals[2]))
    print("The confidence between L(0.5)-L1 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, confidence_intervals[2], mean - (0.50 * standard_deviation)))
    print("The confidence between Mean-L(0.5) = ", statistical_confidence(dataset['Div Yield'], numberofsamples, mean - (0.50 * standard_deviation), mean))
    
    print("")
    
    # Confidence intervals right of mean
    
    print("The confidence between Mean-R(0.5) = ", statistical_confidence(dataset['Div Yield'], numberofsamples, mean, mean + (0.50 * standard_deviation)))
    print("The confidence between R(0.5)-R1 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, mean + (0.50 * standard_deviation), confidence_intervals[3]))
    print("The confidence between R1-R(1.5) = ", statistical_confidence(dataset['Div Yield'], numberofsamples, confidence_intervals[3], mean + (1.50 * standard_deviation)))
    print("The confidence between R(1.5)-R2 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, mean + (1.50 * standard_deviation), confidence_intervals[4]))
    print("The confidence between R2-R3 = ", statistical_confidence(dataset['Div Yield'], numberofsamples, confidence_intervals[4], confidence_intervals[5]))
    
    # Finding out where the current market resides (currently left of mean is not configured due to lack of neccessity)
    
    print("")
    
    if (latest > confidence_intervals[5]):
        print("The current market Div Yield resides beyond R3")
    elif ((latest > confidence_intervals[4]) and (latest < confidence_intervals[5])):
        print("The current market Div Yield resides in the R2-R3 zone")
    elif ((latest > mean + (1.50 * standard_deviation)) and (latest < confidence_intervals[4])):
        print("The current market Div Yield resides in the R(1.5)-R2 zone")
    elif ((latest > confidence_intervals[3]) and (latest < mean + (1.50 * standard_deviation))):
        print("The current market Div Yield resides in the R1-R(1.5) zone")
    elif ((latest > mean + (0.50 * standard_deviation)) and (latest < confidence_intervals[3])):
        print("The current market Div Yield resides in the R(0.5)-R1 zone")
    elif ((latest > mean) and (latest < mean + (0.50 * standard_deviation))):
        print("The current market Div Yield resides in the Mean-R(0.5) zone")
    
    # Building the Distribution Plot
    
    chart = dataset['Div Yield'].plot.kde(color = 'blue', alpha = 0.3, label = 'Div Yield') # Kernel Density Estimation of normal curve
    
    chart.set_xlabel("")
    chart.set_ylabel("")
    
    chart.axvline(x = latest, color = 'black', label ='Current', linestyle = 'dashdot') # Plotting the latest Div Yield Ratio in the chart
    chart.axvline(x = mean, color = 'brown', label ='Mean', linestyle = 'dashed') # Plotting Mean in the chart
    chart.axvline(x = confidence_intervals[3], color = 'green', label ='R1', linestyle = 'dashed') # Plotting 1-Standard Deviation right to mean in the chart
    chart.axvline(x = confidence_intervals[4], color = 'orange', label ='R2', linestyle = 'dashed') # Plotting 2-Standard Deviation right to mean in the chart
    chart.axvline(x = confidence_intervals[5], color = 'red', label ='R3', linestyle = 'dashed') # Plotting 3-Standard Deviation right to mean in the chart
    
    chart.legend(prop = {'size': 15}, loc ="best")
    
    plt.xticks(numpy.array([mean, latest, confidence_intervals[3], confidence_intervals[4], confidence_intervals[5]]), rotation = 90)    
    
    ax = plt.gca() # Get current axes (GCA)
    ax.tick_params(axis = 'both', which = 'major', labelsize = 12)
    
    fig = plt.gcf() # Get current figure (GCF)
    fig.set_size_inches(30, 10)
    fig.savefig("{s} Div Yield Status.png".format(s = symbol), dpi = 100)


################################# Finding out Normal Distribution of Different Indices ###############################

normal_distribution_of_div_yield ('NIFTY 500', 2016)