/**
 * Thin typed wrapper around the API. Real endpoints are added per milestone.
 */
const baseUrl = import.meta.env["VITE_API_BASE_URL"] ?? "/api";

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${baseUrl}/healthz`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return (await response.json()) as { status: string };
}
