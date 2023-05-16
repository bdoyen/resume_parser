import os
from dataclasses import dataclass


@dataclass
class Config:
    # input dir
    INPUT_DIRECTORY_PATH = "./inputs"

    # resume default language
    USED_LANGUAGE: str = "english"
    SPACY_LANGUAGE_MODEL = "en_core_web_sm"

    # models
    MODELS_DIR: str = "./models"
    NLI_MODEL_DIR: str = os.path.join(MODELS_DIR, "nli_model/")
    NER_MODEL_DIR: str = os.path.join(MODELS_DIR, "ner_model/")

    QUANTIZED_NLI_MODEL_DIR: str = os.path.join(MODELS_DIR, "quantized_model_nli/")
    QUANTIZED_NLI_MODEL_ONNX: str = "model_quantized.onnx"
    QUANTIZED_NER_MODEL_DIR: str = os.path.join(MODELS_DIR, "quantized_model_ner/")
    QUANTIZED_NER_MODEL_ONNX: str = "model_quantized.onnx"
    NER_MODEL_SKILLS_DIR: str = os.path.join(MODELS_DIR, "ner_model_for_skills/")

    # resources
    RESOURCES_DIR: str = "./resources"
    SKILLS_CSV = os.path.join(RESOURCES_DIR, "./skills.csv")
    DEGREES_ABBREVIATIONS_CSV = os.path.join(
        RESOURCES_DIR, "./degrees_abbreviations.csv"
    )

    # parsers
    PRESENT_KEYWORDS = ["present", "now", "actual"]
    EMPLOYMENT_NLI_CLASSES: tuple[str] = (
        "institution name",
        "company name",
        "job title",
        "location",
        "other",
    )
    EMPLOYMENT_LOCATION_NLI_CLASSES: tuple[str] = ("location",)
    EMPLOYER_NLI_CLASSES: tuple[str] = (
        "institution name",
        "company name",
    )
    JOB_NLI_CLASSES: tuple[str] = ("job title",)
    JOB_DESCRIPTION_CLASSES: tuple[str] = ("description",)
    SKILLS_NER_TAGS: tuple[str] = ("SKILL", "TOOL")
    DESIGNATION_TAG: str = "Designation"
    PERSON_TAG: str = "PERSON"
    EDUCATION_NLI_CLASSES: tuple[str] = (
        "university or school name",
        "study place",
        "study topic",
        "other",
    )
    DEGREE_MAJOR_CLASSES: tuple[str] = ("study topic",)
    SCHOOL_CLASSES: tuple[str] = (
        "university or school name",
        "study place",
    )

    # messages
    MESSAGE_COMPLETED = "Parsing Complete"
    MESSAGE_UNCOMPLETED = "Parsing Uncomplete"
    MESSAGE_STATUS_SUCCESS = "succeeded"
    MESSAGE_STATUS_UNSUCCESS = "unsucceeded"
