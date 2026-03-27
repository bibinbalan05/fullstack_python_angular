import { Component, OnDestroy, OnInit } from "@angular/core";
import { NavigationEnd, Router, RouterLink } from "@angular/router";
import { CommonModule } from "@angular/common";
import { UserService } from "../services/user.service";
import { AuthService } from "../services/auth.service";
import {
  FilterService,
  SelectedFilters,
} from "../services/filter.service";
import { FrontendFilter, FilterValue } from "../models/filter.model";
import {
  filter,
  firstValueFrom,
  Subject,
  takeUntil,
  debounceTime,
  distinctUntilChanged,
} from "rxjs";
import { FormsModule } from "@angular/forms"; // Import FormsModule

import { NgIcon, provideIcons } from "@ng-icons/core";
import {
  matKeyboardDoubleArrowLeftRound,
  matKeyboardDoubleArrowRightRound,
  matHomeRound,
  matFilterAltRound,
  matAccountCircleRound,
  matClearRound,
} from "@ng-icons/material-icons/round";
import { LoginResponse } from "../models/user";

@Component({
  selector: "app-side-menu",
  standalone: true,
  imports: [RouterLink, CommonModule, FormsModule, NgIcon], // Add FormsModule
  templateUrl: "./side-menu.component.html",
  providers: [
    provideIcons({
      matKeyboardDoubleArrowLeftRound,
      matKeyboardDoubleArrowRightRound,
      matHomeRound,
      matFilterAltRound,
      matAccountCircleRound,
      matClearRound,
    }),
  ],
})
export class SideMenuComponent implements OnInit, OnDestroy {
  readonly BRAND_FILTER_NAME = "Brand";
  readonly PRODUCT_LINE_FILTER_NAME = "Product line";
  readonly MY_PRODUCTS_FILTER_NAME = "My Products";
  readonly SCORE_FILTER_NAME = "Score";

  currentUser: LoginResponse | null;
  filters: FrontendFilter[] = [];
  isMenuVisible: boolean = true;
  isFilterExpanded = false;
  selectedValues: SelectedFilters = {};
  lengths: { [key: string]: number } = {};
  totalSelectedValuesLength: number = 0;
  currentUrl: string = "";

  // Score range properties
  readonly minScoreValue: number = 0;
  readonly maxScoreValue: number = 10;
  scoreMinValue: number = this.minScoreValue;
  scoreMaxValue: number = this.maxScoreValue;
  scoreFilterTicks: number[] = Array.from({ length: 11 }, (_, i) => i); // Ticks 0-10

  private destroy$ = new Subject<void>();
  private scoreUpdateSubject = new Subject<{ min: number; max: number }>(); // Subject for debouncing slider updates

  constructor(
    private filterService: FilterService,
    private authService: AuthService,
    private userService: UserService,
    private router: Router,
  ) {
    this.currentUser = this.userService.getCurrentUser();
  }

  ngOnInit() {
    this.getFilters();

    this.filterService.selectedFilters$
      .pipe(takeUntil(this.destroy$))
      .subscribe((selected) => {
        this.selectedValues = selected;

        // Update score sliders based on service state
        const scoreFilter = selected[this.SCORE_FILTER_NAME];
        let serviceMin = this.minScoreValue;
        let serviceMax = this.maxScoreValue;

        if (
          scoreFilter &&
          scoreFilter.length === 2 &&
          scoreFilter.find((v) => v.id === "min") &&
          scoreFilter.find((v) => v.id === "max")
        ) {
          const minValStr = scoreFilter.find((v) => v.id === "min")?.name;
          const maxValStr = scoreFilter.find((v) => v.id === "max")?.name;
          serviceMin = !isNaN(Number(minValStr))
            ? Number(minValStr)
            : this.minScoreValue;
          serviceMax = !isNaN(Number(maxValStr))
            ? Number(maxValStr)
            : this.maxScoreValue;
        }

        // Update local slider values *only if* they differ from the service state
        // This prevents the subscription from resetting sliders during user interaction
        if (this.scoreMinValue !== serviceMin) {
          this.scoreMinValue = serviceMin;
        }
        if (this.scoreMaxValue !== serviceMax) {
          this.scoreMaxValue = serviceMax;
        }

        this.updateLengths(); // Update counts for all filters
        this.calculateTotalLength(); // Calculate total badge count
      });

    // Subscribe to route changes
    this.router.events
      .pipe(
        filter(
          (event): event is NavigationEnd => event instanceof NavigationEnd,
        ),
        takeUntil(this.destroy$),
      )
      .subscribe((event: NavigationEnd) => {
        this.currentUrl = event.urlAfterRedirects;
        this.updateFilterExpansionBasedOnUrl();
      });

    // Debounce score slider updates before pushing to FilterService
    this.scoreUpdateSubject
      .pipe(
        debounceTime(300), // Wait for 300ms of silence
        distinctUntilChanged(
          (prev, curr) => prev.min === curr.min && prev.max === curr.max,
        ), // Only emit if values change
        takeUntil(this.destroy$),
      )
      .subscribe((scoreRange) => {
        this.updateFilterServiceWithScore(scoreRange.min, scoreRange.max);
      });

    this.currentUrl = this.router.url;
    this.updateFilterExpansionBasedOnUrl();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  updateFilterExpansionBasedOnUrl(): void {
    if (this.currentUrl !== "/" && !this.currentUrl.startsWith("/?")) {
      this.isFilterExpanded = false;
    }
  }

  toggleMenu(): void {
    this.isMenuVisible = !this.isMenuVisible;
    if (!this.isMenuVisible) {
      this.isFilterExpanded = false;
    }
  }

  toggleFilterSection(): void {
    if (this.isMenuVisible) {
      this.isFilterExpanded = !this.isFilterExpanded;
    } else {
      this.isMenuVisible = true;
      this.isFilterExpanded = true;
    }
  }

  toggleFilter(filter: FrontendFilter): void {
    // Keep track of the toggled filter's state
    const wasExpanded = filter.isExpanded;

    // collapse others when one is expanded
    this.filters.forEach((f) => (f.isExpanded = false));

    // Set the new state for the toggled filter
    filter.isExpanded = !wasExpanded;
  }

  selectFilterValue(filterName: string, value: FilterValue): void {
    // This handles checkbox selections (non-score filters)
    const currentSelections = this.selectedValues[filterName]
      ? [...this.selectedValues[filterName]]
      : [];
    const index = currentSelections.findIndex((v) => v.id === value.id);

    if (index === -1) {
      currentSelections.push({ id: value.id, name: value.name });
    } else {
      currentSelections.splice(index, 1);
    }

    const newSelectedFilters = { ...this.selectedValues };

    if (currentSelections.length === 0) {
      delete newSelectedFilters[filterName];
    } else {
      newSelectedFilters[filterName] = currentSelections;
    }
    this.filterService.updateSelectedFilters(newSelectedFilters);
  }

  // Method called when score range sliders change (use (input) event)
  updateSelectedScoreValues(): void {
    // Ensure min doesn't exceed max and vice-versa by clamping
    // Convert to numbers first
    let currentMin = Number(this.scoreMinValue);
    let currentMax = Number(this.scoreMaxValue);

    if (currentMin > currentMax) {
      // If min is dragged past max, clamp max to min's value
      // This assumes the min slider was the one moved. A more robust solution
      // might track which slider triggered the event, but this is simpler.
      this.scoreMaxValue = currentMin;
    }
    // Re-read possibly adjusted values before emitting
    currentMin = Number(this.scoreMinValue);
    currentMax = Number(this.scoreMaxValue);

    // Push the latest values to the debouncing subject
    this.scoreUpdateSubject.next({ min: currentMin, max: currentMax });
  }

  // Actual method to update the FilterService (called after debounce)
  private updateFilterServiceWithScore(
    minScore: number,
    maxScore: number,
  ): void {
    const newSelectedFilters = { ...this.filterService.getCurrentFilters() };

    // Update or remove the score filter based on slider values
    if (minScore !== this.minScoreValue || maxScore !== this.maxScoreValue) {
      // Range is active (not default), store min and max values
      newSelectedFilters[this.SCORE_FILTER_NAME] = [
        { id: "min", name: minScore.toString() },
        { id: "max", name: maxScore.toString() },
      ];
    } else {
      // Range is default (e.g., 0-10), remove the filter
      delete newSelectedFilters[this.SCORE_FILTER_NAME];
    }

    this.filterService.updateSelectedFilters(newSelectedFilters);
  }

  isValueSelected(filterName: string, value: FilterValue): boolean {
    // Only for checkbox filters
    if (filterName === this.SCORE_FILTER_NAME) return false;
    return !!this.selectedValues[filterName]?.some((v) => v.id === value.id);
  }

  updateLengths(): void {
    this.lengths = {};
    this.filters.forEach((filter) => {
      if (filter.name === this.SCORE_FILTER_NAME) {
        // Score filter counts as 1 if it's active (present in selectedValues)
        this.lengths[filter.name] = this.selectedValues[filter.name] ? 1 : 0;
      } else {
        // Other filters count based on the number of selected items
        this.lengths[filter.name] =
          this.selectedValues[filter.name]?.length || 0;
      }
    });
  }

  calculateTotalLength(): void {
    this.totalSelectedValuesLength = Object.entries(this.selectedValues).reduce(
      (total, [filterName, currentArray]) => {
        if (filterName === this.SCORE_FILTER_NAME) {
          // Score filter adds 1 to the total count if active
          return total + (currentArray ? 1 : 0);
        } else {
          // Other filters add the number of selected items
          return total + (currentArray?.length || 0);
        }
      },
      0,
    );
  }

  async getFilters() {
    try {
      const filtersFromApi = await firstValueFrom(
        this.filterService.getFilters(),
      );
      // Preserve expansion state if filters are reloaded
      const currentExpansionState = this.filters.reduce(
        (acc, f) => {
          acc[f.name] = f.isExpanded;
          return acc;
        },
        {} as { [key: string]: boolean },
      );

      this.filters = filtersFromApi.map((f) => ({
        ...f,
        isExpanded: currentExpansionState[f.name] ?? false, // Default to closed unless previously opened
      }));

      // Ensure Score filter exists in the list if not provided by API explicitly
      if (!this.filters.some((f) => f.name === this.SCORE_FILTER_NAME)) {
        this.filters.push({
          name: this.SCORE_FILTER_NAME,
          values: [], // No specific values needed for range sliders
          isExpanded: currentExpansionState[this.SCORE_FILTER_NAME] ?? false, // Persist expansion state if possible
        });
      }

      // Apply current selections from service (triggers subscription update)
      const currentSelectedFilters = this.filterService.getCurrentFilters();
      this.filterService.updateSelectedFilters(currentSelectedFilters); // Re-emit to ensure consistency
    } catch (error) {
      console.error("Failed to load filters:", error);
      this.filters = [];
      // Add score filter manually even if API fails?
      if (!this.filters.some((f) => f.name === this.SCORE_FILTER_NAME)) {
        this.filters.push({
          name: this.SCORE_FILTER_NAME,
          values: [],
          isExpanded: false,
        });
      }
    }
  }

  getFilteredOptions(filter: FrontendFilter): FilterValue[] {
    // This method is now only relevant for non-score filters
    if (filter.name === this.SCORE_FILTER_NAME) {
      return []; // No options to display for score range sliders
    }

    if (filter.name === this.PRODUCT_LINE_FILTER_NAME) {
      const productLineFilter = filter;
      const selectedBrands = this.selectedValues[this.BRAND_FILTER_NAME];

      if (!selectedBrands || selectedBrands.length === 0) {
        return productLineFilter.values || [];
      }

      const selectedBrandIds = new Set(selectedBrands.map((brand) => brand.id));
      return (productLineFilter.values || []).filter(
        (line) =>
          line.brand_fk !== undefined && selectedBrandIds.has(line.brand_fk),
      );
    }

    // Simplified handling for My Products assuming it uses standard values if needed
    if (filter.name === this.MY_PRODUCTS_FILTER_NAME) {
      // Logic for 'only'/'others' if needed, otherwise return values
      const selectedMyProductsId =
        this.selectedValues[this.MY_PRODUCTS_FILTER_NAME]?.[0]?.id;
      if (selectedMyProductsId === "only")
        return [{ name: "Only My Products", id: "only" }];
      if (selectedMyProductsId === "others")
        return [{ name: "Others", id: "others" }];
      return filter.values || []; // Or specific logic based on structure
    }

    return filter.values || [];
  }

  clearAllFilters(): void {
    // Resetting local slider state happens via the subscription when filters are cleared
    this.filterService.clearFilters();
    // Explicitly collapse all filter sections might be desired UX
    this.filters.forEach((f) => (f.isExpanded = false));
    this.isFilterExpanded = false; // Collapse main filter section too
  }

  onLogout() {
    this.filterService.clearFilters(); // Clear filters on logout
    // No need to reset selectedValues, lengths etc. here, subscription handles it
    this.isFilterExpanded = false;
    this.authService.logout();
    this.currentUser = null;
  }
}
