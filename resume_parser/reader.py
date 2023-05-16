import re
import logging
import pdftotext

from utils import normalize_string

logging.basicConfig(
    format='%(levelname)s : %(funcName)s : %(message)s', level=logging.INFO
)

class Reader:


    def pdf_to_text(self, path_to_pdf: str) -> str:
        """
        Convert the content of a PDF file to plain text.

        Args:
            path_to_pdf (str): The path to the PDF file.

        Returns:
            str: The plain text content of the PDF file. Empty string if an error occurs.
        """
        try:
            with open(path_to_pdf, "rb") as f:
                pdf = pdftotext.PDF(f)
            return "".join(pdf)
        except Exception as e:
            logging.error(f"Error in PDF file ({path_to_pdf}) reading : {e}")
            return ""


    def get_document_lines(self, doc_text: str, min_line_length: int = 2) -> list[str]:
        """
        Preprocess the input document text and split it into a list of cleaned lines.

        Args:
            doc_text (str): The input document text.
            min_line_length (int, optional): The minimum length of a line to be included in the output. Defaults to 2.

        Returns:
            List[str]: A list of cleaned lines from the input document text.
        """
        resume_lines = []
        try:
            # Replace multiple newlines with a single newline, and tabs with spaces
            doc_text = re.sub(r'\n+', '\n', doc_text)
            doc_text = doc_text.replace("\r", "\n")
            doc_text = doc_text.replace("\t", " ")

            # Split text blob into individual lines
            resume_lines = doc_text.splitlines(True)

            # Clean and filter lines
            resume_lines = [cleaned_line for line in resume_lines
                            if (cleaned_line := normalize_string(line)) and len(cleaned_line) > min_line_length]
            
            logging.info(f"Successfully extracted {len(resume_lines)} lines from document")
        except Exception as e:
            logging.error(f"Resume lines extraction failed : {e}")

        return resume_lines
    

