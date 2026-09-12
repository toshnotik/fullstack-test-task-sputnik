import type { FileItem, FileUpdatePayload } from "../types/api";
import { buildApiUrl, request } from "./client";

export function getFiles(): Promise<FileItem[]> {
  return request<FileItem[]>("/files", { cache: "no-store" }, "Не удалось загрузить данные");
}

export function uploadFile(title: string, file: File): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  return request<FileItem>(
    "/files",
    {
      method: "POST",
      body: formData,
    },
    "Не удалось загрузить файл",
  );
}

export function updateFile(fileId: string, payload: FileUpdatePayload): Promise<FileItem> {
  return request<FileItem>(
    `/files/${fileId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Не удалось обновить файл",
  );
}

export async function deleteFile(fileId: string): Promise<void> {
  const response = await fetch(buildApiUrl(`/files/${fileId}`), {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Не удалось удалить файл");
  }
}

export function getFileDownloadUrl(fileId: string): string {
  return buildApiUrl(`/files/${fileId}/download`);
}
