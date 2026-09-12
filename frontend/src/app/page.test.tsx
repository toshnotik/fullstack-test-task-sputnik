import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { getAlerts } from "../api/alerts";
import { getFiles, uploadFile } from "../api/files";
import type { AlertItem, FileItem } from "../types/api";
import Page from "./page";

jest.mock("../api/alerts", () => ({
  getAlerts: jest.fn(),
}));

jest.mock("../api/files", () => ({
  getFileDownloadUrl: (fileId: string) => `http://localhost:8000/files/${fileId}/download`,
  getFiles: jest.fn(),
  uploadFile: jest.fn(),
}));

const mockedGetFiles = jest.mocked(getFiles);
const mockedGetAlerts = jest.mocked(getAlerts);
const mockedUploadFile = jest.mocked(uploadFile);

const file: FileItem = {
  id: "file-1",
  title: "Contract",
  original_name: "contract.pdf",
  mime_type: "application/pdf",
  size: 1024,
  processing_status: "processed",
  scan_status: "clean",
  scan_details: "No threats found",
  metadata_json: null,
  requires_attention: false,
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:00:00Z",
};

const alert: AlertItem = {
  id: 1,
  file_id: "file-1",
  level: "info",
  message: "Metadata extracted",
  created_at: "2026-01-01T10:00:00Z",
};

describe("Page", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("loads files and alerts on initial render", async () => {
    mockedGetFiles.mockResolvedValue([file]);
    mockedGetAlerts.mockResolvedValue([alert]);

    render(<Page />);

    expect(await screen.findByText("Contract")).toBeInTheDocument();
    expect(screen.getByText("Metadata extracted")).toBeInTheDocument();
  });

  it("refreshes data after successful upload", async () => {
    const user = userEvent.setup();
    const uploadedFile = new File(["content"], "report.txt", { type: "text/plain" });

    mockedGetFiles.mockResolvedValueOnce([]).mockResolvedValueOnce([file]);
    mockedGetAlerts.mockResolvedValueOnce([]).mockResolvedValueOnce([alert]);
    mockedUploadFile.mockResolvedValue(file);

    render(<Page />);

    await screen.findByText("Файлы пока не загружены");
    await user.click(screen.getByRole("button", { name: "Добавить файл" }));
    await user.type(screen.getByLabelText("Название"), "Contract");
    await user.upload(screen.getByLabelText("Файл"), uploadedFile);
    const submitButton = screen.getByRole("button", { name: "Сохранить" });
    const form = submitButton.closest("form");

    if (!form) {
      throw new Error("Submit button is not inside a form");
    }

    fireEvent.submit(form);

    await waitFor(() => expect(mockedUploadFile).toHaveBeenCalledWith("Contract", uploadedFile));
    expect(await screen.findByText("Contract")).toBeInTheDocument();
    expect(screen.getByText("Metadata extracted")).toBeInTheDocument();
    expect(mockedGetFiles).toHaveBeenCalledTimes(2);
    expect(mockedGetAlerts).toHaveBeenCalledTimes(2);
  });

  it("shows API error alert", async () => {
    mockedGetFiles.mockRejectedValue(new Error("Не удалось загрузить данные"));
    mockedGetAlerts.mockResolvedValue([]);

    render(<Page />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Не удалось загрузить данные");
  });
});
