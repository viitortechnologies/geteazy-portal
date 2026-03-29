import streamlit as st
import pandas as pd
import os
import re
import io
import zipfile
import plotly.express as px
from datetime import timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="GetEazy Admin Portal", layout="wide")

# --- 2. VENDOR COMMISSION DATABASE ---
COMMISSIONS = {
    'IFC Restaurant': 0.06, 'SATTVIC KITCHEN PURE VEG': 0.20, 'Premier Restaurant': 0.10,
    'Sri Geetha Bhavan Udipi Hotel': 0, 'Geetha Bhavan - Armoor': 0.15, 
    'Anu Bakery  & Lassi N Shakes': 0.15, 'Sri Bommarillu Family Restaurant': 0,
    'RUCHI FAST FOOD': 0, 'Mr.360 Drive INN': 0.20, 'Devi 2 Restaurant': 0,
    'Vashishta Biryani & Fast Food': 0, 'Telangana Fast Food': 0.20, 'Anu Fast Food': 0,
    'Chilly\'s Family Restaurant': 0.06, 'Shakes & More': 0.20, 'Varka Sweets & Bakers -  Armr': 0.20,
    'THE SQUARE PIZZA': 0.20, 'Get Eazy Services - Free Delivery': 0.00, 'Varka Sweets & Bakers - Nrml': 0.20,
    'BALAJI CHICKEN PAKODI': 0.10, 'Ruchi Bangalore Bakery - Perkit': 0.20, 'HOTEL MAYURI INN': 0.15,
    'KFC Armr': 0, 'Get Eazy Services - NRML': 0.00, 'Land Mark Family Restaurant': 0.20, 
    'RAMBABU’S BIRYANI': 0.10, 'Madina Milk Center - Old Bus Stand': 0, 'Yaseen Hotel Perkit.': 0.25, 
    'Vijay Fast Food Center': 0.20, 'Evening snacks - Armr': 0, 'Hyderabadi Biryani House': 0.05, 
    'Shree Shawarma Spot': 0.05, 'FARMER\'S MILK CENTRE': 0, 'CREAMY CREATIONS': 0.15, 
    'Delhi Wala Sweets': 0, 'Belgian Waffle': 0, 'SVR Fast Food Corner': 0, 'DOLPHIN BANGALORE BAKERY':0.20,
    'Shri Balaji Sweets & Bakers':0.10, 'Fusion Bakers': 0, 'Nakshatra Biryani House - Armr': 0, 
    'Kavya Mess': 0.10, 'RR Fast Food Center - NRML': 0.20, 'Red Bucket Biryani - NRML': 0, 
    'RED CHILLI\'S Fast Food & Biryani': 0.20, 'Palletoori Vantillu': 0.20, 'Janardhan Tiffins': 0.00, 
    'Medicine Delivery Services - Armoor': 0.00, 'Vijay Tiffin\'s Centre': 0.20, 'Meena Tiffin Center - Armr': 0, 
    'Ganesh Tiffin Center - Armoor': 0, 'Meena Tiffin Center - NRML': 0, 'New Xpress Tiffins - Mrng Only': 0, 
    'Trishakti Restaurant': 0.20, 'Devi Family Restaurant': 0, 'Sri Durga Bhavani Mess': 0.10, 
    'RFC Cloud Kitchen': 0, 'Sagar Fast Food': 0.10, 'SS FAST FOOD': 0.15, 'Chat & Pani Puri': 0,
    'DOLPHIN BANGALORE BAKERY': 0.20, 'Happiness 365 Bakery': 0.20, 'Thirumala Ice Cream Parlor': 0,
    'Lucky Fast Food': 0.10, 'MR PAPAYA IMBF RESTAURANT': 0.10, 'Bhagyalaxmi Milks - Old Bus stand': 0,
    'YOGINI TIFFIN CENTRE': 0, 'Hotel PVR': 0.10, 'ROYAL ARABIAN MANDI': 0,
    'Sri Bhagyalaxmi Bamboo Restaurant': 0, 'Nandini Tiffin Center': 0,
    'Arun Ice Creams - Hapdaily - ARMR': 0, 'IFC Fried Chicken and Fast Food': 0, 
    'Jalalpur Dairy': 0, 'Sri Aadhaya Family Restaurant': 0.15, 'Sri Sathya Sai Super Market': 0,
    'SWA PARADISE FAMILY RESTAURANT': 0.10, 'Gismath Mandi and Restaurant': 0.06, 
    'Viyyalavaari Vindu - Tiffins':0.20,'Viyyalavaari Vindu':0.20,'ARMOOR CHICKEN PAKODI':0.20,
    'RR Frankeee': 0.20, 'Prakruthi Organic Cafe': 0.10, 'Manpreet Punjabi Dhaba': 0,
    'Pavan Santhosh Family Dhaba': 0.12, 'TG18 Family Restaurant': 0, 'Kritunga Restaurant': 0.05,
    'Devi Home Food': 0.20, 'CHAI CLUB - Milk Shakes': 0, 'Grand Kubera family restaurant': 0,
    'Haleem Day': 0, 'Shawarma Spot Nrml': 0, 'VS Biryani House - Mamidipally': 0.20,
    'Vegetables and Fruits': 0, 'Default': 0.10
}

NORMALIZED_COMM = {k.lower().strip(): v for k, v in COMMISSIONS.items()}

# --- 3. UTILS & PDF CLASS ---
def clean_text(text):
    if not isinstance(text, str): text = str(text)
    return text.replace('’', "'").replace('‘', "'").encode('ascii', 'ignore').decode('ascii')

class SettlementPDF(FPDF):
    def __init__(self, vendor_name, week_str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vendor_name = clean_text(vendor_name)
        self.week_str = week_str
    
    def header(self):
        if os.path.exists('watermark.png'):
            with self.local_context(fill_opacity=0.2):
                self.image('watermark.png', x=55, y=100, w=100)
        if self.page_no() == 1:
            if os.path.exists('logo.png'):
                self.image('logo.png', x=10, y=10, w=50)
            self.set_y(15)
            self.set_font("helvetica", 'B', 15)
            self.cell(0, 8, text=self.vendor_name, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("helvetica", 'I', 10)
            self.cell(0, 5, text=f"Settlement: {self.week_str}", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_y(50)

# --- 4. NAVIGATION ---
st.sidebar.title("🍱 GetEazy Admin")
page = st.sidebar.radio("Navigate", ["Vendor Settlements", "Business Analytics"])

# ---------------------------------------------------------
# PAGE: VENDOR SETTLEMENTS
# ---------------------------------------------------------
if page == "Vendor Settlements":
    st.title("📄 Vendor Settlement Generator")
    st.info("Upload any order excel. It will skip empty rows and generate PDFs + Master Summary.")
    
    up_file = st.file_uploader("Upload orders file", type="xlsx")
    
    if up_file:
        raw_df = pd.read_excel(up_file, header=None)
        h_idx = 0
        for i, row in raw_df.iterrows():
            if 'vendor' in [str(v).lower().strip() for v in row.values]:
                h_idx = i; break
        
        df = pd.read_excel(up_file, skiprows=h_idx)
        df.columns = df.columns.astype(str).str.strip()
        
        df['CreatedAt'] = pd.to_datetime(df['CreatedAt'], dayfirst=True)
        df['TotalPrice'] = pd.to_numeric(df['TotalPrice'], errors='coerce').fillna(0)
        df['Status_L'] = df['Status'].str.lower().str.strip()
        week_str = f"{df['CreatedAt'].min().strftime('%d %b')} - {df['CreatedAt'].max().strftime('%d %b %Y')}"
        
        zip_buffer = io.BytesIO()
        master_data = []

        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for vendor in df['Vendor'].unique():
                if pd.isna(vendor): continue
                v_df = df[df['Vendor'] == vendor]
                delivered_v = v_df[v_df['Status_L'].isin(['delivered', 'success', 'completed'])]
                
                gross = delivered_v['TotalPrice'].sum()
                v_key = str(vendor).lower().strip()
                rate = NORMALIZED_COMM.get(v_key, NORMALIZED_COMM['default'])
                comm_amt = gross * rate
                net = gross - comm_amt
                
                master_data.append({
                    'Vendor': vendor, 'Orders': len(delivered_v),
                    'Gross Revenue': gross, 'Comm %': f"{int(rate*100)}%",
                    'Comm Amount': comm_amt, 'Net Payable': net
                })

                pdf = SettlementPDF(vendor, week_str)
                pdf.add_page()
                pdf.set_font("helvetica", 'B', 8); pdf.set_fill_color(200, 200, 200)
                cols = [25, 20, 55, 10, 25, 25, 30]; h = ['Date', 'OID', 'Item', 'Qty', 'Rate', 'Total', 'Status']
                for i in range(len(h)): pdf.cell(cols[i], 8, text=h[i], border=1, align='C', fill=True)
                pdf.ln()
                
                pdf.set_font("helvetica", size=8)
                for _, r in v_df.iterrows():
                    pdf.set_text_color(255, 0, 0) if 'cancel' in str(r['Status_L']) else pdf.set_text_color(0, 0, 0)
                    pdf.cell(cols[0], 7, text=str(r['CreatedAt'].strftime('%d-%m')), border=1)
                    pdf.cell(cols[1], 7, text=str(r['OID']), border=1)
                    pdf.cell(cols[2], 7, text=clean_text(r['Item'])[:35], border=1)
                    pdf.cell(cols[3], 7, text=str(r['Qty']), border=1, align='C')
                    pdf.cell(cols[4], 7, text=f"{r['Price']:.2f}", border=1, align='R')
                    pdf.cell(cols[5], 7, text=f"{r['TotalPrice']:.2f}", border=1, align='R')
                    pdf.cell(cols[6], 7, text=str(r['Status']), border=1, align='C')
                    pdf.ln()

                pdf.set_text_color(0, 0, 0); pdf.ln(5); pdf.set_font("helvetica", 'B', 10)
                pdf.cell(sum(cols[:5]), 8, text="GROSS TOTAL:", align='R')
                pdf.cell(cols[5], 8, text=f"{gross:.2f}", border=1, align='R', new_y=YPos.NEXT, new_x=XPos.LMARGIN)
                pdf.set_fill_color(255, 204, 204)
                pdf.cell(sum(cols[:5]), 8, text=f"COMMISSION ({int(rate*100)}%):", align='R')
                pdf.cell(cols[5], 8, text=f"-{comm_amt:.2f}", border=1, align='R', fill=True, new_y=YPos.NEXT, new_x=XPos.LMARGIN)
                pdf.set_fill_color(144, 238, 144)
                pdf.cell(sum(cols[:5]), 10, text="NET PAYABLE:", align='R')
                pdf.cell(cols[5], 10, text=f"{net:.2f}", border=1, align='R', fill=True)
                
                zf.writestr(f"PDFs/{clean_text(vendor)}_Settlement.pdf", pdf.output())

            master_df = pd.DataFrame(master_data)
            m_excel = io.BytesIO()
            master_df.to_excel(m_excel, index=False)
            zf.writestr("MASTER_SETTLEMENT_LIST.xlsx", m_excel.getvalue())

        zip_buffer.seek(0)
        st.success("✅ Processed! PDFs and Master List are ready.")
        st.download_button("📥 Download Settlements ZIP", zip_buffer.getvalue(), "GetEazy_Settlements.zip")

# ---------------------------------------------------------
# PAGE: BUSINESS ANALYTICS
# ---------------------------------------------------------
elif page == "Business Analytics":
    st.title("📊 360° Business Intelligence Dashboard")
    ana_file = st.file_uploader("Upload file for analysis", type="xlsx")
    
    if ana_file:
        raw_df = pd.read_excel(ana_file, header=None)
        h_idx = 0
        for i, row in raw_df.iterrows():
            if 'vendor' in [str(v).lower().strip() for v in row.values]:
                h_idx = i; break
        
        df = pd.read_excel(ana_file, skiprows=h_idx)
        df.columns = df.columns.astype(str).str.strip()
        df['CreatedAt'] = pd.to_datetime(df['CreatedAt'], dayfirst=True)
        df['Hour'] = df['CreatedAt'].dt.hour
        df['Day'] = df['CreatedAt'].dt.day_name()
        df['TotalPrice'] = pd.to_numeric(df['TotalPrice'], errors='coerce').fillna(0)
        df['Item Purchase Price'] = pd.to_numeric(df['Item Purchase Price'], errors='coerce').fillna(0)
        df['Status_L'] = df['Status'].str.lower().str.strip()
        
        delivered = df[df['Status_L'].isin(['delivered', 'success', 'completed'])]
        cancelled = df[df['Status_L'].isin(['cancelled', 'cancel', 'failed'])]

        # --- KPI CARDS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Business Revenue", f"₹{delivered['TotalPrice'].sum():,.0f}")
        m2.metric("Orders Count", len(df))
        m3.metric("AOV (Avg Order)", f"₹{delivered['TotalPrice'].mean():.1f}")
        m4.metric("Loss (Cancelled)", f"₹{cancelled['TotalPrice'].sum():,.0f}", delta_color="inverse")

        # --- GROUP 1: DE PERFORMANCE ---
        with st.expander("🟢 Group 1: DE Performance (Heroes & Leaking Buckets)", expanded=True):
            de_stats = df.groupby('Deliveryman').agg(
                Total=('OID', 'count'),
                Delivered=('Status_L', lambda x: x.isin(['delivered', 'success', 'completed']).sum()),
                Cancelled=('Status_L', lambda x: x.isin(['cancelled', 'cancel', 'failed']).sum()),
                Revenue=('TotalPrice', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum())
            )
            de_stats['Success_Ratio'] = (de_stats['Delivered'] / de_stats['Total'] * 100).round(1)
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Top Performers (Descending)**")
                st.dataframe(de_stats.sort_values(by='Delivered', ascending=False).head(10))
            with c2:
                st.write("**Highest Cancellations (Red Flags)**")
                st.dataframe(de_stats.sort_values(by='Cancelled', ascending=False).head(10))

        # --- GROUP 2: VENDOR ANALYTICS ---
        with st.expander("🔴 Group 2: Vendor & Restaurant Analytics", expanded=False):
            v_stats = df.groupby('Vendor').agg(
                Orders=('OID', 'count'),
                Delivered=('Status_L', lambda x: x.isin(['delivered', 'success', 'completed']).sum()),
                Cancelled=('Status_L', lambda x: x.isin(['cancelled', 'cancel', 'failed']).sum()),
                Revenue=('TotalPrice', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum()),
                Payable=('Item Purchase Price', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum())
            )
            v_stats['Cancel_Rate'] = (v_stats['Cancelled'] / v_stats['Orders'] * 100).round(1)
            v_stats['Profit_Gap'] = v_stats['Revenue'] - v_stats['Payable']
            st.dataframe(v_stats.sort_values(by='Revenue', ascending=False))

        # --- GROUP 3: ITEM INTELLIGENCE ---
        with st.expander("🍱 Group 3: Item & Category Intelligence", expanded=False):
            item_stats = delivered.groupby('Item').agg(Qty=('Qty', 'sum'), Revenue=('TotalPrice', 'sum'))
            st.write("**Top 10 Bestsellers**")
            st.table(item_stats.sort_values(by='Qty', ascending=False).head(10))

        # --- GROUP 4: TIME & GROWTH ---
        with st.expander("📈 Group 4: Time, Day & Growth Strategy", expanded=False):
            day_counts = delivered['Day'].value_counts()
            st.write(f"📅 **Golden Day:** {day_counts.idxmax()} | 📉 **Dry Day:** {day_counts.idxmin()}")
            st.plotly_chart(px.line(delivered.groupby('Hour')['OID'].count().reset_index(), x='Hour', y='OID', title="Hourly Order Heatmap"))

        # --- EXCEL REPORT ---
        st.divider()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            de_stats.to_excel(writer, sheet_name="DE_Analytics")
            v_stats.to_excel(writer, sheet_name="Vendor_Analytics")
            delivered.to_excel(writer, sheet_name="Success_Data")
        st.download_button("📥 Download Master Analysis Report", buffer.getvalue(), "GetEazy_Full_Analysis.xlsx")
