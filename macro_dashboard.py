import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from fredapi import Fred
import yfinance as yf
from datetime import datetime, timedelta


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
    
    # Get S&P 500 data
    spy = yf.download('^GSPC', start=start_date-timedelta(days=365*10), end=end_date)
    # Calculate annual returns
    spy['Annual_Return'] = spy['Adj Close'].pct_change(periods=252) * 100
    # Calculate 10-year moving average of annual returns
    spy['10Y_MA_Return'] = spy['Annual_Return'].rolling(window=252*10).mean()
    
    return gdp_pct_change, unemployment, inflation_yoy, spy, recession_periods

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
                gdp_growth, unemployment_rate, inflation_rate, spy_data, recession_periods = get_economic_data(start_date, end_date)
                st.session_state['data_loaded'] = True
                st.session_state['gdp_growth'] = gdp_growth
                st.session_state['unemployment_rate'] = unemployment_rate
                st.session_state['inflation_rate'] = inflation_rate
                st.session_state['spy_data'] = spy_data
                st.session_state['recession_periods'] = recession_periods

    # Use stored data for display if available
    if st.session_state['data_loaded']:
        gdp_growth = st.session_state['gdp_growth']
        unemployment_rate = st.session_state['unemployment_rate']
        inflation_rate = st.session_state['inflation_rate']
        spy_data = st.session_state['spy_data']
        recession_periods = st.session_state['recession_periods']
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

except Exception as e:
    st.error(f"Error fetching data: {str(e)}") 