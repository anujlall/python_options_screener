# Python Options Screener

This is a Python code that retrieves options data from tickers given to it, and sorts the data based on given price ranges, expiration dates, and max premiums. Uses: Alpha Vantage API

When run, the code will prompt you to enter a list of tickers 'Enter the tickers:'. Enter up to 30 tickers, separated by spaces(MSFT AAPL TSLA). The code will then ask you to input a price range 'Enter the price range:'. This input determines what the max percentage from the stock price 

The code will then scan each ticker for options data, and will return 'Matches found for (ticker)!' if any contracts from that ticker match the given criteria.
