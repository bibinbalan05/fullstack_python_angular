export interface FilterValue {
  id: number | string; // The ID used by the API (or name if ID missing)
  name: string;        // The display name
  brand_fk?: number; // The brand ID on product lines
}

export interface FrontendFilter {
  name: string;        // e.g., 'Product category', 'Brand'
  values: FilterValue[]; // Array of options like {id: 1, name: 'Electronics'}
  isExpanded: boolean; // UI state - will be added by the service or component
}