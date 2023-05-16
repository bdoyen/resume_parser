import os
import shutil
import re
import random
import logging
import pycountry
import unicodedata
import pandas as pd
import locationtagger
from dateutil import parser
from datetime import datetime

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from langdetect import detect_langs

from config import Config
from data_models import MetaData


def normalize_string(string: str) -> str:
    """
    Normalize a given string by removing non-ascii characters, replacing accents,
    and stripping leading/trailing whitespaces.

    Args:
        string (str): The input string to be normalized.

    Returns:
        str: The normalized string.
    """
    string = unicodedata.normalize("NFD", string).replace("\n", " ")

    return string.encode("ascii", "ignore").decode("utf-8").strip()


def get_next_value(elements: dict, current_key: str) -> str:
    """
    Get the next value in a dictionary based on the index of the current key.

    Args:
        elements (Dict): The input dictionary.
        current_key (str): The current key in the dictionary.

    Returns:
        str: The next value in the dictionary.
    """
    return list(elements)[list(elements.keys()).index(current_key) + 1]


def group_elements_by_index(
    elements: list[tuple[str, int]]
) -> list[tuple[tuple[str, int], tuple[str, int]]]:
    """
    Group elements based on their index value in the input list of tuples.

    Args:
        elements (List[Tuple[str, int]]): A list of tuples where the second element is an index.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing the grouped elements.
    """

    # Create an empty dictionary to store elements based on their index
    index_dict = {}

    # Iterate through elements and group them by index
    for element in elements:
        index = element[1]
        if index not in index_dict:
            index_dict[index] = []

        index_dict[index].append(element)

    # Return grouped elements as a list of tuples
    return [tuple(pair) for pair in index_dict.values() if len(pair) == 2]


def filter_dates_for_a_segment(text, groups_of_dates):
    selected_dates = []
    for dates in groups_of_dates:
        try:
            date_start = parser.parse(dates[0][0], dayfirst=True)
            date_end = parser.parse(dates[1][0], dayfirst=True)
            if dates[0][0] in text or dates[1][0] in text:
                selected_dates.append(
                    (
                        (date_start.strftime("%m/%Y"), dates[0][1]),
                        (date_end.strftime("%m/%Y"), dates[1][1]),
                    )
                )
        except ValueError:
            pass  # Skip if parsing failed

    return selected_dates


def get_max_element(lines, keywords):
    filtered_lines = {k: v for k, v in lines.items() if v[0] in keywords}
    return max(filtered_lines, key=lambda k: lines[k][1]) if filtered_lines else ""


def get_country_code(country_name):
    if country_name:
        country2code = {
            country.name: country.alpha_2 for country in pycountry.countries
        }
        return country2code.get(country_name)
    else:
        return ""


def find_location_entities(text_input):
    # keyword text is necessary here ! (otherwise URL as input)
    return locationtagger.find_locations(text=text_input)


def merge_strings(strings):
    merged_strings = []

    for s1 in strings:
        keep_s1 = True
        for s2 in strings:
            if s1 != s2 and s1 in s2:
                keep_s1 = False
                break
        if keep_s1:
            merged_strings.append(s1)

    return merged_strings


def merge_doubled_words(text: str) -> str:
    # Tokenize the text into words
    words = re.findall(r"\b\w+\b", text)

    # Iterate through the words and only keep the first occurrence of each word
    seen_words = set()
    result_words = []
    for word in words:
        # Compare case-insensitive words
        lower_word = word.lower()
        if lower_word not in seen_words:
            seen_words.add(lower_word)
            result_words.append(word)

    # Join the result words back into a single string
    merged_text = " ".join(result_words)

    return merged_text


def read_csv_list(file_path):
    result = []
    try:
        df = pd.read_csv(file_path)
        return list(df.columns.values)
    except Exception as e:
        logging.error(f"Failed to load file {file_path} : {e}")
        return result


def filter_stopwords(txt, stopwords=set(stopwords.words(Config.USED_LANGUAGE))):
    word_tokens = word_tokenize(txt)
    filtered_sentence = [w for w in word_tokens if not w.lower() in stopwords]
    return " ".join(filtered_sentence)


def timedelta_in_months(start, end):
    start_date = datetime.strptime(start, "%m/%Y")
    end_date = datetime.strptime(end, "%m/%Y")
    return max(
        time_delta := (
            12 * (end_date.year - start_date.year) + (end_date.month - start_date.month)
        ),
        -1 * time_delta,
    )


def get_gender_from_firstname(detector, first_name):
    return detector.get_gender(first_name) if first_name else ""


def generate_metadata(
    text, remark=Config.MESSAGE_COMPLETED, status=Config.MESSAGE_STATUS_SUCCESS
):
    # Generate primary keys for job, resume and candidate
    job_pk = random.getrandbits(16)
    resume_pk = random.getrandbits(16)
    candidate_pk = random.getrandbits(16)
    language_code, language_confidence = "", 0.0

    if text:
        detected_languages = langs[0] if (langs := detect_langs(text)) else ""
        language_code = detected_languages.lang
        language_confidence = detected_languages.prob

    return MetaData(
        job_pk=job_pk,
        remark=remark,
        status=status,
        resume_pk=resume_pk,
        candidate_pk=candidate_pk,
        language_code=language_code,
        language_confidence=language_confidence,
    )


def cleaning_and_creating_tree(
    input_directory_path,
):
    """
    Deletes the existing input directory and creates new empty one
    Args:
        input_directory_path (str): where the input file is stored
    """

    # Deleting the input directory if it exists, and creating a new one
    if os.path.isdir(input_directory_path):
        shutil.rmtree(input_directory_path)
    os.mkdir(input_directory_path)
