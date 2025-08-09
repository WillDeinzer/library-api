import re

# This method 

def process_reviews(reviews):
    keys = ["OverallThoughts", "FavoriteCharacter", "FavoritePart"]

    for review in reviews:
        reviewText = review["review_text"]
        pattern = r"%(" + "|".join(keys) + r")%(.*?)(?=%(" + "|".join(keys) + r")%|$)"
        
        matches = re.findall(pattern, reviewText, flags=re.DOTALL | re.IGNORECASE)

        mapping = {key: "" for key in keys}

        for key, content, _ in matches:
            mapping[key] = content.strip()
        
        review["review_text"] = mapping