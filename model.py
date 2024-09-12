import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.utils.enums import DecodingMethods
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SentenceTransformer model
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


def embed_texts(texts):
    """
    Embed a list of texts into vectors using the SentenceTransformer model.

    Args:
        texts (list of str): List of text strings to be embedded.

    Returns:
        numpy.ndarray: Array of embedded vectors.
    """
    try:
        return model.encode(texts)
    except Exception as e:
        print(f"Error embedding texts: {e}")
        return None


def calculate_similarity(job_description_embedding, profile_embeddings):
    """
    Calculate cosine similarity between a job description embedding and a list of profile embeddings.

    Args:
        job_description_embedding (numpy.ndarray): The embedding of the job description.
        profile_embeddings (numpy.ndarray): Array of embeddings of the profiles.

    Returns:
        numpy.ndarray: Array of cosine similarity scores.
    """
    try:
        return cosine_similarity([job_description_embedding], profile_embeddings)[0]
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return None


def initialize_model(model_id):
    """
    Initialize the IBM Watson Foundation Model with the specified model ID.

    Args:
        model_id (str): The ID of the IBM Watson model.

    Returns:
        Model: Initialized IBM Watson Model instance.
    """
    try:
        generate_params = {
            GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
            GenParams.MAX_NEW_TOKENS: 1024,
        }
        model = Model(
            model_id=model_id,
            params=generate_params,
            credentials={"apikey": os.getenv("GA_API_KEY"), "url": os.getenv("GA_URL")},
            project_id=os.getenv("GA_PROJECT_ID"),
        )
        return model
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None
