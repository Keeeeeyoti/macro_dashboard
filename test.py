import pandas as pd

import pandas as pd

# Convert Unix timestamps to datetime
ism_data = pd.read_csv('test_data.csv')
ism_data['time'] = pd.to_datetime(ism_data['time'], unit='s')  # 's' for seconds
ism_data.set_index('time', inplace=True)

print("First few rows of data:")
print(ism_data.head())
print("\nData shape:", ism_data.shape)