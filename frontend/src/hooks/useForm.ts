/**
 * Form handling hook with validation.
 *
 * Provides:
 * - Form state management
 * - Field validation
 * - Error handling
 * - Dirty state tracking
 */
import { useState, useCallback, type ChangeEvent, type FormEvent } from "react";

/**
 * Validation rule type.
 */
type ValidationRule<T> = {
  validate: (value: T, formData: Record<string, unknown>) => boolean;
  message: string;
};

/**
 * Field configuration.
 */
interface FieldConfig<T> {
  initialValue: T;
  rules?: ValidationRule<T>[];
}

/**
 * Form configuration.
 */
type FormConfig<T extends Record<string, unknown>> = {
  [K in keyof T]: FieldConfig<T[K]>;
};


/**
 * Hook for form handling with validation.
 *
 * @param config - Form configuration
 * @param onSubmit - Submit handler
 * @returns Form state and handlers
 *
 * @example
 * const { values, errors, handleChange, handleSubmit } = useForm(
 *   {
 *     email: {
 *       initialValue: '',
 *       rules: [
 *         { validate: (v) => v.length > 0, message: 'Email is required' },
 *         { validate: (v) => isValidEmail(v), message: 'Invalid email' }
 *       ]
 *     },
 *     password: {
 *       initialValue: '',
 *       rules: [
 *         { validate: (v) => v.length >= 8, message: 'Min 8 characters' }
 *       ]
 *     }
 *   },
 *   async (data) => {
 *     await api.login(data);
 *   }
 * );
 */
export function useForm<T extends Record<string, unknown>>(
  config: FormConfig<T>,
  onSubmit?: (values: T) => Promise<void> | void
) {
  // Initialize values from config
  const initialValues = Object.fromEntries(
    Object.entries(config).map(([key, fieldConfig]) => [
      key,
      (fieldConfig as FieldConfig<unknown>).initialValue,
    ])
  ) as T;

  const initialErrors = Object.fromEntries(
    Object.keys(config).map((key) => [key, null])
  ) as Record<keyof T, string | null>;

  const initialTouched = Object.fromEntries(
    Object.keys(config).map((key) => [key, false])
  ) as Record<keyof T, boolean>;

  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState(initialErrors);
  const [touched, setTouched] = useState(initialTouched);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  /**
   * Validate a single field.
   */
  const validateField = useCallback(
    (name: keyof T, value: unknown): string | null => {
      const fieldConfig = config[name] as FieldConfig<unknown>;
      const rules = fieldConfig.rules || [];

      for (const rule of rules) {
        if (!rule.validate(value, values as Record<string, unknown>)) {
          return rule.message;
        }
      }

      return null;
    },
    [config, values]
  );

  /**
   * Validate all fields.
   */
  const validateAll = useCallback((): boolean => {
    const newErrors: Record<string, string | null> = {};
    let isValid = true;

    for (const [name] of Object.entries(config)) {
      const error = validateField(name as keyof T, values[name as keyof T]);
      newErrors[name] = error;
      if (error) {
        isValid = false;
      }
    }

    setErrors(newErrors as Record<keyof T, string | null>);
    return isValid;
  }, [config, values, validateField]);

  /**
   * Handle input change.
   */
  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value, type } = e.target;
      const newValue =
        type === "checkbox" ? (e.target as HTMLInputElement).checked : value;

      setValues((prev) => ({
        ...prev,
        [name]: newValue,
      }));

      // Validate field on change if touched
      if (touched[name as keyof T]) {
        const error = validateField(name as keyof T, newValue);
        setErrors((prev) => ({
          ...prev,
          [name]: error,
        }));
      }
    },
    [touched, validateField]
  );

  /**
   * Handle field blur.
   */
  const handleBlur = useCallback(
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value } = e.target;

      setTouched((prev) => ({
        ...prev,
        [name]: true,
      }));

      const error = validateField(name as keyof T, value);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    },
    [validateField]
  );

  /**
   * Set a field value programmatically.
   */
  const setValue = useCallback(
    (name: keyof T, value: T[keyof T]) => {
      setValues((prev) => ({
        ...prev,
        [name]: value,
      }));
    },
    []
  );

  /**
   * Set a field error programmatically.
   */
  const setError = useCallback((name: keyof T, error: string | null) => {
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  }, []);

  /**
   * Handle form submission.
   */
  const handleSubmit = useCallback(
    async (e?: FormEvent) => {
      if (e) {
        e.preventDefault();
      }

      // Mark all fields as touched
      setTouched(
        Object.fromEntries(
          Object.keys(config).map((key) => [key, true])
        ) as Record<keyof T, boolean>
      );

      // Validate all fields
      if (!validateAll()) {
        return;
      }

      if (!onSubmit) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError(null);

      try {
        await onSubmit(values);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "An error occurred";
        setSubmitError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [config, validateAll, onSubmit, values]
  );

  /**
   * Reset form to initial values.
   */
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors(initialErrors);
    setTouched(initialTouched);
    setIsSubmitting(false);
    setSubmitError(null);
  }, [initialValues, initialErrors, initialTouched]);

  // Calculate derived state
  const isDirty = Object.keys(values).some(
    (key) => values[key as keyof T] !== initialValues[key as keyof T]
  );

  const isValid = Object.values(errors).every((error) => error === null);

  return {
    values,
    errors,
    touched,
    isValid,
    isDirty,
    isSubmitting,
    submitError,
    handleChange,
    handleBlur,
    handleSubmit,
    setValue,
    setError,
    reset,
    validateAll,
    validateField,
  };
}

/**
 * Common validation rules factory.
 */
export const rules = {
  required: (message = "This field is required"): ValidationRule<string> => ({
    validate: (value) => value.trim().length > 0,
    message,
  }),

  minLength: (
    min: number,
    message?: string
  ): ValidationRule<string> => ({
    validate: (value) => value.length >= min,
    message: message || `Must be at least ${min} characters`,
  }),

  maxLength: (
    max: number,
    message?: string
  ): ValidationRule<string> => ({
    validate: (value) => value.length <= max,
    message: message || `Must be less than ${max} characters`,
  }),

  email: (message = "Invalid email address"): ValidationRule<string> => ({
    validate: (value) =>
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value),
    message,
  }),

  pattern: (
    regex: RegExp,
    message = "Invalid format"
  ): ValidationRule<string> => ({
    validate: (value) => regex.test(value),
    message,
  }),

  match: (
    fieldName: string,
    message = "Fields do not match"
  ): ValidationRule<string> => ({
    validate: (value, formData) => value === formData[fieldName],
    message,
  }),

  password: (message?: string): ValidationRule<string> => ({
    validate: (value) =>
      value.length >= 8 &&
      /[A-Z]/.test(value) &&
      /[a-z]/.test(value) &&
      /\d/.test(value),
    message:
      message ||
      "Password must be 8+ characters with uppercase, lowercase, and number",
  }),
};
