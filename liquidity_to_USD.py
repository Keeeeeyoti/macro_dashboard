import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def convert_to_usd(file_path: str, source_currency: str):
    """
    Convert values in a CSV file from source currency to USD and save back to the same file.
    
    Args:
        file_path (str): Path to the CSV file containing the data
        source_currency (str): Three letter currency code (e.g. 'EUR', 'JPY', 'GBP', 'CNY')
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Convert timestamp to datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        if source_currency == 'USD':
            print(f"Data already in USD, no conversion needed for {file_path}")
            return
            
        # Get forex data for conversion
        start_date = df['time'].min() - timedelta(days=1)  # Get extra day for safety
        end_date = df['time'].max() + timedelta(days=1)
        
        # Construct forex pair symbol
        forex_symbol = f"{source_currency}USD=X"
        
        # Get exchange rate data
        forex_data = yf.download(forex_symbol, start=start_date, end=end_date)
        forex_data = forex_data['Close'].reindex(df['time'].dt.date).fillna(method='bfill').values.ravel()
        
        print(forex_data.shape)
        print(df['close'].shape)
        # Convert close values to USD
        df['close'] = df['close'] * forex_data
        

        new_file_path = file_path.replace('.csv', '_USD.csv')
        # Save back to CSV
        df.to_csv(new_file_path, index=False)
        print(f"Successfully converted {file_path} from {source_currency} to USD")

    #Debugging       
    except Exception as e:
        print(f"Error converting {file_path}: {str(e)}")
        import traceback
        print(traceback.format_exc())  # This shows the full error stack


convert_to_usd('JPCBBS.csv', 'JPY')