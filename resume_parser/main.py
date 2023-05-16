import os
import shutil
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException

from config import Config
from data_models import ResumeParsingResponse
from reader import Reader
from segmenter import TextSegmenter
from parsers import Parsers
from models import Models
from utils import (
    cleaning_and_creating_tree,
    generate_metadata,
)
from headers import Headers

logging.basicConfig(
    format="%(levelname)s : %(funcName)s : %(message)s", level=logging.INFO
)

app = FastAPI()

# instanciate project main objects
segmenter = TextSegmenter()
parsers = Parsers()

# load models
models = Models()


def parse_resume(resume_lines):
    try:
        # segment full text into distinct sections
        full_text = " ".join(resume_lines)
        segments = segmenter.segmenter(full_text)

        # extract skills
        skills = parsers.parse_skills(
            segments.get("skills", ""),
        )

        # extract contact data
        contact = parsers.parse_contact_data(
            segments.get("headline", ""),
        )

        # parse name and current job designation
        name, summary = parsers.parse_headline(
            segments.get("headline", ""),
            models.ner_pipeline,
        )

        # extract personal data
        personal = parsers.parse_personal_data(name)

        # extract languages
        languages = parsers.parse_languages(full_text)

        # extract education
        education = parsers.parse_with_fallback(
            parsers.parse_education_and_trainings,
            resume_lines,
            segments.get("education", ""),
            segments.get(Headers.DEFAULT_SEGMENT, ""),
            models.zero_shot_classifier_pipeline,
        )

        # extract work experience
        experience = parsers.parse_with_fallback(
            parsers.parse_work_experience,
            resume_lines,
            segments.get("experience", ""),
            segments.get(Headers.DEFAULT_SEGMENT, ""),
            models.zero_shot_classifier_pipeline,
        )

        # final part
        metadata = generate_metadata(full_text)

        return ResumeParsingResponse(
            skills=skills,
            contact=contact,
            summary=summary,
            metadata=metadata,
            personal=personal,
            education=education,
            experience=experience,
            languages=languages,
        )

    except Exception as e:
        logging.error(f"Resume Parsing failed : {e}")
        metadata = generate_metadata(
            "",
            remark=Config.MESSAGE_UNCOMPLETED,
            status=Config.MESSAGE_STATUS_UNSUCCESS,
        )
        return ResumeParsingResponse(
            metadata=metadata,
        )


@app.post("/parse_resume/", response_model=ResumeParsingResponse)
def parse_resume_endpoint(upload_file: UploadFile = File(...)):
    reader = Reader()

    # save uploaded file into inputs directory
    logging.info("Cleaning and creating tree for input files")
    cleaning_and_creating_tree(Config.INPUT_DIRECTORY_PATH)
    file_name = upload_file.filename
    _, extension = os.path.splitext(file_name)
    if not extension.lower() == ".pdf":
        logging.error(f"The file {file_name} is not a PDF")
        raise HTTPException(status_code=400, detail="The given file is not a PDF")
    input_file_saving_path = os.path.join(Config.INPUT_DIRECTORY_PATH, file_name)
    with open(input_file_saving_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    upload_file.file.close()

    if not os.path.exists(input_file_saving_path):
        logging.error("Could not save the PDF file")
        raise HTTPException(status_code=500, detail="Could not save the PDF file")

    # extract text from PDF file
    text = reader.pdf_to_text(input_file_saving_path)

    # extract and clean lines layout from doc
    resume_lines = reader.get_document_lines(text)

    # parse info
    resume_info = parse_resume(resume_lines)

    return resume_info
