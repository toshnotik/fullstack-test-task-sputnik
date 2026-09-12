import { render, screen } from "@testing-library/react";

import type { FileItem } from "../types/api";
import { FilesTable } from "./FilesTable";

const file: FileItem = {
  id: "file-1",
  title: "Contract",
  original_name: "contract.pdf",
  mime_type: "application/pdf",
  size: 2048,
  processing_status: "processed",
  scan_status: "clean",
  scan_details: "No threats found",
  metadata_json: null,
  requires_attention: false,
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:00:00Z",
};

describe("FilesTable", () => {
  it("shows initial loading state", () => {
    render(<FilesTable files={[]} isLoading getDownloadUrl={(fileId) => `/download/${fileId}`} />);

    expect(screen.getByRole("status")).toHaveTextContent("Загрузка файлов...");
  });

  it("shows empty state", () => {
    render(<FilesTable files={[]} isLoading={false} getDownloadUrl={(fileId) => `/download/${fileId}`} />);

    expect(screen.getByText("Файлы пока не загружены")).toBeInTheDocument();
  });

  it("renders files and uses provided download URL", () => {
    render(<FilesTable files={[file]} isLoading={false} getDownloadUrl={(fileId) => `/download/${fileId}`} />);

    expect(screen.getByText("Contract")).toBeInTheDocument();
    expect(screen.getByText("contract.pdf")).toBeInTheDocument();
    expect(screen.getByText("processed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Скачать" })).toHaveAttribute("href", "/download/file-1");
  });
});
