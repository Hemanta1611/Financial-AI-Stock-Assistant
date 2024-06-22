import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf

# Set OpenAI API key
openai.api_key = open('API_KEY', 'r').read()

# Function to get the latest stock price
def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

# Function to calculate Simple Moving Average (SMA)
def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

# Function to calculate Exponential Moving Average (EMA)
def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

# Function to calculate Relative Strength Index (RSI)
def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower = 0)
    down = -1 * delta.clip(upper = 0)
    ema_up = up.ewm(com = 14 - 1, adjust=False).mean()
    ema_down = down.ewm(com = 14 - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1+rs)).iloc[-1])

# Function to calculate Moving Average Convergence/Divergence (MACD)
def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal

    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'

# Function to plot stock price
def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    if data.empty:
        st.error(f"No data available for {ticker}. Please check the stock symbol.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'])
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()

# Define functions as a list of dictionaries
functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_SMA',
        'description': 'A simple moving average (SMA) is an arithmetic moving average calculated by adding recent prices and then dividing that figure by the number of time periods in the calculation average. Calculate SMA for a given stock ticket and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                },
                'window': {
                    'type': 'integer',
                    'description': "The timeframe to consider when calculating the SMA."
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_EMA',
        'description': 'The exponential moving average (EMA) is a technical chart indicator that tracks the price of an investment (like a stock or commodity) over time. The EMA is a type of weighted moving average (WMA) that gives more weighting or importance to recent price data. Calculate the EMA for a given stock ticker and a window.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                },
                'window': {
                    'type': 'integer',
                    'description': "The timeframe to consider when calculating the SMA."
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_RSI',
        'description': 'The Relative Strength Index (RSI), developed by J. Welles Wilder, is a momentum oscillator that measures the speed and change of price movements. The RSI oscillates between zero and 100. Traditionally the RSI is considered overbought when above 70 and oversold when below 30. Calculate the RSI for a given stock ticker.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_MACD',
        'description': 'Moving average convergence/divergence (MACD, or MAC-D) is a trend-following momentum indicator that shows the relationship between two exponential moving averages (EMAs) of a security\'s price. The MACD line is calculated by subtracting the 26-period EMA from the 12-period EMA. Calculate the MACD for a given stock ticker.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'plot_stock_price',
        'description': 'It typically shows the current price, historical highs and lows, and trading volumes. Plot the stock price for the last year given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description' : 'The stock ticker symbol for a company (for example AAPL). Note: FB is renamed to META.',
                }
            },
            'required': ['ticker'],
        },
    },
]

# Mapping function names to their corresponding Python functions
available_function = {
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_price': plot_stock_price,
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Set page configuration
st.set_page_config(page_title="Beautiful Stock Assistant", page_config_layout="wide", layout="centered")

# Title
st.title("Financial Stock AI Assistant")

# User Input with a placeholder
user_input = st.text_input("What can I help you with today?", key="user_input")

if user_input:
    try:
        # Store user message with role indicator
        st.session_state['messages'].append({'role': 'user', 'content': user_input})

        # OpenAI Chat completion
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-0613',
            messages=st.session_state['messages'],
            functions=available_function,
            function_call='auto',
        )

        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in ['get_stock_price', 'calculate_RSI', 'calculate_MACD', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_EMA', 'calculate_SMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            function_to_call = available_function[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.png')  
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )
                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo-0613',
                    messages=st.session_state['messages']
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})


    except Exception as e:
        st.error(f"An error occurred: {e}")

# Display conversation history and assistant response in separate columns
col1, col2, col3 = st.columns([1, 3, 1])  # Adjust column widths as needed

with col1:
    st.write("")  # Add any content you want in this column

with col2:
    st.header("Conversation History")
    for message in st.session_state['messages']:
        if message['role'] == 'user':
            st.write(f"**You:** {message['content']}")
        elif message['role'] == 'assistant':
            st.write(f"**Assistant:** {message['content']}")
        else:
            st.write(f"{message['role']}: {message['content']}")

with col3:
    st.write("")  # Add any content you want in this column

with st.expander("Assistant Response"):
    # Add any content you want within the expander
    pass  # Placeholder for now


