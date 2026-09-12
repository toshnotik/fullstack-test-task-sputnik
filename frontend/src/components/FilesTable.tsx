import { Badge, Button, Card, Spinner, Table } from "react-bootstrap";

import type { FileItem } from "../types/api";
import { formatDate, formatSize, getProcessingVariant } from "./displayHelpers";

type FilesTableProps = {
  files: FileItem[];
  isLoading: boolean;
  getDownloadUrl: (fileId: string) => string;
};

export function FilesTable({ files, isLoading, getDownloadUrl }: FilesTableProps) {
  const isInitialLoading = isLoading && files.length === 0;

  return (
    <Card className="shadow-sm border-0 mb-4">
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center gap-3">
          <h2 className="h5 mb-0">Файлы</h2>
          <div className="d-flex align-items-center gap-2">
            {isLoading && !isInitialLoading ? (
              <span className="small text-secondary" role="status" aria-live="polite">
                Обновление...
              </span>
            ) : null}
            <Badge bg="secondary">{files.length}</Badge>
          </div>
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">
        {isInitialLoading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Загрузка файлов...</span>
            </Spinner>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-4 text-secondary">Файлы пока не загружены</div>
        ) : (
          <div className="table-responsive">
            <Table hover bordered className="align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th scope="col">Название</th>
                  <th scope="col">Файл</th>
                  <th scope="col">MIME</th>
                  <th scope="col">Размер</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Проверка</th>
                  <th scope="col">Создан</th>
                  <th scope="col"></th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.id}>
                    <td>
                      <div className="fw-semibold">{file.title}</div>
                      <div className="small text-secondary">{file.id}</div>
                    </td>
                    <td>{file.original_name}</td>
                    <td>{file.mime_type}</td>
                    <td>{formatSize(file.size)}</td>
                    <td>
                      <Badge bg={getProcessingVariant(file.processing_status)}>{file.processing_status}</Badge>
                    </td>
                    <td>
                      <div className="d-flex flex-column gap-1">
                        <Badge bg={file.requires_attention ? "warning" : "success"}>
                          {file.scan_status ?? "pending"}
                        </Badge>
                        <span className="small text-secondary">{file.scan_details ?? "Ожидает обработки"}</span>
                      </div>
                    </td>
                    <td>{formatDate(file.created_at)}</td>
                    <td className="text-nowrap">
                      <Button
                        as="a"
                        href={getDownloadUrl(file.id)}
                        variant="outline-primary"
                        size="sm"
                      >
                        Скачать
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </Card.Body>
    </Card>
  );
}
