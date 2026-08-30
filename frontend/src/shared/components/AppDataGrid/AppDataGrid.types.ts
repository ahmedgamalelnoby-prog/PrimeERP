import type {
  ColumnDef,
  Row,
  Table,
} from "@tanstack/react-table";
import type { ReactNode } from "react";

export interface AppDataGridBulkAction<TData> {
  label: string;
  icon?: ReactNode;
  destructive?: boolean;
  disabled?: boolean;

  onClick: (
    selectedRows: TData[],
  ) => void | Promise<void>;
}

export interface AppDataGridProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];

  loading?: boolean;

  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: ReactNode;

  searchValue?: string;
  searchPlaceholder?: string;
  onSearchChange?: (value: string) => void;

  initialPageSize?: number;
  pageSizeOptions?: number[];

  enableSorting?: boolean;
  enableRowSelection?: boolean;
  enableColumnVisibility?: boolean;

  bulkActions?: AppDataGridBulkAction<TData>[];

  toolbarStart?: ReactNode;
  toolbarEnd?: ReactNode;

  getRowId?: (
    originalRow: TData,
    index: number,
  ) => string;

  onRowClick?: (row: Row<TData>) => void;

  rowClassName?: (
    row: Row<TData>,
  ) => string;

  renderMobileRow?: (
    row: Row<TData>,
    table: Table<TData>,
  ) => ReactNode;
}