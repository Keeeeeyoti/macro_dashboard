import pandas as pd
import yfinance as yf   


def convert_to_usd(csv_path, source_currency):
    """
    Convert values from source currency to USD using historical forex rates
    
    Parameters:
    csv_path (str): Path to the CSV file
    source_currency (str): Source currency code (e.g., 'JPY', 'EUR', 'GBP')
    
    Returns:
    pandas.DataFrame: DataFrame with original and USD-converted values
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        if source_currency != 'USD':    
            # Construct forex pair symbol
            forex_symbol = f"{source_currency}USD=X"
            
            # Download exchange rate data
            forex_data = yf.download(forex_symbol, start=df.index.min(), end=df.index.max())
            
            # Resample exchange rate data to match input data frequency
            forex_rates = forex_data['Close'].reindex(df.index, method='bfill').squeeze()  # Get only the 'Close' column
            print(forex_rates)

            df['close'] = df['close'] * forex_rates

        
        df= df[["close"]]
        # Create output filename by inserting '_USD' before the file extension
        output_path = csv_path.rsplit('.', 1)[0] + '_USD.csv'
        
        # Export to CSV
        df.to_csv(output_path)
            
        return df
        
    except FileNotFoundError:
        st.error(f"CSV file not found at path: {csv_path}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Example usage:
jpcbbs_df = convert_to_usd('JPCBBS.csv', 'JPY')
cncbbs_df = convert_to_usd('CNCBBS.csv', 'CNY')
eucbbs_df = convert_to_usd('EUCBBS.csv', 'EUR') 
gbcbbs_df = convert_to_usd('GBCBBS.csv', 'GBP')
uscbbs_df = convert_to_usd('USCBBS.csv', 'USD')


