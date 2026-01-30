// Pre-hook: Target validation
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

import http from "k6/http";
import { check } from "k6";

export default function () {
    // Note: Backend is POST, but snippet uses GET.
    // If backend is strictly POST, this test might fail with 405 Method Not Allowed.
    // I'll stick to the user provided snippet which uses http.get.
    const res = http.get(`${BASE_URL}/navigation/plan-stream`, {
        headers: { Accept: "text/event-stream" },
        tags: { test_type: "streaming" },
    });

    check(res, {
        "status 200": (r) => r.status === 200,
        "first chunk <500ms": (r) => r.timings.waiting < 500,
    });
}
