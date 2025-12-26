from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
import httpx
from app.helpers.db_helper import get_db
from app.common.models import ISBNRequest, WishlistRequest
from app.helpers.llm_helper import generate_summary, generate_embedding

router = APIRouter()

@router.get("/getAllBooks")
def get_all_books(db=Depends(get_db)):
    result = db.execute(text("SELECT * FROM books"))
    return [dict(row._mapping) for row in result.fetchall()]

@router.post("/addBookFromISBN")
def add_book_from_isbn(request: ISBNRequest, db=Depends(get_db)):
    isbn = request.isbn
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Failed to reach upstream")

    book_data = data.get(f"ISBN:{isbn}", {})
    if not book_data:
        raise HTTPException(status_code=404, detail="Book not found")

    title = book_data.get("title")
    authors = [a.get("name") for a in book_data.get("authors", [])]
    publishers = [p.get("name") for p in book_data.get("publishers", [])]
    publication_date = book_data.get("publish_date")
    genres = [s.get("name") for s in book_data.get("subjects", [])]
    pages = book_data.get("number_of_pages")
    image = book_data.get("cover", {}).get("medium")

    try:
        db.execute(
            text('''INSERT INTO books(isbn, title, authors, publishers, publication_date, genres, pages, image)
                    VALUES (:isbn, :title, :authors, :publishers, :publication_date, :genres, :pages, :image)'''),
            {"isbn": isbn, "title": title, "authors": authors, "publishers": publishers,
             "publication_date": publication_date, "genres": genres, "pages": int(pages) if pages else None, "image": image}
        )
        summary = generate_summary(title, authors[0] if len(authors) > 0 else "", isbn, "../prompts/summary_prompt.txt")
        embedding = generate_embedding(summary)
        db.execute(
            text('''INSERT INTO book_embeddings(isbn, summary, embedding)
                    VALUES (:isbn, :summary, :embedding)'''),
            {"isbn": isbn, "summary": summary, "embedding": embedding}
        )
        db.commit()
        return {"message": "Book added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add book: {str(e)}")

@router.post("/removeBookFromISBN")
def remove_book_from_isbn(request: ISBNRequest, db=Depends(get_db)):
    isbn = request.isbn
    try:
        db.execute(
            text('''DELETE FROM books where isbn = :isbn'''),
            {"isbn": isbn}
        )
        db.execute(
            text('''DELETE FROM book_embeddings WHERE isbn=:isbn'''),
            {"isbn": isbn}
        )
        db.commit()
        return {"message": "Book removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")
    
@router.get('/getBookSummary')
def get_book_summary(request: ISBNRequest, db=Depends(get_db)):
    isbn = request.isbn
    try:
        result = db.execute(
            text('''SELECT summary from book_embeddings WHERE isbn=:isbn'''),
            {"isbn": isbn}
        )
        row = result.first()
        return dict(row._mapping) if row else None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve book summary: {str(e)}")
        
@router.post("/addToWishlist")
def add_book_to_wishlist(request: WishlistRequest, db=Depends(get_db)):
    account_id = request.account_id
    isbn = request.isbn
    try:
        db.execute(
            text('''INSERT INTO wishlist (account_id, isbn)
                    VALUES (:account_id, :isbn)'''),
            {"account_id": account_id, "isbn": isbn}
        )
        db.commit()
        return {"message": "Wishlist item added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add wishlist item: {str(e)}")
    
@router.post("/removeFromWishlist")
def remove_from_wishlist(request: WishlistRequest, db=Depends(get_db)):
    account_id = request.account_id
    isbn = request.isbn
    try:
        db.execute(
            text('''DELETE FROM wishlist
                    WHERE account_id = :account_id AND isbn = :isbn'''),
            {"account_id": account_id, "isbn": isbn}
        )
        db.commit()
        return {"message": "Wishlist item removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove wishlist item: {str(e)}")
    
@router.get("/getWishlistByAccountId")
def get_wishlist_by_account_id(account_id: int = Header(..., alias="account_id"), db=Depends(get_db)):
    try:
        result = db.execute(
            text('''SELECT isbn 
                    FROM wishlist 
                    WHERE account_id = :account_id'''),
            {"account_id": account_id}
        )
        wishlist_items = [row.isbn for row in result]
        return wishlist_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve wishlist: {str(e)}")