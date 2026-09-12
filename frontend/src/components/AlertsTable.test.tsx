import { render, screen } from "@testing-library/react";

import type { AlertItem } from "../types/api";
import { AlertsTable } from "./AlertsTable";

const alerts: AlertItem[] = [
  {
    id: 1,
    file_id: "file-1",
    level: "info",
    message: "Metadata extracted",
    created_at: "2026-01-01T10:00:00Z",
  },
  {
    id: 2,
    file_id: "file-2",
    level: "warning",
    message: "Suspicious file",
    created_at: "2026-01-01T11:00:00Z",
  },
  {
    id: 3,
    file_id: "file-3",
    level: "critical",
    message: "Threat detected",
    created_at: "2026-01-01T12:00:00Z",
  },
];

describe("AlertsTable", () => {
  it("shows initial loading state", () => {
    render(<AlertsTable alerts={[]} isLoading />);

    expect(screen.getByRole("status")).toHaveTextContent("Загрузка алертов...");
  });

  it("shows empty state", () => {
    render(<AlertsTable alerts={[]} isLoading={false} />);

    expect(screen.getByText("Алертов пока нет")).toBeInTheDocument();
  });

  it("renders alert rows and text levels", () => {
    render(<AlertsTable alerts={alerts} isLoading={false} />);

    expect(screen.getByText("Metadata extracted")).toBeInTheDocument();
    expect(screen.getByText("Suspicious file")).toBeInTheDocument();
    expect(screen.getByText("Threat detected")).toBeInTheDocument();
    expect(screen.getByText("info")).toBeInTheDocument();
    expect(screen.getByText("warning")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
  });
});
