import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMCQBanks, useMCQQuestions, useSubmitMCQAnswers } from "@/hooks";
import { cn } from "@/lib/utils";
import type {
  MCQAnswerResponse,
  MCQBankSummary,
  MCQDifficulty,
  MCQOptionResponse,
  MCQQuestionResponse,
  MCQSubmissionResponse,
} from "@/types/mcq";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Radar,
  RefreshCw,
  X,
  Zap,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";

// ── Helpers ──────────────────────────────────────────────────────────────

function difficultyVariant(
  d: MCQDifficulty
): "default" | "secondary" | "warning" | "destructive" {
  switch (d) {
    case "easy":
      return "secondary";
    case "medium":
      return "warning";
    case "hard":
      return "destructive";
    default:
      return "default";
  }
}

function scoreMessage(pct: number): {
  text: string;
  tone: "success" | "warning" | "default";
} {
  if (pct >= 80)
    return { text: "Excellent verification. Path unlocked.", tone: "success" };
  if (pct >= 50)
    return {
      text: "Partial verification. Revisit when ready.",
      tone: "warning",
    };
  return { text: "No penalty. Return anytime to verify.", tone: "default" };
}

// ── Bank selector view ───────────────────────────────────────────────────

function BankSelector({
  banks,
  isLoading,
  onSelect,
  onRefresh,
}: {
  banks: MCQBankSummary[];
  isLoading: boolean;
  onSelect: (bank: MCQBankSummary) => void;
  onRefresh: () => void;
}) {
  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Verification Checkpoint
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Choose a question bank to begin knowledge verification. Nothing bad
            happens if you skip — correct answers unlock smarter paths.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh}>
          <RefreshCw
            className={cn("mr-1.5 h-3.5 w-3.5", isLoading && "animate-spin")}
          />
          Refresh
        </Button>
      </div>

      {/* Metric strip */}
      <Card className="border-[var(--primary)]/20">
        <CardContent className="flex items-center gap-3 p-4">
          <Zap className="h-5 w-5 text-[var(--primary)] shrink-0" />
          <div>
            <p className="text-xs font-medium">
              Universal Participation Metric
            </p>
            <p className="text-[11px] text-[var(--muted-foreground)]">
              Less joules of energy per token. Better, available, and anyone can
              participate — verification improves the modality for everyone.
            </p>
          </div>
        </CardContent>
      </Card>

      {isLoading && !banks.length ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-[var(--muted-foreground)]" />
        </div>
      ) : banks.length === 0 ? (
        <Card className="border-[var(--warning)]/30">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-[var(--warning)] shrink-0" />
            <p className="text-sm text-[var(--muted-foreground)]">
              No question banks available. Create banks via the MCQ API to
              enable verification checkpoints.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {banks.map((bank) => (
            <Card
              key={bank.id}
              className="glass cursor-pointer transition-colors hover:border-[var(--primary)]/40"
              onClick={() => onSelect(bank)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm">
                  <span className="truncate">{bank.name}</span>
                  <ChevronRight className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {bank.description && (
                  <p className="text-xs text-[var(--muted-foreground)] line-clamp-2">
                    {bank.description}
                  </p>
                )}
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px]">
                    {bank.question_count} question
                    {bank.question_count !== 1 ? "s" : ""}
                  </Badge>
                  {bank.is_public && (
                    <Badge variant="secondary" className="text-[10px]">
                      public
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}

// ── Question card (single question in verification flow) ─────────────────

function QuestionCard({
  question,
  index,
  total,
  selectedOptionId,
  onSelect,
}: {
  question: MCQQuestionResponse;
  index: number;
  total: number;
  selectedOptionId: string | undefined;
  onSelect: (optionId: string) => void;
}) {
  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <span>
            Question {index + 1} of {total}
          </span>
          <Badge
            variant={difficultyVariant(question.difficulty)}
            className="text-[10px]"
          >
            {question.difficulty}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm font-medium leading-relaxed">
          {question.question_text}
        </p>
        <div className="space-y-2">
          {question.options.map((opt: MCQOptionResponse) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onSelect(opt.id)}
              className={cn(
                "w-full rounded-md border p-3 text-left text-sm transition-colors",
                selectedOptionId === opt.id
                  ? "border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--primary)]"
                  : "border-[var(--input)] bg-transparent hover:bg-[var(--muted)]"
              )}
            >
              {opt.text}
            </button>
          ))}
        </div>
        {question.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {question.tags.map((tag) => (
              <Badge
                key={tag}
                variant="outline"
                className="text-[9px] font-normal"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Verification flow (questions + submission) ───────────────────────────

function VerificationFlow({
  bank,
  questions,
  isLoading,
  onBack,
}: {
  bank: MCQBankSummary;
  questions: MCQQuestionResponse[];
  isLoading: boolean;
  onBack: () => void;
}) {
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [result, setResult] = useState<MCQSubmissionResponse | null>(null);
  const submit = useSubmitMCQAnswers();

  const answeredCount = Object.keys(selections).length;
  const totalCount = questions.length;
  const allAnswered = answeredCount === totalCount && totalCount > 0;

  const handleSelect = useCallback(
    (questionId: string, optionId: string) => {
      if (result) return; // locked after submission
      setSelections((prev) => ({ ...prev, [questionId]: optionId }));
    },
    [result]
  );

  const handleSubmit = useCallback(() => {
    if (!allAnswered) return;
    submit.mutate(
      {
        bank_id: bank.id,
        answers: Object.entries(selections).map(
          ([question_id, selected_option_id]) => ({
            question_id,
            selected_option_id,
          })
        ),
      },
      {
        onSuccess: (data) => {
          if (data?.data) {
            setResult(data.data);
          }
        },
      }
    );
  }, [allAnswered, bank.id, selections, submit]);

  const answerMap = useMemo(() => {
    if (!result) return new Map<string, MCQAnswerResponse>();
    return new Map(result.answers.map((a) => [a.question_id, a]));
  }, [result]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--muted-foreground)]" />
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <>
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
          Back
        </Button>
        <Card className="border-[var(--warning)]/30">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-[var(--warning)] shrink-0" />
            <p className="text-sm text-[var(--muted-foreground)]">
              This bank has no questions yet. Questions can be added via the MCQ
              API.
            </p>
          </CardContent>
        </Card>
      </>
    );
  }

  const verdict = result ? scoreMessage(result.score_percentage) : null;

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{bank.name}</h1>
            <p className="text-sm text-[var(--muted-foreground)]">
              {bank.description || "Knowledge verification checkpoint"}
            </p>
          </div>
        </div>
        {!result && (
          <Badge variant="outline">
            {answeredCount}/{totalCount} answered
          </Badge>
        )}
      </div>

      {/* Result summary */}
      {result && verdict && (
        <Card
          className={cn(
            "border-2",
            verdict.tone === "success" && "border-[var(--success)]/40",
            verdict.tone === "warning" && "border-[var(--warning)]/40",
            verdict.tone === "default" && "border-[var(--muted-foreground)]/20"
          )}
        >
          <CardContent className="flex items-center gap-4 p-4">
            {verdict.tone === "success" ? (
              <CheckCircle2 className="h-8 w-8 shrink-0 text-[var(--success)]" />
            ) : (
              <Radar className="h-8 w-8 shrink-0 text-[var(--primary)]" />
            )}
            <div className="flex-1">
              <p className="text-sm font-medium">{verdict.text}</p>
              <p className="text-xs text-[var(--muted-foreground)]">
                Score: {result.correct_answers}/{result.total_questions} (
                {result.score_percentage.toFixed(0)}%)
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={onBack}>
              Return to banks
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Questions */}
      {!result ? (
        <div className="space-y-4">
          {questions.map((q, i) => (
            <QuestionCard
              key={q.id}
              question={q}
              index={i}
              total={totalCount}
              selectedOptionId={selections[q.id]}
              onSelect={(optId) => handleSelect(q.id, optId)}
            />
          ))}
          <div className="flex justify-end">
            <Button
              onClick={handleSubmit}
              disabled={!allAnswered || submit.isPending}
            >
              {submit.isPending ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Check className="mr-1.5 h-4 w-4" />
              )}
              Submit Verification
            </Button>
          </div>
        </div>
      ) : (
        /* Post-submission review */
        <div className="space-y-4">
          {questions.map((q, i) => {
            const answer = answerMap.get(q.id);
            return (
              <Card key={q.id} className="glass">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between text-sm">
                    <span>
                      Question {i + 1} of {totalCount}
                    </span>
                    {answer && (
                      <Badge
                        variant={answer.is_correct ? "success" : "destructive"}
                        className="text-[10px]"
                      >
                        {answer.is_correct ? "Correct" : "Incorrect"}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm font-medium leading-relaxed">
                    {q.question_text}
                  </p>
                  <div className="space-y-2">
                    {q.options.map((opt: MCQOptionResponse) => {
                      const isSelected = selections[q.id] === opt.id;
                      const isCorrect = answer?.correct_option_id === opt.id;
                      return (
                        <div
                          key={opt.id}
                          className={cn(
                            "flex items-center gap-2 rounded-md border p-3 text-sm",
                            isCorrect &&
                              "border-[var(--success)] bg-[var(--success)]/10",
                            isSelected &&
                              !isCorrect &&
                              "border-[var(--destructive)] bg-[var(--destructive)]/10",
                            !isSelected &&
                              !isCorrect &&
                              "border-[var(--input)] opacity-60"
                          )}
                        >
                          <span className="flex-1">{opt.text}</span>
                          {isCorrect && (
                            <Check className="h-4 w-4 shrink-0 text-[var(--success)]" />
                          )}
                          {isSelected && !isCorrect && (
                            <X className="h-4 w-4 shrink-0 text-[var(--destructive)]" />
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {answer?.explanation && (
                    <p className="rounded bg-[var(--muted)] p-2 text-xs text-[var(--muted-foreground)]">
                      {answer.explanation}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}

// ── Main page export ─────────────────────────────────────────────────────

export function MCQPage() {
  const [selectedBank, setSelectedBank] = useState<MCQBankSummary | null>(null);
  const banks = useMCQBanks();
  const questions = useMCQQuestions(
    selectedBank ? { bank_id: selectedBank.id } : undefined
  );

  const banksData = banks.data ?? [];

  return (
    <div className="space-y-6 animate-fade-in">
      {selectedBank ? (
        <VerificationFlow
          bank={selectedBank}
          questions={questions.data ?? []}
          isLoading={questions.isLoading}
          onBack={() => setSelectedBank(null)}
        />
      ) : (
        <BankSelector
          banks={banksData}
          isLoading={banks.isLoading}
          onSelect={setSelectedBank}
          onRefresh={() => banks.refetch()}
        />
      )}
    </div>
  );
}
