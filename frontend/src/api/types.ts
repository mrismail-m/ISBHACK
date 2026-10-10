export interface User {
  id: string;
  name: string;
  role: 'teacher' | 'student';
  classroom_id: string;
}

export interface RubricCriterion {
  id: string;
  name: string;
  description: string;
  max_marks: number;
  topic: string;
  levels: string[];
}

export interface Rubric {
  criteria: RubricCriterion[];
}

export interface Assessment {
  id: string;
  classroom_id: string;
  kind: 'assignment' | 'quiz' | 'exam';
  title: string;
  instructions_md: string;
  max_marks: number;
  pass_mark_pct: number;
  rubric: Rubric | null;
  model_answer_md: string | null;
  strictness: 'lenient' | 'normal' | 'strict' | 'very_strict';
  viva_enabled: boolean;
  viva_weight: number;
  viva_question_count: number;
  viva_time_limit_s: number;
  feedback_mode: 'hints' | 'full';
  release_mode: 'after_approval' | 'auto';
  ai_policy: 'not_allowed' | 'allowed_with_disclosure' | 'allowed';
  paste_flag_chars: number;
  topics: string[];
  status: 'draft' | 'open' | 'closed';
  due_at: string;
  created_at: string;
}

export type AssessmentCreate = Omit<Assessment, 'id' | 'status' | 'created_at'>;

export interface Question {
  id: string;
  assessment_id: string;
  kind: 'mcq';
  text: string;
  options: string[];
  answer_key?: number;
  marks: number;
  topic: string;
}

export interface SubmissionAnswer {
  question_id: string;
  choice: number;
  text: string | null;
}

export interface Submission {
  id: string;
  assessment_id: string;
  student_id: string;
  content_md: string;
  answers: SubmissionAnswer[];
  status: 'draft' | 'submitted' | 'graded' | 'approved' | 'released';
  started_at: string;
  submitted_at: string | null;
}

export interface SubmissionRow {
  submission_id: string;
  label: string;
  student_id: string;
  student_name: string;
  status: 'draft' | 'submitted' | 'graded' | 'approved' | 'released';
  submitted_at: string | null;
  ai_total: number | null;
  final_total: number | null;
  max_marks: number;
  understanding: number | null;
  score_pct: number | null;
  score_is_final: boolean;
  overall_confidence: number | null;
  flags: string[];
}

export interface GradeEvidence {
  quote: string;
  start: number;
  end: number;
  verified: boolean;
}

export interface GradeCriterion {
  criterion_id: string;
  level: number;
  minor_errors: number;
  ambiguous: boolean;
  ai_marks: number;
  final_marks: number;
  evidence: GradeEvidence[];
  reasoning: string;
  confidence: number;
  teacher_note: string | null;
}

export interface FeedbackTopic {
  tag: string;
  level: 'strong' | 'ok' | 'weak';
}

export interface FeedbackStrength {
  criterion_id: string;
  text: string;
  quote: string;
}

export interface FeedbackImprovement {
  criterion_id: string;
  text: string;
  quote: string;
  hint?: string;
  explanation?: string;
}

export interface Feedback {
  mode: 'hints' | 'full';
  strengths: FeedbackStrength[];
  improvements: FeedbackImprovement[];
  next_step: string;
  topics: FeedbackTopic[];
}

export interface Grade {
  id: string;
  submission_id: string;
  status: 'ai_draft' | 'approved';
  strictness_used: 'lenient' | 'normal' | 'strict' | 'very_strict';
  prompt_version: string;
  model_id: string;
  max_marks: number;
  criteria: GradeCriterion[];
  ai_total: number;
  final_total: number;
  overall_confidence: number;
  grader_flags: string[];
  feedback: Feedback;
  teacher_note: string | null;
  approved_at: string | null;
  released_at: string | null;
}

export interface StrictnessPreviewLevel {
  strictness: 'lenient' | 'normal' | 'strict' | 'very_strict';
  total: number;
  criteria: { criterion_id: string; marks: number }[];
}

export interface StrictnessPreview {
  levels: StrictnessPreviewLevel[];
  note: string;
}

export interface ApproveRequest {
  criteria_overrides: { criterion_id: string; marks: number; note: string }[];
  teacher_note: string | null;
  feedback_edits?: { next_step?: string };
  release: boolean;
}

export interface StudentResult {
  submission_id: string;
  assessment_id: string;
  max_marks: number;
  work_marks: number;
  understanding: number | null;
  viva_weight: number;
  final_marks: number;
  grace_marks: number;
  final_with_grace: number;
  final_pct: number;
  feedback: Feedback;
  released_at: string | null;
}

export interface VivaQuestion {
  id: string;
  kind: 'explain' | 'change' | 'defend' | 'trace';
  text: string;
  topic: string;
  time_limit_s: number;
}

export interface VivaStart {
  session_id: string;
  questions: VivaQuestion[];
  total_time_limit_s: number;
}

export interface VivaAnswer {
  question_id: string;
  answer_text: string;
  time_taken_s: number;
  pasted: boolean;
  tab_switches: number;
}

export interface VivaResult {
  understanding: number;
  answered: number;
  total: number;
}

export interface VivaDetailItem {
  question_id: string;
  text: string;
  answer_text: string;
  score: number;
  note: string;
  time_taken_s: number;
  pasted: boolean;
  tab_switches: number;
}

export interface VivaDetail {
  status: 'done' | 'in_progress';
  understanding: number;
  items: VivaDetailItem[];
}

export interface ActivityEvent {
  seq: number;
  t: number;
  k: 'start' | 'end' | 'type' | 'paste' | 'drop' | 'cut' | 'del' | 'undo' | 'redo' | 'blur' | 'focus' | 'hidden' | 'visible';
  from: number;
  to: number;
  text: string;
}

export interface ActivityBatch {
  session_id: string;
  session_started_at: string;
  events: ActivityEvent[];
}

export interface ActivityEvents {
  sessions: { session_id: string; started_at: string }[];
  events: (ActivityEvent & { session_id: string })[];
}

export interface PasteChunk {
  session_id: string;
  event_seq: number;
  at: string;
  t: number;
  chars: number;
  survived_chars: number;
  survived_pct: number;
  major: boolean;
  declared_source: string | null;
}

export interface ActivitySummary {
  submission_id: string;
  final_chars: number;
  typed_pct: number;
  pasted_pct: number;
  paste_chunks: PasteChunk[];
  revision_ratio: number;
  active_minutes: number;
  span_minutes: number;
  tab_switches: number;
  sessions: number;
  bucket: 'minute' | 'hour';
  heatmap: { bucket_start: string; edits: number; typed_chars: number; pasted_chars: number }[];
}

export interface AssessmentStats {
  assessment_id: string;
  enrolled: number;
  submitted: number;
  graded: number;
  approved: number;
  released: number;
  pending_review: number;
  final: boolean;
  avg_pct: number;
  median_pct: number;
  pass_rate_pct: number;
  highest_pct: number;
  lowest_pct: number;
  histogram: { bin: string; count: number }[];
  topic_averages: { topic: string; avg_pct: number; n: number }[];
  criterion_averages: { criterion_id: string; name: string; avg_pct: number }[];
  grace_marks_applied: number;
}

export interface ClassPerformance {
  classroom_id: string;
  assessments: { assessment_id: string; title: string; kind: string; due_at: string; avg_pct: number; pass_rate_pct: number }[];
  students: { student_id: string; name: string; scores_pct: number[] }[];
}

export interface AttentionStudent {
  student_id: string;
  name: string;
  reasons: ('below_pass_recent' | 'falling_trend' | 'low_understanding' | 'missing_work')[];
  recent_scores_pct: number[];
  last_understanding: number | null;
}

export interface GracePreview {
  marks: number;
  affected_students: number;
  capped_count: number;
  before: { avg_pct: number; pass_rate_pct: number };
  after: { avg_pct: number; pass_rate_pct: number };
}

export interface GraceState {
  total_marks: number;
  entries: { id: string; marks: number; reason: string; applied_at: string; undone_at: string | null }[];
}

export interface OverrideStats {
  graded: number;
  overridden: number;
  override_rate_pct: number;
  mean_abs_delta_marks: number;
  mean_signed_delta_marks: number;
  by_criterion: { criterion_id: string; override_rate_pct: number; mean_signed_delta_marks: number }[];
}

export interface TrustReport {
  generated_at: string;
  model_id: string;
  prompt_version: string;
  dataset: { assignment: string; n_answers: number; n_raters: number };
  accuracy: { ai_vs_human_mae: number; human_vs_human_mae: number; ai_vs_human_qwk: number; human_vs_human_qwk: number };
  consistency: { runs: number; mean_range_marks: number; max_range_marks: number };
  bias_probes: { name: string; n: number; mean_abs_delta_marks: number; max_abs_delta_marks: number; threshold_marks: number; passed: boolean }[];
  strictness_ordering: { passed: boolean; violations: number };
  editor_signals: { samples: number; typed_flagged: number; pasted_flagged: number; retyped_flagged: number };
  limitations: string[];
}
