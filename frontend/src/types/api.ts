export type SummaryType = "short" | "medium" | "detailed" | "bullet";
export type QuizQuestionType = "mcq" | "true_false" | "fill_blank";

export interface VideoResponse {
  id: string;
  youtube_video_id: string;
  url: string;
  title: string | null;
  description: string | null;
  channel_name: string | null;
  channel_id: string | null;
  thumbnail_url: string | null;
  duration_seconds: number | null;
  view_count: number | null;
  upload_date: string | null;
  original_language: string | null;
  created_at: string;
}

export interface TranscriptSegment {
  start: number;
  duration: number;
  text: string;
}

export interface TranscriptResponse {
  id: string;
  video_id: string;
  language: string;
  is_auto_generated: boolean;
  is_translated: boolean;
  source_language: string | null;
  full_text: string;
  segments: TranscriptSegment[];
}

export interface TimestampedSection {
  timestamp_seconds: number;
  title: string;
  summary: string;
}

export interface KeyTakeaways {
  important_concepts: string[];
  action_items: string[];
  important_quotes: string[];
  definitions: Record<string, string>;
  statistics: string[];
}

export interface Topics {
  main_topics: string[];
  subtopics: string[];
  tags: string[];
}

export interface SummaryResponse {
  id: string;
  video_id: string;
  summary_type: SummaryType;
  content: string;
  key_takeaways: KeyTakeaways;
  timestamped_sections: TimestampedSection[];
  topics: Topics;
  mindmap_markdown: string | null;
  llm_provider: string;
  created_at: string;
}

export interface JobEnqueuedResponse {
  task_id: string;
  status: string;
}

export interface JobStatusResponse<T = unknown> {
  task_id: string;
  status: "PENDING" | "STARTED" | "RETRY" | "SUCCESS" | "FAILURE" | string;
  result: T | null;
  error: string | null;
}

export interface FAQItemResponse {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

export interface FlashcardResponse {
  id: string;
  question: string;
  answer: string;
}

export interface QuizQuestionResponse {
  id: string;
  question_type: QuizQuestionType;
  question_text: string;
  options: string[] | null;
  correct_answer: string;
  explanation: string | null;
}

export interface QuizResponse {
  id: string;
  title: string;
  questions: QuizQuestionResponse[];
}

export interface NoteResponse {
  id: string;
  video_id: string;
  content_markdown: string;
  created_at: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface FavoriteResponse {
  id: string;
  video_id: string;
  created_at: string;
}

export interface BookmarkResponse {
  id: string;
  video_id: string;
  timestamp_seconds: number;
  note: string | null;
  created_at: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}
