export function hasApiError(payload) {
  return Boolean(payload?.error);
}

export function getApiErrorMessage(payload, fallback = "Request failed") {
  const error = payload?.error;

  if (typeof error === "string" && error.trim()) {
    return error;
  }

  if (error && typeof error === "object") {
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }

    if (typeof error.code === "string" && error.code.trim()) {
      return error.code;
    }
  }

  if (typeof payload?.message === "string" && payload.message.trim()) {
    return payload.message;
  }

  // Backward-compatible fallback for older response shapes still in use.
  if (typeof payload?.data?.error === "string" && payload.data.error.trim()) {
    return payload.data.error;
  }

  return fallback;
}
