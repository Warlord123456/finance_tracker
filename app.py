from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import re
from collections import defaultdict
from dateutil import parser
from PIL import Image
import pytesseract
import logging
from typing import List, Optional

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path as necessary

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY,
                        description TEXT,
                        amount REAL,
                        merchant TEXT,
                        invoice_number TEXT,
                        item_names TEXT,
                        date TEXT,
                        receipt_date TEXT,
                        category TEXT
                    )''')
    conn.commit()
    conn.close()

# Preprocess image before OCR
def preprocess_image(file_path):
    with Image.open(file_path) as img:
        img = img.convert('L')  # Convert to grayscale
        img = img.point(lambda x: 0 if x < 128 else 255, '1')  # Binarization
        preprocessed_path = file_path.replace('.jpg', '_preprocessed.jpg')  # Example for jpg files
        img.save(preprocessed_path)
        return preprocessed_path

# OCR processing using Tesseract
# OCR processing using Tesseract and save to text file
def ocr_receipt(file_path):
    try:
        # Preprocess the image
        preprocessed_path = preprocess_image(file_path)
        
        # Perform OCR on the preprocessed image
        ocr_text = pytesseract.image_to_string(Image.open(preprocessed_path))
        
        # Save OCR text to a file
        ocr_text_file = file_path.replace('.jpg', '.txt')  # Save as .txt file
        with open(ocr_text_file, 'w') as f:
            f.write(ocr_text)
        
        return ocr_text, ocr_text_file  # Return both the OCR text and the file path
    except Exception as e:
        print(f"OCR Error: {e}")
        return "", ""


# Route: Homepage
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

# Route: Upload receipt
@app.route('/upload', methods=['GET', 'POST'])
def upload_receipt():
    if request.method == 'POST':
        # Get the uploaded files
        files = request.files.getlist('file')
        
        for file in files:
            if file.filename == '':
                continue  # Skip empty file inputs

            # Save the uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Perform OCR and get both the OCR text and file path
            ocr_text, ocr_text_file = ocr_receipt(file_path)

            # Extract details from the OCR text
            amount, merchant, invoice_number, item_names, receipt_date = extract_details(ocr_text)

            # Categorize items
            categories = [categorize_item(item.strip()) for item in item_names.split(',')]
            category_string = ', '.join(set(categories))  # Unique categories

            # Save the extracted details and OCR file path to the database
            try:
                conn = sqlite3.connect('database.db')
                conn.execute(
                    """INSERT INTO expenses 
                    (description, amount, merchant, invoice_number, item_names, date, receipt_date, category) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                    ("Expense from receipt", amount, merchant, invoice_number, item_names, 
                     "2024-10-10", receipt_date, category_string)
                )
                conn.commit()
            except Exception as e:
                print(f"Database Error: {e}")
            finally:
                conn.close()

        return redirect(url_for('index'))

    return render_template('upload.html')


# Extract details from OCR text
def extract_details(ocr_text):
    try:
        if not ocr_text or ocr_text.strip() == "":
            raise ValueError("OCR text is empty or None. Please check the image quality or ensure Tesseract is installed correctly.")
        
        # Proceed with extracting the details
        invoice_number = extract_invoice_number(ocr_text)
        amount = extract_amount(ocr_text)
        merchant = extract_merchant(ocr_text)
        item_names = extract_item_names(ocr_text)
        receipt_date = extract_receipt_date(ocr_text)
        
        return amount, merchant, invoice_number, item_names, receipt_date
    
    except Exception as e:
        raise ValueError(f"Error extracting details: {str(e)}")



# Extract total amount from OCR text
def extract_amount(ocr_text):
    patterns = [
        r'Net\s*Value\s*[:$]?\s*(\d+(?:\.\d{1,2})?)',
        r'Grand\s*Total\s*[:$]?\s*(\d+(?:\.\d{1,2})?)',
        r'Total\s*[:$]?\s*(\d+(?:\.\d{1,2})?)',
        r'(?i)\btotal\b.*?(\d+(?:\.\d{1,2})?)',
        r'(\d+(?:\.\d{1,2})?)\s*total\s*',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            return float(matches[0])
    return 0.0

# Extract merchant name from OCR text
MERCHANT_KEYWORDS = [
    "merchant", "store", "company", "name", "dine", "bill", "token", 
    "token no", "from", "by", "cashier", "place", "taken"
]

def extract_merchant(ocr_text):
    keyword_pattern = r'(?i)(?:(?:' + '|'.join(MERCHANT_KEYWORDS) + r')\s*[:\-]?\s*|^\s*)([A-Za-z0-9\s&,.()\-]+)(?=\s*[\n\r]|$|(?=\d))'
    matches = re.findall(keyword_pattern, ocr_text)

    if matches:
        merchant_name = clean_string(matches[0])
        return merchant_name if merchant_name else "Unknown Merchant"
    
    # Fallback pattern
    fallback_pattern = r'(?i)^\s*([A-Za-z0-9\s&,.()\-]+)(?=\s*[\n\r]|$)'
    fallback_matches = re.findall(fallback_pattern, ocr_text)
    
    if fallback_matches:
        merchant_name = clean_string(fallback_matches[0])
        return merchant_name if merchant_name else "Unknown Merchant"

    return "Unknown Merchant"

def clean_string(string):
    string = re.sub(r'\s+', ' ', string)  # Replace multiple spaces
    string = re.sub(r'[^A-Za-z0-9\s&,.()\-]', '', string)  # Filter unwanted characters
    string = re.sub(r'\s*\(.*?\)\s*', ' ', string)  # Remove content in parentheses
    string = re.sub(r'(\d+.*|:.*|;.*)', '', string)  # Remove trailing numbers or colons
    return string.strip()

# Extract invoice number from OCR text
def extract_invoice_number(ocr_text: str) -> Optional[str]:
    if not ocr_text:
        logging.error("OCR text is empty or None")
        raise ValueError("OCR text is empty or None")

    # Define a list of possible invoice number patterns
    patterns: List[str] = [
        r'(?:Invoice|Inv|Bill|Receipt|Token|Order|Reference|Account)\s*(?:No|Number|ID|#|Code|Ref)\s*:\s*([0-9]+(?:\s*[0-9]+)*)',  # Matches various keywords with "No", "Number", "ID", etc.
        r'(?:Invoice|Inv|Bill|Receipt|Token|Order|Reference|Account)\s*(?:No|Number|ID|#|Code|Ref)\s*\.\s*([0-9]+(?:\s*[0-9]+)*)',  # Matches with period
        r'(?:Invoice|Inv|Bill|Receipt|Token|Order|Reference|Account)\s*(?:No|Number|ID|#|Code|Ref)\s*([0-9]+(?:\s*[0-9]+)*)',  # Matches without colon or period
        r'(?i)(?<!\d)\b(Invoice|Receipt|Bill)\s*:\s*([A-Z]{2,3}[0-9A-Z]{6,12})\b'
        r'\b(INV|BILL|RCPT|ORD|REF|ACC)\s*([0-9]+(?:\s*[0-9]+)*)\b',  # Matches abbreviations like "INV 12345"
        r'Inv\s*:\s*([A-Za-z0-9]+)',
        r'\b(?:Invoice|Inv|Bill|Receipt|Order|Ref)\s*([0-9]+(?:\s*[0-9]+)*)\b',  # Matches variations with keywords followed by numbers
        r'(?<![A-Za-z])([A-Z]{2,5}\s*[0-9]+(?:\s*[0-9]+)*)\b',  # Matches patterns like "AB 12345"
        r'(?:inv|Inv)\s*[=:]\s*([A-Z]{2,3}[0-9A-Z]{6,12})(?=\s|$)',  # Matches format "inv : LTN02A1920013472"
    ]

    # Iterate over the patterns and search for a match
    for pattern in patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            # If a match is found, return the invoice number
            invoice_number: str = match.group(1)
            logging.info(f"Extracted invoice number: {invoice_number}")
            return invoice_number

    # If no match is found, log an info message and return None
    logging.info("No invoice number found in OCR text")
    return None

# Extract receipt date from OCR text
def extract_receipt_date(ocr_text):
    date_pattern = r'''
        (?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4} |                    # MM/DD/YYYY or DD/MM/YYYY
        \b\w{3}[-/]\d{1,2}[-/]\d{2,4} |                        # MMM/DD/YYYY or MMM-DD-YYYY
        \b\w{3}\s*\d{1,2},?\s*\d{4} |                          # MMM DD, YYYY or MMM DD,YYYY
        \b\w{3}\s*\d{1,2} |                                     # MMM DD
        \d{4}[-/]\d{1,2}[-/]\d{1,2} |                           # YYYY-MM-DD
        \d{1,2}\s+\w{3}\s+\d{4} |                               # DD MMM YYYY
        \d{1,2}[-/]\d{1,2}[-/]\d{2,4} |                         # Alternate formats
        \b\d{1,2}[-]\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-]\d{2,4}\b | # DD-MMM-YY or DD-MMM-YYYY
        \b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-]\d{1,2}[-]\d{2,4}  # MMM-DD-YYYY or MMM-DD-YY
        )'''

    matches = re.findall(date_pattern, ocr_text, re.VERBOSE | re.IGNORECASE)

    for match in matches:
        try:
            # Parse the date considering different formats, especially for DD-MMM-YY
            parsed_date = parser.parse(match.strip(), dayfirst=True)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue  # If parsing fails, try the next match

    return "Unknown Date"

# Extract item names from OCR text
import re

def extract_item_names(ocr_text):
    # Refined regex pattern to capture item names more accurately
    items_pattern = r'(?i)(?<!\d)\b(?!\b(?:Name|Qty|share|your|store|feedback|service|Amount|Price|Total|Sub|Invoice|Tax|Grand|Discount|Subtotal|Receipt|Charge|Line Item|GST|EXCHANGE|DAYS|Thank You|Signature)\b)([A-Za-z\s&\-]+(?:\s+[A-Za-z\s&\-]*)*)(?=\s*\$?\d+(?:\.\d{1,2})?|\s*$)'
    
    # Find all matches using the refined pattern
    matches = re.findall(items_pattern, ocr_text)

    # Clean and filter the matched items
    items = [match.strip() for match in matches if match.strip() and len(match.strip()) > 2]
    
    # Set of terms to exclude for better performance
    exclude_terms = {"Qty", "Amount", "Total", "Sub", "Invoice", "Tax", "Grand", 
                     "Discount", "Subtotal", "Receipt", "Charge", "Line Item", 
                     "GST", "EXCHANGE", "DAYS", "Thank You", "Signature"}

    # Further filter items based on specific criteria
    filtered_items = [
        item for item in items
        if not any(term in item for term in exclude_terms)  # Exclude terms
        and not any(char.isdigit() for char in item)        # Exclude items with digits
        and len(item.split()) > 1                            # Ensure item has more than one word
    ]

    # Return the filtered items as a bullet-separated string or a default message
    return '• ' + '\n• '.join(filtered_items) if filtered_items else "No Items Found"



# Categorize item based on keywords
CATEGORY_KEYWORDS = {
    'food': [
        'burger', 'rolls', 'coke', 'pizza', 'sandwich', 'restaurant', 'meal', 
        'lunch', 'dinner', 'breakfast', 'coffee', 'tea', 'snack', 'beverage', 
        'soda', 'fries', 'salad', 'juice', 'dessert', 'pasta', 'soup', 'chicken', 
        'steak', 'fish', 'seafood', 'beef', 'bacon', 'sausage', 'cake', 'cookie', 
        'chocolate', 'ice cream', 'groceries', 'supermarket', 'market', 'fruit', 
        'vegetable', 'dairy', 'bakery', 'catered', 'vending', 'fast food', 
        'takeout', 'catering', 'treat', 'coffee shop', 'brunch', 'pub', 
        'barbecue', 'buffet', 'deli', 'donuts', 'pastry', 'tea house', 
        'smoothie', 'wrap', 'taco', 'sushi', 'pancakes', 'waffles', 'cereal', 
        'oatmeal', 'bento', 'curry', 'salsa', 'dips', 'spices', 'condiments', 
        'meal prep', 'delivery', 'kitchen gadgets', 'gourmet', 'organic', 
        'meal plan', 'takeaway', 'picnic'
    ],
    'transport': [
        'gas', 'fuel', 'uber', 'taxi', 'parking', 'toll', 'fare', 'train', 
        'bus', 'ticket', 'ride', 'shuttle', 'car rental', 'vehicle', 'airfare', 
        'flight', 'bicycle', 'motorcycle', 'ride-sharing', 'public transport', 
        'commuting', 'road trip', 'limo', 'auto repair', 'insurance', 
        'registration', 'tow', 'vehicle maintenance', 'ferry', 'subway', 
        'carpool', 'vanpool', 'car wash', 'valet', 'fuel cards', 'bridge toll', 
        'travel cards', 'maintenance', 'lease', 'accident repair', 'roadside assistance'
    ],
    'entertainment': [
        'movie', 'theater', 'concert', 'sports', 'event', 'ticket', 'museum', 
        'amusement park', 'zoo', 'arcade', 'bowling', 'game', 'show', 'streaming', 
        'subscription', 'videogame', 'nightclub', 'comedy', 'dancing', 'golf', 
        'spa', 'wellness', 'fitness', 'exercise', 'hobby', 'craft', 'art supplies',
        'live music', 'cultural event', 'festival', 'exhibition', 'online course', 
        'podcast subscription', 'dance class', 'art class', 'cooking class', 
        'personal training', 'fitness membership', 'skating', 'sports club', 
        'season passes', 'season tickets', 'social clubs', 'group activities'
    ],
    'shopping': [
        'clothes', 'shoes', 'accessories', 'jewelry', 'electronics', 'gadget', 
        'furniture', 'decor', 'appliances', 'hardware', 'books', 'stationery', 
        'toys', 'gifts', 'hobbies', 'shopping mall', 'online shopping', 'sale', 
        'discount', 'thrift store', 'boutique', 'marketplace', 'craft fair', 
        'subscription box', 'e-commerce', 'retail', 'warehouse', 'shopping spree', 
        'gift cards', 'fashion', 'second-hand', 'custom items', 'artwork', 
        'craft supplies', 'gift wrapping', 'alterations', 'returns', 'exchanges', 
        'online marketplace', 'auction', 'digital goods', 'seasonal sales'
    ],
    'healthcare': [
        'doctor', 'medical', 'hospital', 'clinic', 'pharmacy', 'prescription', 
        'health insurance', 'dentist', 'check-up', 'vaccination', 'wellness', 
        'therapy', 'medicine', 'supplement', 'gym', 'fitness class', 'yoga', 
        'physical therapy', 'chiropractor', 'optometrist', 'laboratory', 
        'emergency', 'counseling', 'massage', 'nutritionist', 'wellness retreat', 
        'dental care', 'mental health', 'alternative medicine', 'preventive care', 
        'immunization', 'blood tests', 'urgent care', 'eye exam', 'prescriptions', 
        'wellness exam', 'holistic treatments', 'medical equipment', 'therapy sessions'
    ],
    'utilities': [
        'electricity', 'water', 'gas', 'internet', 'phone', 'cable', 'trash', 
        'sewer', 'home insurance', 'property tax', 'maintenance', 'repairs', 
        'cleaning', 'landscaping', 'security', 'pest control', 'heating', 
        'cooling', 'internet streaming', 'mobile plan', 'satellite', 
        'phone upgrade', 'contract', 'service fees', 'subscription services'
    ],
    'travel': [
        'hotel', 'accommodation', 'hostel', 'bed and breakfast', 'resort', 
        'vacation', 'trip', 'sightseeing', 'travel insurance', 'tour', 
        'cruise', 'guide', 'transportation', 'souvenirs', 'exploration', 
        'excursion', 'backpacking', 'road trip', 'camping', 'international', 
        'domestic', 'travel gear', 'passport', 'visa', 'lodging', 
        'meal expenses', 'activities', 'adventure', 'sightseeing tours', 
        'transportation tickets', 'itinerary planning', 'guided tours', 
        'hotel booking', 'car rental', 'adventure tours'
    ],
    'education': [
        'tuition', 'school', 'college', 'university', 'course', 'books', 
        'supplies', 'fees', 'online learning', 'workshop', 'seminar', 
        'tutoring', 'library', 'certification', 'training', 'webinar', 
        'degree', 'extracurricular', 'scholarship', 'study materials', 
        'educational trips', 'field trips', 'education technology', 
        'professional development', 'research materials', 'course materials', 
        'enrollment fees', 'online courses', 'distance learning'
    ],
    'home': [
        'rent', 'mortgage', 'property tax', 'home insurance', 'repairs', 
        'maintenance', 'furniture', 'appliances', 'supplies', 'decor', 
        'gardening', 'renovation', 'cleaning', 'home improvement', 
        'landscaping', 'pest control', 'utilities', 'security', 
        'HVAC maintenance', 'interior design', 'furnishing', 'home services', 
        'homeowners association fees', 'yard care', 'construction', 
        'remodeling', 'appliance installation', 'handyman services'
    ],
    'personal care': [
        'haircut', 'salon', 'spa', 'manicure', 'pedicure', 'skin care', 
        'makeup', 'toiletries', 'fragrance', 'shaving', 'hair products', 
        'beauty treatments', 'cosmetic', 'wellness', 'personal grooming', 
        'barber', 'facial', 'nail care', 'tanning', 'hair coloring', 
        'cosmetic procedures', 'massage therapy', 'essential oils', 
        'wellness products', 'beauty subscriptions','shampoo'
    ],
    'gifts & donations': [
        'gifts', 'donations', 'charity', 'tithing', 'fundraising', 
        'event gifts', 'wedding gifts', 'birthday gifts', 'holiday gifts', 
        'volunteering expenses', 'sponsorship', 'community support', 
        'gifts in kind', 'philanthropy', 'crowdfunding', 'memorial donations', 
        'gift registries', 'charitable contributions'
    ],
    'insurance': [
        'health insurance', 'auto insurance', 'home insurance', 'life insurance', 
        'travel insurance', 'business insurance', 'disability insurance', 
        'liability insurance', 'premium payments', 'deductibles', 
        'coverage', 'policy fees', 'claims', 'insurance broker', 
        'riders', 'endorsements'
    ],
    'miscellaneous': [
        'pet care', 'grooming', 'training', 'pet supplies', 'hobbies', 
        'donations', 'gifts', 'unexpected expenses', 'maintenance', 
        'legal fees', 'bank fees', 'subscriptions', 'membership', 
        'taxes', 'repairs', 'miscellaneous expenses', 'office supplies', 
        'household items', 'decorative items', 'seasonal expenses', 
        'miscellaneous services', 'emergency fund'
    ]
    # Add more categories and keywords as needed
}
@app.route('/reports')
def reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Fetch all expenses
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = cursor.fetchall()
    conn.close()

    # Prepare labels and data for the report
    category_labels = [row[0] for row in category_data]  # Category names
    category_amounts = [row[1] for row in category_data]  # Corresponding total amounts

    return render_template('reports.html', category_labels=category_labels, category_data=category_amounts)




def categorize_item(item):
    item = item.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in item for keyword in keywords):
            return category
    return 'Other'

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404notfound.html'), 404

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
