import { MCQPage } from "@/pages/MCQPage";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

// ── Mock data ────────────────────────────────────────────────────────────

const MOCK_BANKS = [
  {
    id: "bank-1",
    name: "Architecture Fundamentals",
    description: "Core architecture verification questions",
    owner_id: "user-1",
    question_count: 3,
    is_public: true,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "bank-2",
    name: "Security Checkpoint",
    description: null,
    owner_id: "user-1",
    question_count: 0,
    is_public: false,
    created_at: "2026-01-02T00:00:00Z",
  },
];

const MOCK_QUESTIONS = [
  {
    id: "q-1",
    bank_id: "bank-1",
    question_text: "What is the primary purpose of a verification checkpoint?",
    options: [
      {
        id: "opt-1a",
        text: "To block users from proceeding",
        is_correct: false,
      },
      {
        id: "opt-1b",
        text: "To unlock smarter paths through knowledge verification",
        is_correct: true,
      },
      { id: "opt-1c", text: "To generate revenue", is_correct: false },
    ],
    explanation: "Verification checkpoints improve the modality for everyone.",
    tags: ["architecture", "verification"],
    difficulty: "easy" as const,
    created_by: "user-1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
  },
  {
    id: "q-2",
    bank_id: "bank-1",
    question_text: "Which metric reflects universal participation?",
    options: [
      { id: "opt-2a", text: "Revenue per user", is_correct: false },
      {
        id: "opt-2b",
        text: "Less joules of energy per token",
        is_correct: true,
      },
    ],
    explanation: null,
    tags: ["metrics"],
    difficulty: "medium" as const,
    created_by: "user-1",
    created_at: "2026-01-01T01:00:00Z",
    updated_at: null,
  },
];

const MOCK_SUBMISSION_RESPONSE = {
  id: "sub-1",
  bank_id: "bank-1",
  user_id: "user-1",
  total_questions: 2,
  correct_answers: 2,
  score_percentage: 100,
  answers: [
    {
      question_id: "q-1",
      selected_option_id: "opt-1b",
      correct_option_id: "opt-1b",
      is_correct: true,
      explanation:
        "Verification checkpoints improve the modality for everyone.",
    },
    {
      question_id: "q-2",
      selected_option_id: "opt-2b",
      correct_option_id: "opt-2b",
      is_correct: true,
      explanation: null,
    },
  ],
  submitted_at: "2026-01-01T02:00:00Z",
};

// ── Helpers ──────────────────────────────────────────────────────────────

/** Build a mock window.grid.api that routes by method+endpoint. */
function buildMockApi(overrides?: Record<string, unknown>) {
  const responses: Record<string, unknown> = {
    "GET /api/v1/mcq/banks": MOCK_BANKS,
    ...overrides,
  };

  return vi
    .fn()
    .mockImplementation((method: string, endpoint: string, _body?: unknown) => {
      // Match questions for specific bank
      if (method === "GET" && endpoint.startsWith("/api/v1/mcq/questions")) {
        const url = new URL(endpoint, "http://localhost");
        const bankId = url.searchParams.get("bank_id");
        const questionsKey = `GET /api/v1/mcq/questions?bank_id=${bankId}`;
        if (questionsKey in responses) {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: responses[questionsKey],
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          data: responses["GET /api/v1/mcq/questions"] ?? [],
        });
      }

      // Match submission — mutation calls gridClient.post which returns
      // ApiResponse<ApiResponse<MCQSubmissionResponse>>, so the mock must
      // wrap the payload in a `{ data: ... }` envelope matching the backend
      // ApiResponse shape.  The mutation's mutationFn returns `res.data`
      // (the outer envelope body) and the page accesses `data?.data`.
      if (method === "POST" && endpoint === "/api/v1/mcq/submit") {
        const submitKey = "POST /api/v1/mcq/submit";
        const payload =
          submitKey in responses
            ? responses[submitKey]
            : MOCK_SUBMISSION_RESPONSE;
        return Promise.resolve({
          ok: true,
          status: 200,
          data: { success: true, data: payload, message: "ok", meta: {} },
        });
      }

      // Exact match
      const key = `${method} ${endpoint}`;
      if (key in responses) {
        return Promise.resolve({ ok: true, status: 200, data: responses[key] });
      }

      // Fallback
      return Promise.resolve({ ok: true, status: 200, data: {} });
    });
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("MCQPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.grid.api = buildMockApi();
  });

  // ── Bank selector view ────────────────────────────────────────────────

  describe("BankSelector", () => {
    it("renders title and description", () => {
      renderWithProviders(<MCQPage />);
      expect(screen.getByText("Verification Checkpoint")).toBeInTheDocument();
      expect(
        screen.getByText(/correct answers unlock smarter paths/)
      ).toBeInTheDocument();
    });

    it("renders universal participation metric card", () => {
      renderWithProviders(<MCQPage />);
      expect(
        screen.getByText("Universal Participation Metric")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Less joules of energy per token/)
      ).toBeInTheDocument();
    });

    it("renders bank cards after data loads", async () => {
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(
          screen.getByText("Architecture Fundamentals")
        ).toBeInTheDocument();
        expect(screen.getByText("Security Checkpoint")).toBeInTheDocument();
      });
    });

    it("shows question count badges", async () => {
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(screen.getByText("3 questions")).toBeInTheDocument();
        expect(screen.getByText("0 questions")).toBeInTheDocument();
      });
    });

    it("shows public badge for public banks", async () => {
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(screen.getByText("public")).toBeInTheDocument();
      });
    });

    it("shows bank description when present", async () => {
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(
          screen.getByText("Core architecture verification questions")
        ).toBeInTheDocument();
      });
    });

    it("has a refresh button", () => {
      renderWithProviders(<MCQPage />);
      expect(screen.getByText("Refresh")).toBeInTheDocument();
    });

    it("calls refetch when refresh is clicked", async () => {
      const user = userEvent.setup();
      renderWithProviders(<MCQPage />);
      const refreshBtn = screen
        .getByText("Refresh")
        .closest("button") as HTMLButtonElement;
      await user.click(refreshBtn);
      // After initial load + refresh, api should have been called multiple times
      await waitFor(() => {
        const bankCalls = (
          window.grid.api as ReturnType<typeof vi.fn>
        ).mock.calls.filter(
          (call: unknown[]) =>
            call[0] === "GET" && call[1] === "/api/v1/mcq/banks"
        );
        expect(bankCalls.length).toBeGreaterThanOrEqual(2);
      });
    });

    it("shows empty state when no banks exist", async () => {
      window.grid.api = buildMockApi({ "GET /api/v1/mcq/banks": [] });
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/No question banks available/)
        ).toBeInTheDocument();
      });
    });

    it("shows loading spinner initially", () => {
      // Delay the API response to catch loading state
      window.grid.api = vi.fn().mockImplementation(
        () =>
          new Promise((_resolve) => {
            /* never resolves — catches loading state */
          })
      );
      renderWithProviders(<MCQPage />);
      // The spinner has the animate-spin class on the Loader2 svg
      const spinners = document.querySelectorAll(".animate-spin");
      expect(spinners.length).toBeGreaterThan(0);
    });
  });

  // ── Verification flow ─────────────────────────────────────────────────

  describe("VerificationFlow", () => {
    async function selectBank() {
      const user = userEvent.setup();
      window.grid.api = buildMockApi({
        "GET /api/v1/mcq/banks": MOCK_BANKS,
        "GET /api/v1/mcq/questions": MOCK_QUESTIONS,
        "GET /api/v1/mcq/questions?bank_id=bank-1": MOCK_QUESTIONS,
      });
      renderWithProviders(<MCQPage />);
      await waitFor(() => {
        expect(
          screen.getByText("Architecture Fundamentals")
        ).toBeInTheDocument();
      });
      const bankCard = screen
        .getByText("Architecture Fundamentals")
        .closest("[class*='card']") as HTMLElement;
      await user.click(bankCard);
      return user;
    }

    it("navigates to verification flow when bank is clicked", async () => {
      await selectBank();
      await waitFor(() => {
        expect(
          screen.getByText("Architecture Fundamentals")
        ).toBeInTheDocument();
        expect(screen.getByText("Back")).toBeInTheDocument();
      });
    });

    it("displays questions with their text", async () => {
      await selectBank();
      await waitFor(() => {
        expect(
          screen.getByText(
            "What is the primary purpose of a verification checkpoint?"
          )
        ).toBeInTheDocument();
        expect(
          screen.getByText("Which metric reflects universal participation?")
        ).toBeInTheDocument();
      });
    });

    it("displays question counter", async () => {
      await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Question 1 of 2")).toBeInTheDocument();
        expect(screen.getByText("Question 2 of 2")).toBeInTheDocument();
      });
    });

    it("displays difficulty badges", async () => {
      await selectBank();
      await waitFor(() => {
        expect(screen.getByText("easy")).toBeInTheDocument();
        expect(screen.getByText("medium")).toBeInTheDocument();
      });
    });

    it("displays option buttons for each question", async () => {
      await selectBank();
      await waitFor(() => {
        expect(
          screen.getByText("To block users from proceeding")
        ).toBeInTheDocument();
        expect(
          screen.getByText(
            "To unlock smarter paths through knowledge verification"
          )
        ).toBeInTheDocument();
        expect(screen.getByText("To generate revenue")).toBeInTheDocument();
        expect(screen.getByText("Revenue per user")).toBeInTheDocument();
        expect(
          screen.getByText("Less joules of energy per token")
        ).toBeInTheDocument();
      });
    });

    it("displays question tags", async () => {
      await selectBank();
      await waitFor(() => {
        expect(screen.getByText("architecture")).toBeInTheDocument();
        expect(screen.getByText("verification")).toBeInTheDocument();
        expect(screen.getByText("metrics")).toBeInTheDocument();
      });
    });

    it("shows answered counter as 0/2 initially", async () => {
      await selectBank();
      await waitFor(() => {
        expect(screen.getByText("0/2 answered")).toBeInTheDocument();
      });
    });

    it("updates answered counter when options are selected", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("0/2 answered")).toBeInTheDocument();
      });

      // Select answer for first question
      const opt1 = screen.getByText(
        "To unlock smarter paths through knowledge verification"
      );
      await user.click(opt1);
      expect(screen.getByText("1/2 answered")).toBeInTheDocument();

      // Select answer for second question
      const opt2 = screen.getByText("Less joules of energy per token");
      await user.click(opt2);
      expect(screen.getByText("2/2 answered")).toBeInTheDocument();
    });

    it("submit button is disabled until all questions are answered", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      const submitBtn = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      expect(submitBtn).toBeDisabled();

      // Answer first question
      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      expect(submitBtn).toBeDisabled();

      // Answer second question
      await user.click(screen.getByText("Less joules of energy per token"));
      expect(submitBtn).toBeEnabled();
    });

    it("submits answers and shows success result", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      // Answer both questions correctly
      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      await user.click(screen.getByText("Less joules of energy per token"));

      // Submit
      const submitBtn = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("Excellent verification. Path unlocked.")
        ).toBeInTheDocument();
        expect(screen.getByText(/2\/2/)).toBeInTheDocument();
        expect(screen.getByText(/100%/)).toBeInTheDocument();
      });
    });

    it("shows Correct/Incorrect badges in post-submission review", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      await user.click(screen.getByText("Less joules of energy per token"));

      const submitBtn2 = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn2);

      await waitFor(() => {
        const correctBadges = screen.getAllByText("Correct");
        expect(correctBadges.length).toBe(2);
      });
    });

    it("shows explanation text in post-submission review", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      await user.click(screen.getByText("Less joules of energy per token"));

      const submitBtn3 = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn3);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Verification checkpoints improve the modality for everyone."
          )
        ).toBeInTheDocument();
      });
    });

    it("shows partial verification message for mid-range scores", async () => {
      const partialResponse = {
        ...MOCK_SUBMISSION_RESPONSE,
        correct_answers: 1,
        score_percentage: 50,
        answers: [
          { ...MOCK_SUBMISSION_RESPONSE.answers[0], is_correct: true },
          {
            ...MOCK_SUBMISSION_RESPONSE.answers[1],
            selected_option_id: "opt-2a",
            is_correct: false,
          },
        ],
      };

      const user = await selectBank();
      // Override the submit response for this test
      window.grid.api = buildMockApi({
        "GET /api/v1/mcq/banks": MOCK_BANKS,
        "GET /api/v1/mcq/questions": MOCK_QUESTIONS,
        "POST /api/v1/mcq/submit": partialResponse,
      });

      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      await user.click(screen.getByText("Revenue per user"));

      const submitBtn4 = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn4);

      await waitFor(() => {
        expect(
          screen.getByText("Partial verification. Revisit when ready.")
        ).toBeInTheDocument();
      });
    });

    it("shows no penalty message for low scores", async () => {
      const lowResponse = {
        ...MOCK_SUBMISSION_RESPONSE,
        correct_answers: 0,
        score_percentage: 0,
        answers: [
          {
            ...MOCK_SUBMISSION_RESPONSE.answers[0],
            selected_option_id: "opt-1a",
            is_correct: false,
          },
          {
            ...MOCK_SUBMISSION_RESPONSE.answers[1],
            selected_option_id: "opt-2a",
            is_correct: false,
          },
        ],
      };

      const user = await selectBank();
      window.grid.api = buildMockApi({
        "GET /api/v1/mcq/banks": MOCK_BANKS,
        "GET /api/v1/mcq/questions": MOCK_QUESTIONS,
        "POST /api/v1/mcq/submit": lowResponse,
      });

      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      await user.click(screen.getByText("To block users from proceeding"));
      await user.click(screen.getByText("Revenue per user"));

      const submitBtn5 = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn5);

      await waitFor(() => {
        expect(
          screen.getByText("No penalty. Return anytime to verify.")
        ).toBeInTheDocument();
      });
    });

    it("shows Return to banks button after submission", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Submit Verification")).toBeInTheDocument();
      });

      await user.click(
        screen.getByText(
          "To unlock smarter paths through knowledge verification"
        )
      );
      await user.click(screen.getByText("Less joules of energy per token"));

      const submitBtn6 = screen
        .getByText("Submit Verification")
        .closest("button") as HTMLButtonElement;
      await user.click(submitBtn6);

      await waitFor(() => {
        expect(screen.getByText("Return to banks")).toBeInTheDocument();
      });
    });

    it("returns to bank selector when Back is clicked", async () => {
      const user = await selectBank();
      await waitFor(() => {
        expect(screen.getByText("Back")).toBeInTheDocument();
      });

      const backBtn = screen
        .getByText("Back")
        .closest("button") as HTMLButtonElement;
      await user.click(backBtn);

      await waitFor(() => {
        expect(screen.getByText("Verification Checkpoint")).toBeInTheDocument();
      });
    });

    it("shows empty questions message for bank with no questions", async () => {
      const user = userEvent.setup();
      window.grid.api = buildMockApi({
        "GET /api/v1/mcq/banks": MOCK_BANKS,
        "GET /api/v1/mcq/questions": [],
        "GET /api/v1/mcq/questions?bank_id=bank-2": [],
      });
      renderWithProviders(<MCQPage />);

      await waitFor(() => {
        expect(screen.getByText("Security Checkpoint")).toBeInTheDocument();
      });

      const bankCard = screen
        .getByText("Security Checkpoint")
        .closest("[class*='card']") as HTMLElement;
      await user.click(bankCard);

      await waitFor(() => {
        expect(
          screen.getByText(/This bank has no questions yet/)
        ).toBeInTheDocument();
      });
    });
  });
});
