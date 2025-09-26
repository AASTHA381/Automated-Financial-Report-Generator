import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

# Optional imports with fallbacks
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

class FinancialReportGenerator:
    """
    A comprehensive financial report generator for SEC filing data analysis.
    """
    
    def __init__(self):
        self.data = None
        self.report_summary = {}
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load financial data from CSV file."""
        try:
            self.data = pd.read_csv(filepath)
            # Clean column names
            self.data.columns = self.data.columns.str.strip()
            # Convert Date column to datetime if exists
            if 'Date' in self.data.columns:
                self.data['Date'] = pd.to_datetime(self.data['Date'])
            return self.data
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def generate_basic_report(self) -> Dict:
        """Generate basic financial metrics summary."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        # Calculate basic metrics
        summary = {
            "total_companies": self.data['Company'].nunique(),
            "total_revenue": self.data['Revenue'].sum(),
            "total_expenses": self.data['Expenses'].sum(),
            "total_net_income": self.data['Net_Income'].sum(),
            "average_revenue": self.data['Revenue'].mean(),
            "average_expenses": self.data['Expenses'].mean(),
            "average_net_income": self.data['Net_Income'].mean(),
            "revenue_std": self.data['Revenue'].std(),
            "profit_margin_avg": (self.data['Net_Income'] / self.data['Revenue']).mean() * 100,
            "expense_ratio_avg": (self.data['Expenses'] / self.data['Revenue']).mean() * 100
        }
        
        # Add market cap analysis if available
        if 'Market_Cap' in self.data.columns:
            summary.update({
                "total_market_cap": self.data['Market_Cap'].sum(),
                "average_market_cap": self.data['Market_Cap'].mean(),
                "market_cap_std": self.data['Market_Cap'].std()
            })
        
        self.report_summary = summary
        return summary
    
    def get_company_insights(self) -> pd.DataFrame:
        """Generate detailed company-wise financial insights."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        # Group by company and calculate metrics
        company_metrics = self.data.groupby('Company').agg({
            'Revenue': ['sum', 'mean'],
            'Expenses': ['sum', 'mean'], 
            'Net_Income': ['sum', 'mean'],
            'Market_Cap': 'mean' if 'Market_Cap' in self.data.columns else lambda x: 0
        }).round(2)
        
        # Flatten column names
        company_metrics.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in company_metrics.columns.values]
        
        # Calculate additional metrics
        company_metrics['Profit_Margin'] = (
            company_metrics['Net_Income_sum'] / company_metrics['Revenue_sum'] * 100
        ).round(2)
        
        company_metrics['Expense_Ratio'] = (
            company_metrics['Expenses_sum'] / company_metrics['Revenue_sum'] * 100
        ).round(2)
        
        return company_metrics.reset_index()
    
    def get_sector_analysis(self) -> pd.DataFrame:
        """Analyze financial performance by sector."""
        if self.data is None or 'Sector' not in self.data.columns:
            return pd.DataFrame()
        
        sector_analysis = self.data.groupby('Sector').agg({
            'Revenue': ['sum', 'mean', 'count'],
            'Net_Income': ['sum', 'mean'],
            'Market_Cap': 'sum' if 'Market_Cap' in self.data.columns else lambda x: 0
        }).round(2)
        
        # Flatten column names
        sector_analysis.columns = ['_'.join(col).strip() 
                                 for col in sector_analysis.columns.values]
        
        # Calculate sector profit margins
        sector_analysis['Avg_Profit_Margin'] = (
            sector_analysis['Net_Income_sum'] / sector_analysis['Revenue_sum'] * 100
        ).round(2)
        
        return sector_analysis.reset_index()
    
    def identify_top_performers(self, metric: str = 'Net_Income', top_n: int = 5) -> pd.DataFrame:
        """Identify top performing companies based on specified metric."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        if metric not in self.data.columns:
            raise ValueError(f"Metric '{metric}' not found in data columns.")
        
        top_performers = self.data.nlargest(top_n, metric)[
            ['Company', 'Revenue', 'Expenses', 'Net_Income', 'Sector']
        ]
        
        # Add profit margin calculation
        top_performers['Profit_Margin'] = (
            top_performers['Net_Income'] / top_performers['Revenue'] * 100
        ).round(2)
        
        return top_performers
    
    def generate_risk_assessment(self) -> Dict:
        """Generate risk assessment based on financial ratios."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        # Calculate risk metrics
        self.data['Debt_to_Revenue'] = self.data['Expenses'] / self.data['Revenue']
        self.data['Volatility_Score'] = (
            abs(self.data['Net_Income'] - self.data['Net_Income'].mean()) / 
            self.data['Net_Income'].std()
        )
        
        risk_assessment = {
            "high_debt_companies": len(self.data[self.data['Debt_to_Revenue'] > 0.8]),
            "low_profit_margin_companies": len(
                self.data[(self.data['Net_Income'] / self.data['Revenue']) < 0.05]
            ),
            "average_volatility": self.data['Volatility_Score'].mean(),
            "companies_at_risk": self.data[
                (self.data['Debt_to_Revenue'] > 0.8) | 
                ((self.data['Net_Income'] / self.data['Revenue']) < 0.05)
            ]['Company'].tolist()
        }
        
        return risk_assessment
    
    def create_visualizations(self) -> Dict:
        """Create various financial visualizations."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        visualizations = {}
        
        if not HAS_PLOTLY:
            return {"error": "Plotly not installed. Install with: pip install plotly"}
        
        # 1. Revenue vs Net Income scatter plot
        fig1 = px.scatter(
            self.data, 
            x='Revenue', 
            y='Net_Income',
            color='Sector' if 'Sector' in self.data.columns else None,
            hover_data=['Company'],
            title='Revenue vs Net Income by Company'
        )
        visualizations['revenue_vs_income'] = fig1
        
        # 2. Sector-wise revenue distribution
        if 'Sector' in self.data.columns:
            fig2 = px.pie(
                self.data, 
                values='Revenue', 
                names='Sector',
                title='Revenue Distribution by Sector'
            )
            visualizations['sector_revenue_pie'] = fig2
        
        # 3. Company performance bar chart
        top_companies = self.data.nlargest(10, 'Revenue')
        fig3 = px.bar(
            top_companies,
            x='Company',
            y=['Revenue', 'Expenses', 'Net_Income'],
            title='Top 10 Companies by Revenue',
            barmode='group'
        )
        fig3.update_xaxes(tickangle=45)
        visualizations['top_companies_bar'] = fig3
        
        return visualizations

def create_sample_data_variations():
    """Create different sample datasets for testing."""
    
    # Dataset 1: Technology companies
    tech_data = {
        'Company': ['TechCorp A', 'TechCorp B', 'TechCorp C'],
        'Date': ['2024-03-31', '2024-03-31', '2024-03-31'],
        'Revenue': [50000000, 75000000, 120000000],
        'Expenses': [35000000, 55000000, 85000000],
        'Net_Income': [15000000, 20000000, 35000000],
        'Sector': ['Technology', 'Technology', 'Technology'],
        'Market_Cap': [500000000, 800000000, 1200000000]
    }
    
    # Dataset 2: Mixed sectors with some losses
    mixed_data = {
        'Company': ['RetailCorp', 'HealthCorp', 'EnergyCorp', 'StartupCorp'],
        'Date': ['2024-03-31', '2024-03-31', '2024-03-31', '2024-03-31'],
        'Revenue': [25000000, 40000000, 80000000, 5000000],
        'Expenses': [22000000, 35000000, 85000000, 8000000],
        'Net_Income': [3000000, 5000000, -5000000, -3000000],
        'Sector': ['Retail', 'Healthcare', 'Energy', 'Technology'],
        'Market_Cap': [200000000, 450000000, 600000000, 50000000]
    }
    
    return tech_data, mixed_data