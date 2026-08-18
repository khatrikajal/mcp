/**
 * Reusable API hooks for data fetching and mutations.
 *
 * Provides:
 * - Loading state management
 * - Error handling
 * - Retry logic
 * - Caching (optional)
 */
import { useState, useCallback, useEffect, useRef } from "react";

/**
 * API hook state.
 */
interface ApiState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
}

/**
 * API hook options.
 */
interface UseApiOptions {
  /** Retry failed requests up to this many times */
  retries?: number;
  /** Delay between retries in ms */
  retryDelay?: number;
  /** Cache key for caching results */
  cacheKey?: string;
  /** Cache TTL in ms (default: 5 minutes) */
  cacheTtl?: number;
}

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();

/**
 * Hook for making API calls with loading/error state management.
 *
 * @param fetchFn - Async function that returns data
 * @param options - Configuration options
 * @returns State and control functions
 *
 * @example
 * const { data, error, isLoading, execute } = useApi(
 *   () => api.getAgents(),
 *   { cacheKey: 'agents' }
 * );
 */
export function useApi<T>(
  fetchFn: () => Promise<T>,
  options: UseApiOptions = {}
) {
  const { retries = 0, retryDelay = 1000, cacheKey, cacheTtl = 300000 } = options;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    isLoading: false,
  });

  // Track component mount status
  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const execute = useCallback(
    async (skipCache = false): Promise<T | null> => {
      // Check cache first
      if (!skipCache && cacheKey) {
        const cached = cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < cacheTtl) {
          const cachedData = cached.data as T;
          if (isMounted.current) {
            setState({ data: cachedData, error: null, isLoading: false });
          }
          return cachedData;
        }
      }

      if (isMounted.current) {
        setState((prev) => ({ ...prev, isLoading: true, error: null }));
      }

      let lastError: Error | null = null;
      let attempts = 0;

      while (attempts <= retries) {
        try {
          const data = await fetchFn();

          // Cache the result
          if (cacheKey) {
            cache.set(cacheKey, { data, timestamp: Date.now() });
          }

          if (isMounted.current) {
            setState({ data, error: null, isLoading: false });
          }

          return data;
        } catch (error) {
          lastError = error instanceof Error ? error : new Error(String(error));
          attempts++;

          if (attempts <= retries) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
          }
        }
      }

      const errorMessage = extractErrorMessage(lastError);
      if (isMounted.current) {
        setState({ data: null, error: errorMessage, isLoading: false });
      }

      return null;
    },
    [fetchFn, retries, retryDelay, cacheKey, cacheTtl]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, isLoading: false });
  }, []);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      cache.delete(cacheKey);
    }
  }, [cacheKey]);

  return {
    ...state,
    execute,
    reset,
    clearCache,
  };
}

/**
 * Hook for mutations (POST, PUT, DELETE) with optimistic updates.
 *
 * @param mutateFn - Async function that performs the mutation
 * @returns State and control functions
 *
 * @example
 * const { mutate, isLoading, error } = useMutation(
 *   (data) => api.createAgent(data)
 * );
 *
 * const handleSubmit = async () => {
 *   const result = await mutate({ name: 'New Agent' });
 *   if (result) {
 *     // Success
 *   }
 * };
 */
export function useMutation<TData, TResult>(
  mutateFn: (data: TData) => Promise<TResult>
) {
  const [state, setState] = useState<{
    isLoading: boolean;
    error: string | null;
    isSuccess: boolean;
  }>({
    isLoading: false,
    error: null,
    isSuccess: false,
  });

  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const mutate = useCallback(
    async (data: TData): Promise<TResult | null> => {
      if (isMounted.current) {
        setState({ isLoading: true, error: null, isSuccess: false });
      }

      try {
        const result = await mutateFn(data);

        if (isMounted.current) {
          setState({ isLoading: false, error: null, isSuccess: true });
        }

        return result;
      } catch (error) {
        const errorMessage = extractErrorMessage(error);

        if (isMounted.current) {
          setState({ isLoading: false, error: errorMessage, isSuccess: false });
        }

        return null;
      }
    },
    [mutateFn]
  );

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, isSuccess: false });
  }, []);

  return {
    ...state,
    mutate,
    reset,
  };
}

/**
 * Hook for lazy data loading (load on demand).
 *
 * @param fetchFn - Async function that returns data
 * @returns State and control functions
 */
export function useLazyApi<T>(fetchFn: () => Promise<T>) {
  const { data, error, isLoading, execute, reset } = useApi(fetchFn);
  const [hasLoaded, setHasLoaded] = useState(false);

  const load = useCallback(async () => {
    setHasLoaded(true);
    return execute();
  }, [execute]);

  return {
    data,
    error,
    isLoading,
    hasLoaded,
    load,
    reset,
  };
}

/**
 * Extract error message from various error types.
 */
function extractErrorMessage(error: unknown): string {
  if (!error) {
    return "An unknown error occurred";
  }

  // Axios error
  if (typeof error === "object" && error !== null) {
    const axiosError = error as {
      response?: { data?: { detail?: string } };
      message?: string;
    };

    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }

    if (axiosError.message) {
      return axiosError.message;
    }
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message;
  }

  // String error
  if (typeof error === "string") {
    return error;
  }

  return "An unknown error occurred";
}

/**
 * Clear all cached data.
 */
export function clearAllCache(): void {
  cache.clear();
}

/**
 * Prefetch data and cache it.
 *
 * @param fetchFn - Async function that returns data
 * @param cacheKey - Key for caching
 */
export async function prefetch<T>(
  fetchFn: () => Promise<T>,
  cacheKey: string
): Promise<void> {
  try {
    const data = await fetchFn();
    cache.set(cacheKey, { data, timestamp: Date.now() });
  } catch {
    // Silently fail prefetch
  }
}
