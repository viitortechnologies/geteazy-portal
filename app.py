import streamlit as st
import pandas as pd
import os
import re
import io
import zipfile
from datetime import timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- VENDOR COMMISSION DATABASE (Your Original Data) ---
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
    'Delhi Wala Sweets': 0, 'Belgian Waffle': 0, 'SVR Fast Food Corner': 0, 'DOLPHIN BANGALORE BAKERY':0.20,'Shri Balaji Sweets & Bakers':0.10,
    'Fusion Bakers': 0, 'Nakshatra Biryani House - Armr': 0, 'Kavya Mess': 0.10, 'RR Fast Food Center - NRML': 0.20,
    'Red Bucket Biryani - NRML': 0, 'RED CHILLI\'S Fast Food & Biryani': 0.20, 
    'Palletoori Vantillu': 0.20, 'Janardhan Tiffins': 0.00, 'Medicine Delivery Services - Armoor': 0.00, 
    'Vijay Tiffin\'s Centre': 0.20, 'Meena Tiffin Center - Armr': 0, 'Ganesh Tiffin Center - Armoor': 0, 
    'Meena Tiffin Center - NRML': 0, 'New Xpress Tiffins - Mrng Only': 0, 'Trishakti Restaurant': 0.20,
    'Devi Family Restaurant': 0, 'Sri Durga Bhavani Mess': 0.10, 'RFC Cloud Kitchen': 0,
    'Sagar Fast Food': 0.10, 'SS FAST FOOD': 0.15, 'Chat & Pani Puri': 0,
    'DOLPHIN BANGALORE BAKERY': 0.20, 'Happiness 365 Bakery': 0.20, 'Thirumala Ice Cream Parlor': 0,
    'Lucky Fast Food': 0.10, 'MR PAPAYA IMBF RESTAURANT': 0.10, 'Bhagyalaxmi Milks - Old Bus stand': 0,
    'YOGINI TIFFIN CENTRE': 0, 'Hotel PVR': 0.10, 'ROYAL ARABIAN MANDI': 0,
    'Sri Bhagyalaxmi Bamboo Restaurant': 0, 'Nandini Tiffin Center': 0,
    'Arun Ice Creams - Hapdaily - ARMR': 0, 'IFC Fried Chicken and Fast Food': 0, 
    'Jalalpur Dairy': 0, 'Sri Aadhaya Family Restaurant': 0.15, 'Sri Sathya Sai Super Market': 0,
    'SWA PARADISE FAMILY RESTAURANT': 0.10, 'Gismath Mandi and Restaurant': 0.06, 'Viyyalavaari Vindu - Tiffins':0.20,'Viyyalavaari Vindu':0.20,'ARMOOR CHICKEN PAKODI':0.20,
    'RR Frankeee': 0.20, 'Prakruthi Organic Cafe': 0.10, 'Manpreet Punjabi Dhaba': 0,
    'Pavan Santhosh Family Dhaba': 0.12, 'TG18 Family Restaurant': 0, 'Kritunga Restaurant': 0.05,
    'Devi Home Food': 0.20, 'CHAI CLUB - Milk Shakes': 0, 'Grand Kubera family restaurant': 0,
    'Haleem Day': 0, 'Shawarma Spot Nrml': 0, 'VS Biryani House - Mamidipally': 0.20,
    'Vegetables and Fruits': 0, 'Default': 0
}

def clean_text(text):
    if not isinstance(text, str): text = str(text)
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"').replace('–', '-')
    return text.encode('ascii', 'ignore').decode('ascii')

class SettlementPDF(FPDF):
    def __init__(self, vendor_name, week_str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vendor_name = clean_text(vendor_name)
        self.week_str = week_str

st.title("🚀 GetEazy Vendor Settlement Portal")
st.write("Upload the `orders.xlsx` file to generate all PDFs and Summaries.")

uploaded_file = st.file_uploader("Choose Excel File", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # Process Dates
    date_col, vendor_col, oid_col = 'CreatedAt', 'Vendor', 'OID'
    status_col, item_col, price_col, qty_col = 'Status', 'Item', 'Item Purchase Price', 'Qty'
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
    start_date = df[date_col].min()
    end_date = start_date + timedelta(days=6)
    week_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"

    # Calculations
    df['Final_Rate'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
    df['is_cancelled'] = df[status_col].astype(str).str.contains('Cancel', case=False, na=False)
    df.loc[df['is_cancelled'], 'Final_Rate'] = 0
    df['Total Price'] = df[qty_col] * df['Final_Rate']

    df_sorted = pd.concat([df[df['is_cancelled']], df[~df['is_cancelled']]])

    # ZIP Creation
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for vendor in df_sorted[vendor_col].unique():
            clean_v = re.sub(r'[\\/*?:"<>|]', "", str(vendor))
            v_df = df_sorted[df_sorted[vendor_col] == vendor]
            
            pdf = SettlementPDF(vendor_name=vendor, week_str=week_str)
            pdf.add_page()
            pdf.set_font("helvetica", 'B', 8)
            w = [25, 18, 57, 10, 25, 25, 30] 
            headers = ['Date', 'OID', 'Item Name', 'Qty', 'Rate', 'Total', 'Status']
            for i in range(len(headers)): pdf.cell(w[i], 8, text=headers[i], border=1, align='C')
            pdf.ln()
            
            pdf.set_font("helvetica", size=8)
            for _, row in v_df.iterrows():
                pdf.set_text_color(255, 0, 0) if row['is_cancelled'] else pdf.set_text_color(0, 0, 0)
                pdf.cell(w[0], 7, text=str(row[date_col].strftime('%d-%m-%Y')), border=1)
                pdf.cell(w[1], 7, text=str(row[oid_col]), border=1)
                pdf.cell(w[2], 7, text=clean_text(row[item_col])[:35], border=1)
                pdf.cell(w[3], 7, text=str(row[qty_col]), border=1, align='C')
                pdf.cell(w[4], 7, text=f"{row['Final_Rate']:.2f}", border=1, align='R')
                pdf.cell(w[5], 7, text=f"{row['Total Price']:.2f}", border=1, align='R')
                pdf.cell(w[6], 7, text=str(row[status_col]), border=1, align='C')
                pdf.ln()

            # Commission Logic
            gross_sum = v_df['Total Price'].sum()
            rate = COMMISSIONS.get(vendor, COMMISSIONS['Default'])
            comm_amt = gross_sum * rate
            net_payable = gross_sum - comm_amt

            pdf.set_text_color(0, 0, 0); pdf.ln(10); pdf.set_font("helvetica", 'B', 11)
            pdf.cell(sum(w[:5]), 8, text="NET PAYABLE:", align='R')
            pdf.cell(w[5], 8, text=f"{net_payable:.2f}", border=1, align='R')

            # Save PDF to ZIP
            pdf_str = pdf.output(dest='S').encode('latin-1')
            zf.writestr(f"{clean_v}_Settlement.pdf", pdf_str)

    st.success("✅ All Settlements Processed!")
    st.download_button(
        label="📥 Download All Files (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Vendor_Settlements.zip",
        mime="application/zip"
    )
