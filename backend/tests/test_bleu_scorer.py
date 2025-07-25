import pytest
from unittest.mock import MagicMock, patch
from translation_service.utils.bleu_scorer import preprocess_text, compute_bleu_score


def test_preprocess_text():
    """Test text preprocessing with punctuation removal"""
    # Test basic preprocessing
    text = "Hello, World!!!"
    result = preprocess_text(text)
    assert result == ["hello", "world"]
    
    # Test multiple spaces and punctuation
    text = "This   is  a    test...   sentence!!!"
    result = preprocess_text(text)
    assert result == ["this", "is", "a", "test", "sentence"]
    
    # Test empty text
    text = ""
    result = preprocess_text(text)
    assert result == []
    
    # Test text with special characters and punctuation
    text = "Hello! こんにちは! 你好! Let's test: some; complex, punctuation."
    result = preprocess_text(text)
    assert "hello" in result
    assert "lets" in result  # Note: apostrophe is removed
    assert "test" in result
    assert "some" in result
    assert "complex" in result
    assert "punctuation" in result
    assert "こんにちは" in result
    assert "你好" in result
    
    # Test text with numbers and punctuation
    text = "Test123! 456.789, (test)"
    result = preprocess_text(text)
    assert result == ["test123", "456789", "test"]

def test_compute_bleu_score():
    """Test BLEU score computation with punctuation-free text"""
    # Test perfect match
    reference = "This is a test"
    candidate = "This is a test"
    score = compute_bleu_score(reference, candidate)
    assert score == 1.0  # Should be perfect match after removing punctuation
    
    # Test partial match
    reference = "This is a test sentence"
    candidate = "This is a trial sentence"
    score = compute_bleu_score(reference, candidate)
    assert 0 <= score <= 1.0
    
    # Test no match
    reference = "This is a test"
    candidate = "Something completely different"
    score = compute_bleu_score(reference, candidate)
    assert score == 0.0
    
    # Test empty strings
    score = compute_bleu_score("", "")
    assert score == 0.0
    
    score = compute_bleu_score("Test", "")
    assert score == 0.0
    
    score = compute_bleu_score("", "Test")
    assert score == 0.0

@patch('translation_service.utils.bleu_scorer.sentence_bleu')
def test_compute_bleu_score_nltk_error(mock_sentence_bleu):
    """Test BLEU score computation with NLTK error"""
    mock_sentence_bleu.side_effect = Exception("NLTK Error")
    score = compute_bleu_score("Test", "Test")
    assert score == 0.0