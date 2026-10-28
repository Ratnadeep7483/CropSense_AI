/**
 * CropSense AI — API Client
 *
 * Base HTTP client configured with the backend URL from environment.
 * All API modules import from this file to avoid scattered fetch() calls.
 */

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/** Default request timeout in milliseconds. */
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Standard error shape returned by CropSense AI backend on failure.
 */
export interface ApiError {
  success: false;
  error: string;
  detail?: string;
}

export class ApiHttpError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiHttpError";
  }
}

function getApiErrorMessage(raw: unknown, status: number): string {
  if (typeof raw === "object" && raw !== null) {
    const body = raw as {
      detail?: unknown;
      error?: unknown;
    };
    const detail = body.detail;
    if (Array.isArray(detail)) {
      const validationMessages = detail.flatMap((item) => {
        if (typeof item !== "object" || item === null) return [];
        const error = item as { loc?: unknown; msg?: unknown };
        if (typeof error.msg !== "string") return [];
        const location = Array.isArray(error.loc)
          ? error.loc
              .filter((part): part is string | number =>
                typeof part === "string" || typeof part === "number",
              )
              .slice(1)
              .join(".")
          : "";
        return [location ? `${location}: ${error.msg}` : error.msg];
      });
      if (validationMessages.length > 0) return validationMessages.join("; ");
    }
    if (typeof detail === "object" && detail !== null && "error" in detail) {
      const message = (detail as { error?: unknown }).error;
      if (typeof message === "string" && message) return message;
    }
    if (typeof detail === "string" && detail) return detail;
    if (typeof body.error === "string" && body.error) return body.error;
  }

  return `Server error (${status}). Please try again later.`;
}

/**
 * Perform a JSON request to the backend.
 *
 * @param path   – Relative path (e.g. "/api/crop/recommend")
 * @param options – Standard RequestInit overrides
 * @returns Parsed JSON response body
 * @throws Error with a user-friendly message on network/server failure
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    DEFAULT_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let raw: unknown = null;
      try {
        raw = await response.json();
      } catch {
        // Response body wasn't JSON — fall through
      }
      throw new ApiHttpError(
        getApiErrorMessage(raw, response.status),
        response.status,
      );
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again.",
      );
    }

    if (err instanceof TypeError && err.message === "Failed to fetch") {
      throw new Error(
        "Unable to connect to the CropSense AI prediction service. " +
          "Please make sure the backend is running.",
      );
    }

    // Re-throw if it's already our formatted error
    throw err;
  }
}

/** Perform a multipart request without overriding the browser's content type. */
export async function apiFetchFormData<T>(
  path: string,
  body: FormData,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    DEFAULT_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      body,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let raw: unknown;
      try {
        raw = await response.json();
      } catch {
        raw = null;
      }
      throw new ApiHttpError(
        getApiErrorMessage(raw, response.status),
        response.status,
      );
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again.",
      );
    }
    if (err instanceof TypeError && err.message === "Failed to fetch") {
      throw new Error(
        "Unable to connect to the CropSense AI prediction service. " +
          "Please make sure the backend is running.",
      );
    }
    throw err;
  }
}
