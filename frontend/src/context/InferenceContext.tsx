import React, { createContext, useContext, useReducer, ReactNode } from "react";
import { apiClient } from "../api/client";

interface InferenceRequest {
  prompt: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  context?: Record<string, unknown>;
}

interface InferenceResponse {
  result: string;
  model: string;
  tokens_used: number;
  processing_time: number;
  metadata?: Record<string, unknown>;
}

interface InferenceState {
  currentRequest: InferenceRequest | null;
  currentResponse: InferenceResponse | null;
  asyncTasks: Record<
    string,
    {
      status: "queued" | "processing" | "completed" | "failed";
      result?: InferenceResponse;
      error?: string;
    }
  >;
  isLoading: boolean;
  error: string | null;
  models: string[];
  defaultModel: string;
}

interface InferenceAction {
  type:
    | "SET_LOADING"
    | "SET_REQUEST"
    | "SET_RESPONSE"
    | "SET_ERROR"
    | "CLEAR_ERROR"
    | "START_ASYNC_TASK"
    | "UPDATE_ASYNC_TASK"
    | "SET_MODELS"
    | "CLEAR_RESPONSE";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload?: any;
}

const initialState: InferenceState = {
  currentRequest: null,
  currentResponse: null,
  asyncTasks: {},
  isLoading: false,
  error: null,
  models: [],
  defaultModel: "gpt-3.5-turbo",
};

function inferenceReducer(
  state: InferenceState,
  action: InferenceAction
): InferenceState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_REQUEST":
      return { ...state, currentRequest: action.payload };
    case "SET_RESPONSE":
      return {
        ...state,
        currentResponse: action.payload,
        isLoading: false,
        error: null,
      };
    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case "CLEAR_ERROR":
      return { ...state, error: null };
    case "START_ASYNC_TASK":
      return {
        ...state,
        asyncTasks: {
          ...state.asyncTasks,
          [action.payload.taskId]: {
            status: "queued",
          },
        },
      };
    case "UPDATE_ASYNC_TASK":
      return {
        ...state,
        asyncTasks: {
          ...state.asyncTasks,
          [action.payload.taskId]: action.payload.taskData,
        },
      };
    case "SET_MODELS":
      return {
        ...state,
        models: action.payload.models,
        defaultModel: action.payload.default,
      };
    case "CLEAR_RESPONSE":
      return {
        ...state,
        currentRequest: null,
        currentResponse: null,
        error: null,
      };
    default:
      return state;
  }
}

interface InferenceContextType extends InferenceState {
  createInference: (request: InferenceRequest) => Promise<void>;
  createAsyncInference: (request: InferenceRequest) => Promise<string>;
  checkAsyncStatus: (taskId: string) => Promise<void>;
  loadModels: () => Promise<void>;
  clearResponse: () => void;
  clearError: () => void;
}

const InferenceContext = createContext<InferenceContextType | undefined>(
  undefined
);

export const useInference = (): InferenceContextType => {
  const context = useContext(InferenceContext);
  if (!context) {
    throw new Error("useInference must be used within an InferenceProvider");
  }
  return context;
};

interface InferenceProviderProps {
  children: ReactNode;
}

export const InferenceProvider: React.FC<InferenceProviderProps> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(inferenceReducer, initialState);

  const createInference = async (request: InferenceRequest): Promise<void> => {
    try {
      dispatch({ type: "SET_LOADING", payload: true });
      dispatch({ type: "SET_REQUEST", payload: request });
      dispatch({ type: "CLEAR_ERROR" });

      const response = await apiClient.createInference(request);
      dispatch({ type: "SET_RESPONSE", payload: response });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const errorMessage = err.response?.data?.detail || "Inference failed";
      dispatch({ type: "SET_ERROR", payload: errorMessage });
    }
  };

  const createAsyncInference = async (
    request: InferenceRequest
  ): Promise<string> => {
    try {
      dispatch({ type: "SET_REQUEST", payload: request });
      dispatch({ type: "CLEAR_ERROR" });

      const { task_id } = await apiClient.createAsyncInference(request);
      dispatch({ type: "START_ASYNC_TASK", payload: { taskId: task_id } });

      return task_id;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const errorMessage =
        err.response?.data?.detail || "Async inference failed";
      dispatch({ type: "SET_ERROR", payload: errorMessage });
      throw error;
    }
  };

  const checkAsyncStatus = async (taskId: string): Promise<void> => {
    try {
      const status = await apiClient.getInferenceStatus(taskId);
      dispatch({
        type: "UPDATE_ASYNC_TASK",
        payload: {
          taskId,
          taskData: status,
        },
      });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      dispatch({
        type: "UPDATE_ASYNC_TASK",
        payload: {
          taskId,
          taskData: {
            status: "failed",
            error: err.response?.data?.detail || "Status check failed",
          },
        },
      });
    }
  };

  const loadModels = async (): Promise<void> => {
    try {
      const { models, default: defaultModel } =
        await apiClient.getAvailableModels();
      dispatch({
        type: "SET_MODELS",
        payload: { models, default: defaultModel },
      });
    } catch (error: unknown) {
      console.warn("Failed to load models:", error);
    }
  };

  const clearResponse = (): void => {
    dispatch({ type: "CLEAR_RESPONSE" });
  };

  const clearError = (): void => {
    dispatch({ type: "CLEAR_ERROR" });
  };

  const value: InferenceContextType = {
    ...state,
    createInference,
    createAsyncInference,
    checkAsyncStatus,
    loadModels,
    clearResponse,
    clearError,
  };

  return (
    <InferenceContext.Provider value={value}>
      {children}
    </InferenceContext.Provider>
  );
};
