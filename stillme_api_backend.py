"""
StillMe API Backend for Community Dashboard
==========================================
This file extends the existing api_server.py to support community dashboard features.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

# Import existing StillMe framework
try:
    from stillme_core.framework import StillMeFramework
    stillme_framework = StillMeFramework()
except ImportError:
    # Fallback for development
    class MockStillMeFramework:
        def chat(self, message: str) -> str:
            return f"StillMe: I received your message: '{message}'. I'm currently learning Python Advanced Programming."
        
        def learn(self, lesson_content: str) -> Dict:
            return {
                "status": "learning_completed",
                "lesson": lesson_content,
                "timestamp": datetime.now().isoformat()
            }
    
    stillme_framework = MockStillMeFramework()

# Initialize FastAPI app
app = FastAPI(
    title="StillMe Community API",
    description="API for StillMe Community Dashboard",
    version="1.0.0"
)

# Add CORS middleware for Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "stillme_community.db"

def init_database():
    """Initialize SQLite database for community features"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            votes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_id) REFERENCES lessons (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            response TEXT,
            model_used TEXT,
            latency REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample lessons
    sample_lessons = [
        ("AI Ethics & Safety", "Learn about ethical AI development, bias prevention, and safety measures", "AI Ethics content...", 23),
        ("Machine Learning Fundamentals", "Deep dive into ML algorithms, neural networks, and practical applications", "ML content...", 18),
        ("Modern Web Development", "Learn React, Node.js, and full-stack development practices", "Web dev content...", 12)
    ]
    
    for lesson in sample_lessons:
        cursor.execute('''
            INSERT OR IGNORE INTO lessons (title, description, content, votes)
            VALUES (?, ?, ?, ?)
        ''', lesson)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    model: str
    latency: float
    timestamp: str

class VoteRequest(BaseModel):
    lesson_id: int
    user_id: str

class VoteResponse(BaseModel):
    status: str
    votes: int
    needed: int
    message: str

class LessonResponse(BaseModel):
    id: int
    title: str
    description: str
    votes: int
    status: str

class LearningProgressResponse(BaseModel):
    current_lesson: str
    completed_lessons: int
    total_lessons: int
    progress_percentage: float

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StillMe Community API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stillme_status": "active"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_stillme(request: ChatRequest):
    """Chat with StillMe"""
    start_time = time.time()
    
    try:
        # Get response from StillMe
        response = stillme_framework.chat(request.message)
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (user_id, message, response, model_used, latency)
            VALUES (?, ?, ?, ?, ?)
        ''', (request.user_id, request.message, response, "deepseek-v3-0324", latency))
        conn.commit()
        conn.close()
        
        return ChatResponse(
            response=response,
            model="deepseek-v3-0324",
            latency=round(latency, 2),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/vote", response_model=VoteResponse)
async def vote_for_lesson(request: VoteRequest):
    """Vote for a lesson"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user already voted
        cursor.execute('''
            SELECT id FROM votes WHERE lesson_id = ? AND user_id = ?
        ''', (request.lesson_id, request.user_id))
        
        if cursor.fetchone():
            conn.close()
            return VoteResponse(
                status="already_voted",
                votes=0,
                needed=0,
                message="You have already voted for this lesson"
            )
        
        # Add vote
        cursor.execute('''
            INSERT INTO votes (lesson_id, user_id) VALUES (?, ?)
        ''', (request.lesson_id, request.user_id))
        
        # Update vote count
        cursor.execute('''
            UPDATE lessons SET votes = votes + 1 WHERE id = ?
        ''', (request.lesson_id,))
        
        # Get current vote count
        cursor.execute('''
            SELECT votes FROM lessons WHERE id = ?
        ''', (request.lesson_id,))
        
        vote_count = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        # Check if threshold reached (50 votes)
        if vote_count >= 50:
            # Trigger learning
            await trigger_learning(request.lesson_id)
            return VoteResponse(
                status="learning_started",
                votes=vote_count,
                needed=0,
                message="🎉 Đủ votes! StillMe đang học bài này!"
            )
        
        return VoteResponse(
            status="voted",
            votes=vote_count,
            needed=50 - vote_count,
            message=f"Vote recorded! {vote_count}/50 votes"
        )
        
    except Exception as e:
        logging.error(f"Error voting: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/lessons", response_model=List[LessonResponse])
async def get_lessons():
    """Get all lessons with vote counts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, votes, status FROM lessons
            ORDER BY votes DESC
        ''')
        
        lessons = []
        for row in cursor.fetchall():
            lessons.append(LessonResponse(
                id=row[0],
                title=row[1],
                description=row[2],
                votes=row[3],
                status=row[4]
            ))
        
        conn.close()
        return lessons
        
    except Exception as e:
        logging.error(f"Error getting lessons: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/progress", response_model=LearningProgressResponse)
async def get_learning_progress():
    """Get StillMe's learning progress"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current lesson
        cursor.execute('''
            SELECT title FROM lessons WHERE status = 'learning' LIMIT 1
        ''')
        current_lesson_row = cursor.fetchone()
        current_lesson = current_lesson_row[0] if current_lesson_row else "Python Advanced Programming"
        
        # Get completed lessons count
        cursor.execute('''
            SELECT COUNT(*) FROM lessons WHERE status = 'completed'
        ''')
        completed_lessons = cursor.fetchone()[0]
        
        # Get total lessons
        cursor.execute('''
            SELECT COUNT(*) FROM lessons
        ''')
        total_lessons = cursor.fetchone()[0]
        
        conn.close()
        
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        return LearningProgressResponse(
            current_lesson=current_lesson,
            completed_lessons=completed_lessons,
            total_lessons=total_lessons,
            progress_percentage=round(progress_percentage, 1)
        )
        
    except Exception as e:
        logging.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def trigger_learning(lesson_id: int):
    """Trigger StillMe to learn a lesson"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get lesson content
        cursor.execute('''
            SELECT title, content FROM lessons WHERE id = ?
        ''', (lesson_id,))
        
        lesson_data = cursor.fetchone()
        if not lesson_data:
            return
        
        title, content = lesson_data
        
        # Update lesson status
        cursor.execute('''
            UPDATE lessons SET status = 'learning' WHERE id = ?
        ''', (lesson_id,))
        
        conn.commit()
        conn.close()
        
        # Trigger StillMe learning
        result = stillme_framework.learn(content)
        
        # Mark as completed
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE lessons SET status = 'completed' WHERE id = ?
        ''', (lesson_id,))
        conn.commit()
        conn.close()
        
        # Send notifications (implement based on your notification system)
        await send_notifications(f"StillMe đã hoàn thành bài học: {title}")
        
        logging.info(f"StillMe completed learning lesson: {title}")
        
    except Exception as e:
        logging.error(f"Error triggering learning: {e}")

async def send_notifications(message: str):
    """Send notifications via email, telegram, etc."""
    # Implement your notification system here
    # This could include:
    # - Email notifications
    # - Telegram bot messages
    # - Dashboard notifications
    # - Webhook calls
    
    logging.info(f"Notification sent: {message}")
    
    # Example implementation:
    # await send_email_notification(message)
    # await send_telegram_notification(message)
    # await send_dashboard_notification(message)

# Admin endpoints (for your private admin dashboard)
@app.post("/api/admin/lesson")
async def add_lesson_admin(title: str, description: str, content: str):
    """Admin endpoint to add lessons directly"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO lessons (title, description, content, status)
            VALUES (?, ?, ?, 'pending')
        ''', (title, description, content))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Lesson added successfully"}
        
    except Exception as e:
        logging.error(f"Error adding lesson: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/admin/learn")
async def force_learn_lesson(lesson_id: int):
    """Admin endpoint to force StillMe to learn a lesson"""
    await trigger_learning(lesson_id)
    return {"status": "success", "message": "Learning triggered"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
