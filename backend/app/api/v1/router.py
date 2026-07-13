from fastapi import APIRouter

from app.api.v1.endpoints import chat, faq, flashcards, health, notes, quiz, summarize, transcript, video

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

# Registered incrementally as each feature is built:
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(history.router, tags=["history"])
# api_router.include_router(downloads.router, tags=["download"])
