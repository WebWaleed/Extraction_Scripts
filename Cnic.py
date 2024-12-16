
# import numpy as np
# import cv2
# import easyocr
# import re
# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# import uvicorn
# from io import BytesIO
# from PIL import Image

# app = FastAPI()

# def extract_cnic_info(image):

#     # Increase contrast and brightness without converting to grayscale
#     alpha = 1.5  # Increase contrast
#     beta = 0     # Brightness
#     adjusted_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

#     # Resize the image for better OCR accuracy
#     resized_image = cv2.resize(adjusted_image, (0, 0), fx=1.5, fy=1.5)

#     # Use EasyOCR to extract text (no thresholding to avoid loss of information)
#     reader = easyocr.Reader(['en', 'ur'], gpu=False)  # Disable GPU for faster startup
#     result = reader.readtext(resized_image)

#     # Save extracted text from image
#     recognized_text_lines = [word[1] for word in result]  # Extract text lines
#     recognized_text = "\n".join(recognized_text_lines)

#     # Pattern to find dates
#     date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
#     all_dates = re.findall(date_pattern, recognized_text)

#     # Heuristic function to match dates to labels
#     def match_dates_to_labels(labels, lines):
#         matched_dates = {label: "Not Found" for label in labels}
#         used_dates = set()
        
#         for label in labels:
#             try:
#                 # Find index of the label in the recognized text lines
#                 label_index = next(i for i, line in enumerate(lines) if label in line)

#                 # Search for a date within the next few lines after the label
#                 for i in range(label_index + 1, len(lines)):
#                     # Check if a valid date exists nearby
#                     date_match = re.search(date_pattern, lines[i])
#                     if date_match and date_match.group(0) not in used_dates:
#                         matched_dates[label] = date_match.group(0)
#                         used_dates.add(date_match.group(0))
#                         break
#             except StopIteration:
#                 continue

#         # Fallback mechanism: Try to assign remaining unassigned labels from the list of all found dates
#         remaining_dates = [date for date in all_dates if date not in used_dates]
        
#         for label in labels:
#             if matched_dates[label] == "Not Found" and remaining_dates:
#                 matched_dates[label] = remaining_dates.pop(0)
        
#         return matched_dates

#     # Extract the dates using the updated approach
#     date_labels = ['Date of Birth', 'Date of Issue', 'Date of Expiry']
#     matched_dates = match_dates_to_labels(date_labels, recognized_text_lines)

#     # Extracted information using regex
#     data = {
#         "name": re.search(r'Name\s+([A-Za-z\s]+)', recognized_text),
#         "father_name": re.search(r'Father Name\s+([A-Za-z\s]+)', recognized_text),
#         "identity_number": re.search(r'(\d{5}-\d{7}-\d)', recognized_text),
#         "gender": re.search(r'Gender\s*.*?\n.*?([MF])', recognized_text, re.IGNORECASE),
#         "date_of_birth": matched_dates['Date of Birth'],
#         "date_of_issue": matched_dates['Date of Issue'],
#         "date_of_expiry": matched_dates['Date of Expiry']
#     }

#     # Format the extracted information
#     formatted_data = {}
#     for key, value in data.items():
#         if isinstance(value, re.Match):  # If it's a regex match object
#             # Apply `.strip()` to remove any leading/trailing whitespace including `\n`
#             formatted_data[key.replace('_', ' ').capitalize()] = value.group(1).strip()
#         elif value:  # If it's a string (like date fields)
#             formatted_data[key.replace('_', ' ').capitalize()] = value
#         else:
#             formatted_data[key.replace('_', ' ').capitalize()] = "Not Found"
    
#     return formatted_data

# @app.post("/Extract-Cnic/")
# async def extract_cnic(file: UploadFile = File(...)):
#     # Read image file as a byte stream and load it with PIL
#     image_data = await file.read()
#     image = Image.open(BytesIO(image_data)).convert('RGB')

#     # Convert the image to a NumPy array
#     image_np = np.array(image)

#     # Extract CNIC info
#     extracted_info = extract_cnic_info(image_np)

#     return JSONResponse(content=extracted_info)
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import easyocr
import numpy as np
import re
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()

# MongoDB Initialization
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["cnic_work"]
collection = db["cnic__data"]

# Function to match dates to labels
def match_dates_to_labels(labels, lines):
    lines = [s.replace(',', '.') for s in lines]
    date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'  # Matches dates in DD.MM.YYYY format
    matched_dates = {label: "Not Found" for label in labels}
    used_dates = set()

    all_dates = re.findall(date_pattern, "\n".join(lines))

    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD format
        except ValueError:
            return date_str  # If conversion fails, return original format

    for label in labels:
        try:
            label_index = next(i for i, line in enumerate(lines) if label in line)

            for i in range(label_index + 1, len(lines)):
                date_match = re.search(date_pattern, lines[i])
                if date_match and date_match.group(0) not in used_dates:
                    matched_dates[label] = format_date(date_match.group(0))
                    used_dates.add(date_match.group(0))
                    break
        except StopIteration:
            continue

    remaining_dates = [date for date in all_dates if date not in used_dates]

    for label in labels:
        if matched_dates[label] == "Not Found" and remaining_dates:
            matched_dates[label] = format_date(remaining_dates.pop(0))

    return matched_dates

@app.post("/Extract_cnic/")
async def extract_cnic(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_data = await file.read()
        image = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(content={"error": "Invalid image file"}, status_code=400)

        # Increase contrast and brightness
        alpha = 0.8
        beta = -25
        adjusted_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        # Resize the image
        resized_image = cv2.resize(adjusted_image, (0, 0), fx=1.5, fy=1.5)

        # Use EasyOCR to extract text
        reader = easyocr.Reader(['en', 'ur'], gpu=False)
        result = reader.readtext(resized_image)

        if not result:
            return JSONResponse(content={"error": "No text detected in the image"}, status_code=400)

        recognized_text_lines = [word[1] for word in result]
        recognized_text = "\n".join(recognized_text_lines)

        # Extract dates
        date_labels = ['Date of Birth', 'Date of Issue', 'Date of Expiry']
        matched_dates = match_dates_to_labels(date_labels, recognized_text_lines)

        # Extract Name
        res = []
        sub1 = "Name"
        sub2 = "Father"

        idx1 = recognized_text.index(sub1)
        idx2 = recognized_text.index(sub2)

        res = recognized_text[idx1 + len(sub1) + 1: idx2].splitlines()
        extractname = res[0]

        # Extract Father Name
        father_res = []
        sub1 = "Father"
        sub2 = "Gender"

        idx1 = recognized_text.index(sub1)
        idx2 = recognized_text.index(sub2)
        father_res = recognized_text[idx1 + len(sub1) + 1: idx2].splitlines()

        def contains_english(word):
            return bool(re.search('[a-zA-Z]', word))

        father_res = [word for word in father_res if contains_english(word)]
        extractfather = father_res[1]

        idt_number = re.search(r'(\d{5}-\d{7}-\d)', recognized_text).group(0) if re.search(r'(\d{5}-\d{7}-\d)', recognized_text) else "Not Found"
        idtnew = idt_number.replace("-", "")
        idtnew = int(idtnew)

        Gender = ""
        if "\nM\n" in recognized_text:
            Gender = "M"
        elif "\nF\n" in recognized_text:
            Gender = "F"

        all_dates = []
        date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
        recognized_text_lines = [s.replace(',', '.') for s in recognized_text_lines]
        all_dates = re.findall(date_pattern, "\n".join(recognized_text_lines))

        formatted_dates = [datetime.strptime(date, '%d.%m.%Y').strftime('%Y-%m-%d') for date in all_dates]

        # Assign the formatted dates to respective variables
        dateofbirth = formatted_dates[0]
        dateofissue = formatted_dates[1]
        dateofexpiry = formatted_dates[2]

        # Extract CNIC information using regex
        extracted_data = {
            "name": extractname,
            "father_name": extractfather,
            "identity_number": idtnew,
            "gender": Gender,
            "date_of_birth": dateofbirth,
            "date_of_issue": dateofissue,
            "date_of_expiry": dateofexpiry
        }

        # Insert extracted data into MongoDB
        result = collection.insert_one(extracted_data)

        # Prepare the response
        response = {
            "message": "Data extracted and inserted successfully",
            "extracted_data": {
                **extracted_data,
                "_id": str(result.inserted_id)  # Convert ObjectId to string
            }
        }

        # Return the response
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(content={"error": "An internal error occurred. Please try again later."}, status_code=500)
