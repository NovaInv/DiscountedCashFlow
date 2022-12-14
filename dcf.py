# NovaInv October 20, 2022
# Discounted Cash Flow valuation using simple formula: ulFCF = EBIT - Taxes + DA - NWC - CAPEX
# Two options.
# Option 1: Use revenue growth and vertical analysis based upon revenue to forecast fcf.
# - Assumption: Future income and balance sheet items remain the same percentage of revenue.
# Option 2: Calculate previous Unlevered Free Cash Flow and use that to forecast growth.
# Until improvement, Data is pre-downloaded from https://www.stockrow.com
# Until improvement, must input wacc and perpetuity growth manually.


import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


def read_in_data(filename):
	# pull data from file and rearrange
	data = pd.read_excel(filename) #read from excel file
	colNames = data.Index #save column headers
	data = data.iloc[:,1:].transpose() #transpose data
	data.columns = colNames #reset column names
	return data

def get_most_recent_price(ticker):
	# return most recent price of ticker symbol from yahoo finance
	today = date.today()
	start_date = today - timedelta(days=5)
	end_date = today + timedelta(days=1)

	df = yf.download(ticker,start=start_date,end=end_date,progress=False)['Adj Close']
	return df[-1]

def growth_rate(data):
	# computes annual growth rate over period
	rate = (data[-1]/data[0])**(1/len(data)) - 1
	return rate

periodsToPredict = 5 # how many periods to forecast ahead
lookbackForGrowth = 8 # how many periods to lookback when calculating growth rate
perpetuityGrownth = 0.02 # long term growth rate of cash flows beyond forecast
wacc = 0.05 # discount rate
ticker = 'COST' # ticker used (Costco Wholesale Corporation)

#def ulFCF(EBIT,DA,Taxes,NWC,NCS)
IS = read_in_data("Data/COST_IS.xls")
BS = read_in_data("Data/COST_BS.xls")

BS['WC'] = BS['Total current assets'] - BS['Total current liabilities'] # add Working Capital column
IS['DA Expense'] = IS['EBITDA'] - IS['EBIT'] # add Depreciation & Amoritization expense
IS['Tax Rate'] = IS['Income Tax Provision'] / IS['EBT']


def use_revenue_to_forecast():
	# grab last total debt and cash position to use in equity value later
	last_debt = float(BS[-1:]['Total Debt'])
	last_cash = float(BS[-1:]['Cash and Short Term Investments'])
	average_tax_rate = IS['Tax Rate'][-lookbackForGrowth:].mean()

	last_year_rev = IS.iloc[-1:,0].values # second index slice choose what column to use for vertical percentages and growth rate
	IS_percentages = np.array(IS.iloc[-1:])/last_year_rev
	BS_percentages = np.array(BS.iloc[-1:])/last_year_rev
	rev_growth_rate = growth_rate(IS.iloc[-lookbackForGrowth:,0].values)

	#start new dataframe for forecasted data
	#IS_index = IS.columns.to_list()
	IS_forecast = pd.DataFrame(index = IS.columns)
	BS_forecast = pd.DataFrame(index = BS.columns)
	IS_forecast['Year0'] = IS[-1:].transpose()
	BS_forecast['Year0'] = BS[-1:].transpose()

	nwc = [0] #list to store net working capital calculations
	ncs = [0] #list to store net capital spending calculations
	ulfcf = [] # Unlevered Free Cash Flow list
	discounted_ulFCF = [] # Discounted Unlevered Free Cash Flow list

	for i in range(1,periodsToPredict+1):
		IS_forecast[f'Year{i}'] = last_year_rev * (1 + rev_growth_rate) * IS_percentages.T
		BS_forecast[f'Year{i}'] = last_year_rev * (1 + rev_growth_rate) * BS_percentages.T
		last_year_rev *= (1 + rev_growth_rate) # reset last year revenue to current year

		# calculate variables in forecasted data to be used in FCF calculation
		# Specifically: Change in WC and Net Capital Spending (CAPEX)
		nwc.append(BS_forecast.loc['WC'][f'Year{i}'] - BS_forecast.loc['WC'][f'Year{i-1}'])
		ncs.append(BS_forecast.loc['Property, Plant, Equpment (Net)'][f'Year{i}'] - BS_forecast.loc['Property, Plant, Equpment (Net)'][f'Year{i-1}'] + IS_forecast.loc['DA Expense'][f'Year{i-1}'])

	# add nwc and ncs caclulations to dataframe
	BS_forecast.loc['NWC'] = nwc
	BS_forecast.loc['NCS'] = ncs

	#calculate unlevered free cash flow and discount it
	for i in range(1,periodsToPredict+1):
		fcf = (IS_forecast.loc['Operating Income'][f'Year{i}'] * (1 - average_tax_rate) + IS_forecast.loc['DA Expense'][f'Year{i}']
		 - BS_forecast.loc['NWC'][f'Year{i}'] - BS_forecast.loc['NCS'][f'Year{i}'])

		disc_fcf = fcf/((1 + wacc)**(1/i))
		ulfcf.append(fcf)
		discounted_ulFCF.append(disc_fcf)


	#print(sum(discounted_ulFCF))

	# Gordon growth model from free cash flow beyond forecasted period
	terminal_val = (ulfcf[-1] * (1 + perpetuityGrownth)) / (wacc - perpetuityGrownth)
	discounted_terminal_val = terminal_val/ ((1 + wacc)**(1/periodsToPredict))

	# combine npv of forecasted cashflows and discounted terminal value to otain enterprise value
	enterprise_value = discounted_terminal_val + sum(discounted_ulFCF)

	# remove debt and add cash to enterprise value. Then divide by diluted share count to arrive at equity value per share.
	equity_val_per_share = (enterprise_value - last_debt + last_cash) / IS_forecast.loc['Shares (Diluted, Average)']['Year0']

	recent_price = get_most_recent_price(ticker)

	percent_diff = (equity_val_per_share / recent_price - 1) * 100 # % difference between forecasted price and current price

	print(f'{ticker}:\nDCF Valued Price: ${equity_val_per_share:.2f}\nRecent Price: ${recent_price:.2f}\nPercent Difference: {percent_diff:.2f}%')
	print(f'Assumed growth rate: {rev_growth_rate*100:.2f}%\nAssumed long term growth rate: {perpetuityGrownth*100}%\nDiscount Rate: {wacc*100}%')
	print('(Revenue used to forecast growth)')


def use_past_fcf_to_forecast():
	# grab last total debt and cash position to use in equity value later
	last_debt = float(BS['Total Debt'][-1:])
	last_cash = float (BS['Cash and Short Term Investments'][-1:])
	average_tax_rate = IS['Tax Rate'][-lookbackForGrowth:].mean()

	BS['NWC'] = BS['WC'].diff() # difference in working capital each year
	BS['NCS'] = BS['Property, Plant, Equpment (Net)'].diff() + IS['DA Expense'] #Capital Expenditure each year
	ulFCF = (IS['Operating Income'] * (1 - average_tax_rate) + IS['DA Expense'] - BS['NWC'] - BS['NCS']).values # unlevered free cash flow (ulfcf)

	fcf_growth_rate = growth_rate(ulFCF[-lookbackForGrowth:]) # growth rate of previous ulfcf
	last_fcf = ulFCF[-1]

	forecasted_ulFCF = []
	discounted_ulFCF = []
	
	for i in range(1,periodsToPredict+1):
		forecast = last_fcf * (1 + fcf_growth_rate)
		forecasted_ulFCF.append(forecast)
		discounted_ulFCF.append(forecast / ((1 + wacc)**(1/i)))
		last_fcf = forecast

	#print(forecasted_ulFCF)
	# Gordon growth model from free cash flow beyond forecasted period
	terminal_val = (forecasted_ulFCF[-1] * (1 + perpetuityGrownth)) / (wacc - perpetuityGrownth)
	discounted_terminal_val = terminal_val/ ((1 + wacc)**(1/periodsToPredict))

	# combine npv of forecasted cashflows and discounted terminal value to otain enterprise value
	enterprise_value = discounted_terminal_val + sum(discounted_ulFCF)

	# remove debt and add cash to enterprise value. Then divide by diluted share count to arrive at equity value per share.
	equity_val_per_share = (enterprise_value - last_debt + last_cash) / IS['Shares (Diluted, Average)'][-1]

	recent_price = get_most_recent_price(ticker)

	percent_diff = (equity_val_per_share / recent_price - 1) * 100 # % difference between forecasted price and current price

	print(f'\n{ticker}:\nDCF Valued Price: ${equity_val_per_share:.2f}\nRecent Price: ${recent_price:.2f}\nPercent Difference: {percent_diff:.2f}%')
	print(f'Assumed growth rate: {fcf_growth_rate*100:.2f}%\nAssumed long term growth rate: {perpetuityGrownth*100}%\nDiscount Rate: {wacc*100}%')
	print('(Past FCF used to forecast growth)')


use_revenue_to_forecast()

use_past_fcf_to_forecast()