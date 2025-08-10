from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from app.helpers.db_helper import get_db
from app.helpers.llm_helper import get_most_similar, generate_query_response

router = APIRouter()

@router.get("/chat")
def chat(query: str, db=Depends(get_db)):
    try:
        result = db.execute(
            text('''SELECT b.isbn, b.title, b.authors, be.embedding
                FROM books b join book_embeddings be ON b.isbn = be.isbn'''))
        books = result.fetchall()

        most_similar = get_most_similar(books, query)
        query_response = generate_query_response(query, most_similar, "../prompts/chat_prompt.txt")

        return {"response": query_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get response: {str(e)}")





        





