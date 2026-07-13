from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    bookmarks,
    chat,
    faq,
    favorites,
    flashcards,
    health,
    history,
    notes,
    quiz,
    summarize,
    transcript,
    video,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(video.router)
api_router.include_router(transcript.router)
api_router.include_router(summarize.router)
api_router.include_router(chat.router)
api_router.include_router(quiz.router)
api_router.include_router(flashcards.router)
api_router.include_router(faq.router)
api_router.include_router(notes.router)
api_router.include_router(auth.router)
api_router.include_router(history.router)
api_router.include_router(favorites.router)
api_router.include_router(bookmarks.router)

# Registered incrementally as each feature is built:
# api_router.include_router(downloads.router, tags=["download"])
