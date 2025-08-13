from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from app.helpers.db_helper import get_db
from app.helpers.contest_helper import choose_winner
from app.helpers.reviews_helper import process_reviews

router = APIRouter()

@router.post("/submitReview")
def submit_review(request: dict, db=Depends(get_db)):
    account_id = request.get("account_id")
    review_text = request.get("review_text")
    rating = request.get("rating")
    book_isbn = request.get("book_isbn")

    try:
        db.execute(
            text('''INSERT INTO reviews (account_id, review_text, rating, review_date, book_isbn)
                    VALUES (:account_id, :review_text, :rating, NOW(), :book_isbn)'''),
                {"account_id": account_id, "review_text": review_text, "rating": rating, "book_isbn": book_isbn}
        )
        db.commit()
        return {"message": "Review submitted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")
    
@router.get("/getReviewsByBook")
def get_reviews_by_book(book_isbn: str = Header(..., alias="isbn"), db=Depends(get_db)):
    try:
        result = db.execute(
            text('''SELECT r.review_id, r.review_text, r.rating, r.review_date, r.book_isbn, a.username, r.likes
                    FROM reviews r join accounts a on r.account_id = a.account_id WHERE r.book_isbn = :book_isbn'''),
                {"book_isbn": book_isbn}
        )
        reviews = [dict(row._mapping) for row in result.fetchall()]
        process_reviews(reviews)
        print(reviews)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@router.post("/modifyLikeCount")
def modify_like_count(request: dict, db=Depends(get_db)):
    review_id = request.get("review_id")
    action = request.get("action")

    if action not in ("like", "unlike"):
        raise HTTPException(status_code=400, detail="Invalid action")

    increment = 1 if action == "like" else -1

    try:
        db.execute(
            text("""
                UPDATE reviews
                SET likes = likes + :inc
                WHERE review_id = :review_id
            """),
            {"inc": increment, "review_id": review_id}
        )
        db.commit()
        return {"message": "Review likes updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Likes action failed: {str(e)}")
    
@router.get("/selectContestWinner")
def select_contest_winner(db=Depends(get_db)):
    try:
        rows = db.execute(
            text('''SELECT a.username, COUNT(*) as review_count FROM accounts a JOIN reviews r
                    ON a.account_id = r.account_id GROUP BY a.username HAVING COUNT(*) > 0''')
        ).mappings().all()
        
        accounts_and_counts = [(row['username'], row['review_count']) for row in rows]

        if not accounts_and_counts:
            return {"message": "No reviews found to select a winner."}
        
        return {"winner": choose_winner(accounts_and_counts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")