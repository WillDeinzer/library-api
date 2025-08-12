from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.helpers.db_helper import get_db
from app.helpers.llm_helper import get_most_similar, generate_query_response

router = APIRouter()

@router.get("/chat")
def chat(query: str = Header(..., alias="query"), db=Depends(get_db)):
    try:
        result = db.execute(
            text('''SELECT b.isbn, b.title, b.authors, be.embedding
                FROM books b join book_embeddings be ON b.isbn = be.isbn'''))
        books = result.fetchall()

        most_similar = get_most_similar(books, query)

        return StreamingResponse(
            generate_query_response(query, most_similar, "../prompts/chat_prompt.txt"),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get response: {str(e)}")





        





