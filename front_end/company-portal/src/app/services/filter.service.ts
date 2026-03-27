import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable, of } from "rxjs";
import { catchError, map } from "rxjs/operators";
import { HttpService } from "./http.service";
import { FrontendFilter } from "../models/filter.model";
import { HttpClient } from "@angular/common/http";

// Define the structure for a selected filter value, including its ID
export interface SelectedFilterValue {
  id: number | string;
  name: string;
}

// Define the structure for selected filters, mapping filter name to an array of selected values
export interface SelectedFilters {
  [filterName: string]: SelectedFilterValue[];
}

@Injectable({
  providedIn: "root",
})
export class FilterService extends HttpService {
  /**
   * Use BehaviorSubject to store and emit the current filter state
   * Initialize with an empty object
   */
  private selectedFiltersSubject = new BehaviorSubject<SelectedFilters>({});

  selectedFilters$ = this.selectedFiltersSubject.asObservable();

  constructor(http: HttpClient) {
    super(http);
  }

  /**
   * Method to update the selected filters
   */
  updateSelectedFilters(newFilters: SelectedFilters): void {
    this.selectedFiltersSubject.next(newFilters);
  }

  /**
   * Method to get the current value of the filters synchronously
   */
  getCurrentFilters(): SelectedFilters {
    return this.selectedFiltersSubject.getValue();
  }

  /**
   * Helper to clear all filters
   */
  clearFilters(): void {
    this.selectedFiltersSubject.next({});
  }

  /**
   * Observable that emits true if any filter category has at least one selected value,
   * false otherwise.
   */
  public get hasActiveFilters$(): Observable<boolean> {
    return this.selectedFilters$.pipe(
      map((currentFilters) => {
        return Object.values(currentFilters).some(
          (filterValues) => filterValues.length > 0,
        );
      }),
    );
  }

  /**
   * Synchronously checks if any filter category has at least one selected value.
   */
  public hasActiveFilters(): boolean {
    const currentFilters = this.getCurrentFilters();
    return Object.values(currentFilters).some(
      (filterValues) => filterValues.length > 0,
    );
  }

  getFilters(): Observable<FrontendFilter[]> {
    return this.get<FrontendFilter[]>(`/models/all-filters/`).pipe(
      map((filters) => {
        return filters.map((f) => ({
          ...f,
          isExpanded: false,
        }));
      }),
      catchError((error) => {
        console.error("Error loading filters:", error);
        return of([]);
      }),
    );
  }
}
