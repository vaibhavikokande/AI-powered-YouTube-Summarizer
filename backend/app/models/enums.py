import enum


class SummaryType(str, enum.Enum):
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"
    BULLET = "bullet"


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class QuizQuestionType(str, enum.Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class LLMProviderName(str, enum.Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
