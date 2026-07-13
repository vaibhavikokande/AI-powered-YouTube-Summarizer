from fastapi import APIRouter

from app.api.v1.endpoints import health, transcript, video

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(video.router)
api_router.include_router(transcript.router)

# Registered incrementally as each feature is built:
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(summarize.router, tags=["summarize"])
# api_router.include_router(chat.router, tags=["chat"])
# api_router.include_router(quiz.router, tags=["quiz"])
# api_router.include_router(flashcards.router, tags=["flashcards"])
# api_router.include_router(faq.router, tags=["faq"])
# api_router.include_router(notes.router, tags=["notes"])
# api_router.include_router(history.router, tags=["history"])
# api_router.include_router(downloads.router, tags=["download"])
