/**
 * MCQ (Multiple Choice Questions) API types.
 *
 * Types for MCQ bank and question management, aligned with backend schemas.
 */

// =============================================================================
// Enums
// =============================================================================

export type MCQDifficulty = "easy" | "medium" | "hard";

// =============================================================================
// MCQ Option Types
// =============================================================================

export interface MCQOptionCreate {
  text: string;
  is_correct: boolean;
}

export interface MCQOptionResponse {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface MCQOptionUpdate {
  text?: string;
  is_correct?: boolean;
}

// =============================================================================
// MCQ Question Types
// =============================================================================

export interface MCQQuestionCreate {
  bank_id: string;
  question_text: string;
  options: MCQOptionCreate[];
  explanation?: string;
  tags?: string[];
  difficulty?: MCQDifficulty;
}

export interface MCQQuestionUpdate {
  question_text?: string;
  options?: MCQOptionCreate[];
  explanation?: string;
  tags?: string[];
  difficulty?: MCQDifficulty;
}

export interface MCQQuestionResponse {
  id: string;
  bank_id: string;
  question_text: string;
  options: MCQOptionResponse[];
  explanation: string | null;
  tags: string[];
  difficulty: MCQDifficulty;
  created_by: string;
  created_at: string;
  updated_at: string | null;
}

export interface MCQQuestionListParams {
  bank_id?: string;
  difficulty?: MCQDifficulty;
  tags?: string[];
  created_by?: string;
  page?: number;
  page_size?: number;
}

// =============================================================================
// MCQ Bank Types
// =============================================================================

export interface MCQBankCreate {
  name: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface MCQBankUpdate {
  name?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface MCQBankResponse {
  id: string;
  name: string;
  description: string | null;
  tags: string[];
  is_public: boolean;
  owner_id: string;
  question_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface MCQBankListParams {
  owner_id?: string;
  is_public?: boolean;
  tags?: string[];
  page?: number;
  page_size?: number;
}

export interface MCQBankSummary {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  question_count: number;
  is_public: boolean;
  created_at: string;
}

// =============================================================================
// MCQ Submission Types
// =============================================================================

export interface MCQAnswerSubmission {
  question_id: string;
  selected_option_id: string;
}

export interface MCQAnswerResponse {
  question_id: string;
  selected_option_id: string;
  correct_option_id: string | null;
  is_correct: boolean;
  explanation: string | null;
}

export interface MCQSubmissionCreate {
  bank_id: string;
  answers: MCQAnswerSubmission[];
}

export interface MCQSubmissionResponse {
  id: string;
  bank_id: string;
  user_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  answers: MCQAnswerResponse[];
  submitted_at: string;
}
