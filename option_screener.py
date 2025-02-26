import requests
import pandas as pd

#calculating break even, max profit, and max loss for calls and puts
def calculate_calls (dataframe):
    new_df = dataframe.copy()
    new_df['breakeven'] = new_df['strike'] + new_df['mark']
    new_df['max profit'] = float('inf')
    new_df['max loss'] = -new_df['mark'] * 100
    new_df['percent to BE'] = ((new_df['breakeven'] - new_df['stock price']) / new_df['stock price']) * 100
    return new_df
def calculate_puts (dataframe):
    new_df = dataframe.copy()
    new_df['breakeven'] = new_df['strike'] - new_df['mark']
    new_df['max profit'] = (new_df['strike'] - new_df['mark']) * 100
    new_df['max loss'] = -float('inf')
    new_df['percent to BE'] = ((new_df['stock price'] - new_df['breakeven']) / new_df['stock price']) * 100
    return new_df

#calculating debit spreads for calls and puts
def calculate_calldebits (dataframe, spread_distance):
    call_debits = dataframe.copy()
    call_debits = call_debits.drop(['IV'], axis=1)
    strike_dist = call_debits['strike'].shift(-spread_distance) - call_debits['strike']
    call_debits['strikes'] = call_debits['strike'].astype(str) + "/" + call_debits['strike'].shift(-1).astype(str)
    call_debits.loc[:, 'bid'] = call_debits['bid'] - call_debits['ask'].shift(-spread_distance)
    call_debits.loc[:, 'ask'] = call_debits['ask'] - call_debits['bid'].shift(-spread_distance)
    call_debits = call_debits[call_debits['bid'] >= 0]
    call_debits.loc[:, 'mark'] = (call_debits['ask'] + call_debits['bid']) / 2
    call_debits['mark'] = call_debits['mark'].round(2)
    call_debits = call_debits.dropna()
    call_debits = call_debits[['symbol', 'expiration', 'strikes', 'type', 'mark', 'bid', 'ask', 'date', 'stock price', 'strike']]
    call_debits['max profit'] = (strike_dist * 100) - (call_debits['mark'] * 100)
    call_debits['max loss'] = -(call_debits['mark'] * 100)
    call_debits['breakeven'] = call_debits['strike'] + call_debits['mark']
    call_debits['percent to BE'] = ((call_debits['breakeven'] - call_debits['stock price']) / call_debits['stock price']) * 100
    return call_debits
def calculate_putdebits (dataframe, spread_distance):
    put_debits = dataframe.copy()
    put_debits = put_debits.drop(['IV'], axis=1)
    strike_dist = put_debits['strike'].shift(spread_distance) - put_debits['strike']
    put_debits['strikes'] = put_debits['strike'].astype(str) + "/" + put_debits['strike'].shift(1).astype(str)
    put_debits.loc[:, 'bid'] = put_debits['bid'] - put_debits['ask'].shift(spread_distance)
    put_debits.loc[:, 'ask'] = put_debits['ask'] - put_debits['bid'].shift(spread_distance)
    put_debits = put_debits[put_debits['bid'] >= 0]
    put_debits.loc[:, 'mark'] = (put_debits['ask'] + put_debits['bid']) / 2
    put_debits['mark'] = put_debits['mark'].round(2)
    put_debits = put_debits.dropna()
    put_debits = put_debits[['symbol', 'expiration', 'strikes', 'type', 'mark', 'bid', 'ask', 'date', 'stock price', 'strike']]
    put_debits['max profit'] = - (strike_dist * 100) - (put_debits['mark'] * 100)
    put_debits['max loss'] = -(put_debits['mark'] * 100)
    put_debits['breakeven'] = put_debits['strike'] - put_debits['mark']
    put_debits['percent to BE'] = ((put_debits['breakeven'] - put_debits['stock price']) / put_debits['stock price']) * 100
    return put_debits

#filtering results by strike, expiration, and percentage to BE
def filters (dataframe, min_strike, max_strike, expiration):
    if (expiration == 'N/A') or (expiration == 'None'):
        filtered_data = dataframe.loc[(dataframe['strike'] >= min_strike) & (dataframe['strike'] <= max_strike)]
    else:
        filtered_data = dataframe.loc[(dataframe['strike'] >= min_strike) & (dataframe['strike'] <= max_strike) & (dataframe['expiration'] == expiration)]
    return filtered_data

#sorting filtered results by premium
def sort_by_premium (dataframe, upper_limit):
    if (dataframe['mark'] <= upper_limit).any():
        new_df = dataframe.loc[dataframe['mark'] <= upper_limit]
        return new_df

#checking if a dataframe is empty
def check_if_dataframe_is_none(df):
  return df is None

#main function
def get_optionsData(price_range, expiration, max_premium):
    for ticker in tickers:
        #accessing api and converting to dictionary json
        options_url = 'https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=' + ticker + '&apikey=RG86RTYFVEG6TCN2'
        response = requests.get(options_url)
        data_dict = response.json()

        #converting dictionary to pandas dataframe
        options_data = data_dict.get('data', [])
        dataframes[ticker] = pd.DataFrame(options_data)

        num_cols = len(dataframes[ticker].columns)
        if num_cols == 0:
            print('No options data for ' + ticker)
            continue

        #accessing api for stock price
        stock_url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + ticker + '&entitlement=delayed&apikey=RG86RTYFVEG6TCN2'
        r = requests.get(stock_url)
        stock_data = r.json()
        price_str = stock_data['Global Quote - DATA DELAYED BY 15 MINUTES']['05. price']
        price = float(price_str)

        #cleaning up dataframe
        dataframes[ticker] = dataframes[ticker].drop(columns=['contractID', 'last', 'open_interest', 'gamma', 'vega', 'rho', 'bid_size', 'ask_size', 'volume', 'delta', 'theta'])
        dataframes[ticker] = dataframes[ticker].rename(columns={'implied_volatility':'IV'})

        #adding price as a constant column
        dataframes[ticker]['stock price'] = price

        #converting to numeric
        for string in ['strike', 'bid', 'ask', 'mark']:
            dataframes[ticker][string] = pd.to_numeric(dataframes[ticker][string], errors='coerce')

        #making separate dataframes for calls and puts
        dataframes[ticker + '_calls'] = dataframes[ticker][dataframes[ticker]['type'] == 'call']
        dataframes[ticker + '_puts'] = dataframes[ticker][dataframes[ticker]['type'] == 'put']

        #filtering results
        filtered[ticker + '_calls'] = filters(dataframes[ticker + '_calls'], price * (1.0 - price_range), price * (1.0 + price_range), expiration)
        filtered[ticker + '_puts'] = filters(dataframes[ticker + '_puts'], price * (1.0 - price_range), price * (1.0 + price_range), expiration)

        #sorting filtered results by premium
        filtered[ticker + '_calls'] = sort_by_premium(filtered[ticker + '_calls'], max_premium)
        filtered[ticker + '_puts'] = sort_by_premium(filtered[ticker + '_puts'], max_premium)
        
        if isinstance(filtered[ticker + '_calls'], pd.DataFrame) == False or isinstance(filtered[ticker + '_puts'], pd.DataFrame) == False:
            print('No matches for ' + ticker)
        else:
            print('Matches found for ' + ticker + '!')

dataframes = {}
filtered = {}

#user inputs
tickers_input = input('Enter the tickers: ')
tickers = tickers_input.split()
price_input = input('Enter the price range: ')
price_num = float(price_input)
expiration = input('Enter the expiration date: ')
max_pre_input= input('Enter the maximum premium: ')
max_premium = float(max_pre_input)

#######FIX OPTION SPREADS AND PRICE RANGE#######

#user interface
if (price_num > 0) and (max_premium > 0):
    get_optionsData(price_num, expiration, max_premium)
    if (dataframes == {}):
        print('No options data found for tickers')
    else:
        while True:
            ticker_select = input('Enter the ticker: ')
            if (ticker_select + '_calls') in filtered and (ticker_select + '_puts') in filtered:
                while True:
                    type_select = input('Enter the type of option: ')
                    if type_select == 'calls':
                        if check_if_dataframe_is_none(filtered[ticker_select + '_calls']):
                            print('No call options data for ' + ticker_select)
                            break
                        filtered[ticker_select + '_calls'] = calculate_calls(filtered[ticker_select + '_calls'])
                        print(filtered[ticker_select + '_calls'])
                        break
                    elif type_select == 'puts':
                        if check_if_dataframe_is_none(filtered[ticker_select + '_puts']):
                            print('No put options data for ' + ticker_select)
                            break
                        filtered[ticker_select + '_puts'] = calculate_puts(filtered[ticker_select + '_puts'])
                        print(filtered[ticker_select + '_puts'])
                        break
                    elif type_select == 'both':
                        if check_if_dataframe_is_none(filtered[ticker_select + '_calls']):
                            print('No call options data for ' + ticker_select)
                        else:
                            filtered[ticker_select + '_calls'] = calculate_calls(filtered[ticker_select + '_calls'])
                            print(filtered[ticker_select + '_calls'])
                        if check_if_dataframe_is_none(filtered[ticker_select + '_puts']):
                            print('No put options data for ' + ticker_select)
                            break
                        else:
                            filtered[ticker_select + '_puts'] = calculate_puts(filtered[ticker_select + '_puts'])
                            print(filtered[ticker_select + '_puts'])
                        break
                    elif type_select == 'call spreads':
                        spread_distance = int(input('Enter the spread distance(in rows shifted): '))
                        call_spreads = calculate_calldebits(dataframes[ticker_select + '_calls'], spread_distance)
                        call_spreads = sort_by_premium(call_spreads, max_premium)
                        call_spreads = filters(call_spreads, call_spreads['stock price'] * (1.0 - price_num), call_spreads['stock price'] * (1.0 + price_num), expiration)
                        if check_if_dataframe_is_none(call_spreads):
                            print('No call spread data for ' + ticker_select)
                            break
                        else:
                            print(call_spreads.drop(columns=['strike']))
                        break
                    elif type_select == 'put spreads':
                        spread_distance = int(input('Enter the spread distance(in rows shifted): '))
                        put_spreads = calculate_putdebits(dataframes[ticker_select + '_puts'], spread_distance)
                        put_spreads = sort_by_premium(put_spreads, max_premium)
                        put_spreads = filters(put_spreads, put_spreads['stock price'] * (1.0 - price_num), put_spreads['stock price'] * (1.0 + price_num), expiration)
                        if check_if_dataframe_is_none(put_spreads):
                            print('No put spread data for ' + ticker_select)
                            break
                        else:
                            print(put_spreads.drop(columns=['strike']))
                        break
                    else:
                        print('Invalid option type')
            elif ticker_select == 'exit' or ticker_select == 'Exit':
                break
            else:
                print('Invalid ticker')
            continue_program = input('Print data for more tickers? (y/n): ')
            if continue_program == 'n' or continue_program == 'N' or continue_program == 'no' or continue_program == 'No':
                break
            else:
                continue
elif (price_num > 0) and (max_premium <= 0):
    print('Invalid max premium input')
elif (price_num <= 0) and (max_premium > 0):
    print('Invalid price range input')
else:
    print('Invalid price range and max premium inputs')

print('Exiting program')
#end of program
