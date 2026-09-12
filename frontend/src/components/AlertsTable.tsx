import { Badge, Card, Spinner, Table } from "react-bootstrap";

import type { AlertItem } from "../types/api";
import { formatDate, getLevelVariant } from "./displayHelpers";

type AlertsTableProps = {
  alerts: AlertItem[];
  isLoading: boolean;
};

export function AlertsTable({ alerts, isLoading }: AlertsTableProps) {
  const isInitialLoading = isLoading && alerts.length === 0;

  return (
    <Card className="shadow-sm border-0">
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center gap-3">
          <h2 className="h5 mb-0">Алерты</h2>
          <div className="d-flex align-items-center gap-2">
            {isLoading && !isInitialLoading ? (
              <span className="small text-secondary" role="status" aria-live="polite">
                Обновление...
              </span>
            ) : null}
            <Badge bg="secondary">{alerts.length}</Badge>
          </div>
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">
        {isInitialLoading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Загрузка алертов...</span>
            </Spinner>
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-4 text-secondary">Алертов пока нет</div>
        ) : (
          <div className="table-responsive">
            <Table hover bordered className="align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">File ID</th>
                  <th scope="col">Уровень</th>
                  <th scope="col">Сообщение</th>
                  <th scope="col">Создан</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td className="small">{item.file_id}</td>
                    <td>
                      <Badge bg={getLevelVariant(item.level)}>{item.level}</Badge>
                    </td>
                    <td>{item.message}</td>
                    <td>{formatDate(item.created_at)}</td>
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
