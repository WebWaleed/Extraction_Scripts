# import re
# from pdfminer.high_level import extract_text
# import spacy
# from spacy.matcher import Matcher
# from fastapi import FastAPI, UploadFile, File

# # Initialize FastAPI app
# app = FastAPI()

# # Function to extract text from PDF
# def extract_text_from_pdf(pdf_path):
#     return extract_text(pdf_path)

# # Function to extract contact number
# def extract_contact_number_from_resume(text):
#     contact_number = None
#     pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
#     match = re.search(pattern, text)
#     if match:
#         contact_number = match.group()
#     return contact_number

# # Function to extract email
# def extract_email_from_resume(text):
#     email = None
#     pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
#     match = re.search(pattern, text)
#     if match:
#         email = match.group()
#     return email

# # Function to extract skills
# def extract_skills_from_resume(text, skills_list):
#     skills = []
#     for skill in skills_list:
#         pattern = r"\b{}\b".format(re.escape(skill))
#         match = re.search(pattern, text, re.IGNORECASE)
#         if match:
#             skills.append(skill)
#     return skills

# # Function to extract education
# def extract_education_from_resume(text):
#     education = []
#     text = text.replace('\n', ' ')
#     pattern = r"(?i)(B\.?E|B\.?A|Bachelor(?:s)?|Bsc|M\.?E|M\.?A|Master(?:s)?|Ph\.?D|M\.?Com|B\.?Com)\s+(?:of\s+)?([A-Za-z\s]+(?:\s+in\s+[A-Za-z\s]+)?)"
#     matches = re.findall(pattern, text)
#     for match in matches:
#         degree_subject = ' '.join(filter(None, match)).strip()
#         if degree_subject:
#             education.append(degree_subject)
#     education = list(set(education))
#     education = [degree.replace('  ', ' ').strip() for degree in education]
#     education = [degree for degree in education if degree]
#     return education

# # Function to extract name using spaCy
# def extract_name(resume_text):
#     nlp = spacy.load('en_core_web_sm')
#     matcher = Matcher(nlp.vocab)
#     patterns = [
#         [{'POS': 'PROPN'}, {'POS': 'PROPN'}],
#         [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],
#         [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]
#     ]
#     for pattern in patterns:
#         matcher.add('NAME', patterns=[pattern])
#     doc = nlp(resume_text)
#     matches = matcher(doc)
#     for match_id, start, end in matches:
#         span = doc[start:end]
#         return span.text
#     return None

# # Function to extract experience
# def extract_experience(text):
#     experience_pattern = re.compile(r'(?i)PROFESSIONAL EXPERIENCE\s*([\s\S]*?)(?=\n\s*EDUCATION|$)', re.DOTALL)
#     experience_matches = experience_pattern.findall(text)
   
#     experiences = []
#     if not experience_matches:
#         return ["No experience found."]
   
#     for experience_section in experience_matches:
#         detail_pattern = re.compile(r'([A-Za-z\s]+)\n([A-Za-z\s]+)\n\n.*?(\d{1,2}/\d{4}\s*–\s*(?:present|\d{1,2}/\d{4}))', re.DOTALL)
#         detail_matches = detail_pattern.findall(experience_section)
       
#         for _, company, dates in detail_matches:
#             experiences.append(f"{company.strip()} {dates.strip()}")
   
#     return experiences if experiences else ["No experience found."]

# # API route to handle file uploads and extract information
# @app.post("/extract/")
# async def extract_resume_data(file: UploadFile = File(...)):
#     # Save uploaded PDF
#     contents = await file.read()
#     with open("temp_resume.pdf", "wb") as f:
#         f.write(contents)
    
#     # Extract text from PDF
#     text = extract_text_from_pdf("temp_resume.pdf")

#     # Extract various information from the resume
#     name = extract_name(text)
#     contact_number = extract_contact_number_from_resume(text)
#     email = extract_email_from_resume(text)
#     skills_list = ['Python', 'Data Analysis', 'Machine Learning', 'Communication', 'Project Management', 'Deep Learning', 'SQL', 'Tableau']
#     skills = extract_skills_from_resume(text, skills_list)
#     education = extract_education_from_resume(text)
#     experience = extract_experience(text)

#     # Return extracted data as JSON
#     return {
#         "name": name or "Name not found",
#         "contact_number": contact_number or "Contact number not found",
#         "email": email or "Email not found",
#         "skills": skills or "No skills found",
#         "education": education or "No education information found",
#         "experience": experience or "No experience found"
#     }

# # To run the server: uvicorn main:app --reload
import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from fastapi import FastAPI, UploadFile, File
from pymongo import MongoClient
import requests

# Initialize FastAPI app
app = FastAPI()

# MongoDB Initialization
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Resume_work"]
collection = db["resume_information"]

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

# Function to extract contact number
def extract_contact_number_from_resume(text):
    contact_number = None
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, text)
    if match:
        contact_number = match.group()
    return contact_number

# Function to extract email
#def extract_email_from_resume(text):
#    email = None
#    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
#    match = re.search(pattern, text)
#    if match:
#       email = match.group()
#    return email

def extract_email_from_resume(text):
    url = "http://192.168.100.75:3535/ask_anything/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Data to be sent in the request
    data = {
          'query': f'extract user\'s mail from this text "{text}"'
    }
    response = requests.post(url, headers=headers, data=data)
    email = None
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, response.json())
    if match:
        email = match.group()
    return email

# Function to extract skills
def extract_skills_from_resume(text, skills_list):
    skills = []
    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            skills.append(skill)
    return skills

# Function to extract education
def extract_education_from_resume(text):
    education = []
    text = text.replace('\n', ' ')
    pattern = r"(?i)(B\.?E|B\.?A|Bachelor(?:s)?|Bsc|M\.?E|M\.?A|Master(?:s)?|Ph\.?D|M\.?Com|B\.?Com)\s+(?:of\s+)?([A-Za-z\s]+(?:\s+in\s+[A-Za-z\s]+)?)"
    matches = re.findall(pattern, text)
    for match in matches:
        degree_subject = ' '.join(filter(None, match)).strip()
        if degree_subject:
            education.append(degree_subject)
    education = list(set(education))
    education = [degree.replace('  ', ' ').strip() for degree in education]
    education = [degree for degree in education if degree]
    return education

# Function to extract name using spaCy
def extract_name(resume_text):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}],
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]
    ]
    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text
    return None

# Function to extract experience
def extract_experience(text):
    experience_pattern = re.compile(r'(?i)PROFESSIONAL EXPERIENCE\s*([\s\S]*?)(?=\n\s*EDUCATION|$)', re.DOTALL)
    experience_matches = experience_pattern.findall(text)
   
    experiences = []
    if not experience_matches:
        return ["No experience found."]
   
    for experience_section in experience_matches:
        detail_pattern = re.compile(r'([A-Za-z\s]+)\n([A-Za-z\s]+)\n\n.*?(\d{1,2}/\d{4}\s*â€“\s*(?:present|\d{1,2}/\d{4}))', re.DOTALL)
        detail_matches = detail_pattern.findall(experience_section)
       
        for _, company, dates in detail_matches:
            experiences.append(f"{company.strip()} {dates.strip()}")
   
    return experiences if experiences else ["No experience found."]

# API route to handle file uploads and extract information
@app.post("/resume_extract/")
async def extract_resume_data(file: UploadFile = File(...)):
    # Save uploaded PDF
    contents = await file.read()
    with open("temp_resume.pdf", "wb") as f:
        f.write(contents)
    
    # Extract text from PDF
    text = extract_text_from_pdf("temp_resume.pdf")

    # Extract various information from the resume
    name = extract_name(text)
    contact_number = extract_contact_number_from_resume(text)
    email = extract_email_from_resume(text)
    skills_list = ['Python', 'Data Analysis', 'Machine Learning', 'Communication', 'Project Management', 'Deep Learning', 'SQL', 'Tableau']
    skills = extract_skills_from_resume(text, skills_list)
    education = extract_education_from_resume(text)
    experience = extract_experience(text)

    # Create a document to insert into MongoDB
    extracted_data = {
        "name": name or "Name not found",
        "contact_number": contact_number or "Contact number not found",
        "email": email or "Email not found",
        "skills": skills or "No skills found",
        "education": education or "No education information found",
        "experience": experience or "No experience found"
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

    return response

# To run the server: uvicorn main:app --reload
