"""
Feedback router - handles user ratings (like/dislike) for StillMe responses
"""

import os
import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from backend.api.models.feedback import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackStats,
    FeedbackAnalysis,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "feedback.db"


def get_db_connection():
    """Get SQLite database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_feedback_db():
    """Initialize feedback database tables"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating IN (-1, 0, 1)),
                feedback_text TEXT,
                user_id TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
            CREATE INDEX IF NOT EXISTS idx_feedback_message_id ON feedback(message_id);
        """)
        conn.commit()
        logger.info("Feedback database initialized")
    finally:
        conn.close()


# Initialize database on module load
init_feedback_db()


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback (like/dislike) for a StillMe response
    
    Args:
        feedback: Feedback request with message_id, question, response, rating
        
    Returns:
        FeedbackResponse with feedback_id and status
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Insert or update feedback (upsert)
        cursor.execute("""
            INSERT OR REPLACE INTO feedback 
            (message_id, question, response, rating, feedback_text, user_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.message_id,
            feedback.question,
            feedback.response,
            feedback.rating,
            feedback.feedback_text,
            feedback.user_id,
            json.dumps(feedback.metadata) if feedback.metadata else None,
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        feedback_id = cursor.lastrowid
        
        logger.info(f"Feedback submitted: message_id={feedback.message_id}, rating={feedback.rating}")
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message_id=feedback.message_id,
            rating=feedback.rating,
            status="success",
            message="Feedback recorded successfully"
        )
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
    finally:
        conn.close()


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """
    Get feedback statistics
    
    Returns:
        FeedbackStats with total feedback, likes, dislikes, like rate
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total counts
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as likes, SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as dislikes, SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as neutral FROM feedback")
        row = cursor.fetchone()
        
        total = row["total"] or 0
        likes = row["likes"] or 0
        dislikes = row["dislikes"] or 0
        neutral = row["neutral"] or 0
        
        like_rate = (likes / total * 100) if total > 0 else 0.0
        
        # Get recent feedback (last 10)
        cursor.execute("""
            SELECT message_id, rating, feedback_text, created_at 
            FROM feedback 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent = [dict(row) for row in cursor.fetchall()]
        
        return FeedbackStats(
            total_feedback=total,
            likes=likes,
            dislikes=dislikes,
            neutral=neutral,
            like_rate=like_rate,
            recent_feedback=recent,
        )
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback stats: {str(e)}")
    finally:
        conn.close()


@router.get("/analysis", response_model=FeedbackAnalysis)
async def analyze_feedback():
    """
    Analyze feedback patterns to identify what makes responses good or bad
    
    Returns:
        FeedbackAnalysis with positive/negative patterns and recommendations
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get liked responses
        cursor.execute("SELECT response, metadata FROM feedback WHERE rating = 1 LIMIT 100")
        liked = [dict(row) for row in cursor.fetchall()]
        
        # Get disliked responses
        cursor.execute("SELECT response, metadata FROM feedback WHERE rating = -1 LIMIT 100")
        disliked = [dict(row) for row in cursor.fetchall()]
        
        # Analyze patterns (simplified - can be enhanced with ML)
        positive_patterns = []
        negative_patterns = []
        
        # Check for common patterns in liked responses
        if liked:
            # Example: Check if citations are present
            cited_count = sum(1 for r in liked if "[1]" in r["response"] or "[2]" in r["response"])
            if cited_count > len(liked) * 0.7:
                positive_patterns.append("Responses with citations tend to be liked")
            
            # Check response length
            avg_length = sum(len(r["response"]) for r in liked) / len(liked)
            if avg_length < 500:
                positive_patterns.append("Concise responses (under 500 chars) are preferred")
        
        # Check for common patterns in disliked responses
        if disliked:
            # Example: Check if too many citations
            over_cited = sum(1 for r in disliked if r["response"].count("[") > 5)
            if over_cited > len(disliked) * 0.5:
                negative_patterns.append("Too many citations can be disliked")
            
            # Check if responses are too long
            avg_length = sum(len(r["response"]) for r in disliked) / len(disliked)
            if avg_length > 1000:
                negative_patterns.append("Very long responses (over 1000 chars) are often disliked")
        
        recommendations = []
        if positive_patterns:
            recommendations.append("Continue patterns that users like")
        if negative_patterns:
            recommendations.append("Avoid patterns that users dislike")
        
        return FeedbackAnalysis(
            positive_patterns=positive_patterns,
            negative_patterns=negative_patterns,
            recommendations=recommendations,
        )
    except Exception as e:
        logger.error(f"Error analyzing feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze feedback: {str(e)}")
    finally:
        conn.close()


# Import json for metadata serialization
import json

