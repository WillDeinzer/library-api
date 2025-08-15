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
            text('''SELECT r.review_id, r.review_text, r.rating, r.review_date, r.book_isbn, a.account_id, a.username, r.likes
                    FROM reviews r join accounts a on r.account_id = a.account_id WHERE r.book_isbn = :book_isbn'''),
                {"book_isbn": book_isbn}
        )
        reviews = [dict(row._mapping) for row in result.fetchall()]
        process_reviews(reviews)
        print(reviews)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@router.post("/deleteReviewByReviewId")
def delete_review_by_review_id(request: dict, db=Depends(get_db)):
    review_id = request.get("review_id")

    try:
        db.execute(
            text('''DELETE FROM reviews WHERE review_id = :review_id'''),
                {"review_id": review_id}
        )
        db.commit()
        return {"message": "Review deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete review: {str(e)}")
    
@router.post("/modifyLikeCount")
def modify_like_count(request: dict, db=Depends(get_db)):
    review_id = request.get("review_id")
    action = request.get("action")
    account_id = request.get("account_id")
    isbn = request.get("isbn")

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
        if action == "like":
            db.execute(
                text('''INSERT INTO review_likes (review_id, account_id, isbn) VALUES (:review_id, :account_id, :isbn)'''),
                    {"review_id": review_id, "account_id": account_id, "isbn": isbn}
            )
        else:
            db.execute(
                text('''DELETE FROM review_likes WHERE review_id = :review_id AND account_id = :account_id'''),
                    {"review_id": review_id, "account_id": account_id}
            )
        db.commit()
        return {"message": "Review likes updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Likes action failed: {str(e)}")
    
# Get the reviews a user liked for a given book

@router.get("/getLikedByISBN")
def get_liked_by_isbn(book_isbn: str = Header(..., alias="book_isbn"), account_id: str = Header(..., alias="account_id"), db=Depends(get_db)):
    try:
        result = db.execute(
            text('''SELECT review_id from review_likes WHERE isbn = :book_isbn AND account_id = :account_id'''),
                {"book_isbn": book_isbn, "account_id": account_id}
        )
        liked_ids = [row[0] for row in result.fetchall()]
        return liked_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@router.post("/selectContestWinner")
def select_contest_winner(db=Depends(get_db)):
    try:
        rows = db.execute(
            text('''SELECT a.username, COUNT(*) as review_count FROM accounts a JOIN reviews r
                    ON a.account_id = r.account_id GROUP BY a.username HAVING COUNT(*) > 0''')
        ).mappings().all()
        
        accounts_and_counts = [(row['username'], row['review_count']) for row in rows]

        if not accounts_and_counts:
            return {"message": "No reviews found to select a winner."}
        
        winner = choose_winner(accounts_and_counts)
        
        db.execute(
            text('''INSERT INTO contest_winners (winner_username, win_time)
                    VALUES (:winner, NOW())'''),
                {"winner": winner}
        )
        db.commit()
        
        return {"winner": winner}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@router.get("/getRecentWinners")
def get_recent_winners(db=Depends(get_db)):
    """
    Returns up to the 5 most recent contest winners, ordered by win_time descending.
    """
    try:
        rows = db.execute(
            text('''
                SELECT winner_username, win_time
                FROM contest_winners
                ORDER BY win_time DESC
                LIMIT 5
            ''')
        ).mappings().all()

        recent_winners = [
            {"winner_username": row["winner_username"], "win_time": row["win_time"]}
            for row in rows
        ]

        return {"recent_winners": recent_winners}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent winners: {str(e)}")