import streamlit as st
import pandas as pd
import json
from bkp_parser import process_bkp_file_content
import io

st.set_page_config(page_title="BKP Parser", page_icon="📊", layout="wide")

st.title("BKP File Parser")
st.markdown("Upload a BKP file to extract and analyze blocks")

# File uploader
uploaded_file = st.file_uploader("Choose a BKP file", type=['bkp'])

if uploaded_file is not None:
    try:
        # Read the uploaded file
        file_content = uploaded_file.read().decode('utf-8')
        
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # Process the file
        with st.spinner('Processing file...'):
            result = process_bkp_file_content(
                file_content, 
                output_json=False  # We'll handle JSON ourselves
            )
        
        # Get the JSON data
        from bkp_parser import extract_components_blocks, convert_blocks_to_json_format
        components, blocks = extract_components_blocks(file_content)
        json_data = convert_blocks_to_json_format(blocks)
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Blocks", json_data['total_blocks'])
        with col2:
            st.metric("Components Found", len(components))
        
        # Display results in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Table View", "📄 Formatted Text", "💾 JSON"])
        
        with tab1:
            # Convert to DataFrame for table view
            df = pd.DataFrame(json_data['blocks'])
            st.dataframe(df, use_container_width=True)
            
            # Download as CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download as CSV",
                data=csv,
                file_name=f"{uploaded_file.name}_blocks.csv",
                mime="text/csv"
            )
        
        with tab2:
            st.text(result)
            st.download_button(
                label="⬇️ Download as TXT",
                data=result,
                file_name=f"{uploaded_file.name}_blocks.txt",
                mime="text/plain"
            )
        
        with tab3:
            st.json(json_data)
            json_str = json.dumps(json_data, indent=2)
            st.download_button(
                label="⬇️ Download as JSON",
                data=json_str,
                file_name=f"{uploaded_file.name}_blocks.json",
                mime="application/json"
            )
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)

else:
    st.info("Upload a BKP file to get started")
    
    # Add instructions
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        1. Click the **Browse files** button above
        2. Select your BKP file
        3. View the parsed results in different formats
        4. Download the results as CSV, TXT, or JSON
        """)