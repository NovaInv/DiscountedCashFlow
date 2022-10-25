# Discounted Cash Flow Valuation
The dcf python script forecasts and discounts unleveraged free cash flow. One function uses revenue to estimate growth rate and vertical analysis percentages to forecast
n periods of free cash flow components. The second function uses historical free cash flow to estimate growth rate and forecast n periods from last period free cash flow. 
In both cases, the free cash flow is expected to grow at a set perpetuity rate. The terminal value of the perpetual cash flows is discounted to present day and added to 
the sum of discounted forecasted cash flows.

Example output:
COST:
DCF Valued Price: $525.45
Recent Price: $496.97
Percent Difference: 5.73%
Assumed growth rate: 8.73%
Assumed long term growth rate: 2.0%
Discount Rate: 5.0%
(Revenue used to forecast growth)

# Monte Carlo Simulation
The montecarlo labeled script uses monte carlo simulation to sample revenue growth rate and EBT margin from historical distributions. The remaining calculation is 
carried out as in the revenue based dcf script. A histogram of estimated current prices is plotted.

Example output:
COST:
Mean DCF Valued Price: $494.49

Assumed long term growth rate: 2.0%
Discount Rate: 5.0%
(Revenue used to forecast growth)

10th Percentile: 359.46788172909277,

20th Percentile: 404.8887135961368, 

30th Percentile: 438.0907860553996, 

40th Percentile: 465.73905436558925, 

50th Percentile: 492.50625997998077, 

60th Percentile: 518.2680718099278, 

70th Percentile: 549.0238427800596,  

80th Percentile: 583.5279169329751, 

90th Percentile: 632.8118382995914, 

100th Percentile: 1067.8758003381413
![image](https://user-images.githubusercontent.com/45056473/197664587-c3078b75-80f7-49c8-a9a7-66882f3892a1.png)
