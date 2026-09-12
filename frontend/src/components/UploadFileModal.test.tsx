import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { FormEvent } from "react";

import { UploadFileModal } from "./UploadFileModal";

type Props = Parameters<typeof UploadFileModal>[0];

function renderModal(overrides: Partial<Props> = {}) {
  const props: Props = {
    show: true,
    title: "",
    isSubmitting: false,
    onHide: jest.fn(),
    onSubmit: jest.fn((event: FormEvent<HTMLFormElement>) => event.preventDefault()),
    onTitleChange: jest.fn(),
    onFileChange: jest.fn(),
    ...overrides,
  };

  render(<UploadFileModal {...props} />);

  return props;
}

describe("UploadFileModal", () => {
  it("exposes title and file inputs by label", () => {
    renderModal();

    expect(screen.getByLabelText("Название")).toBeInTheDocument();
    expect(screen.getByLabelText("Файл")).toBeInTheDocument();
  });

  it("calls callbacks when title and file change", async () => {
    const user = userEvent.setup();
    const props = renderModal();
    const file = new File(["content"], "report.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("Название"), { target: { value: "Report" } });
    await user.upload(screen.getByLabelText("Файл"), file);

    expect(props.onTitleChange).toHaveBeenCalledWith("Report");
    expect(props.onFileChange).toHaveBeenCalledWith(file);
  });

  it("submits the form", async () => {
    const user = userEvent.setup();
    const props = renderModal({ title: "Report" });
    const file = new File(["content"], "report.txt", { type: "text/plain" });

    await user.upload(screen.getByLabelText("Файл"), file);
    const submitButton = screen.getByRole("button", { name: "Сохранить" });
    const form = submitButton.closest("form");

    if (!form) {
      throw new Error("Submit button is not inside a form");
    }

    fireEvent.submit(form);

    expect(props.onSubmit).toHaveBeenCalledTimes(1);
  });

  it("disables controls and shows submitting label", () => {
    renderModal({ isSubmitting: true });

    expect(screen.getByLabelText("Название")).toBeDisabled();
    expect(screen.getByLabelText("Файл")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Отмена" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Добавление..." })).toBeDisabled();
  });
});
