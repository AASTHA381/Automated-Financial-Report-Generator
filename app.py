import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from financial_report import FinancialReportGenerator, create_sample_data_variations
from gpt_summary import GPTFinancialAnalyzer, generate_basic_summary
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Automated Financial Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Main title
    st.markdown('<h1 class="main-header">📊 Automated Financial Report Generator</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key (Optional)", 
            type="password",
            help="Enter your OpenAI API key for GPT-4 powered insights"
        )
        
        # Analysis options
        st.subheader("📈 Analysis Options")
        show_visualizations = st.checkbox("Show Visualizations", value=True)
        show_sector_analysis = st.checkbox("Sector Analysis", value=True)
        show_risk_assessment = st.checkbox("Risk Assessment", value=True)
        show_gpt_insights = st.checkbox("GPT-4 Insights", value=bool(api_key))
        
        # Sample data options
        st.subheader("🔧 Sample Data")
        if st.button("Load Sample Data"):
            st.session_state.use_sample = True
        
        if st.button("Load Tech Companies"):
            st.session_state.use_tech_sample = True
            
        if st.button("Load Mixed Sectors"):
            st.session_state.use_mixed_sample = True

    # Initialize the financial report generator
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = FinancialReportGenerator()
    
    # File upload section
    st.header("📤 Data Upload")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Financial Data (CSV)", 
            type=["csv"],
            help="Upload a CSV file with columns: Company, Date, Revenue, Expenses, Net_Income"
        )
    
    with col2:
        st.info("""
        **Required CSV Columns:**
        - Company
        - Revenue  
        - Expenses
        - Net_Income
        
        **Optional:**
        - Date
        - Sector
        - Market_Cap
        """)
    
    # Handle data loading
    data_loaded = False
    df = None
    
    # Check for sample data requests
    if st.session_state.get('use_sample', False):
        df = pd.read_csv('data/sample_edgar.csv')
        data_loaded = True
        st.success("✅ Sample data loaded successfully!")
        st.session_state.use_sample = False
    
    elif st.session_state.get('use_tech_sample', False):
        tech_data, _ = create_sample_data_variations()
        df = pd.DataFrame(tech_data)
        data_loaded = True
        st.success("✅ Technology companies sample data loaded!")
        st.session_state.use_tech_sample = False
    
    elif st.session_state.get('use_mixed_sample', False):
        _, mixed_data = create_sample_data_variations()
        df = pd.DataFrame(mixed_data)
        data_loaded = True
        st.success("✅ Mixed sectors sample data loaded!")
        st.session_state.use_mixed_sample = False
    
    elif uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            data_loaded = True
            st.success("✅ Data uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    # Main analysis section
    if data_loaded and df is not None:
        
        # Load data into report generator
        try:
            # Save temporarily for the report generator
            temp_path = "temp_data.csv"
            df.to_csv(temp_path, index=False)
            st.session_state.report_generator.load_data(temp_path)
            os.remove(temp_path)  # Clean up
            
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            return
        
        # Display raw data
        st.header("📋 Raw Data Preview")
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(df, use_container_width=True)
            st.info(f"Dataset contains {len(df)} companies with {len(df.columns)} metrics")
        
        # Generate basic report
        st.header("📊 Financial Analysis Dashboard")
        
        try:
            # Basic financial metrics
            basic_report = st.session_state.report_generator.generate_basic_report()
            
            # Display key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Revenue",
                    value=f"${basic_report['total_revenue']:,.0f}",
                    delta=f"{basic_report['total_companies']} companies"
                )
            
            with col2:
                st.metric(
                    label="Total Net Income", 
                    value=f"${basic_report['total_net_income']:,.0f}",
                    delta=f"{basic_report['profit_margin_avg']:.1f}% avg margin"
                )
            
            with col3:
                st.metric(
                    label="Average Revenue",
                    value=f"${basic_report['average_revenue']:,.0f}",
                    delta=f"per company"
                )
            
            with col4:
                st.metric(
                    label="Expense Ratio",
                    value=f"{basic_report['expense_ratio_avg']:.1f}%",
                    delta="of revenue"
                )
            
            # Company insights
            st.subheader("🏢 Company Performance Analysis")
            company_insights = st.session_state.report_generator.get_company_insights()
            
            # Display top performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Top Companies by Revenue:**")
                top_revenue = company_insights.nlargest(5, 'Revenue_sum')[
                    ['Company', 'Revenue_sum', 'Profit_Margin']
                ]
                st.dataframe(top_revenue, use_container_width=True)
            
            with col2:
                st.write("**Most Profitable Companies:**")
                top_profit = company_insights.nlargest(5, 'Profit_Margin')[
                    ['Company', 'Net_Income_sum', 'Profit_Margin']
                ]
                st.dataframe(top_profit, use_container_width=True)
            
            # Sector analysis (if sector data available)
            if show_sector_analysis and 'Sector' in df.columns:
                st.subheader("🏭 Sector Analysis")
                sector_analysis = st.session_state.report_generator.get_sector_analysis()
                
                if not sector_analysis.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Sector revenue pie chart
                        fig_pie = px.pie(
                            sector_analysis, 
                            values='Revenue_sum', 
                            names='Sector',
                            title='Revenue Distribution by Sector'
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Sector profitability bar chart
                        fig_bar = px.bar(
                            sector_analysis,
                            x='Sector',
                            y='Avg_Profit_Margin',
                            title='Average Profit Margin by Sector',
                            color='Avg_Profit_Margin',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    st.dataframe(sector_analysis, use_container_width=True)
            
            # Visualizations
            if show_visualizations:
                st.subheader("📈 Financial Visualizations")
                
                # Revenue vs Net Income scatter plot
                fig_scatter = px.scatter(
                    df,
                    x='Revenue',
                    y='Net_Income',
                    color='Sector' if 'Sector' in df.columns else None,
                    size='Market_Cap' if 'Market_Cap' in df.columns else None,
                    hover_data=['Company'],
                    title='Revenue vs Net Income Analysis',
                    labels={'Revenue': 'Revenue ($)', 'Net_Income': 'Net Income ($)'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Top companies bar chart
                top_10 = df.nlargest(10, 'Revenue')
                fig_bar = px.bar(
                    top_10,
                    x='Company',
                    y=['Revenue', 'Expenses', 'Net_Income'],
                    title='Top 10 Companies - Financial Breakdown',
                    barmode='group'
                )
                fig_bar.update_xaxes(tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Risk Assessment
            if show_risk_assessment:
                st.subheader("⚠️ Risk Assessment")
                risk_data = st.session_state.report_generator.generate_risk_assessment()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "High Debt Companies",
                        risk_data['high_debt_companies'],
                        delta="Companies with debt ratio > 80%"
                    )
                
                with col2:
                    st.metric(
                        "Low Margin Companies", 
                        risk_data['low_profit_margin_companies'],
                        delta="Companies with margin < 5%"
                    )
                
                with col3:
                    st.metric(
                        "Average Volatility",
                        f"{risk_data['average_volatility']:.2f}",
                        delta="Risk score"
                    )
                
                if risk_data['companies_at_risk']:
                    st.warning(f"⚠️ **Companies requiring attention:** {', '.join(risk_data['companies_at_risk'])}")
            
            # GPT-4 Analysis Section
            if show_gpt_insights and api_key:
                st.header("🤖 AI-Powered Financial Insights")
                
                with st.spinner("Generating GPT-4 analysis..."):
                    gpt_analyzer = GPTFinancialAnalyzer(api_key)
                    
                    # Prepare data for GPT analysis
                    analysis_data = {
                        'basic_report': basic_report,
                        'company_insights': company_insights.to_dict('records'),
                        'risk_assessment': risk_data
                    }
                    
                    # Add sector analysis if available
                    if show_sector_analysis and 'Sector' in df.columns:
                        sector_analysis = st.session_state.report_generator.get_sector_analysis()
                        if not sector_analysis.empty:
                            analysis_data['sector_analysis'] = sector_analysis.to_dict('records')
                    
                    # Add top performers
                    top_performers = st.session_state.report_generator.identify_top_performers()
                    analysis_data['top_performers'] = top_performers.to_dict('records')
                    
                    # Generate comprehensive GPT report
                    gpt_report = gpt_analyzer.create_comprehensive_report(analysis_data)
                    
                    # Display GPT insights in tabs
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "Executive Summary", 
                        "Company Analysis", 
                        "Sector Insights", 
                        "Risk Analysis", 
                        "Investment Recommendations"
                    ])
                    
                    with tab1:
                        if 'executive_summary' in gpt_report:
                            st.markdown(f'<div class="success-box">{gpt_report["executive_summary"]}</div>', 
                                      unsafe_allow_html=True)
                    
                    with tab2:
                        if 'company_analysis' in gpt_report:
                            st.write(gpt_report['company_analysis'])
                    
                    with tab3:
                        if 'sector_insights' in gpt_report:
                            st.write(gpt_report['sector_insights'])
                    
                    with tab4:
                        if 'risk_analysis' in gpt_report:
                            st.markdown(f'<div class="warning-box">{gpt_report["risk_analysis"]}</div>', 
                                      unsafe_allow_html=True)
                    
                    with tab5:
                        if 'investment_recommendations' in gpt_report:
                            st.write(gpt_report['investment_recommendations'])
            
            elif show_gpt_insights and not api_key:
                st.header("💡 Basic Financial Summary")
                basic_summary = generate_basic_summary(basic_report)
                st.text(basic_summary)
                st.info("💡 Enter your OpenAI API key in the sidebar for AI-powered insights!")
            
            # Export options
            st.header("📁 Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Download Company Report"):
                    csv = company_insights.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"company_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if show_sector_analysis and 'Sector' in df.columns:
                    if st.button("🏭 Download Sector Analysis"):
                        sector_csv = sector_analysis.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=sector_csv,
                            file_name=f"sector_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
            
            with col3:
                if st.button("📈 Download Full Report"):
                    # Create comprehensive report
                    full_report = {
                        "Summary": basic_report,
                        "Companies": company_insights.to_dict('records'),
                        "Risk_Assessment": risk_data
                    }
                    
                    import json
                    report_json = json.dumps(full_report, indent=2, default=str)
                    st.download_button(
                        label="Download JSON",
                        data=report_json,
                        file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                        
        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
            st.info("Please ensure your data has the required columns: Company, Revenue, Expenses, Net_Income")
    
    else:
        # Welcome message and instructions
        st.info("""
        👋 **Welcome to the Automated Financial Report Generator!**
        
        **Getting Started:**
        1. Upload a CSV file with your financial data, or
        2. Use one of the sample datasets from the sidebar
        3. Configure analysis options in the sidebar
        4. Optionally add your OpenAI API key for AI-powered insights
        
        **Sample Data Available:**
        - 📊 **Sample Data**: Fortune 500 companies with comprehensive metrics
        - 💻 **Tech Companies**: Technology sector focused dataset  
        - 🏭 **Mixed Sectors**: Diverse sectors including some loss-making companies
        """)
        
        # Display sample data format
        with st.expander("📋 Expected CSV Format", expanded=False):
            sample_format = pd.DataFrame({
                'Company': ['Apple Inc', 'Microsoft Corp', 'Amazon.com Inc'],
                'Date': ['2024-03-31', '2024-03-31', '2024-03-31'],
                'Revenue': [123000000000, 61900000000, 143300000000],
                'Expenses': [95000000000, 45100000000, 135200000000],
                'Net_Income': [28000000000, 16800000000, 8100000000],
                'Sector': ['Technology', 'Technology', 'E-commerce'],
                'Market_Cap': [2800000000000, 2900000000000, 1600000000000]
            })
            st.dataframe(sample_format, use_container_width=True)
            st.caption("Required: Company, Revenue, Expenses, Net_Income | Optional: Date, Sector, Market_Cap")

if __name__ == "__main__":
    main()