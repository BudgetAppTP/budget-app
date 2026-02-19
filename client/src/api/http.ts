import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "/api";

export const http = axios.create({
  baseURL,
  withCredentials: true
});

export type ApiResponse<T> = {
  data: T | null;
  error: { code: string; message: string } | null;
};

export async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const r = await p;
  if (r.data.error) {
    throw new Error(`${r.data.error.code}: ${r.data.error.message}`);
  }
  if (r.data.data === null) {
    throw new Error("Empty data");
  }
  return r.data.data;
}
