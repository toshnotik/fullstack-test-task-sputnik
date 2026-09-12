import type { AlertItem } from "../types/api";
import { request } from "./client";

export function getAlerts(): Promise<AlertItem[]> {
  return request<AlertItem[]>("/alerts", { cache: "no-store" }, "Не удалось загрузить данные");
}
