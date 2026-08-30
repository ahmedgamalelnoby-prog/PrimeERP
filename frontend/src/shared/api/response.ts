export interface ApiResponse<T> {
  data: T;
}

export interface ApiListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}