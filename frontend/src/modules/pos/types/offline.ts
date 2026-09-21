export type PosConnectivity = "online" | "offline";

export type OfflineOrderView = {
  id: string;
  number: string;
  total?: number | string;
  status: "offline-pending" | "offline-failed";
  createdAt: string;
};
