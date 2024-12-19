from flask import Flask, send_file
from flask import Blueprint, render_template,request,redirect, url_for
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side   
from openpyxl import load_workbook
from fuzzywuzzy import fuzz, process
import re
import os
import io
import pandas as pd
from . import constants 
import pdb
from num2words import num2words


# app_job_work = Flask(__name__)

app_job_work = Blueprint('app_job_work', __name__, template_folder='templates')

# Ensure the output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(__file__),"outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Styles for the Excel file
BOLD_FONT = Font(bold=True, size=12)
CENTER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT_ALIGN = Alignment(horizontal='left', vertical='top', wrap_text=True)
THIN_BORDER = Border(left=Side(style='thin'), right=Side(style='thin'),
                     top=Side(style='thin'), bottom=Side(style='thin'))
DARK_BOTTOM_BORDER = Border(bottom=Side(style='medium'))
DARK_VERTICAL_BORDER = Border(right=Side(style='medium'))
DARK_BOTTOM_EXTENDED_BORDER = Border(bottom=Side(style='medium'), right=Side(style='medium'))
VERTICAL_BOLD_BORDER = Border(left=Side(style='medium'))  # For bold vertical borders
WRAP_TEXT_ALIGN = Alignment(wrap_text=True)  # To wrap the paragraph text


# Helper function to set cell value, style, and borders
def set_cell(ws, cell, value, font=None, alignment=None, border=None):
    ws[cell] = value
    if font:
        ws[cell].font = font
    if alignment:
        ws[cell].alignment = alignment
    if border:
        ws[cell].border = border

# @app.route('/')

@app_job_work.route('/upload_job_work')
def upload_job_work():
    return render_template('upload_job_work.html') # HTML template for file upload

# def upload_file():
#     return render_template('upload.html')  # HTML template for file upload

@app_job_work.route('/process', methods=['POST'])
def process_file():
        # Check if an input file was uploaded
    if 'file' not in request.files:
        return "No file uploaded", 400

    input_file = request.files['file']
    if input_file.filename == '':
        return "No selected file", 400

    # Load the input Excel file
    wb_input = load_workbook(input_file)
    ws_input = wb_input.active  # Assuming data is in the first sheet

    # Find the "Metal KT" column and collect unique data
    metal_kt_data = []
    metal_kt_index = None
    for row in ws_input.iter_rows(min_row=1, max_row=ws_input.max_row, values_only=True):
        if "Metal KT" in row and metal_kt_index is None:
            metal_kt_index = row.index("Metal KT")  # Find the index of "Metal KT" column
            continue  # Skip the header row
        if metal_kt_index is not None:
            value = row[metal_kt_index]
            if value and value not in metal_kt_data:  # Avoid empty cells and duplicates
                metal_kt_data.append(value)

    # Generate formatted headers, ensuring "Net" and "Pure" columns are side-by-side

    paired_headers = []
    other_headers = []
    fixed_headers = []
    silver_present = False
    platinum_present = False

    for item in metal_kt_data:
        if isinstance(item, str):
            if re.search(r'\d+(kt|ekt)', item, re.IGNORECASE):  # For Gold entries like "18KT" or "22EKT"
                number = re.search(r'\d+', item).group()  # Extract the number before "kt" or "ekt"
                if "ekt" in item.lower():
                    net_header = f"Net Wt (gms) {number}EKT Gold"
                    pure_header = f"Pure Wt (gms) {number}EKT Gold"
                else:
                    net_header = f"Net Wt (gms) {number}KT Gold"
                    pure_header = f"Pure Wt (gms) {number}KT Gold"
                paired_headers.extend([net_header, pure_header])
            elif "S.S" in item or "Silver" in item:  # For "S.S" or "Silver"
                silver_present = True
            elif re.search(r'\b(platinum|plt)\b', item, re.IGNORECASE):  # For "Platinum" or "plt"
                platinum_present = True
            else:
            # Capture any other unique Metal KT values for inclusion as headers
                other_headers.append(item)

# Add the silver column if needed
    if silver_present:
        paired_headers.extend(["Net Wt (gms) Silver", "Pure Wt (gms) Silver"])  # Ensure side-by-side placement

# Add the platinum column if needed
    if platinum_present:
        paired_headers.extend(["Net Wt (gms) Platinum", "Pure Wt (gms) Platinum"])  # Ensure side-by-side placement

# Combine all headers
    all_headers = fixed_headers + paired_headers + other_headers

    # Create a new Excel workbook and active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice"

    # Setting up the heading
    ws.merge_cells('A1:D1')
    set_cell(ws, 'A1', "INVOICE", font=BOLD_FONT, alignment=CENTER_ALIGN)

    # Create a horizontal line between row 31 and 32 from column A to P
    for col in range(1, 17):  # Columns A (1) to P (16)
        cell = ws.cell(row=31, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Add "Banker :" in row 26, column 5 in bold letters
    set_cell(ws, 'E26', "Banker :", font=BOLD_FONT, alignment=LEFT_ALIGN)
    
    # Create a horizontal line between row 26 and 27 from column D to P
    for col in range(4, 17):  # Columns D (4) to P (16)
        cell = ws.cell(row=26, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Create a horizontal line between row 30 and 31 from column A to P
    for col in range(1, 17):  # Columns A (1) to P (16)
        cell = ws.cell(row=30, column=col)
        cell.border = DARK_BOTTOM_BORDER


    # Adding a horizontal line between row 20 and 21 from column D to P
    for col in range(4, 17):  # Columns D (4) to P (16)
        cell = ws.cell(row=20, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Adding "Country of Origin Of Goods :" in row 21, columns E, F, G in bold letters
    ws.merge_cells('E21:G21')  # Merge cells E21, F21, and G21
    set_cell(ws, 'E21', "Country of Origin Of Goods :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding "INDIA" in row 22, column E without bold letters
    set_cell(ws, 'E22', "INDIA", font=None, alignment=LEFT_ALIGN)
    
    # Adding "Bank Details :" in column 5 (E), row 16, in bold letters
    set_cell(ws, 'E16', "Bank Details :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding a bold bottom border between row 14 and 15, from column D to P
    for col in range(4, 17):  # Columns D (4) to P (16)
        cell = ws.cell(row=14, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Merge columns 5, 6, and 7 in row 10
    ws.merge_cells('E10:G10')
    set_cell(ws, 'E10', "Buyer's Ord No. & Date Ref. : 437", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Merge columns E, F, and G in row 11
    ws.merge_cells('E11:G11')  # Columns E, F, and G merged
    set_cell(ws, 'E11', "Buyer (if other than consignee) :", alignment=LEFT_ALIGN)

    # Merge cells for "Invoice No. & Date :" label
    ws.merge_cells('E2:F2')
    set_cell(ws, 'E2', "Invoice No. & Date :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    invoice_no_date = request.form.get('invoice_no_date')

# Merge cells for the actual invoice value (entered from the form)
    ws.merge_cells('E3:F3')
    set_cell(ws, 'E3', invoice_no_date, alignment=LEFT_ALIGN)

# Merge cells for "Exporter's Ref:" label
    ws.merge_cells('I2:J2')
    set_cell(ws, 'I2', "Exporter's Ref:", font=BOLD_FONT, alignment=LEFT_ALIGN)

    Exporter_Ref = request.form.get('Exporter_Ref')

# Merge cells for the actual Exporter's Ref value (entered from the form)
    ws.merge_cells('I3:J3')
    set_cell(ws, 'I3', Exporter_Ref,alignment=LEFT_ALIGN)

    # Adding a horizontal bold bottom border between Row 8 and Row 9 from Column D to P
    for col in range(4, 17):  # Columns D (4) to P (16)
        cell = ws.cell(row=8, column=col)
        cell.border = Border(bottom=Side(style='medium'))  # Apply bold bottom border


    # Adding a vertical bold line between Columns D and E for Rows 2 to 31
    for row in range(2, 32):  # Rows 2 to 31
        ws.cell(row=row, column=4).border = Border(right=Side(style='medium'))  # Bold right border for Column D


    # Exporter Section (Heading Only)
    ws.merge_cells('A2:D2')
    set_cell(ws, 'A2', "Exporter :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Factory Address Section
    ws.merge_cells('A3:B7')
    set_cell(ws, 'A3', "Factory Address :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    ws.merge_cells('C3:D7')
    set_cell(ws, 'C3', ("M/S. UNI DESIGN ELITE JEWELLERY PVT LTD\n"
                        "Survey No.280091, Mahendra Brothers Exports Pvt Ltd\n"
                        "Gandevi Road, Jamalpore\n"
                        "At Village Navasari, At Taluka Navasari, At District Navasari\n"
                        "Pin No.396445\n"
                        "IGST NO:24AAACK3499E1ZL"), alignment=LEFT_ALIGN)

    # Sales Office Address Section
    ws.merge_cells('A9:B9')
    set_cell(ws, 'A9', "Sales Office Address :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    ws.merge_cells('C9:D14')
    set_cell(ws, 'C9', ("Unidesign Elite Jewellery Pvt Ltd\n"
                        "UNI DESIGN ELITE JEWELLERY PVT LTD\n"
                        "PLOT NO D-7/1, 1ST FLOOR, ASIAN HOUSE, ROAD NO 16\n"
                        "OPP. PRASAD LAB, MIDC ANDHERI -(E), M-93\n"
                        "Tel : 30815888\n"
                        "GST NO: 27AAACK3499E2ZE\n"
                        "LUT ARN No- AD270324023939U\n"
                        "Date: 01/4/2024 To 31/03/2025"), alignment=LEFT_ALIGN)

    # Adding a dark bottom border for row 14
    for col in range(1, 5):  # Columns A to D
        cell = ws.cell(row=14, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Consignee Section
    ws.merge_cells('A16:B16')
    set_cell(ws, 'A16', "Consignee :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    ws.merge_cells('C16:D22')
    set_cell(ws, 'C16', ("UNIDESIGN JEWELLERY PVT.LTD. UNIT III\n"
                         "PLOT # 4, 5 & 6 (Part), Seepz, Sez,\n"
                         "Andheri (East), Mumbai-400096\n\n"
                         "Tel : 022 6668 1050\n"
                         "Fax : GST - 27AAACU0572GIZH\n"
                         "GST : 27AAACU0572G1ZH\n"
                         "Pan No. : AAACU0572G"), alignment=LEFT_ALIGN)

    # Adding a dark bottom border for row 22
    for col in range(1, 5):  # Columns A to D
        cell = ws.cell(row=22, column=col)
        cell.border = DARK_BOTTOM_BORDER

    # Pre-Carriage Section
    ws.merge_cells('A24:B24')
    set_cell(ws, 'A24', "Pre-Carriage by :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding "Place of Receipt by Pre-Carrier :" in column 3, row 24
    set_cell(ws, 'C24', "Place of Receipt by Pre-Carrier :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding "N.A" in column A just below "Pre-Carriage by :"
    set_cell(ws, 'A25', "N.A", alignment=LEFT_ALIGN)

    # Adding "N.A." in column 3, row 25
    set_cell(ws, 'C25', "N.A.", alignment=LEFT_ALIGN)

    # Adding "Port of Loading :" in column 3, row 26
    set_cell(ws, 'C26', "Port of Loading :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding "Final Destination :" in column 3, row 27
    set_cell(ws, 'C27', "Final Destination :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding "INDIA " in column 3, row 28
    set_cell(ws, 'C28', "INDIA", alignment=LEFT_ALIGN)

    # Adding extended bold bottom border for rows 25 and 26
    for col in range(1, 3):  # Columns A to C
        cell = ws.cell(row=25, column=col)
        cell.border = DARK_BOTTOM_EXTENDED_BORDER

    # Adding "Vessel/Flight No. :" in row 26
    set_cell(ws, 'A26', "Vessel/Flight No. :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding extended bold bottom border for rows 26 and 27
    for col in range(1, 3):  # Columns A to C
        cell = ws.cell(row=26, column=col)
        cell.border = DARK_BOTTOM_EXTENDED_BORDER

    # Adding "Port of Discharge :" in row 27
    set_cell(ws, 'A27', "Port of Discharge :", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding bold vertical border between columns B and D for rows 22 to 30
    for row in range(23, 31):  # Rows 22 to 30
        ws.cell(row=row, column=3).border = VERTICAL_BOLD_BORDER  # Bold vertical line between columns B

    # Add a horizontal line between row 22 and 23 from columns D to P
    for col in range(4, 17):  # Columns D to P (4 to 16)
        cell = ws.cell(row=22, column=col)
        cell.border = Border(bottom=Side(style='medium'))
    
    # Add a horizontal line between row 1 and 2 from columns D to P
    for col in range(4, 17):  # Columns D to P (4 to 16)
        cell = ws.cell(row=1, column=col)
        cell.border = Border(bottom=Side(style='medium'))

    # Adding horizontal line (bottom border) between row 25 and 26 from column B to E
    for col in range(2, 5):  # Columns B to E
        cell = ws.cell(row=25, column=col)
        cell.border = Border(bottom=Side(style='medium'))

    for col in range(2, 5):  # Columns B to E
        cell = ws.cell(row=26, column=col)
        cell.border = Border(bottom=Side(style='medium'))
    
    # Adding "Terms of Delivery & Payment :" in row 23, columns E, F, and G in bold letters
    ws.merge_cells('E23:G23')  # Merge columns E, F, and G in row 23
    set_cell(ws, 'E23', "Terms of Delivery & :", font=BOLD_FONT, alignment=LEFT_ALIGN)

# Adding "Payment Term: Immediate" in row 24, columns E, F, and G
    ws.merge_cells('E24:G24')  # Merge columns E, F, and G in row 24
    set_cell(ws, 'E24', "Payment Term: Immediate", font=None, alignment=LEFT_ALIGN)

# Create a horizontal line between row 25 and 26 from column D to P
    for col in range(4, 17):  # Columns D to P (4 to 16)
        cell = ws.cell(row=25, column=col)
        cell.border = Border(bottom=Side(style='medium'))
        
    # Adding Metal KT data as a table in the output Excel
    start_row = ws.max_row + 2  # Start below the existing formatted data

    # First column: "Marks & Nos./ Container No."
    set_cell(ws, f'A{start_row}', "Marks & Nos./ Container No.", font=BOLD_FONT, alignment=CENTER_ALIGN)
    set_cell(ws, f'B{start_row}', "No. & Kind of Pkgs", font=BOLD_FONT, alignment=CENTER_ALIGN)
    # set_cell(ws, f'C{start_row}', "Description of Goods", font=BOLD_FONT, alignment=CENTER_ALIGN)
    
    from openpyxl.styles import Font, Alignment

    # Set the "Description of Goods" header at C{start_row}
    set_cell(ws, f'C{start_row}', "Description of Goods", font=BOLD_FONT, alignment=CENTER_ALIGN)

# Print "71131913" just above the "Description of Goods"
    description_goods_row = start_row - 1  # Row immediately above "Description of Goods"
    ws[f'C{description_goods_row}'] = "71131913"  # Print the value
    ws[f'C{description_goods_row}'].font = Font(size=10, color="808080")  # Light font (gray) and smaller font size
    ws[f'C{description_goods_row}'].alignment = Alignment(horizontal='right', vertical='top', wrap_text=False)  # Right-aligned text

    
    set_cell(ws, f'D{start_row}', "Gross Wt (gms)", font=BOLD_FONT, alignment=CENTER_ALIGN)
    
   # Adding all Metal KT data headers
    current_col = 5  # Start from column E
    for header in all_headers:  # all_headers contains Metal KT-related columns
        col_letter = ws.cell(row=start_row, column=current_col).column_letter
        set_cell(ws, f'{col_letter}{start_row}', header, font=BOLD_FONT, alignment=CENTER_ALIGN)
        current_col += 1

    # Adding "Qty. Pcs" column
    qty_pcs_col_letter = ws.cell(row=start_row, column=current_col).column_letter
    set_cell(ws, f'{qty_pcs_col_letter}{start_row}', "Qty. Pcs", font=BOLD_FONT, alignment=CENTER_ALIGN)
    current_col += 1  # Increment column index for the next column

    # Adding "Rate Av. Per Pc" column
    rate_av_col_letter = ws.cell(row=start_row, column=current_col).column_letter
    set_cell(ws, f'{rate_av_col_letter}{start_row}', "Rate Av. Per Pc", font=BOLD_FONT, alignment=CENTER_ALIGN)
    current_col += 1  # Increment column index for any subsequent additions

    # Adding "Labor Amt" column
    labor_amt_col_letter = ws.cell(row=start_row, column=current_col).column_letter
    set_cell(ws, f'{labor_amt_col_letter}{start_row}', "Labour Amt", font=BOLD_FONT, alignment=CENTER_ALIGN)
    current_col += 1  # Increment column index for any subsequent additions
    
    # Adding "Metal Amt." column
    metal_amt_col_letter = ws.cell(row=start_row, column=current_col).column_letter
    set_cell(ws, f'{metal_amt_col_letter}{start_row}', "Metal Amt.", font=BOLD_FONT, alignment=CENTER_ALIGN)
    current_col += 1  # Increment column index for any subsequent additions
    
    # Adding "Diamond CTS" column after "Metal Amt."
    diamond_cts_col_letter = ws.cell(row=start_row, column=current_col).column_letter
    set_cell(ws, f'{diamond_cts_col_letter}{start_row}', "Diamond CTS", font=BOLD_FONT, alignment=CENTER_ALIGN)
    current_col += 1  # Increment column index for the next column
    
   # Find the position of "Diamond CTS" column dynamically
    diamond_cts_col = None
    for col_idx in range(1, ws.max_column + 1):
        if ws.cell(row=start_row, column=col_idx).value == "Diamond CTS":
            diamond_cts_col = col_idx
            break

# Add "Diamond Amt." column immediately after "Diamond CTS"
    if diamond_cts_col is not None:
    # Calculate the column letter after "Diamond CTS"
        diamond_amt_col_letter = ws.cell(row=start_row, column=diamond_cts_col + 1).column_letter
        set_cell(ws, f'{diamond_amt_col_letter}{start_row}', "Diamond Amt.", font=BOLD_FONT, alignment=CENTER_ALIGN)

    # Find the position of "Diamond Amt." column dynamically
    diamond_amt_col = None
    for col_idx in range(1, ws.max_column + 1):
        if ws.cell(row=start_row, column=col_idx).value == "Diamond Amt.":
            diamond_amt_col = col_idx
            break

# Add "Color Stone CTS" column immediately after "Diamond Amt."
    if diamond_amt_col is not None:
    # Calculate the column letter after "Diamond Amt."
        color_stone_cts_col_letter = ws.cell(row=start_row, column=diamond_amt_col + 1).column_letter
        set_cell(ws, f'{color_stone_cts_col_letter}{start_row}', "Color Stone CTS", font=BOLD_FONT, alignment=CENTER_ALIGN)

    # Find the position of "Color Stone CTS" column dynamically
    color_stone_cts_col = None
    for col_idx in range(1, ws.max_column + 1):
        if ws.cell(row=start_row, column=col_idx).value == "Color Stone CTS":
            color_stone_cts_col = col_idx
            break

# Add "Color Stone Amt." column immediately after "Color Stone CTS."
    if color_stone_cts_col is not None:
    # Calculate the column letter after "Color Stone CTS."
        color_stone_amt_col_letter = ws.cell(row=start_row, column=color_stone_cts_col + 1).column_letter
        set_cell(ws, f'{color_stone_amt_col_letter}{start_row}', "Color Stone Amt.", font=BOLD_FONT, alignment=CENTER_ALIGN)
    # Add "Amount US$" as the last column in the output Excel file
    last_col_index = ws.max_column + 1  # Determine the next available column
    last_col_letter = ws.cell(row=start_row, column=last_col_index).column_letter
    set_cell(ws, f'{last_col_letter}{start_row}', "Amount US$", font=BOLD_FONT, alignment=CENTER_ALIGN)


    # Adjust column widths
    ws.column_dimensions['A'].width = 40
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 50
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    
    # Adjust widths for dynamically added columns
    for col_index in range(5, ws.max_column + 1):  # From the first added column to the last
        col_letter = ws.cell(row=start_row, column=col_index).column_letter
        ws.column_dimensions[col_letter].width = 15  # Adjust as needed for clarity
    
    
    output_header = [cell.value.strip() for cell in ws[33]]
   
  # Load the parsed data
    df = pd.read_excel(input_file, header=3)

# Step 1: Clean column names
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
    df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)  # Replace multiple spaces with a single space
    df.columns = df.columns.str.replace(r'[^A-Za-z0-9 ]+', '', regex=True)  # Remove special characters

# Step 2: Add default values for missing columns
    required_columns = [
        'INR LABOUR', 'Inv Rm Wt', 'Design', 'Ctg', 'Metal KT', 
        'Gross Wt', 'DsgCtg', 'Karatage', 'Inv Pure Wt', 
        'Inv Rate', 'Inv Value', 'Labour', 'Qty'
    ]
# Check for missing columns and add them with default value of 0
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0  # Add the missing column with default value 0

# Step 3: Perform aggregation
    grouped = df.groupby(["Design", "Ctg", "Metal KT"], dropna=False).agg({
        "Gross Wt": "sum",
        "DsgCtg": "first",
        "Karatage": "first",
        "Inv Rm Wt": "sum",
        "Inv Pure Wt": "sum",
        "Inv Rate": "mean",  # Average rate
        "Inv Value": "sum",
        "Labour": "sum",
        "INR LABOUR": "sum",
        "Qty": "sum"
    }).reset_index()

    
    final_list = []
    prev = None
    gross_wt = qty = labour = rate_avg_pp = metal_amt = total_usd = stone_amt = 0
    design_ctg = product_name = ''
    ctg = []
    temp_dict = {}
    metal_temp = {}

    for index, row in grouped.iterrows():
        if not prev:
            prev = row['Design']
        elif prev != row['Design'] or index == (grouped.shape[0] - 1):
            if index == (grouped.shape[0] - 1):
                ctg.append(f"{row['Ctg']},{row['Metal KT']}")
                design_ctg = row['DsgCtg']
                gross_wt += row['Gross Wt']
                qty += row['Qty']
                labour += row['Labour']
                metal_amt += row['Inv Value'] if row['Ctg'] in ['G','M','S'] else 0
                stone_amt += row['Inv Value'] if row['Ctg'] in ['C','D'] else 0
                metal_temp.update(get_metal_mapping(output_header, row, row['Ctg'], row['Metal KT']))

            
            total_usd = labour + metal_amt + stone_amt
            rate_avg_pp = total_usd / qty
            product_name = get_product_name(ctg)
            design_ctg = (constants.DESIGN_CATEGORY[design_ctg] if design_ctg in constants.DESIGN_CATEGORY else '')

            temp_dict = {
                'Marks & Nos./ Container No.': f'{product_name},\r\n {round(qty)}, {design_ctg}',
                'No. & Kind of Pkgs': '',
                'Description of Goods': '',
                'Design': prev,
                'Gross Wt (gms)': round(gross_wt, 3),
                'Qty. Pcs': round(qty),
                'Labour Amt': round(labour, 2),
                'Metal Amt.': round(metal_amt, 2),
                'Rate Av. Per Pc': round(rate_avg_pp, 2),
                'Amount US$': round(total_usd, 2)
            }

            temp_dict.update(metal_temp)
            final_list.append(temp_dict)

        # Reset variables for the next Design
            gross_wt = qty = labour = rate_avg_pp = metal_amt = total_usd = stone_amt = 0
            design_ctg = product_name = ''
            ctg = []
            temp_dict = {}
            metal_temp = {}
            prev = row['Design']

        ctg.append(f"{row['Ctg']},{row['Metal KT']}")
        design_ctg = row['DsgCtg']
        gross_wt += row['Gross Wt']
        qty += row['Qty']
        labour += row['Labour']
        metal_amt += row['Inv Value'] if row['Ctg'] in ['G','M','S'] else 0
        stone_amt += row['Inv Value'] if row['Ctg'] in ['C','D'] else 0
        metal_temp.update(get_metal_mapping(output_header, row, row['Ctg'], row['Metal KT']))

    # Map headers to the final output
    mapped_data = map_headers_to_data(output_header, final_list)
    # print(mapped_data)

    # Create final DataFrame from the mapped data
    final_output = pd.DataFrame(mapped_data)
    # print(final_output.to_string())

    # Step 1: Clean the column names (strip spaces and convert to lowercase for consistency)
    final_output.columns = final_output.columns.str.strip().str.lower()  # Make column names lowercase and strip spaces

    # Step 2: Check if 'metal amt.' column exists (case insensitive)
    metal_amt_column_name = [col for col in final_output.columns if 'metal amt' in col.lower()]

    if metal_amt_column_name:
        # Step 3: Sum the 'Metal Amt.' column
        metal_amt_sum = final_output[metal_amt_column_name[0]].sum()  # Use the first matching column
        print(f"Sum of '{metal_amt_column_name[0]}':", metal_amt_sum)
    else:
        print("Error: 'Metal Amt.' column not found.")
    
    
    numeric_columns = final_output.select_dtypes(include=['number']).columns

    # Calculate the sum for each numeric column
    totals_row = {col: final_output[col].sum() for col in numeric_columns}

    # Add a label for the totals row (e.g., in the first column)
    totals_row.update({col: None for col in final_output.columns if col not in numeric_columns})

    # Append the totals row to the DataFrame
    final_output_total = pd.concat([final_output, pd.DataFrame([totals_row])], ignore_index=True)    
    from openpyxl.utils.dataframe import dataframe_to_rows

    last_row_of_total = final_output_total.iloc[-1]
    # If mapped_data is a list of dictionaries or rows

    from openpyxl.styles import Font
    
    # Write the final DataFrame to the Excel file

    start_row = 34
    for j, header in enumerate(final_output.columns):
        ws.cell(row=start_row - 1, column=j + 1, value=header)

    for i, row in final_output.iterrows():
        for j, value in enumerate(row):
  
            ws.cell(row=start_row + i, column=j + 1, value=value) 
    last_row = start_row + len(final_output)  # Calculate the row where the mapping ends
    
  
    # Get multiple RM, QTY PCS, Met. Wt.Gms, and Value US$ from the form
    
    rm_list = request.form.getlist('rm[]')
    qty_pcs_list = request.form.getlist('qty_pcs[]')  
    met_wt_gms_list = request.form.getlist('met_wt_gms[]')
    value_usd_list = request.form.getlist('value_usd[]')

    # Insert Headers for RM, QTY PCS, Met. Wt.Gms, and Value US$ with bold font
    headers_row_number = last_row + 5  # Place the headers right after the mapping section
  
    
    # Create the headers
    ws.cell(row=headers_row_number, column=1, value="RM.")
    ws.cell(row=headers_row_number, column=1).font = Font(bold=True)  # Make the text bold

    # Check if any value is provided for QTY PCS
    qty_pcs_exists = any(qty for qty in qty_pcs_list if qty)  # Boolean flag to determine if QTY PCS exists
    
    if qty_pcs_exists:  # Print QTY PCS header only if at least one value exists
        ws.cell(row=headers_row_number, column=2, value="QTY PCS")
        ws.cell(row=headers_row_number, column=2).font = Font(bold=True)  
        met_wt_gms_col = 3  # Met. Wt.Gms will be in column 3
        value_usd_col = 4  # Value US$ will be in column 4
    else:
        met_wt_gms_col = 2  # Met. Wt.Gms will be in column 2 if QTY PCS does not exist
        value_usd_col = 3  # Value US$ will be in column 3 if QTY PCS does not exist

    ws.cell(row=headers_row_number, column=met_wt_gms_col, value="Met. Wt.Gms")
    ws.cell(row=headers_row_number, column=met_wt_gms_col).font = Font(bold=True)  # Make the text bold

    ws.cell(row=headers_row_number, column=value_usd_col, value="Value US$")
    ws.cell(row=headers_row_number, column=value_usd_col).font = Font(bold=True)  # Make the text bold
    
    # Step 3: Insert RM, QTY PCS, Met. Wt.Gms, and Value US$ Data Below the Headers
    data_start_row = headers_row_number + 1  # Row immediately after the headers
    total_qty_pcs = 0  # Initialize total for QTY PCS
    total_met_wt_gms = 0  # Initialize sum for Met. Wt.Gms
    total_value_usd = 0  # Initialize sum for Value US$

    for i in range(len(rm_list)):
        rm = rm_list[i]
        qty_pcs = float(qty_pcs_list[i]) if qty_pcs_list[i] else 0  # Get QTY PCS value or default to 0
        met_wt_gms = float(met_wt_gms_list[i]) if met_wt_gms_list[i] else 0
        value_usd = float(value_usd_list[i]) if value_usd_list[i] else 0
    
    # Write data to the worksheet
        ws.cell(row=data_start_row + i, column=1, value=rm).alignment = LEFT_ALIGN
    
        if qty_pcs_exists:  # Print QTY PCS only if at least one value exists
            ws.cell(row=data_start_row + i, column=2, value=qty_pcs).alignment = LEFT_ALIGN
    
    # Write Met. Wt.Gms and Value US$
        ws.cell(row=data_start_row + i, column=met_wt_gms_col, value=met_wt_gms).alignment = LEFT_ALIGN
        ws.cell(row=data_start_row + i, column=value_usd_col, value=value_usd).alignment = LEFT_ALIGN

    # Add to the totals
        total_qty_pcs += qty_pcs
        total_met_wt_gms += met_wt_gms
        total_value_usd += value_usd

    # Step 4: Add Totals in the Last Row of Data
    last_data_row = data_start_row + len(rm_list)  # Get the last row of the data

    # Insert total labels and values
    ws.cell(row=last_data_row + 1, column=1, value="Total").alignment = LEFT_ALIGN
    ws.cell(row=last_data_row + 1, column=1).font = Font(bold=True) # Make the text bold

    if qty_pcs_exists:  # Print QTY PCS total only if QTY PCS exists
        ws.cell(row=last_data_row + 1, column=2, value=total_qty_pcs).alignment = LEFT_ALIGN
        ws.cell(row=last_data_row + 1, column=2).font = Font(bold=True)

    # Write Met. Wt.Gms and Value US$ totals
    ws.cell(row=last_data_row + 1, column=met_wt_gms_col, value=total_met_wt_gms).alignment = LEFT_ALIGN
    ws.cell(row=last_data_row + 1, column=met_wt_gms_col).font = Font(bold=True)

    # Write the Value US$ total
    cell = ws.cell(row=last_data_row + 1, column=value_usd_col, value=total_value_usd)
    cell.alignment = LEFT_ALIGN  # Set left alignment
    cell.font = Font(bold=True)  # Set bold font
    
        
    # Get the input without forcing it into a string
    banker_detail_value = request.form.get('Banker_details', '')

    # Print the banker header
    ws['E26'] = "Banker :"
    ws['E26'].font = Font(bold=True)
    ws['E26'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=False)

    # Write the banker details below the header
    ws['E27'] = banker_detail_value
    ws['E27'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=False)

    # ** Concatenate RM values with commas and write in a single cell ** 
    rm_values_string = ', '.join([str(rm) for rm in rm_list])  # Join all RM values with commas
    ws['E27'] = f"{banker_detail_value} {rm_values_string}"  # Combine Banker details with RM values
    ws['E27'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=False)
    
    
    # Get the input value for Challan No.
    challan_no_value = request.form.get('challan_no', '')

    # Add "Challan No." header at row 29, column E
    ws['E29'] = "Challan No."
    ws['E29'].font = Font(bold=True)  # Make the header bold
    ws['E29'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=False)  # Align left and prevent wrap

    # Print the value of the Challan No. in the next column (F29)
    ws['F29'] = challan_no_value  # Assign the Challan No. value
    ws['F29'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=False)  # Align left and prevent wrap
    


    # Calculate where to print the exchange rate
    table = last_data_row + 8
    exchange_rate_row_number = table + 17 # Add a 5-line gap (3 for data, 2 for space)

    diamond_stone_table = df.loc[df['Ctg'].isin(['C','D'])].groupby(["Ctg"], dropna=False).agg({
        "Inv Rm Wt": "sum",
        "Inv Value": "sum",
        "Inv Rm Qty": "sum"
    }).reset_index()
   
    diamond_wt = diamond_value = diamond_qty = CS_wt = CS_value = CS_qty = 0
    for i, row in diamond_stone_table.iterrows():
        if row['Ctg'] == 'D':
            diamond_wt = (row['Inv Rm Wt'])
            diamond_value = (row['Inv Value'])
            diamond_qty = (row['Inv Rm Qty'])
        elif row['Ctg'] == 'C':
            CS_wt = (row['Inv Rm Wt'])
            CS_value = (row['Inv Value'])
            CS_qty = (row['Inv Rm Qty'])
   
   # Adding "Type", "PCS", "Total CTW", "Net Payable by You"
    set_cell(ws, f'B{table}', "PCS", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'C{table}', "Total CTW", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'D{table}', "Net Payable by You", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table}', "Type", font=BOLD_FONT, alignment=LEFT_ALIGN)

    # Adding data row (e.g., "Diamond")
    set_cell(ws, f'A{table + 1}', "Diamond", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table + 2}', "Precious/Semi Precious Color Stone", font=BOLD_FONT, alignment=LEFT_ALIGN)

    set_cell(ws, f'A{table + 5}', "Type", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'B{table + 5}', "Value", font=BOLD_FONT, alignment=LEFT_ALIGN)

    set_cell(ws, f'A{table + 6}', "Diamond", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table + 7}', "Precious/Semi Precious Color Stone", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table + 8}', "Labour", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table + 9}', "Grand Total", font=BOLD_FONT, alignment=LEFT_ALIGN)
    set_cell(ws, f'A{table + 3}', "Grand Total", font=BOLD_FONT, alignment=LEFT_ALIGN)
    
   
    target_row = table + 11  # Replace 'table' with your variable's actual value
    target_row_calculation = target_row + 1
    target_row_calculation_for_net_realization =  target_row_calculation + 1
    last_row_of_total_values = last_row_of_total.tolist()

    for col_idx, value in enumerate(last_row_of_total_values, start=1):  # start=1 for column A
        ws.cell(row=target_row, column=col_idx, value=value)
    
    if isinstance(last_row_of_total, pd.Series):
        # Convert the Series to a list of values
        last_row_of_total_values = last_row_of_total.tolist()
        
        # Calculate the index for the last column (using len to find the total number of columns)
        last_column_index = len(last_row_of_total_values) - 1  # Last column index
        
        # Convert index to Excel column letter (e.g., 0 -> 'A', 1 -> 'B', etc.)
        last_column_letter = chr(64 + last_column_index)  # 65 corresponds to 'A'
        last_column_letter_for_metal = chr(65 + last_column_index)  # 65 corresponds to 'A'

        # Ensure you have the correct target row (replace 'target_row_calculation' with your dynamic row number)
        set_cell(ws, f'{last_column_letter}{target_row_calculation}', "Less: Metal Cost US$", font=BOLD_FONT, alignment=LEFT_ALIGN)
        set_cell(ws, f'{last_column_letter}{target_row_calculation_for_net_realization}', "Net Realization US$", font=BOLD_FONT, alignment=LEFT_ALIGN)
    
    final_output.columns = final_output.columns.str.strip().str.lower()  # Make column names lowercase and strip spaces

    # Step 2: Check if 'metal amt.' column exists (case insensitive)
    metal_amt_column_name = [col for col in final_output.columns if 'metal amt' in col.lower()]
    amount_col = [col for col in final_output.columns if 'amount us$' in col.lower()]
    
    if metal_amt_column_name:
        # Step 3: Sum the 'Metal Amt.' column
        metal_amt_sum = final_output[metal_amt_column_name[0]].sum()  # Use the first matching column
        set_cell(ws, f'{last_column_letter_for_metal}{target_row_calculation}', metal_amt_sum, font=BOLD_FONT, alignment=LEFT_ALIGN)
    

    if amount_col:
        # Step 3: Sum the 'Metal Amt.' column
        amt_col_sum = final_output[amount_col[0]].sum()  # Use the first matching column
        net_realization_value = amt_col_sum - metal_amt_sum
        set_cell(ws, f'{last_column_letter_for_metal}{target_row_calculation_for_net_realization}', net_realization_value, font=BOLD_FONT, alignment=LEFT_ALIGN)
      
    if "Inv Rm Qty" in df.columns:
        ws[f'B{table + 1}'] = diamond_qty 
        ws[f'B{table + 1}'].font = BOLD_FONT
        ws[f'B{table + 1}'].alignment = LEFT_ALIGN
        ws[f'B{table + 2}'] = CS_qty
        ws[f'B{table + 2}'].font = BOLD_FONT
        ws[f'B{table + 2}'].alignment = LEFT_ALIGN
        total_qty_table = diamond_qty + CS_qty
      
        ws[f'B{table + 3}'] = total_qty_table 
        ws[f'B{table + 3}'].font = BOLD_FONT
        ws[f'B{table + 3}'].alignment = LEFT_ALIGN

    if "Inv Rm Wt" in df.columns:
        ws[f'C{table + 1}'] = diamond_wt
        ws[f'C{table + 1}'].font = BOLD_FONT
        ws[f'C{table + 1}'].alignment = LEFT_ALIGN
        ws[f'C{table + 2}'] = CS_wt 
        ws[f'C{table + 2}'].font = BOLD_FONT
        ws[f'C{table + 2}'].alignment = LEFT_ALIGN

        total_rm_wt_table = diamond_wt + CS_wt
        ws[f'C{table + 3}'] = total_rm_wt_table 
        ws[f'C{table + 3}'].font = BOLD_FONT
        ws[f'C{table + 3}'].alignment = LEFT_ALIGN

    if "Inv Value" in df.columns:
        try:
            # Diamond values
            ws[f'D{table + 1}'] = diamond_value
            ws[f'B{table + 6}'] = diamond_value
            ws[f'D{table + 1}'].font = BOLD_FONT
            ws[f'D{table + 1}'].alignment = LEFT_ALIGN

            # Precious/Semi-Precious Stone values
            ws[f'D{table + 2}'] = CS_value
            ws[f'B{table + 7}'] = CS_value
            ws[f'D{table + 2}'].font = BOLD_FONT
            ws[f'D{table + 2}'].alignment = LEFT_ALIGN


            total_inv_value_table = diamond_value + CS_value
            ws[f'D{table + 3}'] = total_inv_value_table 
            ws[f'D{table + 3}'].font = BOLD_FONT
            ws[f'D{table + 3}'].alignment = LEFT_ALIGN
        except Exception as e:
            print(f"Error processing 'Inv Value': {e}")
   
    df.columns = df.columns.str.strip()  # Ensure no leading/trailing spaces in column names
    if 'Labour' in df.columns:
        try:
            df['Labour'] = pd.to_numeric(df['Labour'], errors='coerce')
            labour_sum = df['Labour'].sum(skipna=True)
            ws[f'B{table + 8}'] = labour_sum
        except Exception as e:
            print(f"Error processing 'Labour': {e}")
    else:
        labour_sum = 0
        print("No 'Labour' column found. Setting labour_sum to 0.")

    # Calculate table total
    
    table_total = diamond_value + CS_value + labour_sum
    ws[f'B{table + 9}'] = table_total  # Write total to the cell

    # Split the number into dollars and cents
    dollars = int(table_total)
    cents = round((table_total - dollars) * 100)  # Get the cents part as an integer

    # Convert the dollar part and cents part to words
    dollar_words = num2words(dollars).title()  # Convert to words and capitalize each word
    cents_words = num2words(cents).title()  # Convert cents to words

    # Create the final text in the required format
    if cents > 0:
        words = f"Total Net Realisation Dollar {dollar_words} & Cent {cents_words} Only."
    else:
        words = f"Total Net Realisation Dollar {dollar_words} Only."

    # Write the final text to the Excel file
    # ws[f'B{table + 10}'] = words  # Write the text in the next row
    
   
    exchange_rate_value = float(request.form['exchange_rate'])  
    amount_chargeable_row_number = exchange_rate_row_number + 2  # Leave 1 row after exchange rate for amount chargeable 
    line_1 = amount_chargeable_row_number + 3  # Leave 1 row after exchange rate for amount chargeable 
    line_2 = line_1 + 3  # Leave 2 row after line 1 for line 2
    line_3 = line_2 + 2  # Leave 2 row after line 1 for line 2
    line_4 = line_3 + 2  # Leave 2 row after line 1 for line 2
    line_5 = line_4 + 1 # Leave 2 row after line 1 for line 2
    line_6 = line_5 + 2 # Leave 2 row after line 1 for line 2
    line_7 = line_6 + 1 # Leave 1 row after line 1 for line 2
    line_8 = line_7 + 1 # Leave 1 row after line 1 for line 2

    # Write the Exchange Rate in the first column
    ws.cell(row=exchange_rate_row_number, column=1, value=f"Exchange Rate: {exchange_rate_value}")
    from openpyxl.styles import Font
    ws.cell(row=exchange_rate_row_number, column=1).font = Font(bold=True)  # Make the text bold
    
     # Leave one blank row and write "Amount Chargeable (in Words)" below the Exchange Rate
    ws.cell(row=amount_chargeable_row_number, column=1, value="Amount Chargeable (in Words)")
    ws.cell(row=amount_chargeable_row_number, column=3, value= words)

    ws.cell(row=amount_chargeable_row_number, column=1).font = Font(bold=True)  # Make the text bold
    ws.cell(row=amount_chargeable_row_number, column=3).font = Font(bold=True)  # Make the text bold
  
    ws.cell(row=line_1, column=1, value="""I/we hereby certify that my/our registration certificate under Goods and Services Tax Act,2017 is in force on the date on which the supply of goods / services specified in this Tax Invoice/ Consignment sale is made by me/us and that the transaction of sale covered by this tax invoice/Consignment sales has been effected by me/us & it shall be accounted for in the turnover of sales while filling of return & the due tax, if any, payable on the sale has been paid or shall paid.""")																						
    ws.cell(row=line_1, column=1).font = Font(bold=True)  # Make the text bold
   
    ws.cell(row=line_2, column=1, value="""SUPPLY TO SEZ UNIT IS UNDER ZERO RATED SUPPLY AS PER THE IGST RULE.""")
    ws.cell(row=line_2, column=1).font = Font(bold=True)  # Make the text bold
    
    ws.cell(row=line_3, column=1, value="""SUPPLY MEANT FOR EXPORT/SUPPLY TO SEZ UNIT UNDER BOND OR LETTER OF UNDERTAKING WITHOUT PAYMENT OF INTERGRATED TAX AS PER THE IGST RULE""")
    ws.cell(row=line_3, column=1).font = Font(bold=True)  # Make the text bold
    
    # Print the same data inside the provided sentence
    formatted_sentence = f"Gold & Silver received from SEZ UNIT vide invoice No.{invoice_no_date} being returned after job work"
    ws.cell(row=line_4, column=1, value=formatted_sentence) 
    ws.cell(row=line_4, column=1).font = Font(bold=True)  # Make the text bold
    
    ws.cell(row=line_5, column=1, value="""This Invoice is for only Labour & Diamond Charges""")
    ws.cell(row=line_5, column=1).font = Font(bold=True)  # Make the text bold
   
    ws.cell(row=line_6, column=1, value="Declaration")
    ws.cell(row=line_6, column=1).font = Font(bold=True)  # Make the text bold
    
    ws.cell(row=line_7, column=1, value="We declare that this Invoice shows the actual price of the")
    ws.cell(row=line_7, column=1).font = Font(bold=True)  # Make the text bold
   
    ws.cell(row=line_8, column=1, value="goods described and that all particulars are true and correct.")
    ws.cell(row=line_8, column=1).font = Font(bold=True)  # Make the text bold

    
       
    # Save the file
    output_file = os.path.join(OUTPUT_DIR, "Formatted_Invoice.xlsx")
    wb.save(output_file)

    # Send the file for download
    return send_file(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name="Formatted_Invoice.xlsx")

def get_metal_mapping(output_header, row, ctg, metal_kt):
    return_dict = {}
    common_column = "Inv Rm Wt"
    metals = ['G','S', 'M', 'NTL', 'STL']
    metal_column = "Inv Pure Wt"
    stones = ['D', 'C']
    stone_column = "Inv Value"
    skip_headers = ['Metal Amt.'] 
    for header in output_header:
        if header in skip_headers: continue
        if constants.CATEGORY_DICT.get(ctg, '') in header.strip() or str(metal_kt) in header.strip():
            if ctg in metals:
                if ctg == 'G' and metal_kt not in header:
                    continue
                if 'pure' in header.lower():
                    return_dict[header] = round(row[metal_column], 3)
                else:
                    return_dict[header] = round(row[common_column], 3)
            elif ctg in stones:
                if 'cts' in header.lower():
                    return_dict[header] = round(row[common_column], 3)
                else:
                    return_dict[header] = round(row[stone_column], 2)

    return return_dict


def get_product_name(ctg):
    product_name = ''
    skip_list = ['nan', 'M']
    for i in ctg:
        value_list = i.split(',')
        for j in value_list:
            if j in skip_list:
                continue
            product_name = product_name + ' ' + (constants.STATEMENT_DICT.get(j, ''))

    return product_name.strip() + ' Jwellery'
        

def map_headers_to_data(headers, data):
    mapped_data = []
    for row in data:
        mapped_row = {header.strip(): row.get(header.strip(), None) for header in headers}
        mapped_data.append(mapped_row)
    return mapped_data


if __name__ == '__main__':
    app_job_work.run(debug=True)




																						
