// Pre-hook: Environment check
// ALL NETWORK ACTIVITY DISABLED - Projects closed for server activity
const useStreaming = false; // Hardcoded disabled
const serverActivityDisabled = true; // Hardcoded disabled

interface NavigationRequest {
    goal: string;
    context?: any;
    [key: string]: any;
}

// Mock functions for context
declare const updateProgressBar: (progress: number) => void;
declare const commitNavigationResult: (result: any) => void;
declare const fallbackToLegacyAPI: (request: NavigationRequest) => void;
declare const logEvent: (event: string) => void;

// Streaming client implementation - DISABLED
export const streamNavigationPlan = (request: NavigationRequest) => {
    // All network activity disabled - projects closed for server activity
    console.warn('[DISABLED] All streaming and fetch requests are disabled until further notice');
    return;
};
