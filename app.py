import yfinance as yf
import streamlit as st
import pandas as pd

class CalculateMetric:
    def __init__(self, symbol: str):
        self.ticker = yf.Ticker(symbol)

        # Get financial statements and info
        balance_sheet = self.ticker.balance_sheet
        income_statement = self.ticker.financials
        cash_flow = self.ticker.cashflow

        # Transpose the DataFrames to have dates as rows
        balance_sheet = balance_sheet.T
        income_statement = income_statement.T
        cash_flow = cash_flow.T

        # Sort the DataFrames by date in descending order
        self.balance_sheet = balance_sheet.sort_index(ascending=False)
        self.income_statement = income_statement.sort_index(ascending=False)
        self.cash_flow = cash_flow.sort_index(ascending=False)

        self.z_weightage = 0.6
        self.f_weightage = 0.4

    def calculate_F_Score(self) -> int:
        latest = 0
        previous = 1

        # Criterion 1: Positive Net Income
        net_income_latest = self.income_statement["Net Income"].iloc[latest]
        net_income_prev = self.income_statement["Net Income"].iloc[previous]
        c1 = 1 if net_income_latest > 0 and net_income_latest > net_income_prev else 0

        # Criterion 2: Positive Operating Cash Flow
        op_cash_flow_latest = self.cash_flow["Operating Cash Flow"].iloc[latest]
        c2 = 1 if op_cash_flow_latest > 0 else 0

        # Criterion 3: Return on Assets improving
        total_assets_latest = self.balance_sheet["Total Assets"].iloc[latest]
        total_assets_prev = self.balance_sheet["Total Assets"].iloc[previous]
        roa_latest = (
            net_income_latest / total_assets_latest if total_assets_latest != 0 else 0
        )
        roa_prev = net_income_prev / total_assets_prev if total_assets_prev != 0 else 0
        c3 = 1 if roa_latest > roa_prev else 0

        # Criterion 4: Quality of Earnings
        c4 = 1 if op_cash_flow_latest > net_income_latest else 0

        # Criterion 5: No New Debt or Debt Reduction
        long_term_debt_latest = self.balance_sheet["Long Term Debt"].iloc[latest]
        long_term_debt_prev = self.balance_sheet["Long Term Debt"].iloc[previous]
        c5 = 1 if long_term_debt_latest <= long_term_debt_prev else 0

        # Criterion 6: Improvement in Current Ratio
        current_assets_latest = self.balance_sheet["Current Assets"].iloc[latest]
        current_liabilities_latest = self.balance_sheet["Current Liabilities"].iloc[
            latest
        ]
        current_ratio_latest = (
            current_assets_latest / current_liabilities_latest
            if current_liabilities_latest != 0
            else 0
        )
        current_assets_prev = self.balance_sheet["Current Assets"].iloc[previous]
        current_liabilities_prev = self.balance_sheet["Current Liabilities"].iloc[
            previous
        ]
        current_ratio_prev = (
            current_assets_prev / current_liabilities_prev
            if current_liabilities_prev != 0
            else 0
        )
        c6 = 1 if current_ratio_latest > current_ratio_prev else 0

        # Criterion 7: No New Shares Issued
        shares_outstanding_latest = self.balance_sheet["Common Stock"].iloc[latest]
        shares_outstanding_prev = self.balance_sheet["Common Stock"].iloc[previous]
        c7 = 1 if shares_outstanding_latest <= shares_outstanding_prev else 0

        # Criterion 8: Improvement in Gross Margin
        gross_profit_latest = self.income_statement["Gross Profit"].iloc[latest]
        total_revenue_latest = self.income_statement["Total Revenue"].iloc[latest]
        gross_margin_latest = (
            gross_profit_latest / total_revenue_latest
            if total_revenue_latest != 0
            else 0
        )
        gross_profit_prev = self.income_statement["Gross Profit"].iloc[previous]
        total_revenue_prev = self.income_statement["Total Revenue"].iloc[previous]
        gross_margin_prev = (
            gross_profit_prev / total_revenue_prev if total_revenue_prev != 0 else 0
        )
        c8 = 1 if gross_margin_latest > gross_margin_prev else 0

        # Criterion 9: Improvement in Asset Turnover
        total_revenue_prev = self.income_statement["Total Revenue"].iloc[previous]
        total_assets_prev = self.balance_sheet["Total Assets"].iloc[previous]
        asset_turnover_latest = (
            total_revenue_latest / total_assets_latest
            if total_assets_latest != 0
            else 0
        )
        asset_turnover_prev = (
            total_revenue_prev / total_assets_prev if total_assets_prev != 0 else 0
        )
        c9 = 1 if asset_turnover_latest > asset_turnover_prev else 0

        # Calculate Piotroski F-Score
        f_score = c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9

        return f_score

    def calculate_altman_z_score(self) -> float:
        info = self.ticker.info

        current_assets = self.balance_sheet["Current Assets"].iloc[0] / 1000000
        current_liabilities = (
            self.balance_sheet["Current Liabilities"].iloc[0] / 1000000
        )
        total_assets = self.balance_sheet["Total Assets"].iloc[0] / 1000000
        retained_earnings = self.balance_sheet["Retained Earnings"].iloc[0] / 1000000
        ebit = self.income_statement["EBIT"].iloc[0] / 1000000
        sales = self.income_statement["Total Revenue"].iloc[0] / 1000000
        market_cap = info["marketCap"] / 1000000
        total_liabilities = (
            self.balance_sheet["Total Liabilities Net Minority Interest"].iloc[0]
            / 1000000
        )

        X1 = (current_assets - current_liabilities) / total_assets
        X2 = retained_earnings / total_assets
        X3 = ebit / total_assets
        X4 = market_cap / total_liabilities
        X5 = sales / total_assets

        # Calculate Altman Z-Score for non-manufacturing firms
        Z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3 + 0.6 * X4 + 1.0 * X5

        return Z

    def health(self):
        try:
            combined_metric = (
                (self.f_weightage * self.calculate_F_Score())
                + (self.z_weightage * self.calculate_altman_z_score())
            )
        except:
            return "Error: Unable to calculate metrics", 0, False
        is_investable = False

        if combined_metric >= 7:
            is_investable = True
            message = "The company's fundamentals are Extremely Strong"
            return message, combined_metric, is_investable
        elif combined_metric >=4:
            is_investable = True
            message = "The company's fundamentals are Strong"
            return message, combined_metric, is_investable
        else:
            message = "The company's fundamentals are Weak"
            return message, combined_metric, is_investable

st.set_page_config(page_title='Fundler', page_icon='💰')

st.title('Fundler 💰')
st.write('Enter a Yahoo Finance compatible ticker symbol to get investment recommendations based on fundamental analysis.')

ticker_symbol = st.text_input('Enter Ticker Symbol', help='e.g., AAPL for Apple Inc.', value='MSFT')

if st.button('Submit'):
    try:
        calculator = CalculateMetric(ticker_symbol)
        message, score, invest = calculator.health()
        # Display the results
        st.subheader('Analysis Results:')
        st.write(f'**Message:** {message}')
        st.write(f'**Score:** {score:.2f}')
        if invest:
            st.write('**Investment Decision:** Yes, consider investing in this stock.')
        else:
            st.write('**Investment Decision:** No, do not invest in this stock.')
    except Exception as e:
        st.error(f'An error occurred: {e}')

st.write("---")

st.markdown("Made By Adeeb [GitHub](https://github.com/Itachi-Uchiha581)")

st.subheader('Ticker Symbol Naming Conventions for Different Exchanges')


data = {
    "Exchange Name": [
        "Bombay Stock Exchange (BSE)",
        "National Stock Exchange (NSE)",
        "New York Stock Exchange (NYSE)",
        "NASDAQ",
        "London Stock Exchange (LSE)",
        "Tokyo Stock Exchange (TSE)",
        "Hong Kong Stock Exchange (HKEX)",
        "Shanghai Stock Exchange (SSE)",
        "Shenzhen Stock Exchange (SZSE)",
        "Euronext Amsterdam",
        "Euronext Paris",
        "Toronto Stock Exchange (TSX)",
        "Australian Securities Exchange (ASX)",
        "Deutsche Börse Xetra (Frankfurt)",
        "Swiss Exchange (SIX)",
        "Milan Stock Exchange (Borsa Italiana)",
        "Vienna Stock Exchange (WBAG)",
        "Madrid Stock Exchange (BME)",
        "Stockholm Stock Exchange (OMX)",
        "Johannesburg Stock Exchange (JSE)",
        "São Paulo Stock Exchange (B3)",
        "Moscow Exchange (MOEX)",
        "Taiwan Stock Exchange (TWSE)",
        "Korean Stock Exchange (KRX)",
        "OTC Markets (Over-the-Counter, US)",
        "Currency Exchange (Forex)",
        "Cryptocurrencies",
    ],
    "Suffix": [
        ".BO", ".NS", "No Suffix Required", "No Suffix Required", ".L", ".T", ".HK", ".SS", ".SZ", ".AS", ".PA", ".TO",
        ".AX", ".DE", ".SW", ".MI", ".VI", ".MC", ".ST", ".JO", ".SA", ".ME", ".TW",
        ".KS", ".OTC", ".X", ".CRYPTO"
    ],
    "Example Ticker Symbol": [
        "RELIANCE.BO, TCS.BO",
        "RELIANCE.NS, TCS.NS",
        "AAPL, MSFT",
        "GOOGL, TSLA",
        "HSBA.L, RIO.L",
        "7203.T (Toyota), 6758.T (Sony)",
        "0005.HK (HSBC), 0700.HK (Tencent)",
        "600519.SS (Kweichow Moutai)",
        "000001.SZ (Ping An Bank)",
        "ADYEN.AS, PHIA.AS",
        "BNP.PA, AIR.PA",
        "RY.TO, TD.TO",
        "BHP.AX, CBA.AX",
        "DBK.DE (Deutsche Bank), SAP.DE",
        "NESN.SW, UBSG.SW",
        "ENEL.MI, ISP.MI",
        "EBS.VI, ANDR.VI",
        "SAN.MC, IBE.MC",
        "ERIC.ST, VOLV.ST",
        "NPN.JO, AGL.JO",
        "PETR4.SA, VALE3.SA",
        "GAZP.ME, SBER.ME",
        "2330.TW (TSMC), 2303.TW",
        "005930.KS (Samsung), 000660.KS",
        "TCEHY.OTC, BABA.OTC",
        "USDINR=X, EURUSD=X",
        "BTC-USD, ETH-USD"
    ],
}


exchange_df = pd.DataFrame(data)

# Display the table
st.table(exchange_df)