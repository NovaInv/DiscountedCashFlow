# NovaInv October 21, 2022
# Discounted Cash Flow valuation using simple formula: ulFCF = EBIT - Taxes + DA - NWC - CAPEX
# Components are forecasted as percentage of free cashflow.
# Revenue growth rate and ebt margin are sample from a normal distribution of historical mean and standard deviation
# Many simulations are run to give probability distribution based on varying growth rates and margins.
# References: https://www.youtube.com/watch?v=eXhCXobViJc&t=616s&ab_channel=AswathDamodaran

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
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

num_simulations = 5000
periodsToPredict = 5 # how many periods to forecast ahead
lookbackForGrowth = 5 # how many periods to lookback when calculating growth rate
perpetuityGrownth = 0.02 # long term growth rate of cash flows beyond forecast
wacc = 0.085 # discount rate
ticker = 'COST' # ticker used (Costco Wholesale Corporation)

#def ulFCF(EBIT,DA,Taxes,NWC,NCS)
IS = read_in_data("Data/COST_IS.xls")
BS = read_in_data("Data/COST_BS.xls")

BS['WC'] = BS['Total current assets'] - BS['Total current liabilities'] # add Working Capital column
IS['DA Expense'] = IS['EBITDA'] - IS['EBIT'] # add Depreciation & Amoritization expense
IS['EBT Margin'] = IS['EBT'] / IS['Revenue'] 
IS['Tax Rate'] = IS['Income Tax Provision'] / IS['EBT']

def use_revenue_to_forecast():
	# grab last total debt and cash position to use in equity value later
	last_debt = float(BS[-1:]['Total Debt'])
	last_cash = float(BS[-1:]['Cash and Short Term Investments'])

	last_year_rev = float(IS[-1:]['Revenue']) # 
	IS_percentages = np.array(IS.iloc[-1:])/last_year_rev
	BS_percentages = np.array(BS.iloc[-1:])/last_year_rev

	average_tax_rate = IS['Tax Rate'][-lookbackForGrowth:].mean()
	revenue_mu = IS['Revenue Growth'][-lookbackForGrowth:].mean()
	revenue_sigma = IS['Revenue Growth'][-lookbackForGrowth:].std()
	ebit_margin_mu = IS['EBIT Margin'][-lookbackForGrowth:].mean()
	ebit_margin_sigma = IS['EBIT Margin'][-lookbackForGrowth:].std()
	#print(average_tax_rate)


	#start new dataframe for forecasted data
	#IS_index = IS.columns.to_list()
	IS_forecast = pd.DataFrame(index = IS.columns)
	BS_forecast = pd.DataFrame(index = BS.columns)
	IS_forecast['Year0'] = IS[-1:].transpose()
	BS_forecast['Year0'] = BS[-1:].transpose()

	valuations = []

	for s in range(num_simulations):

		ulfcf = [] # Unlevered Free Cash Flow list
		discounted_ulFCF = [] # Discounted Unlevered Free Cash Flow list
		last_year_rev = float(IS[-1:]['Revenue'])

		for i in range(1,periodsToPredict+1):
			rev_growth_rate = np.random.normal(revenue_mu, revenue_sigma)
			ebit_margin_used = np.random.normal(ebit_margin_mu, ebit_margin_sigma)

			IS_forecast[f'Year{i}'] = last_year_rev * (1 + rev_growth_rate) * IS_percentages.T
			BS_forecast[f'Year{i}'] = last_year_rev * (1 + rev_growth_rate) * BS_percentages.T
			last_year_rev *= (1 + rev_growth_rate) # reset last year revenue to current year

			# calculate variables in forecasted data to be used in FCF calculation
			# Specifically: Change in WC and Net Capital Spending (CAPEX)
			nopat_ = last_year_rev * ebit_margin_used * (1 - average_tax_rate)
			da_ = IS_forecast.loc['DA Expense'][f'Year{i}']
			nwc_ = BS_forecast.loc['WC'][f'Year{i}'] - BS_forecast.loc['WC'][f'Year{i-1}']
			ncs_ = BS_forecast.loc['Property, Plant, Equpment (Net)'][f'Year{i}'] - BS_forecast.loc['Property, Plant, Equpment (Net)'][f'Year{i-1}'] + da_
			fcf = nopat_ + da_ - nwc_ - ncs_
			disc_fcf = fcf/((1 + wacc)**(1/i))
			ulfcf.append(fcf)
			discounted_ulFCF.append(disc_fcf)
		

		# Gordon growth model from free cash flow beyond forecasted period
		terminal_val = (ulfcf[-1] * (1 + perpetuityGrownth)) / (wacc - perpetuityGrownth)
		discounted_terminal_val = terminal_val/ ((1 + wacc)**(1/periodsToPredict))

		#print(sum(discounted_ulFCF) ,discounted_terminal_val)
		# combine npv of forecasted cashflows and discounted terminal value to otain enterprise value
		enterprise_value = discounted_terminal_val + sum(discounted_ulFCF)

		# remove debt and add cash to enterprise value. Then divide by diluted share count to arrive at equity value per share.
		equity_val_per_share = (enterprise_value - last_debt + last_cash) / IS_forecast.loc['Shares (Diluted, Average)']['Year0']

		valuations.append(equity_val_per_share)

	print(f'{ticker}:\nMean DCF Valued Price: ${np.mean(valuations):.2f}')
	print(f'\nAssumed long term growth rate: {perpetuityGrownth*100}%\nDiscount Rate: {wacc*100}%')
	print('(Revenue used to forecast growth)\n')

	for t in range(1,11):
		print(f'{t*10}th Percentile: {np.percentile(valuations,t*10)}')

	#print(valuations[-20:])
	n, bins, patches = plt.hist(valuations, 20)
	plt.show()


use_revenue_to_forecast()