import streamlit as st
import pandas as pd
import pdfplumber
import re

# Function to extract text from PDF using pdfplumber
def extract_pdf_text(pdf):
    with pdfplumber.open(pdf) as pdf_file:
        text = ''
        for page in pdf_file.pages:
            text += page.extract_text()
    return text

# Function to dynamically parse transactions from text
def parse_pdf_to_dataframe(text):
    # Basic logic to identify patterns (adjust according to your PDF structure)
    # For example, using regex to identify common transaction patterns
    pattern = re.compile(r'(?P<date>\d{2}-\w{3}-\d{2})\s+(?P<trx_type>[\w\s]+)\s+(?P<amount>[\d,]+\.\d{2})')
    matches = pattern.finditer(text)
    
    # Extract matches into a structured dataframe
    data = []
    for match in matches:
        date = match.group('date')
        trx_type = match.group('trx_type')
        amount = float(match.group('amount').replace(',', ''))
        data.append({"Date": date, "Trx Type": trx_type, "Amount": amount})
    
    return pd.DataFrame(data)

# Main Streamlit app
def main():
    st.title("Dynamic PDF Transaction Analyzer")
    
    # Upload PDF file
    uploaded_pdf = st.file_uploader("Upload your bank statement (PDF)", type="pdf")
    
    if uploaded_pdf is not None:
        # Extract text from the PDF
        pdf_text = extract_pdf_text(uploaded_pdf)
        
        # Parse the PDF text to create a dynamic DataFrame
        df = parse_pdf_to_dataframe(pdf_text)
        
        if not df.empty:
            # Show the DataFrame to the user
            st.write("Extracted Transactions", df)
            
            # Display the columns and allow filtering by selected column
            selected_column = st.selectbox("Select Column to Filter", df.columns)
            filter_value = st.text_input(f"Filter {selected_column} by value:")
            
            # Filter the DataFrame
            if filter_value:
                filtered_df = df[df[selected_column].astype(str).str.contains(filter_value, case=False)]
            else:
                filtered_df = df
                
            st.write("Filtered Data", filtered_df)
            
            # Button to calculate total for the 'Amount' column
            if st.button("Calculate Total Amount"):
                total = filtered_df['Amount'].sum()
                st.write(f"Total Amount: {total}")
        else:
            st.write("No transactions found. Please ensure the PDF is a statement and contains structured transaction data.")
    
if __name__ == "__main__":
    main()
