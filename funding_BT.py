import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Constants
initial_principal = 100000
position_size = 1  # Position size in BTC
take_profit_pct = 0.2  # 1% take profit
stop_loss_pct = -0.1  # 0.5% stop loss

# Load data
funding_data = pd.read_excel("binance_funding_rate_data_2020_2024.xlsx")
price_data = pd.read_excel("binance_btcusdt_perp_close_prices_1h_2020_2024.xlsx")

# Merge data
merged_data = pd.merge(funding_data, price_data, on="timestamp", how="inner")

# Signal Generation
merged_data['signal'] = 0
merged_data.loc[merged_data['fundingRate'] > 0.0005, 'signal'] = -1  # Short signal
merged_data.loc[merged_data['fundingRate'] < -0.000, 'signal'] = 1  # Long signal

# Order Execution
merged_data['position'] = 0
current_position = 0
entry_price = 0

for i in range(len(merged_data)):
    if current_position == -1 and merged_data.at[i, 'close'] >= entry_price * (1 + take_profit_pct):
        current_position = 0  # Take profit for short position
    elif current_position == 1 and merged_data.at[i, 'close'] <= entry_price * (1 - take_profit_pct):
        current_position = 0  # Take profit for long position
    elif current_position == -1 and merged_data.at[i, 'close'] <= entry_price * (1 - stop_loss_pct):
        current_position = 0  # Stop loss for short position
    elif current_position == 1 and merged_data.at[i, 'close'] >= entry_price * (1 + stop_loss_pct):
        current_position = 0  # Stop loss for long position
    elif current_position == 0:
        current_position = merged_data.at[i, 'signal']
        entry_price = merged_data.at[i, 'close']

    merged_data.at[i, 'position'] = current_position

# Performance Metrics Calculation
merged_data['return'] = merged_data['close'].pct_change() * merged_data['position'].shift() * 100  # Calculate return as percentage
total_return = merged_data['return'].cumsum()  # Cumulative return in percentage

sharpe_ratio = (merged_data['return'].mean() / merged_data['return'].std()) * np.sqrt(252)
max_drawdown = (total_return - total_return.expanding().max()).min()

# Calculate total return as percentage
total_return_pct = total_return.iloc[-1]

# Calculate the number of long and short signals
num_long_signals = (merged_data['signal'] == 1).sum()
num_short_signals = (merged_data['signal'] == -1).sum()

# Plot the equity curve
plt.figure(figsize=(10, 6))
plt.plot(merged_data['timestamp'], total_return)
plt.xlabel('Timestamp')
plt.ylabel('Total Return (USD)')
plt.title('Equity Curve')
plt.show()

# Plot the price movement and signals
plt.figure(figsize=(14, 7))
plt.plot(merged_data['timestamp'], merged_data['close'], label='Closing Price', color='blue')
plt.scatter(merged_data[merged_data['signal'] == 1]['timestamp'],
            merged_data[merged_data['signal'] == 1]['close'],
            marker='^', color='green', label='Long Signal')
plt.scatter(merged_data[merged_data['signal'] == -1]['timestamp'],
            merged_data[merged_data['signal'] == -1]['close'],
            marker='v', color='red', label='Short Signal')
plt.title('Price Movement with Funding Rate Signals')
plt.xlabel('Timestamp')
plt.ylabel('Price')
plt.legend()
plt.grid()
plt.show()

# Print performance metrics
print(f"Total Return: {total_return.iloc[-1]:.2f} USD")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Max Drawdown: {max_drawdown:.2f}")
print(f"Number of Long Signals: {num_long_signals}")
print(f"Number of Short Signals: {num_short_signals}")
