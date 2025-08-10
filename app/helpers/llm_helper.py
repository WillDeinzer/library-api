import os
import numpy as np
from openai import OpenAI
from app.common.constants import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def load_prompt(filepath: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, filepath)
    with open(full_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def generate_summary(title: str, author: str, isbn: str, prompt_path: str) -> str:
    prompt_template = load_prompt(prompt_path)
    prompt = prompt_template.format(title=title, author=author, isbn=isbn)
    
    response = client.responses.create(
        model="gpt-3.5-turbo",
        input=prompt,
        max_output_tokens=400
    )

    return response.output_text

def generate_query_response(query: str, most_similar, prompt_path: str) -> str:
    prompt_template = load_prompt(prompt_path)

    context_parts = []
    for i in range(len(most_similar)):
        author = most_similar[i]["authors"][0] if (most_similar[i]["authors"] and len(most_similar[i]["authors"]) > 0) else ""
        title = most_similar[i]["title"]
        context_parts.append(
            f"Book {i + 1} Title: {title}\nAuthor: {author}\n"
        )
    
    context_text = "\n---\n".join(context_parts)
    prompt = prompt_template.format(context=context_text, query=query)

    response = client.responses.create(
        model="gpt-3.5-turbo",
        input=prompt,
        max_output_tokens=400
    )

    return response.output_text

def generate_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    embedding_vector = response.data[0].embedding
    return embedding_vector

# Calculates the cosine similarity between two embedding vectors
def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Returns the three most relevant books to a user's query
def get_most_similar(books, query):
    query_embedding = generate_embedding(query)
    similarities = []
    for book in books:
        sim = cosine_similarity(query_embedding, book.embedding)
        similarities.append({
            "isbn": book.isbn,
            "title": book.title,
            "authors": book.authors,
            "similarity": sim
        })

    similarities.sort(key=lambda x: x["similarity"], reverse=True)

    return similarities[:3]