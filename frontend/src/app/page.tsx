"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Row } from "react-bootstrap";

import { getAlerts } from "../api/alerts";
import { getFileDownloadUrl, getFiles, uploadFile } from "../api/files";
import { AlertsTable } from "../components/AlertsTable";
import { FilesTable } from "../components/FilesTable";
import { UploadFileModal } from "../components/UploadFileModal";
import type { AlertItem, FileItem } from "../types/api";

export default function Page() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadData(): Promise<void> {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [filesData, alertsData] = await Promise.all([getFiles(), getAlerts()]);

      setFiles(filesData);
      setAlerts(alertsData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Произошла ошибка");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!title.trim() || !selectedFile) {
      setErrorMessage("Укажите название и выберите файл");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await uploadFile(title.trim(), selectedFile);
      setShowModal(false);
      setTitle("");
      setSelectedFile(null);
      await loadData();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Произошла ошибка");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <Card className="shadow-sm border-0 mb-4">
            <Card.Body className="p-4">
              <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                  <h1 className="h3 mb-2">Управление файлами</h1>
                  <p className="text-secondary mb-0">
                    Загрузка файлов, просмотр статусов обработки и ленты алертов.
                  </p>
                </div>
                <div className="d-flex gap-2">
                  <Button variant="outline-secondary" onClick={() => void loadData()}>
                    Обновить
                  </Button>
                  <Button variant="primary" onClick={() => setShowModal(true)}>
                    Добавить файл
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>

          {errorMessage ? (
            <Alert variant="danger" className="shadow-sm">
              {errorMessage}
            </Alert>
          ) : null}

          <FilesTable files={files} isLoading={isLoading} getDownloadUrl={getFileDownloadUrl} />
          <AlertsTable alerts={alerts} isLoading={isLoading} />
        </Col>
      </Row>

      <UploadFileModal
        show={showModal}
        title={title}
        isSubmitting={isSubmitting}
        onHide={() => setShowModal(false)}
        onSubmit={handleSubmit}
        onTitleChange={setTitle}
        onFileChange={setSelectedFile}
      />
    </Container>
  );
}
