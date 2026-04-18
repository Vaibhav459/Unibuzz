from better_profanity import profanity

# Initialize profanity filter with default wordlist
profanity.load_censor_words()

def contains_bad_words(text):
    """
    Checks if the given text contains any profanity or bad words.
    Returns True if bad words are found, False otherwise.
    """
    if not text:
        return False
    return profanity.contains_profanity(text)

def is_image_inappropriate(image_file, text_context=""):
    """
    Checks if the uploaded image contains inappropriate content (like nudity).
    Currently a placeholder for an AI API or local image moderation library.
    Returns True if the image is inappropriate, False otherwise.
    """
    if not image_file:
        return False
        
    # TODO: Implement image moderation (e.g., using Sightengine, Clarifai, or OpenAI Vision API)
    # For now, we return False to allow images until an API is set up.
    return False
