import streamlit as st
import pandas as pd
import os
import re
from datetime import timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io
import zipfile

# --- VENDOR COMMISSION DATABASE ---
COMMISSIONS = {
    'IFC Restaurant': 0.15, 'SATTVIC KITCHEN PURE VEG': 0.20, 'Premier Restaurant': 0.10,
    'Sri Geetha Bhavan Udipi Hotel': 0.15, 'Geetha Bhavan - Armoor': 0.15, 
    'Anu Bakery & Lassi N Shakes': 0.15, 'Sri Bommarillu Family Restaurant': 0.15,
    'RUCHI FAST FOOD': 0.10, 'Mr.360 Drive INN': 0.20, 'Devi 2 Restaurant': 0.15,
    'Vashishta Biryani & Fast Food': 0.20, 'Telangana Fast Food': 0.20, 'Anu Fast Food': 0.20,
    'Chilly\'s Family Restaurant': 0.15, 'Shakes & More': 0.20, 'Varka Sweets & Bakers - Armr': 0.20,
    'THE SQUARE PIZZA': 0.20, 'Get Eazy Services - Free Delivery': 0.00, 'Varka Sweets & Bakers - Nrml': 0.20,
    'BALAJI CHICKEN PAKODI': 0.10, 'Ruchi Bangalore Bakery - Perkit': 0.20, 'HOTEL MAYURI INN': 0.15,
    'KFC Armr': 0.15, 'Get Eazy Services - NRML': 0.00, 'Land Mark Family Restaurant': 0.20, 
    'RAMBABU’S BIRYANI': 0.10, 'Madina Milk Center - Old Bus Stand': 0.10, 'Yaseen Hotel Perkit.': 0.25, 
    'Vijay Fast Food Center': 0.20, 'Evening snacks - Armr': 0.20, 'Hyderabadi Biryani House': 0.05, 
    'Shree Shawarma Spot': 0.05, 'FARMER\'S MILK CENTRE': 0.10, 'CREAMY CREATIONS': 0.15, 
    'Delhi Wala Sweets': 0.15, 'Belgian Waffle': 0.20, 'SVR Fast Food Corner': 0.10, 
    'Fusion Bakers': 0.20, 'Nakshatra Biryani House - Armr': 0.15, 'Kavya Mess': 0.10, 
    'Red Bucket Biryani - NRML': 0.15, 'RED CHILLI\'S Fast Food & Biryani': 0.20, 
    'Palletoori Vantillu': 0.20, 'Janardhan Tiffins': 0.00, 'Medicine Delivery Services - Armoor': 0.00, 
    'Vijay Tiffin\'s Centre': 0.10, 'Meena Tiffin Center - Armr': 0.10, 'Ganesh Tiffin Center - Armoor': 0.10, 
    'Meena Tiffin Center - NRML': 0.10, 'New Xpress Tiffins - Mrng Only': 0.10, 'Trishakti Restaurant': 0.20,
    'Devi Family Restaurant': 0.15, 'Sri Durga Bhavani Mess': 0.10, 'RFC Cloud Kitchen': 0.15,
    'Sagar Fast Food': 0.10, 'SS FAST FOOD': 0.10, 'Chat & Pani Puri': 0.10,
    'DOLPHIN BANGALORE BAKERY': 0.20, 'Happiness 365 Bakery': 0.20, 'Thirumala Ice Cream Parlor': 0.15,
    'Lucky Fast Food': 0.10, 'MR PAPAYA IMBF RESTAURANT': 0.10, 'Bhagyalaxmi Milks - Old Bus stand': 0.10,
    'YOGINI TIFFIN CENTRE': 0.10, 'Hotel PVR': 0.20, 'ROYAL ARABIAN MANDI': 0.15,
    'Sri Bhagyalaxmi Bamboo Restaurant': 0.15, 'Nandini Tiffin Center': 0.10,
    'Arun Ice Creams - Hapdaily - ARMR': 0.15, 'IFC Fried Chicken and Fast Food': 0.15, 
    'Jalalpur Dairy': 0.10, 'Sri Aadhaya Family Restaurant': 0.15, 'Sri Sathya Sai Super Market': 0.05,
    'SWA PARADISE FAMILY RESTAURANT': 0.15, 'Gismath Mandi and Restaurant': 0.15,
    'RR Frankeee': 0.20, 'Prakruthi Organic Cafe': 0.15, 'Manpreet Punjabi Dhaba': 0.10,
    'Pavan Santhosh Family Dhaba': 0.10, 'TG18 Family Restaurant': 0.15, 'Kritunga Restaurant': 0.15,
    'Devi Home Food': 0.10, 'CHAI CLUB - Milk Shakes': 0.20, 'Grand Kubera family restaurant': 0.15,
    'Haleem Day': 0.15, 'Shawarma Spot Nrml': 0.05, 'VS Biryani House - Mamidipally': 0.20,
    'Vegetables and Fruits': 0.05, 'Default': 0.10 
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
def header(self):
        # 1. High-Visibility Watermark (Modern Transparency Method)
        if os.path.exists('watermark.png'):
            try:
                # This 'with' block handles the transparency safely
                with self.local_context(fill_opacity=0.35):
                    self.image('watermark.png', x=55, y=100, w=100)
            except AttributeError:
                # If the library version is different, it will skip transparency to prevent crash
                self.image('watermark.png', x=55, y=100, w=100)

        # 2. Main Page Header Logic
        if self.page_no() == 1:
            if os.path.exists('logo.png'):
                # Logo 70mm width
                self.image('logo.png', x=10, y=10, w=70)
            
            self.set_y(15)
            self.set_font("helvetica", 'B', 14)
            self.cell(0, 8, text="VENDOR SETTLEMENT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            self.set_font("helvetica", 'B', 11)
            self.cell(0, 6, text=str(self.vendor_name), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            self.set_font("helvetica", 'I', 10)
            self.cell(0, 5, text=f"Period: {self.week_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
            # Ensure the table starts below the logo (y=55)
            self.set_y(55)
        else:
            # Margin for subsequent pages
            self.set_y(10)

st.set_page_config(page_title="GetEazy Settlement", page_icon="🚀")
st.title("GetEazy Settlement Portal")
st.write("Upload any orders Excel file below to generate all PDFs instantly.")

# Accepts any filename as long as it is .xlsx
uploaded_file = st.file_uploader("Select Excel File", type=["xlsx"])

if uploaded_file is not None:
    if st.button("Generate & Download ZIP"):
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.astype(str).str.strip()
        
        # Core Column Logic
        date_col, vendor_col, oid_col = 'CreatedAt', 'Vendor', 'OID'
        status_col, item_col, price_col, qty_col = 'Status', 'Item', 'Item Purchase Price', 'Qty'
        
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
        start_date = df[date_col].min()
        week_str = f"{start_date.strftime('%d %b %Y')} to {(start_date + timedelta(days=6)).strftime('%d %b %Y')}"
        
        df['Final_Rate'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
        df['is_cancelled'] = df[status_col].astype(str).str.contains('Cancel', case=False, na=False)
        df.loc[df['is_cancelled'], 'Final_Rate'] = 0
        df['Total Price'] = df[qty_col] * df['Final_Rate']
        
        cancelled_df = df[df['is_cancelled']].sort_values(by=[date_col])
        valid_df = df[~df['is_cancelled']].sort_values(by=[oid_col, date_col])
        df_sorted = pd.concat([cancelled_df, valid_df])

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for vendor in df_sorted[vendor_col].unique():
                clean_v = re.sub(r'[\\/*?:"<>|]', "", str(vendor))
                v_df = df_sorted[df_sorted[vendor_col] == vendor]
                
                pdf = SettlementPDF(vendor, week_str, orientation='P', unit='mm', format='A4')
                pdf.add_page()
                
                pdf.set_fill_color(200, 200, 200); pdf.set_font("helvetica", 'B', 8)
                w = [25, 18, 57, 10, 25, 25, 30] 
                headers = ['Date', 'OID', 'Item Name', 'Qty', 'Rate', 'Total', 'Status']
                for i in range(len(headers)): pdf.cell(w[i], 8, text=headers[i], border=1, align='C', fill=True)
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

                gross = v_df['Total Price'].sum()
                rate = COMMISSIONS.get(vendor, 0.10)
                for v_name, v_rate in COMMISSIONS.items():
                    if v_name.lower() in str(vendor).lower(): rate = v_rate; break
                
                net = gross - (gross * rate)
                pdf.set_text_color(0, 0, 0); pdf.ln(10); pdf.set_font("helvetica", 'B', 11)
                pdf.cell(sum(w[:5]), 8, text="GROSS TOTAL:", align='R')
                pdf.cell(w[5], 8, text=f"{gross:.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
                pdf.set_fill_color(255, 255, 0)
                pdf.cell(sum(w[:5]), 10, text="NET PAYABLE:", align='R')
                pdf.cell(w[5], 10, text=f"{net:.2f}", border=1, fill=True, align='R')

                zip_file.writestr(f"{clean_v}_Settlement.pdf", pdf.output())


        st.download_button("Click here to Download ZIP", data=zip_buffer.getvalue(), file_name="Settlements.zip")


