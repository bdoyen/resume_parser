import os
import logging
from typing import Union
import spacy
from transformers import AutoTokenizer, pipeline
from optimum.onnxruntime import (
    ORTQuantizer,
    ORTModelForSequenceClassification,
    ORTModelForTokenClassification,
)
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from config import Config

logging.basicConfig(
    format="%(levelname)s : %(funcName)s : %(message)s", level=logging.INFO
)


class ModelHandlingError(Exception):
    """Custom exception class for handling model loading/converting errors."""

    pass


class Models:
    """
    A class to handle loading and quantizing, using NLI or NER models.

    Attributes:
        nli_model_tag (str): The model tag for the NLI model.
        ner_model_skills_dir (str): The directory containing the NER model for skills.
        nli_model_onnx (ORTModelForSequenceClassification): The loaded NLI model.
        zero_shot_classifier (pipeline): The zero-shot classification pipeline with the quantized NLI model.
        ner_for_skills (spacy.Language): The loaded NER model for skills extraction.
    """

    def __init__(
        self,
        nli_model_name: str = Config.NLI_MODEL_DIR,
        ner_model_name: str = Config.NER_MODEL_DIR,
        ner_model_skills_dir: str = Config.NER_MODEL_SKILLS_DIR,
    ):
        self.nli_model_name = nli_model_name
        self.ner_model_name = ner_model_name
        self.ner_model_skills_dir = ner_model_skills_dir

        logging.info("Starting models loading...")
        # Load the NLI model and quantize it (if not done already)
        if not os.path.isfile(
            os.path.join(
                Config.QUANTIZED_NLI_MODEL_DIR, Config.QUANTIZED_NLI_MODEL_ONNX
            )
        ):
            self.nli_model_onnx = self.load_model(
                self.nli_model_name, ORTModelForSequenceClassification
            )
            self.quantize_and_save_model(
                self.nli_model_onnx, Config.QUANTIZED_NLI_MODEL_DIR
            )

        # Load the quantized NLI model as a zero-shot classifier
        self.zero_shot_classifier_pipeline = self.load_quantized_model(
            Config.QUANTIZED_NLI_MODEL_DIR,
            Config.QUANTIZED_NLI_MODEL_ONNX,
            ORTModelForSequenceClassification,
            "zero-shot-classification",
        )

        if not os.path.isfile(
            os.path.join(
                Config.QUANTIZED_NER_MODEL_DIR, Config.QUANTIZED_NER_MODEL_ONNX
            )
        ):
            self.ner_model_onnx = self.load_model(
                self.ner_model_name, ORTModelForTokenClassification
            )
            self.quantize_and_save_model(
                self.ner_model_onnx, Config.QUANTIZED_NER_MODEL_DIR
            )

        # Load generic NER pipeline
        self.ner_pipeline = self.load_quantized_model(
            Config.QUANTIZED_NER_MODEL_DIR,
            Config.QUANTIZED_NER_MODEL_ONNX,
            ORTModelForTokenClassification,
            "ner",
        )

        # Load the NER model for skills extraction
        # self.ner_for_skills = spacy.load(self.ner_model_skills_dir)
        logging.info("Successfully loaded all models ✔")

    def load_model(self, model_name, ORTModel):
        """
        Load model and convert it to ONNX format.

        Returns:
            ORTModel: The loaded model.
        """
        try:
            logging.info("Starting models loading and export to ONNX format...")
            model_onnx = ORTModel.from_pretrained(model_name, export=True)
            return model_onnx
        except Exception as e:
            raise ModelHandlingError(f"Failed to load NLI model: {e}")

    def quantize_and_save_model(
        self,
        model_onnx,
        save_dir,
    ) -> None:
        """
        Quantize the given model and save it to a specified directory.

        Args:
            model_onnx (ORTModel): The model to be quantized.
        """
        logging.info(f"Load ONNX model {model_onnx}")
        quantizer = ORTQuantizer.from_pretrained(model_onnx)

        # Define the quantization strategy by creating the appropriate configuration
        dqconfig = AutoQuantizationConfig.avx512_vnni(
            is_static=False, per_channel=False
        )

        logging.info(f"Start Quantization of model {model_onnx} into {save_dir}")
        try:
            # Quantize the model and save it to the specified directory
            quantizer.quantize(
                save_dir=save_dir,
                quantization_config=dqconfig,
            )
        except Exception as e:
            raise ModelHandlingError(f"Failed Quantization of model {model_onnx}: {e}")

    def load_quantized_model(
        self, save_dir, model_file_name, ORTModel, type
    ) -> Union[pipeline, None]:
        """
        Load the quantized model and create a zero-shot classification pipeline.

        Returns:
            pipeline: The zero-shot or token classification pipeline using quantized model
        """
        try:
            tokenizer = AutoTokenizer.from_pretrained(save_dir)
            q_model = ORTModel.from_pretrained(
                save_dir,
                file_name=model_file_name,
            )
            nlp_pipeline = pipeline(type, model=q_model, tokenizer=tokenizer)
            return nlp_pipeline
        except Exception as e:
            raise ModelHandlingError(
                f"Failed loading of quantized model from {save_dir}: {e}"
            )
