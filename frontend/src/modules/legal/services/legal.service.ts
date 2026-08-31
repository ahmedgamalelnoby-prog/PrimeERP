import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";

export type LegalDocumentType = "terms" | "privacy";

export interface LegalDocument {
  id: number;
  document_type: LegalDocumentType;
  title_ar: string;
  title_en: string;
  content_ar: string;
  content_en: string;
  version: number;
  is_published: boolean;
  published_at: string | null;
  updated_at: string | null;
}

function authConfig() {
  const token = storage.getAccessToken();
  return {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  };
}

export async function getLegalDocument(type: LegalDocumentType) {
  const response = await client.get<{ success: boolean; data: LegalDocument }>(`/legal/${type}`);
  return response.data.data;
}

export async function updateLegalDocument(
  type: LegalDocumentType,
  payload: Pick<LegalDocument, "title_ar" | "title_en" | "content_ar" | "content_en" | "is_published">,
) {
  const response = await client.put<{ success: boolean; data: LegalDocument }>(
    `/legal/${type}`,
    payload,
    authConfig(),
  );
  return response.data.data;
}

export async function acceptLegalDocument(type: LegalDocumentType, version: number) {
  await client.post(
    "/legal/accept",
    { document_type: type, version },
    authConfig(),
  );
}

export const legalService = {
  getLegalDocument,
  updateLegalDocument,
  acceptLegalDocument,
};
