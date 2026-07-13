from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    bookmarks,
    chat,
    download,
    faq,
    favorites,
    flashcards,
    health,
    history,
    notes,
    quiz,
    share,
    summarize,
    transcript,
    tts,
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
api_router.include_router(download.router)
api_router.include_router(share.router)
api_router.include_router(tts.router)
