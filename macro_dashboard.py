import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from fredapi import Fred
import yfinance as yf
from datetime import datetime, timedelta
import os


# Initialize ALL session state variables first, before any other code
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
if 'gdp_growth' not in st.session_state:
    st.session_state['gdp_growth'] = None
if 'unemployment_rate' not in st.session_state:
    st.session_state['unemployment_rate'] = None
if 'inflation_rate' not in st.session_state:
    st.session_state['inflation_rate'] = None
if 'spy_data' not in st.session_state:
    st.session_state['spy_data'] = None
if 'recession_periods' not in st.session_state:
    st.session_state['recession_periods'] = None
if 'ism_data' not in st.session_state:
    st.session_state['ism_data'] = None

# Set up the page configuration
st.set_page_config(page_title="Economic Cycle Dashboard", layout="wide")

# Initialize FRED API (you'll need to get an API key from https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY = "b5013e138cb52bb7de668894a00a86ad"  # Remove the trailing space
fred = Fred(api_key=FRED_API_KEY)

# Add date range selector to sidebar
st.sidebar.header("Date Range Selection")

# Get min and max dates from the S&P 500 data for the date picker
spy_data = yf.download('^GSPC', start='1927-01-01')
min_date = datetime(1948, 1, 1).date() 
max_date = spy_data.index.max().date()

# Add date input widgets
start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)
end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Add a search button
search_button = st.sidebar.button('Update Dashboard', type='primary')


# Function to fetch and process economic data
def get_economic_data(start_date, end_date):
    try:
        # Get recession data
        recession_data = fred.get_series('USREC', observation_start=start_date, observation_end=end_date)
        recession_periods = []
        
        # Find recession start and end dates
        in_recession = False
        rec_start = None
        
        for date, value in recession_data.items():
            if value == 1 and not in_recession:
                rec_start = date
                in_recession = True
            elif value == 0 and in_recession:
                recession_periods.append(dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=rec_start,
                    x1=date,
                    y0=0,
                    y1=1,
                    fillcolor="LightGray",
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                ))
                in_recession = False
        
        # Get GDP growth rate (Quarterly)
        gdp = fred.get_series('GDP', observation_start=start_date, observation_end=end_date)
        gdp_pct_change = gdp.pct_change() * 100
        
        # Get Unemployment Rate (Monthly)
        unemployment = fred.get_series('UNRATE', observation_start=start_date, observation_end=end_date)
        
        # Get Inflation Rate (CPI, Monthly)
        inflation = fred.get_series('CPIAUCSL', observation_start=start_date, observation_end=end_date)
        inflation_yoy = inflation.pct_change(periods=12) * 100
        
        # Get S&P 500 data with specific error handling
        try:
            spy = yf.download('^GSPC', start=start_date-timedelta(days=365*10), end=end_date)
            if spy.empty:
                print("No S&P 500 data retrieved")
                return None, None, None, None, None, None
                
            # Check if 'Adj Close' column exists
            if 'Close' not in spy.columns:
                print("'Close' column not found in S&P 500 data")
                print(f"Available columns: {spy.columns.tolist()}")
                return None, None, None, None, None, None
                
            # Calculate annual returns
            spy['Annual_Return'] = spy['Close'].pct_change(periods=252) * 100
            # Calculate 10-year moving average of annual returns
            spy['10Y_MA_Return'] = spy['Annual_Return'].rolling(window=252*10).mean()
            
        except Exception as e:
            print(f"Error processing S&P 500 data: {e}")
            print(f"S&P 500 data shape: {spy.shape if 'spy' in locals() else 'Not downloaded'}")
            return None, None, None, None, None, None

        # Load ISM data from local file
        try:
            print("Attempting to load ISM data...")  # Debug print
            ism_data = pd.read_csv('test_data.csv')
            ism_data['time'] = pd.to_datetime(ism_data['time'], unit='s')  # 's' for seconds
            ism_data.set_index('time', inplace=True)
            # Filter for date range
            ism_data = ism_data[start_date:end_date]
            ism_data = ism_data["close"]
            print(f"ISM data after filtering: {ism_data.shape}")  # Debug print
        except Exception as e:
            print(f"Error loading ISM data: {e}")
            ism_data = None
        
        return gdp_pct_change, unemployment, inflation_yoy, spy, recession_periods, ism_data
        
    except Exception as e:
        print(f"Error in get_economic_data: {e}")
        return None, None, None, None, None, None

# Main dashboard layout
st.title("Economic Cycle Dashboard")



try:
    # Only fetch and update data when search button is clicked
    if search_button or not st.session_state['data_loaded']:
        # Validate date range
        if start_date >= end_date:
            st.error("Start date must be before end date")
        else:
            with st.spinner('Fetching data...'):
                # Fetch data with date range
                gdp_growth, unemployment_rate, inflation_rate, spy_data, recession_periods, ism_data = get_economic_data(start_date, end_date)
                
                # Check if any data is None
                if any(x is None for x in [gdp_growth, unemployment_rate, inflation_rate, spy_data]):
                    st.error("Failed to fetch some economic data. Please try again.")
                    st.session_state['data_loaded'] = False
                else:
                    st.session_state['data_loaded'] = True
                    st.session_state['gdp_growth'] = gdp_growth
                    st.session_state['unemployment_rate'] = unemployment_rate
                    st.session_state['inflation_rate'] = inflation_rate
                    st.session_state['spy_data'] = spy_data
                    st.session_state['recession_periods'] = recession_periods
                    st.session_state['ism_data'] = ism_data

    # Only proceed with display if data is loaded successfully
    if st.session_state['data_loaded']:
        gdp_growth = st.session_state['gdp_growth']
        unemployment_rate = st.session_state['unemployment_rate']
        inflation_rate = st.session_state['inflation_rate']
        spy_data = st.session_state['spy_data']
        recession_periods = st.session_state['recession_periods']
        ism_data = st.session_state['ism_data']
        # Create three columns for the main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("GDP Growth (Latest)", 
                     f"{gdp_growth.iloc[-1]:.1f}%",
                     f"{gdp_growth.iloc[-1] - gdp_growth.iloc[-2]:.1f}%")
        
        with col2:
            st.metric("Unemployment Rate (Latest)", 
                     f"{unemployment_rate.iloc[-1]:.1f}%",
                     f"{unemployment_rate.iloc[-1] - unemployment_rate.iloc[-2]:.1f}%")
        
        with col3:
            st.metric("Inflation Rate (Latest)", 
                     f"{inflation_rate.iloc[-1]:.1f}%",
                     f"{inflation_rate.iloc[-1] - inflation_rate.iloc[-2]:.1f}%")

        # Create charts
        # GDP Growth Chart
        fig_gdp = px.line(gdp_growth, 
                         title='GDP Growth Rate (Quarterly)',
                         labels={'value': 'Growth Rate (%)', 'index': 'Date', 'variable': ''})
        fig_gdp.data[0].showlegend = False
        
        # Add base customization
        fig_gdp.update_layout(
            hovermode='x unified',
            yaxis_tickformat='.1f',
            shapes=recession_periods
        )
        st.plotly_chart(fig_gdp, use_container_width=True)

        # Unemployment Rate Chart
        fig_unemployment = px.line(unemployment_rate, 
                                 title='Unemployment Rate (Monthly)',
                                 labels={'value': 'Rate (%)', 'index': 'Date', 'variable': ''})
        fig_unemployment.data[0].showlegend = False
        
        # Add base customization
        fig_unemployment.update_layout(
            hovermode='x unified',
            yaxis_tickformat='.1f',
            shapes=recession_periods
        )
        st.plotly_chart(fig_unemployment, use_container_width=True)

        # Inflation Rate Chart
        fig_inflation = px.line(inflation_rate, 
                              title='Inflation Rate (YoY)',
                              labels={'value': 'Rate (%)', 'index': 'Date', 'variable': ''})
        fig_inflation.data[0].showlegend = False
        
        # Add base customization
        fig_inflation.update_layout(
            hovermode='x unified',
            yaxis_tickformat='.1f',
            shapes=recession_periods
        )
        st.plotly_chart(fig_inflation, use_container_width=True)

        # S&P 500 Returns Section
        
        # Add the 10Y MA Return chart only
        fig_spy_ma = px.line(spy_data[start_date:], # Only plot data from start_date onwards
                             x=spy_data[start_date:].index,
                             y='10Y_MA_Return',
                             title='S&P 500 10-Year Moving Average Annual Return',
                             labels={'10Y_MA_Return': 'Annual Return (%)', 
                                    'index': 'Date'})
        
        # Customize the chart
        fig_spy_ma.update_layout(
            showlegend=False,
            hovermode='x unified',
            yaxis_tickformat='.1f',
            shapes=recession_periods
        )
        
        # Add reference lines
        fig_spy_ma.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_spy_ma.add_hline(y=15, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig_spy_ma, use_container_width=True)


        # ISM Manufacturing PMI Chart
        print("ISM data in session state:", st.session_state['ism_data'] is not None)  # Debug print
        if st.session_state['ism_data'] is not None:
            print(f"ISM data shape: {st.session_state['ism_data'].shape}")  # Debug print
            
            fig_ism = px.line(ism_data, 
                             title='ISM Manufacturing PMI',
                             labels={'value': 'PMI', 'index': 'Date'})
            fig_ism.data[0].showlegend = False
            
            # Debug prints
            print(f"ISM data range: {ism_data.index.min()} to {ism_data.index.max()}")
            print(f"First few rows of ISM data:\n{ism_data.head()}")

            # Filter recession periods to match ISM data timeframe
            filter_start_date = pd.to_datetime(ism_data.index.min())
            filter_end_date = pd.to_datetime(ism_data.index.max())

            # Debug print to verify
            print(f"Start date type: {type(filter_start_date)}")
            print(f"Start date value: {filter_start_date}")

            # Filter recession periods
            filtered_recession_periods = [item for item in recession_periods 
                                        if filter_start_date <= pd.to_datetime(item['x1']) <= filter_end_date]
            
            # Add base customization
            fig_ism.update_layout(
                hovermode='x unified',
                yaxis_tickformat='.1f',
                shapes=filtered_recession_periods,
                xaxis=dict(
                    autorange=True,
                    type='date'
                ),
                yaxis=dict(
                    autorange=True
            ))
            
            # Add reference line at 50 (expansion/contraction threshold)
            fig_ism.add_hline(y=50, line_dash="dash", line_color="red")
            
            st.plotly_chart(fig_ism, use_container_width=True)

        # Simple cycle assessment
        st.subheader("Current Macro Outlook")
        st.markdown("""
        *Analysis by Keeeeeyoti  
        Last Updated: December 2024*
        """)
        
        # Simple rule-based assessment
        latest_gdp = gdp_growth.iloc[-1]
        latest_unemployment = unemployment_rate.iloc[-1]
        latest_inflation = inflation_rate.iloc[-1]
        
        if latest_gdp > 2 and latest_unemployment < 5:
            cycle_stage = "Expansion/Peak"
            color = "green"
        elif latest_gdp < 0:
            cycle_stage = "Recession"
            color = "red"
        elif latest_gdp > 0 and latest_unemployment > 5:
            cycle_stage = "Early Recovery"
            color = "yellow"
        else:
            cycle_stage = "Late Cycle"
            color = "orange"
        
        st.markdown(f"**Quick economy health check:** ::{color}[{cycle_stage}]")
        
        # Add explanatory text
        st.markdown("""
        - GDP Growth: {:.1f}% ({})
        - Unemployment: {:.1f}% ({})
        - Inflation: {:.1f}% ({})
        """.format(
            latest_gdp, 
            "Expanding" if latest_gdp > 0 else "Contracting",
            latest_unemployment,
            "High" if latest_unemployment > 5 else "Low",
            latest_inflation,
            "High" if latest_inflation > 2.5 else "Moderate" if latest_inflation > 1.5 else "Low"
        ))

        st.markdown("""
        bullish baby  
        asfdasdf  
        asdfasd
                    
        *Note: This is a simplified analysis and may not capture all economic nuances. For a more comprehensive assessment, consider additional indicators and economic models.*  
        
        """)
        # Notes 
        st.subheader("Notes")
        st.markdown("""
        #### 10 Key Indicators of a Cycle Top

        1. **Excessive Debt** - Debt levels become unsustainable across households, businesses, and governments

        2. **Overvalued Assets** - Asset prices like stocks and real estate detach from fundamentals, driven by speculation

        3. **Tight Monetary Policy** - Central banks raise interest rates and tighten credit to curb overheating

        4. **Rising Inflation** - Persistent inflation above target levels strains growth and profitability

        5. **Market Euphoria** - Overconfidence and speculative frenzy dominate with "this time is different" narratives

        6. **Wealth Inequality** - Widening gaps in wealth fuel political and social tensions, impacting stability

        7. **Overheating Sectors** - Overinvestment leads to excess capacity or bubbles in key industries

        8. **Geopolitical Risks** - Trade wars, political unrest, or global tensions disrupt economic stability

        9. **Productivity Stagnation** - Growth relies on debt and speculation instead of real productivity gains

        10. **Credit Contraction** - Slowing credit growth, rising defaults, and tighter lending signal the cycle's peak

        """)


except Exception as e:
    st.error(f"Error fetching data: {str(e)}") 