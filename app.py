# ---------------------------------------------------------
# PAGE 2: BUSINESS ANALYTICS (The 360° Command Center)
# ---------------------------------------------------------
elif page == "Business Analytics":
    st.title("📊 GetEazy Business Intelligence Dashboard")
    st.markdown("---")
    
    ana_file = st.file_uploader("Upload Data for Analysis", type="xlsx", key="ana_up")
    
    if ana_file:
        # Load and detect header
        raw_df = pd.read_excel(ana_file, header=None)
        h_idx = 0
        for i, row in raw_df.iterrows():
            if 'vendor' in [str(v).lower().strip() for v in row.values]:
                h_idx = i; break
        
        df = pd.read_excel(ana_file, skiprows=h_idx)
        df.columns = df.columns.astype(str).str.strip()
        
        # Data Pre-processing
        df['CreatedAt'] = pd.to_datetime(df['CreatedAt'], dayfirst=True)
        df['Hour'] = df['CreatedAt'].dt.hour
        df['Day'] = df['CreatedAt'].dt.day_name()
        df['TotalPrice'] = pd.to_numeric(df['TotalPrice'], errors='coerce').fillna(0)
        df['Item Purchase Price'] = pd.to_numeric(df['Item Purchase Price'], errors='coerce').fillna(0)
        df['Status_L'] = df['Status'].str.lower().str.strip()
        
        # Apply "Lokesh Filter"
        delivered = df[df['Status_L'].isin(['delivered', 'success', 'completed'])]
        cancelled = df[df['Status_L'].isin(['cancelled', 'cancel', 'failed'])]

        # --- TOP LEVEL KPI CARDS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Business Revenue", f"₹{delivered['TotalPrice'].sum():,.0f}")
        m2.metric("Orders Count", len(df))
        m3.metric("AOV (Avg Order)", f"₹{delivered['TotalPrice'].mean():,.0f}")
        m4.metric("Loss (Cancelled)", f"₹{cancelled['TotalPrice'].sum():,.0f}")

        # --- GROUP 1: DELIVERY EXECUTIVE (DE) PERFORMANCE ---
        with st.expander("🟢 Group 1: DE Performance (Heroes & Leaking Buckets)", expanded=True):
            de_stats = df.groupby('Deliveryman').agg(
                Total=('OID', 'count'),
                Delivered=('Status_L', lambda x: (x.isin(['delivered', 'success', 'completed'])).sum()),
                Cancelled=('Status_L', lambda x: (x.isin(['cancelled', 'cancel', 'failed'])).sum()),
                Revenue=('TotalPrice', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum()),
                Avg_Price=('TotalPrice', 'mean'),
                Unique_Days=('Day', 'nunique'),
                Locations=('VendorLocation', 'nunique')
            )
            de_stats['Success_Ratio'] = (de_stats['Delivered'] / de_stats['Total'] * 100).round(1)
            
            # Slot Specialist logic
            evening_de = df[df['Hour'] >= 18].groupby('Deliveryman')['OID'].count().idxmax()
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Top Performers (Delivered Count)**")
                st.dataframe(de_stats[['Delivered', 'Success_Ratio']].sort_values(by='Delivered', ascending=False).head(10))
                st.write(f"🏆 **Slot Specialist (Evening):** {evening_de}")
            with c2:
                st.write("**Cancellation Kings (Red Flags)**")
                st.dataframe(de_stats[['Cancelled', 'Total']].sort_values(by='Cancelled', ascending=False).head(10))
                st.write(f"📍 **Area Dominance (Most Locations):** {de_stats['Locations'].idxmax()}")

        # --- GROUP 2: VENDOR & RESTAURANT ANALYTICS ---
        with st.expander("🔴 Group 2: Vendor & Restaurant Analytics", expanded=False):
            v_stats = df.groupby('Vendor').agg(
                Total_Orders=('OID', 'count'),
                Confirmed=('Status_L', lambda x: (x.isin(['delivered', 'success', 'completed'])).sum()),
                Cancelled=('Status_L', lambda x: (x.isin(['cancelled', 'cancel', 'failed'])).sum()),
                Revenue=('TotalPrice', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum()),
                Payable=('Item Purchase Price', lambda x: x[df.loc[x.index, 'Status_L'].isin(['delivered', 'success', 'completed'])].sum()),
                Unique_Items=('Item', 'nunique'),
                Remarks=('Remarks', 'count')
            )
            v_stats['Cancel_Rate'] = (v_stats['Cancelled'] / v_stats['Total_Orders'] * 100).round(1)
            v_stats['Profit_Gap'] = v_stats['Revenue'] - v_stats['Payable']
            
            st.write("**Revenue Leader & Profit Gap**")
            st.dataframe(v_stats[['Revenue', 'Payable', 'Profit_Gap', 'Cancel_Rate']].sort_values(by='Revenue', ascending=False))
            
            st.write(f"🔥 **Busiest Location:** {df['VendorLocation'].value_counts().idxmax()}")
            st.write(f"💬 **Most Remarks (Special Instructions):** {v_stats['Remarks'].idxmax()}")

        # --- GROUP 3: ITEM & CATEGORY INTELLIGENCE ---
        with st.expander("🍱 Group 3: Item & Category Intelligence", expanded=False):
            item_stats = delivered.groupby('Item').agg(Qty=('Qty', 'sum'), Revenue=('TotalPrice', 'sum'))
            
            i1, i2 = st.columns(2)
            with i1:
                st.write("**Bestsellers (By Quantity)**")
                st.table(item_stats.sort_values(by='Qty', ascending=False).head(10))
            with i2:
                st.write("**Ghost Items (Should be removed?)**")
                st.table(item_stats.sort_values(by='Qty', ascending=True).head(5))
                
            st.write(f"🍕 **Most Common Size:** {delivered['Size'].value_counts().idxmax()}")
            st.write(f"🏷️ **Price Sweet Spot:** Avg Item Price is ₹{delivered['Price'].mode()[0]:.2f}")

        # --- GROUP 4: TIME, DAY & GROWTH ---
        with st.expander("📈 Group 4: Time, Day & Growth Strategy", expanded=False):
            day_counts = delivered['Day'].value_counts()
            
            g1, g2 = st.columns(2)
            with g1:
                st.write(f"📅 **Golden Day:** {day_counts.idxmax()} ({day_counts.max()} orders)")
                st.write(f"📉 **Recovery Day (Max Cancels):** {cancelled['Day'].value_counts().idxmax()}")
            with g2:
                morning = len(delivered[(delivered['Hour'] >= 6) & (delivered['Hour'] < 12)])
                evening = len(delivered[(delivered['Hour'] >= 18)])
                st.write(f"🌅 **Morning vs Evening:** {morning} vs {evening}")
                st.write(f"💰 **Total Net Margin:** ₹{delivered['TotalPrice'].sum() - delivered['Item Purchase Price'].sum():,.2f}")

        # --- GRAPHS SECTION ---
        st.markdown("### 📊 Visual Trends")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Hourly Trend
            hourly_trend = delivered.groupby('Hour')['OID'].count().reset_index()
            st.plotly_chart(px.line(hourly_trend, x='Hour', y='OID', title="Order Heatmap (Hourly)", markers=True))
            
        with chart_col2:
            # Day Performance
            day_trend = delivered['Day'].value_counts().reset_index()
            st.plotly_chart(px.bar(day_trend, x='Day', y='count', title="Success Count by Day", color='count'))

        # --- FINAL EXCEL REPORT ---
        st.divider()
        st.subheader("📥 Download Master Analysis Report")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            de_stats.to_excel(writer, sheet_name="DE_Analytics")
            v_stats.to_excel(writer, sheet_name="Vendor_Analytics")
            item_stats.to_excel(writer, sheet_name="Item_Analytics")
            delivered.to_excel(writer, sheet_name="Full_Success_Data")
        
        st.download_button(
            label="Download Complete Business Report (Excel)",
            data=buffer.getvalue(),
            file_name="GetEazy_Full_Analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
