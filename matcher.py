from utils import get_profiles
from model import embed_texts, calculate_similarity
import numpy as np


def match_profiles_with_job_description(job_description):
    """
    Match job description with profiles based on cosine similarity of embeddings.

    Args:
        job_description (str): The job description text.

    Returns:
        list: A list of tuples containing top profiles and their similarity scores.
              Each tuple contains (profile, similarity_score).
    """
    try:
        # Retrieve profiles
        profiles = get_profiles()

        # Combine profile fields into a single string for each profile
        profile_texts = [
            " ".join([profile[3], str(profile[4]), profile[5]]) for profile in profiles
        ]

        # Embed the job description and profiles
        job_description_embedding = embed_texts([job_description])[0]
        profile_embeddings = embed_texts(profile_texts)

        # Calculate cosine similarity between job description and profiles
        similarities = calculate_similarity(
            job_description_embedding, profile_embeddings
        )

        # Get the top 10 profiles with the highest similarity scores
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_profiles = [
            (profiles[i], float(similarities[i])) for i in top_indices
        ]  # Convert numpy.float32 to Python float

        return top_profiles

    except Exception as e:
        print(f"Error matching profiles with job description: {e}")
        return []
