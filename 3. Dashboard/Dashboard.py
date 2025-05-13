import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

#  Streamlit page config
st.set_page_config(layout="wide", page_title="E-Commerce Dashboard", page_icon="📊")
st.title("📊 E-Commerce Analytics Dashboard")

#  Loading Data
@st.cache_data
def load_data():
    df = pd.read_excel('../1. Data/Online Retail.xlsx', engine='openpyxl')
    
    # Data Cleaning
    df = df.dropna(subset=['Description'])
    df = df[df['UnitPrice'] > 0]
    
    keywords = ['sample', 'AMAZON fee', 'postage', 'charges', 'manual', 'amazon', 'cruk', 'adjust','Discount']
    df = df[~df['Description'].str.contains('|'.join(keywords), case=False)]
    
    df.drop_duplicates(subset=['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID'], inplace=True)
    
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    df['Date'] = df['InvoiceDate'].dt.date
    df['Year'] = df['InvoiceDate'].dt.year
    df['Quarter'] = df['InvoiceDate'].dt.quarter
    df['Month'] = df['InvoiceDate'].dt.month
    df['WeekDay'] = df['InvoiceDate'].dt.day_name()
    df['Hour'] = df['InvoiceDate'].dt.hour
    
    df.dropna(subset=['CustomerID'], inplace=True)
    
    return df

df = load_data()

# Data Preparation for Analysis  
def prepare_data(df):
    # Revenue by Year
    revenue_by_year = df.groupby('Year')['Revenue'].sum().reset_index()
    
    # Top 10 Products by Quantity
    top_10_products = df[df['Quantity'] > 0].groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(10).reset_index()
    
    # Revenue by Country
    revenue_by_country = df.groupby('Country')['Revenue'].sum().sort_values(ascending=False).reset_index()
    
    # Customer Segmentation (RFM)
    last_date = df['InvoiceDate'].max()
    rfm = df.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (last_date - x.max()).days,
        'InvoiceNo': 'nunique',
        'Revenue': 'sum'
    }).reset_index().rename(columns={'InvoiceDate':'Recency', 'InvoiceNo':'Frequency', 'Revenue':'Monetary'})
    
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    rfm[['R_Score', 'F_Score', 'M_Score']] = rfm[['R_Score', 'F_Score', 'M_Score']].astype(int)
    rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
    
    # Returns Analysis
    returns_df = df[df['Quantity'] < 0].copy()
    returns_df["ReturnValue"] = returns_df["Quantity"] * returns_df["UnitPrice"]
    monthly_returns = returns_df.resample('ME', on='InvoiceDate').sum(numeric_only=True)['ReturnValue'].reset_index()
    top_returned_products = returns_df.groupby('Description')['Quantity'].sum().sort_values().head(10).reset_index()
    
    return {
        'revenue_by_year': revenue_by_year,
        'top_10_products': top_10_products,
        'revenue_by_country': revenue_by_country,
        'rfm': rfm,
        'monthly_returns': monthly_returns,
        'top_returned_products': top_returned_products
    }

data = prepare_data(df)



# Navigation sidebar
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", ["Overview", "Customer Analysis", "Product Analysis", "Market Analysis", "Billing & Returns"])

if section == "Overview":
    st.header("Overview Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Revenue by Year")
        fig = px.bar(data['revenue_by_year'], x='Year', y='Revenue', 
                     color='Revenue', text='Revenue',
                     labels={'Revenue': 'Total Revenue'})
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Top 10 Products by Quantity Sold")
        fig = px.bar(data['top_10_products'], x='Description', y='Quantity', 
                     color='Quantity', text='Quantity',
                     labels={'Quantity': 'Quantity Sold'})
        fig.update_layout(xaxis_title="Product", yaxis_title="Quantity Sold")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Data Sample")
    st.dataframe(df.head(10))

elif section == "Customer Analysis":
    st.header("Customer Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Segmentation (RFM)")
        fig = px.scatter(data['rfm'], x='Frequency', y='Monetary', color='Recency',
                         size='RFM_Score', hover_data=['CustomerID'],
                         labels={'Frequency': 'Frequency', 'Monetary': 'Monetary Value', 'Recency': 'Recency'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("RFM Score Distribution")
        fig = px.histogram(data['rfm'], x='RFM_Score', nbins=20,
                          labels={'RFM_Score': 'RFM Score'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Top Customers by Revenue")
    top_customers = data['rfm'].sort_values('Monetary', ascending=False).head(10)
    st.dataframe(top_customers)

elif section == "Product Analysis":
    st.header("Product Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Products by Revenue")
        top_products_revenue = df.groupby('Description')['Revenue'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_products_revenue, x='Description', y='Revenue', 
                     color='Revenue', text='Revenue',
                     labels={'Revenue': 'Total Revenue'})
        fig.update_layout(xaxis_title="Product", yaxis_title="Revenue")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Product Price Distribution")
        fig = px.box(df, y='UnitPrice', points=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Product Sales Over Time")
    product_sales_time = df.groupby(['Date', 'Description'])['Quantity'].sum().reset_index()
    top_products = product_sales_time.groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(5).index
    
    fig = px.line(product_sales_time[product_sales_time['Description'].isin(top_products)], 
                  x='Date', y='Quantity', color='Description',
                  labels={'Quantity': 'Quantity Sold', 'Date': 'Date'})
    st.plotly_chart(fig, use_container_width=True)

elif section == "Market Analysis":
    st.header("Market Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue by Country")
        fig = px.bar(data['revenue_by_country'].head(10), x='Country', y='Revenue', 
                     color='Revenue', text='Revenue',
                     labels={'Revenue': 'Total Revenue'})
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig.update_layout(xaxis_title="Country", yaxis_title="Revenue")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Quantity Sold by Country")
        quantity_by_country = df.groupby('Country')['Quantity'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.pie(quantity_by_country, values='Quantity', names='Country',
                     labels={'Quantity': 'Quantity Sold'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Average Invoice Revenue by Country")
    invoice_revenue = df.groupby(['Country', 'InvoiceNo'])['Revenue'].sum().reset_index()
    avg_invoice_revenue = invoice_revenue.groupby('Country')['Revenue'].mean().sort_values(ascending=False).reset_index().head(10)
    
    fig = px.bar(avg_invoice_revenue, x='Country', y='Revenue', 
                 color='Revenue', text='Revenue',
                 labels={'Revenue': 'Average Revenue per Invoice'})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(xaxis_title="Country", yaxis_title="Average Revenue")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

elif section == "Billing & Returns":
    st.header("Billing & Returns Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Returns Value")
        fig = px.line(data['monthly_returns'], x='InvoiceDate', y='ReturnValue',
                      labels={'ReturnValue': 'Return Value', 'InvoiceDate': 'Month'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Returned Products")
        fig = px.bar(data['top_returned_products'], x='Description', y='Quantity', 
                     color='Quantity', text='Quantity',
                     labels={'Quantity': 'Quantity Returned'})
        fig.update_layout(xaxis_title="Product", yaxis_title="Quantity Returned")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Invoice Analysis")
    invoice_amount = df.groupby('InvoiceNo')['Revenue'].sum().reset_index().rename(columns={'Revenue': 'amount'})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Invoices", invoice_amount.shape[0])
    
    with col2:
        st.metric("Average Invoice Amount", f"${invoice_amount['amount'].mean():,.2f}")
    
    fig = px.histogram(invoice_amount, x='amount', nbins=50,
                      labels={'amount': 'Invoice Amount'})
    st.plotly_chart(fig, use_container_width=True)

# Page Footer 
st.sidebar.markdown("---")
st.sidebar.markdown("Built with Streamlit")
st.sidebar.markdown("Data Source: Online Retail Dataset")