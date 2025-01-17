import pandas as pd
import yfinance as yf

# Read CSV and convert time
df = pd.read_csv("JPCBBS.csv")
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

# Debug prints for df
print("DF index length:", len(df.index))
print("DF index date length:", len(df.index.date))
print("DF first few dates:", list(df.index.date)[:5])

# Get forex data with proper date range
forex_data = yf.download("JPYUSD=X", 
                        start=df.index.min(),  # Use actual data range
                        end=df.index.max())

# Reindex and forward fill forex data
forex_rates = forex_data['Close'].reindex(df.index.date).fillna(method='bfill').values.ravel()  # Use ravel() to flatten

# Debug prints
print("Forex rates shape:", forex_rates.shape)
print("df['close'] shape:", df['close'].shape)

print(forex_rates[1])
print(df['close'][1])

# Convert close values to USD
df['close'] = df['close'] * forex_rates

print(df)

# Read CSV and convert time

# df = pd.read_csv("JPCBBS.csv")

# df['time'] = pd.to_datetime(df['time'], unit='s')

# df.set_index('time', inplace=True)

# # Get forex data

# forex_data = yf.download("JPYUSD=X", start="2024-01-01", end="2025-01-02")



# # Reindex and forward fill forex data

# forex_rates = forex_data.reindex(df.index.date).fillna(method='ffill')

# print(type(df))
# print(type(forex_rates))
# print(df.index)
# print(forex_rates.index)

# print("Shape of forex_rates.values:", forex_rates["Close"].shape)

# print("Shape of df:", df["close"].shape)

#CANNOT FIGURE THIS OUT
