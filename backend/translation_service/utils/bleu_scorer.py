import nltk
from nltk.translate.bleu_score import sentence_bleu
from typing import List
import re
import string

def preprocess_text(text: str) -> List[str]:
    """
    Preprocess text for BLEU score computation:
    1. Convert to lowercase
    2. Remove all punctuation
    3. Normalize whitespace
    4. Tokenize into words
    """
    # Convert to lowercase
    text = text.lower()

    # Remove all punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Normalize whitespace
    text = ' '.join(text.split())

    # Split into words
    return text.split()

def compute_bleu_score(reference: str, candidate: str) -> float:
    """
    Compute BLEU score between reference and candidate translations using NLTK
    
    Args:
        reference: The reference (existing) translation
        candidate: The candidate (LLM) translation
        
    Returns:
        float: BLEU score between 0 and 100
    """
    try:
        # Download required NLTK data if not already present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        # Preprocess and tokenize texts
        reference_tokens = preprocess_text(reference)
        candidate_tokens = preprocess_text(candidate)
        
        # If either is empty, return 0
        if not reference_tokens or not candidate_tokens:
            return 0.0
        
        # Use NLTK's sentence_bleu
        score = sentence_bleu(
            references=[reference_tokens],  # NLTK expects a list of references
            hypothesis=candidate_tokens
        )
        
        return score
        
    except Exception as e:
        print(f"BLEU computation error: {str(e)}")
        return 0.0 