import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# Load the funding rate data and closing price data from Excel files
funding_data = pd.read_excel("binance_funding_rate_data_full.xlsx")
price_data = pd.read_excel("binance_btcusdt_perp_closing_prices_full.xlsx")

# Merge the funding rate data with the daily closing price data
merged_data = pd.merge(funding_data, price_data, on="timestamp", how="inner")

# Define thresholds for signals and take profit/stop loss
threshold_high = 0.0002  # Funding rate threshold for a short signal
threshold_low = -0.000  # Funding rate threshold for a long signal
take_profit = 0.05  # 1% take profit level
stop_loss = -0.01  # 0.5% stop loss level
max_position_size = 1  # Maximum position size

merged_data['signal'] = 0
merged_data.loc[merged_data['fundingRate'] > threshold_high, 'signal'] = -1  # Short signal
merged_data.loc[merged_data['fundingRate'] < threshold_low, 'signal'] = 1  # Long signal

# Backtest logic with take profit, stop loss, position management, and position size limit
merged_data['position'] = 0
current_position = 0  # Track current position size
for i in range(1, len(merged_data)):
    if current_position == -1 and merged_data.at[i, 'close'] >= (1 + take_profit) * merged_data.at[i - 1, 'close']:
        current_position = 0  # Take profit
    elif current_position == 1 and merged_data.at[i, 'close'] <= (1 + stop_loss) * merged_data.at[i - 1, 'close']:
        current_position = 0  # Stop loss
    elif current_position == 0:
        current_position = merged_data.at[i, 'signal']
    else:
        current_position = current_position

    # Apply position size limit
    if current_position != 0:
        current_position = np.sign(current_position)  # Ensure position is either 1 or -1
        if np.abs(current_position) > max_position_size:
            current_position = max_position_size * np.sign(current_position)

    merged_data.at[i, 'position'] = current_position

# Calculate returns based on the signals
merged_data['return'] = merged_data['close'].pct_change() * merged_data['position']

# Plot the equity curve
equity_curve = (1 + merged_data['return']).cumprod()
plt.figure(figsize=(14, 7))
plt.plot(merged_data['timestamp'], equity_curve, label='Equity Curve', color='purple')
plt.title('Equity Curve based on Funding Rate Levels')
plt.xlabel('Timestamp')
plt.ylabel('Equity')
plt.legend()
plt.grid()
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

# Calculate the number of long and short signals
num_long_signals = (merged_data['signal'] == 1).sum()
num_short_signals = (merged_data['signal'] == -1).sum()

# Calculate returns based on the signals
merged_data['position'] = merged_data['signal'].shift()
merged_data['return'] = merged_data['close'].pct_change() * merged_data['position']

# Calculate Sharpe Ratio
risk_free_rate = 0.05  # Assume a risk-free rate for the calculation
daily_returns = merged_data['return']
daily_std = daily_returns.std()
sharpe_ratio = (daily_returns.mean() - risk_free_rate) / daily_std

# Calculate cumulative returns
merged_data['cumulative_return'] = (1 + merged_data['return']).cumprod()

# Calculate maximum drawdown (MDD)
merged_data['cumulative_return_high'] = merged_data['cumulative_return'].cummax()
merged_data['drawdown'] = merged_data['cumulative_return'] / merged_data['cumulative_return_high'] - 1
max_drawdown = merged_data['drawdown'].min()

print(f"Number of Long Signals: {num_long_signals}")
print(f"Number of Short Signals: {num_short_signals}")
print(f"Total Return: {merged_data['return'].sum()}")
print(f"Maximum Drawdown: {max_drawdown}")
print(f"Sharpe Ratio: {sharpe_ratio}")