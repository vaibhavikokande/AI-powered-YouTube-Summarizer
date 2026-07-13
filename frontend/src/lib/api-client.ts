import { api } from "@/services/api";
import type {
  BookmarkResponse,
  FAQItemResponse,
  FavoriteResponse,
  FlashcardResponse,
  JobEnqueuedResponse,
  JobStatusResponse,
  NoteResponse,
  PaginatedResponse,
  QuizQuestionType,
  QuizResponse,
  SummaryType,
  Token,
  TranscriptResponse,
  UserResponse,
  VideoResponse,
} from "@/types/api";

// --- Video / transcript ---

export const getVideo = (url: string) =>
  api.get<VideoResponse>("/video", { params: { url } }).then((r) => r.data);

export const getTranscript = (url: string, language = "en") =>
  api
    .get<TranscriptResponse>("/transcript", { params: { url, language } })
    .then((r) => r.data);

// --- Job-based content generation (Step 11) ---

export const requestSummary = (params: {
  url: string;
  summary_types: SummaryType[];
  language?: string;
  include_mindmap?: boolean;
}) => api.post<JobEnqueuedResponse>("/summarize", params).then((r) => r.data);

export const requestQuiz = (params: {
  url: string;
  question_types?: QuizQuestionType[];
  count?: number;
}) => api.post<JobEnqueuedResponse>("/quiz", params).then((r) => r.data);

export const requestFlashcards = (params: { url: string; count?: number }) =>
  api.post<JobEnqueuedResponse>("/flashcards", params).then((r) => r.data);

export const requestFAQ = (params: { url: string; count?: number }) =>
  api.post<JobEnqueuedResponse>("/faq", params).then((r) => r.data);

export const requestNotes = (params: { url: string }) =>
  api.post<JobEnqueuedResponse>("/notes", params).then((r) => r.data);

export const getJobStatus = <T = unknown>(taskId: string) =>
  api.get<JobStatusResponse<T>>(`/jobs/${taskId}`).then((r) => r.data);

// --- Auth ---

export const register = (params: { email: string; password: string; full_name?: string }) =>
  api.post<Token>("/register", params).then((r) => r.data);

export const login = (params: { email: string; password: string }) =>
  api.post<Token>("/login", params).then((r) => r.data);

export const loginWithGoogle = (idToken: string) =>
  api.post<Token>("/login/google", { id_token: idToken }).then((r) => r.data);

export const getMe = () => api.get<UserResponse>("/me").then((r) => r.data);

// --- Dashboard ---

export const getHistory = (params: { search?: string; limit?: number; offset?: number } = {}) =>
  api.get<PaginatedResponse<VideoResponse>>("/history", { params }).then((r) => r.data);

export const listFavorites = () =>
  api.get<FavoriteResponse[]>("/favorites").then((r) => r.data);

export const addFavorite = (videoId: string) =>
  api.post<FavoriteResponse>(`/favorites/${videoId}`).then((r) => r.data);

export const removeFavorite = (videoId: string) => api.delete(`/favorites/${videoId}`);

export const listBookmarks = () =>
  api.get<BookmarkResponse[]>("/bookmarks").then((r) => r.data);

export const addBookmark = (params: { video_id: string; timestamp_seconds: number; note?: string }) =>
  api.post<BookmarkResponse>("/bookmarks", params).then((r) => r.data);

export const removeBookmark = (bookmarkId: string) => api.delete(`/bookmarks/${bookmarkId}`);

// --- Export / share ---

export const downloadUrl = (summaryId: string, format: "pdf" | "docx" | "markdown" | "txt") =>
  `/api/v1/download?summary_id=${summaryId}&format=${format}`;

export const ttsUrl = (summaryId: string) => `/api/v1/tts?summary_id=${summaryId}`;

export const createShareLink = (summaryId: string) =>
  api.post<{ token: string }>("/share", { summary_id: summaryId }).then((r) => r.data);

export type {
  FAQItemResponse,
  FlashcardResponse,
  NoteResponse,
  QuizResponse,
};
