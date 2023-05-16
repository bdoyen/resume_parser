import re
import logging
import pycountry
import phonenumbers
from datetime import datetime
from urlextract import URLExtract
from nameparser import HumanName
from transformers import pipeline
import gender_guesser.detector as gender

from config import Config
from utils import (
    get_max_element,
    find_location_entities,
    get_country_code,
    filter_stopwords,
    timedelta_in_months,
    # get_gender_from_firstname,
    group_elements_by_index,
    filter_dates_for_a_segment,
    merge_doubled_words,
    read_csv_list,
)
from data_models import (
    ContactData,
    Experience,
    ExperienceData,
    SkillsData,
    Education,
    EducationData,
    PersonalData,
    LanguagesData,
    SummaryData,
)

logging.basicConfig(
    format="%(levelname)s : %(funcName)s : %(message)s", level=logging.INFO
)

DEGREES = read_csv_list(Config.DEGREES_ABBREVIATIONS_CSV)
SKILLS = read_csv_list(Config.SKILLS_CSV)
logging.info("Successfully loaded other resources ✔")

RE_PHONE_NUMBERS = r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"
RE_MAIL = r"([^@|\s]+@[^@]+\.[^@|\s]+)"
# for numerical and non_numerical months
RE_DATES = r"(\b\d{1,2}[-/](?:\d{1,2}|[a-zA-Z]+)[-/]\d{2,4}\b|\b\d{1,2}[-/]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:\d{1,2},?\s+)?\d{2,4}\b|\b\d{4}\b)"


class Parsers:
    # def __init__(self,):
    # self.gender_detector = gender.Detector(case_sensitive=False)

    def parse_phone_number(self, text: str, possible_country: str | None = None) -> str:
        """
        Extract phone numbers from a given text.

        Args:
            text (str): The input text.
            possible_country (Optional[str]): The possible country to use for phone number extraction.

        Returns:
            str: The extracted phone number or an empty string if not found.
        """
        try:
            return [
                {"type": "Telephone", "value": phone.raw_string}
                for phone in list(
                    iter(phonenumbers.PhoneNumberMatcher(text, possible_country))
                )
            ]
        except:
            try:
                return [
                    {"type": "Telephone", "value": phone}
                    for phone in re.findall(RE_PHONE_NUMBERS, text)
                ]
            except:
                return [{"type": "Telephone", "value": ""}]

    def parse_email(self, text: str) -> str:
        """
        Extract the first email address from the given text.

        Args:
            text (str): The input text.

        Returns:
            str: The extracted email address or an empty string if not found.
        """
        emails = re.findall(RE_MAIL, text)
        if emails:
            try:
                return [{"value": email.split()[0].strip(";")} for email in emails]
            except IndexError:
                return [{"value": ""}]

    def parse_url(self, text: str) -> str:
        """
        Extract URLs from the given text.

        Args:
            text (str): The input text.

        Returns:
            List[str]: A list of extracted URLs.
        """
        extractor = URLExtract()

        return urls[:1] if (urls := extractor.find_urls(text)) else ""

    def parse_headline(self, text, ner_pipeline):
        entities = ner_pipeline(text, aggregation_strategy="simple")
        name, designation = "", ""
        for ent in entities:
            if ent["entity_group"] == Config.DESIGNATION_TAG:
                designation = " ".join((designation, ent["word"]))
            elif ent["entity_group"] == Config.PERSON_TAG:
                name += " ".join((name, ent["word"]))
            else:
                continue

        return (
            merge_doubled_words(name.strip()),
            SummaryData(description=merge_doubled_words(designation.strip())),
        )

    def parse_personal_data(self, full_name):
        name_parts = HumanName(full_name.lower())
        # gender = get_gender_from_firstname(
        #    detector,
        #    first_name:=name_parts.first
        # )

        return PersonalData(
            full_name=full_name,
            first_name=name_parts.first,
            middle_name=name_parts.middle.capitalize(),
            family_name=name_parts.last.capitalize(),
        )

    def parse_contact_data(self, text):
        emails = self.parse_email(text)
        phones = self.parse_phone_number(text)
        website = self.parse_url(text)

        return ContactData(
            email=emails,
            phone=phones,
            website=website,
        )

    def parse_languages(self, text: str, min_language_length=3):
        # Get a list of language names
        lang2code = {lang.name: lang.alpha_3 for lang in pycountry.languages}
        languages = list(lang2code.keys())

        # Tokenize the text into words
        words = re.findall(r"\b\w+\b", text)

        # Find the intersection of words and languages (case-insensitive)
        detected_languages = list(
            set(
                word
                for word in words
                if word.lower() in (lang.lower() for lang in languages)
            )
        )

        return LanguagesData(
            languages=[
                {"code": lang2code.get(lang, ""), "name": lang, "description": ""}
                for lang in detected_languages
                if lang2code.get(lang) and len(lang) >= min_language_length
            ]
        )

    def parse_dates(self, lines: list[str]) -> list[tuple[str, int]]:
        """
        Parse dates from a list of text lines.

        Args:
            lines (list[str]): List of text lines.

        Returns:
            dates (list[tuple[str, int]]): A list of tuples containing parsed dates and their positions.
        """
        dates = []
        for idx, line in enumerate(lines):
            # Replace "Present" or other mentions with today's date
            for now_word in Config.PRESENT_KEYWORDS:
                line = line.lower().replace(
                    now_word, datetime.today().strftime("%d/%m/%Y")
                )

            # Find all substrings that look like dates and their positions
            potential_dates = [(m.group(), idx) for m in re.finditer(RE_DATES, line)]
            dates.extend(potential_dates)

        # Sort the dates by their position in the input string
        dates.sort(key=lambda x: x[1])

        return dates

    def get_dates_for_segment(self, resume_lines, segment_text):
        dates = self.parse_dates(resume_lines)
        groups_of_dates = group_elements_by_index(dates) if dates else []

        return filter_dates_for_a_segment(segment_text, groups_of_dates)

    def parse_work_experience(
        self,
        resume_lines: list[str],
        segment_text: str,
        zero_shot_classifier_pipeline: pipeline,
        window: int = 2,
    ) -> list[ExperienceData]:
        """
        Parse work experience from a list of text lines using dates and a zero-shot classifier pipeline.

        Args:
            dates (list[tuple[str, int]]): List of tuples containing parsed dates and their positions.
            resume_lines (list[str]): List of text lines.
            zero_shot_classifier_pipeline (pipeline): A zero-shot classifier pipeline.
            window (int, optional): The window size for selecting lines around a date. Defaults to 3.

        Returns:
            list[ExperienceData]: A list of dictionaries containing the parsed work experience.
        """
        dates = self.get_dates_for_segment(resume_lines, segment_text)
        experience = []
        for pair_of_dates in dates:
            idx = pair_of_dates[0][1]
            lines = {}
            for i in range(
                max(idx - window, 0), min(idx + window, len(resume_lines)) + 1
            ):
                if i != idx:
                    line = resume_lines[i]
                    classification = zero_shot_classifier_pipeline(
                        line, Config.EMPLOYMENT_NLI_CLASSES
                    )
                    label, score = (
                        classification["labels"][0],
                        classification["scores"][0],
                    )
                    lines[line] = (label, score)

            # get location and parse it
            location = get_max_element(
                lines, keywords=Config.EMPLOYMENT_LOCATION_NLI_CLASSES
            )
            try:
                place_entity = find_location_entities(location)
                city = ", ".join(cities) if (cities := place_entity.cities) else ""
                country = countries[0] if (countries := place_entity.countries) else ""
                country_code = get_country_code(country)
            except:
                logging.info("No location found")
                city, country, country_code = "", "", ""

            # get job title
            title = get_max_element(lines, keywords=Config.JOB_NLI_CLASSES)

            # get employer name
            employer = get_max_element(lines, keywords=Config.EMPLOYER_NLI_CLASSES)

            # get job description
            description = ""

            # get starting and ending dates
            start_date, end_date = pair_of_dates[0][0], pair_of_dates[1][0]
            experience.append(
                Experience(
                    city=city,
                    title=title,
                    country=country,
                    employer=employer,
                    end_date=end_date,
                    start_date=start_date,
                    description=description,
                    country_code=country_code,
                )
            )

        return ExperienceData(experience=experience)

    def skills_parser_from_list(
        self, txt_segment: str, skills_list: list[str], min_length: int = 2
    ) -> list[str]:
        """
        Extracts skills from the given text segment based on a list of known skills.

        Args:
            txt_segment (str): Text segment to extract skills from.
            skills_list (list[str]): List of known skills.
            min_length (int): Minimum length of the skill string to be considered valid.

        Returns:
            list[str]: List of extracted skills.
        """
        skills = []
        for skill in skills_list:
            if skill in txt_segment.lower() and len(skill) > min_length:
                skills.append(skill)

        return skills

    def skills_parser_ner(
        self, txt_segment: str, ner_pipeline, min_length: int = 2
    ) -> list[str]:
        """
        Extracts skills from the given text segment using Named Entity Recognition (NER) pipeline.

        Args:
            txt_segment (str): Text segment to extract skills from.
            ner_pipeline: NER pipeline to be used for skill extraction.
            min_length (int): Minimum length of the skill string to be considered valid.

        Returns:
            list[str]: List of extracted skills.
        """
        res = ner_pipeline.pipe([txt_segment], disable=["tagger", "parser"])
        skills = []
        for doc in res:
            for ent in doc.ents:
                text_name = re.sub("[^A-Za-z0-9]+", " ", ent.text).strip().lower()
                if ent.label_ in Config.SKILLS_NER_TAGS:
                    skills.extend(text_name.split())

        return list(filter(lambda x: len(x) > min_length, skills))

    def parse_skills(
        self, txt_segment: str, all_skills: list[str] = SKILLS
    ) -> SkillsData:
        """
        Extracts skills from the given text segment using both NER and a list of known skills.

        Args:
            txt_segment (str): Text segment to extract skills from.
            all_skills (list[str]): List of known skills.

        Returns:
            SkillsData: List of extracted skills.
        """
        # not use here for performances reasons
        # skills_from_ner = self.skills_parser_ner(txt_segment, ner_pipeline)
        skills_from_list = self.skills_parser_from_list(txt_segment, all_skills)

        return SkillsData(skills=skills_from_list)

    def parse_degree_name(self, txt_line: str, degree_abbreviations: list[str]) -> str:
        """
        Parse the degree name from a given text line.

        Args:
            txt_line (str): Text line containing the degree name.
            degree_abbreviations_file_path (str): File path to the degree abbreviations CSV.

        Returns:
            str: The parsed degree name.
        """
        abbreviations_pattern = "|".join(
            re.escape(abbreviation) for abbreviation in degree_abbreviations
        )

        return (
            abbreviations[0]
            if (abbreviations := re.findall(abbreviations_pattern, txt_line))
            else ""
        )

    def parse_education_and_trainings(
        self,
        resume_lines: list[str],
        segment_text: str,
        zero_shot_classifier,
        degrees: list[str] = DEGREES,
        window_min: int = 3,
        window_max: int = 5,
        min_education_time: int = 12,
    ) -> list[EducationData]:
        """
        Parse the education and training information from the resume lines.

        Args:
            dates_education (list): List of pairs of education start and end dates.
            resume_lines (list[str]): List of text lines from the resume.
            zero_shot_classifier: Zero-shot classifier pipeline.
            degrees (list[str]): List of degrees abbreviations
            window_min (int): Minimum window size for searching the information around the dates.
            window_max (int): Maximum window size for searching the information around the dates.
            min_education_time (int): Minimum education time in months to be considered as valid.

        Returns:
            list[EducationData]: List of parsed education data.
        """
        dates = self.get_dates_for_segment(resume_lines, segment_text)
        education = []
        for pair_of_dates in dates:
            idx = pair_of_dates[0][1]
            lines, flatten_lines, degree_name = {}, "", ""
            for i in range(
                max(idx - window_min, 0),
                min(idx + window_min, len(resume_lines) - 1) + 1,
            ):
                line = resume_lines[i]
                flatten_lines += line
                if i != idx:
                    degree_name = max(
                        self.parse_degree_name(line, degrees), degree_name
                    )
                    cleaned_line = (
                        filter_stopwords(re.sub(degree_name, "", line).strip())
                        if degree_name
                        else line
                    )
                    classification = zero_shot_classifier(
                        line, Config.EDUCATION_NLI_CLASSES
                    )
                    label, score = (
                        classification["labels"][0],
                        classification["scores"][0],
                    )
                    lines[cleaned_line] = (label, score)

            if not degree_name:
                for i in range(
                    max(idx - window_max, 0),
                    min(idx + window_max, len(resume_lines) - 1) + 1,
                ):
                    degree_name = max(
                        self.parse_degree_name(resume_lines[i], degrees), degree_name
                    )

            # get starting and ending dates
            start_date, end_date = pair_of_dates[0][0], pair_of_dates[1][0]

            # filter dates
            if timedelta_in_months(start_date, end_date) >= min_education_time:
                # parse location
                try:
                    place_entity = find_location_entities(flatten_lines)
                    city = ", ".join(cities) if (cities := place_entity.cities) else ""
                    country = (
                        countries[0] if (countries := place_entity.countries) else ""
                    )
                    country_code = get_country_code(country)
                except:
                    logging.info("No location found")
                    city, country, country_code = "", "", ""

                # get degree major
                degree_major = get_max_element(
                    lines, keywords=Config.DEGREE_MAJOR_CLASSES
                )

                # get school/uni name
                school = get_max_element(lines, keywords=Config.SCHOOL_CLASSES)

                # get description
                description = ""

                education.append(
                    Education(
                        city=city,
                        school=school,
                        country=country,
                        end_date=end_date,
                        start_date=start_date,
                        degree_name=degree_name,
                        description=description,
                        country_code=country_code,
                        degree_major=degree_major,
                    )
                )

        return EducationData(education=education)

    def parse_with_fallback(
        self,
        parsing_function,
        resume_lines,
        init_segment_text,
        fallback_segment_text,
        zero_shot_classifier,
        **kwargs,
    ):
        parsing_result = parsing_function(
            resume_lines,
            init_segment_text,
            zero_shot_classifier,
            **kwargs,
        )
        field = fields[0] if (fields := list(parsing_result.__fields__)) else ""

        return (
            parsing_function(
                resume_lines,
                fallback_segment_text,
                zero_shot_classifier,
                **kwargs,
            )
            if not parsing_result.dict().get(field, [])
            else parsing_result
        )
