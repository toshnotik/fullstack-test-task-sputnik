import type { ChangeEvent, FormEvent } from "react";
import { Button, Form, Modal } from "react-bootstrap";

type UploadFileModalProps = {
  show: boolean;
  title: string;
  isSubmitting: boolean;
  onHide: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTitleChange: (title: string) => void;
  onFileChange: (file: File | null) => void;
};

export function UploadFileModal({
  show,
  title,
  isSubmitting,
  onHide,
  onSubmit,
  onTitleChange,
  onFileChange,
}: UploadFileModalProps) {
  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    onFileChange(event.target.files?.[0] ?? null);
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={onSubmit}>
        <Modal.Header closeButton>
          <Modal.Title>Добавить файл</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Название</Form.Label>
            <Form.Control
              value={title}
              onChange={(event) => onTitleChange(event.target.value)}
              placeholder="Например, Договор с подрядчиком"
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Файл</Form.Label>
            <Form.Control type="file" onChange={handleFileChange} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>
            Отмена
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? "Загрузка..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
