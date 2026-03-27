import { CommonModule } from "@angular/common";
import { HttpClientModule } from "@angular/common/http";
import {
  Component,
  CUSTOM_ELEMENTS_SCHEMA,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
} from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, Router } from "@angular/router";
import "@archr-se/score-card";
import { NgIcon, provideIcons } from "@ng-icons/core";
import {
  matErrorRound,
  matFormatListBulletedRound,
  matGridViewRound,
} from "@ng-icons/material-icons/round";
import { LoadingBarService } from "@ngx-loading-bar/core";
import {
  debounceTime,
  distinctUntilChanged,
  firstValueFrom,
  map,
  Observable,
  Subject,
  takeUntil,
} from "rxjs";

import { FileUploadComponent } from "../bulk-upload/file-upload/file-upload.component";
//import { UploadProduct } from '../models/upload-product-model';
//import { ProductCsvService } from '../services/productCsvService';
import { environment } from '../../environments/environment';
import { Company } from '../models/company';
import { BackendPaginatedResult, FrontendProductModel } from '../models/product-entities.model';
import { UploadProduct } from '../models/upload-product-model';
import { ProductFormService } from '../product-components/services/product-form.service';
import { FilterService, SelectedFilters } from '../services/filter.service';
import { ProductCsvService } from '../services/productCsvService';
import { UserService } from '../services/user.service';
import { ProductService } from '../services/product.service';

export const PAGE_SIZE = 20;

const SCORE_FILTER_NAME = "Score";
const PRODUCTBRAND_FILTER_NAME = "Brand";
const PRODUCT_LINE_FILTER_NAME = "Product line";
const MY_PRODUCTS_FILTER_NAME = "My Products";
const CATEGORY_FILTER_NAME = "Product category";
const QUESTIONNAIRE_CATEGORY_FILTER_NAME = "Questionnaire category";

@Component({
  selector: "app-home",
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    NgIcon,
    FileUploadComponent,
  ],
  templateUrl: "./home.component.html",
  providers: [
    ProductCsvService,
    provideIcons({
      matFormatListBulletedRound,
      matGridViewRound,
      matErrorRound,
    }),
  ],
})
export class HomeComponent implements OnInit, OnDestroy {
  baseUrl = environment.apiUrl;

  @ViewChild("fileInput", { static: false }) fileInput!: ElementRef;

  // --- Data & State ---
  products: FrontendProductModel[] = [];
  selectedProducts: FrontendProductModel[] = [];
  currentCompany!: Company;
  error: string | null = null;
  loading: boolean = true; // Main loading indicator (for initial load and page transitions)
  listView: boolean = false;
  searchTerm: string = "";
  totalProducts: number = 0;
  currentPage: number = 1; // Driven by URL query param
  totalPages: number = 0; // Calculated from totalProducts and PAGE_SIZE

  // --- RxJS Subjects and Subscriptions ---
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  // --- Services & Utils ---
  loader; // NgxLoadingBar reference

  // --- Getters for Template Logic ---
  get canAddSelection(): boolean {
    return (
      this.selectedProducts.length > 0 &&
      this.selectedProducts.every((p) => !p.is_my_product)
    );
  }
  get canRemoveSelection(): boolean {
    return (
      this.selectedProducts.length > 0 &&
      this.selectedProducts.every((p) => p.is_my_product)
    );
  }
  get isMixedSelection(): boolean {
    if (this.selectedProducts.length === 0) return false;
    const hasMyProduct = this.selectedProducts.some((p) => p.is_my_product);
    const hasOtherProduct = this.selectedProducts.some((p) => !p.is_my_product);
    return hasMyProduct && hasOtherProduct;
  }

  /** Exposes FilterService's active filter status as an Observable for the template */
  public get hasActiveFilters$(): Observable<boolean> {
    return this.filterService.hasActiveFilters$;
  }

  // --- Constructor ---
  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private productService: ProductService,
    private userService: UserService,
    private filterService: FilterService,
    private loadingBar: LoadingBarService,
    private productFormService: ProductFormService,
  ) {
    this.loader = this.loadingBar.useRef();
  }

  // --- Lifecycle Hooks ---
  ngOnInit(): void {
    this.loader.start();
    this.loading = true;

    try {
      this.currentCompany = this.userService.getCurrentCompany();
      if (!this.currentCompany?.name) {
        this.handleInitializationError(
          "Your account is not linked to a company.",
        );
        return;
      }

      // Setup reactive listeners (search, filters) BEFORE subscribing to route params
      this.setupReactiveListeners();

      // Subscribe to Query Param changes to drive pagination and initial load
      this.route.queryParamMap
        .pipe(
          map((params) => params.get("page")), // Get 'page' string
          map((page) => parseInt(page || "1", 10)), // Parse to number, default 1
          map((page) => (isNaN(page) || page < 1 ? 1 : page)), // Validate, default 1
          takeUntil(this.destroy$), // Auto-unsubscribe
        )
        .subscribe((pageFromUrl) => {
          this.currentPage = pageFromUrl;

          // If totalPages is known and requested page is out of bounds, redirect
          if (this.totalPages > 0 && this.currentPage > this.totalPages) {
            console.warn(
              `Requested page ${this.currentPage} is out of bounds (${this.totalPages}). Redirecting to ${this.totalPages}.`,
            );
            this.goToPage(this.totalPages); // This triggers a new navigation cycle
            return; // Stop processing for this invalid page
          }

          this.fetchProducts();
        });
    } catch (error: any) {
      this.handleInitializationError(
        `Initialization error: ${error.message || error}`,
      );
    }
  }

  setupReactiveListeners(): void {
    // --- Subscribe to search term changes ---
    this.searchSubject
      .pipe(debounceTime(400), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe((searchTerm) => {
        this.goToPage(1);
      });

    // --- Subscribe to filter changes ---
    this.filterService.selectedFilters$
      .pipe(takeUntil(this.destroy$))
      .subscribe((filters) => {
        // Check if the component is initialized and not currently loading to avoid loops
        if (!this.loading) {
          // Basic check to prevent triggering fetch while one is ongoing
          console.log("Reactive filter change triggered:", filters);
          // Navigate to page 1 whenever filters change
          this.goToPage(1);
        } else {
          console.log(
            "Filter change detected, but loading is true. Skipping navigation trigger.",
          );
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.loader.stop(); // Ensure loading bar stops
  }

  // --- Data Fetching Logic ---

  fetchProducts(): void {
    this.loading = true;
    this.error = null;
    this.products = [];
    this.loader.start();
    this.selectedProducts = [];

    // Get the latest filters from the service
    const currentFilters = this.filterService.getCurrentFilters();
    // Build the options object for the GET query params
    const apiOptions = this.buildApiQueryParams(currentFilters); // Uses this.currentPage

    console.log(
      `Workspaceing products: Page ${this.currentPage}, API Request Body:`,
      apiOptions,
    );

    // Call the updated searchProducts method which uses GET with query params
    this.productService.searchProducts(apiOptions).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response: BackendPaginatedResult<FrontendProductModel>) => {
        console.log(`Received ${response.results.length} products. Total count from API: ${response.count}`);
        this.totalProducts = response.count;
        const effectivePageSize = apiOptions.page_size || PAGE_SIZE;
        this.totalPages = Math.ceil(this.totalProducts / effectivePageSize);

          if (
            this.totalPages > 0 &&
            this.currentPage > this.totalPages &&
            this.totalProducts > 0
          ) {
            console.warn(
              `Current page ${this.currentPage} is now invalid (${this.totalPages} total pages). Redirecting to page ${this.totalPages}.`,
            );
            this.loading = false;
            this.loader.stop();
            this.goToPage(this.totalPages);
            return;
          }

          this.products = response.results.map((p) => {
            // Use the isAnswered value from the backend if it exists
            return { ...p, isClicked: false };
          });
          console.log(
            "Products with concern counts:",
            this.products.map((p) => ({
              id: p.id,
              name: p.name,
              concernCount: p.concernCount,
            })),
          );
          this.loading = false;
          this.loader.stop();
        },
        error: (err) => {
          this.handleFetchError(err, "Failed to load products");
        },
      });
  }

  private buildApiQueryParams(filters: SelectedFilters): any {
    // Define default min/max scores expected by the backend if no filter is applied
    const ABSOLUTE_MIN_SCORE = 0;
    const ABSOLUTE_MAX_SCORE = 10;

    const opts: {
      page?: number;
      page_size?: number;
      search?: string | null;
      category_names?: string[] | null; // Expecting array of names
      questionnaire_category_ids?: number[] | null; // Expecting array of IDs
      line_ids?: number[] | null; // Expecting array of IDs
      brand_ids?: number[] | null; // Expecting array of IDs
      min_score?: string | null; // Expecting string
      max_score?: string | null; // Expecting string
      my_products_filter?: "only" | "others" | null; // Expecting string
    } = {
      page: this.currentPage,
      page_size: PAGE_SIZE,
      search: this.searchTerm || undefined,
    };

    // --- Map selected filters to query params ---
    const selectedMyProductsFilter = filters["My Products"]?.[0]?.id;
    if (
      selectedMyProductsFilter &&
      (selectedMyProductsFilter === "only" ||
        selectedMyProductsFilter === "others")
    ) {
      opts.my_products_filter = selectedMyProductsFilter;
    }

    // Category Names (assuming filters['Product category'] holds {id: string, name: string}[])
    const selectedCategories = filters["Product category"]; // Use the exact key from FilterService
    if (selectedCategories && selectedCategories.length > 0) {
      // Extract the 'name' property from each selected category object
      opts.category_names = selectedCategories
        .map((cat) => cat.name)
        .filter((name) => name); // Filter out empty names just in case
    }

    // Questionnaire Category IDs
    const selectedQuestionnaireCategories =
      filters[QUESTIONNAIRE_CATEGORY_FILTER_NAME];
    if (
      selectedQuestionnaireCategories &&
      selectedQuestionnaireCategories.length > 0
    ) {
      // Extract the 'id' property from each selected questionnaire category object
      opts.questionnaire_category_ids = selectedQuestionnaireCategories
        .map((cat) => cat.id)
        .filter((id) => id != null && typeof id === "number"); // Filter out null/undefined IDs
    }

    // Line IDs (assuming filters['Product line'] holds {id: number, name: string}[])
    const selectedLines = filters["Product line"]; // Use the exact key from FilterService
    if (selectedLines && selectedLines.length > 0) {
      // Extract the 'id' property from each selected line object
      opts.line_ids = selectedLines
        .map((line) => line.id)
        .filter((id) => id != null && typeof id === "number"); // Filter out null/undefined IDs
    }

    const selectedBrands = filters[PRODUCTBRAND_FILTER_NAME];
    if (selectedBrands && selectedBrands.length > 0) {
      // Extract the 'id' property from each selected product brand object
      opts.brand_ids = selectedBrands
        .map((brand) => brand.id)
        .filter((id) => id != null && typeof id === "number"); // Filter out null/undefined IDs
    }

    const scoreFilterValues = filters[SCORE_FILTER_NAME];
    if (scoreFilterValues && scoreFilterValues.length === 2) {
      const minValEntry = scoreFilterValues.find((v) => v.id === "min");
      const maxValEntry = scoreFilterValues.find((v) => v.id === "max");
      const minValStr = minValEntry?.name;
      const maxValStr = maxValEntry?.name;

      // Add min_score if it's valid and different from the absolute minimum
      if (minValStr && !isNaN(Number(minValStr))) {
        const numMinVal = Number(minValStr);
        if (numMinVal !== ABSOLUTE_MIN_SCORE) {
          opts.min_score = numMinVal.toString();
        }
      }
      // Add max_score if it's valid and different from the absolute maximum
      if (maxValStr && !isNaN(Number(maxValStr))) {
        const numMaxVal = Number(maxValStr);
        if (numMaxVal !== ABSOLUTE_MAX_SCORE) {
          opts.max_score = numMaxVal.toString();
        }
      }
    }

    // Clean up undefined/null/empty array properties before sending
    Object.keys(opts).forEach((key: string) => {
      const typedKey = key as keyof typeof opts;
      if (opts[typedKey] === undefined || opts[typedKey] === null) {
        delete opts[typedKey];
      } else if (
        Array.isArray(opts[typedKey]) &&
        (opts[typedKey] as any[]).length === 0
      ) {
        delete opts[typedKey];
      }
    });

    return opts;
  }

  private handleFetchError(error: any, context: string): void {
    console.error(`${context}:`, error);
    // Try to get a meaningful message
    const message =
      error?.error?.detail ||
      error?.error?.error ||
      error?.message ||
      "Unknown server error";
    this.error = `${context}: ${message}`;
    this.products = []; // Clear data on error
    this.totalProducts = 0;
    this.totalPages = 0;
    this.loading = false; // Ensure loading stops
    this.loader.stop(); // Complete loader to hide it
  }

  private handleInitializationError(message: string): void {
    console.error("Initialization Error:", message);
    this.error = message;
    this.loading = false;
    this.loader.stop();
    this.products = [];
    this.totalProducts = 0;
    this.totalPages = 0;
  }

  // --- Navigation ---
  goToPage(page: number): void {
    // Basic validation: Don't navigate if page is invalid or already the current page
    if (
      page < 1 ||
      (this.totalPages > 0 && page > this.totalPages) ||
      page === this.currentPage
    ) {
      if (page === this.currentPage) {
        console.log(`goToPage: Already on page ${page}.`);
        this.fetchProducts();
        return;
      } else {
        console.warn(
          `goToPage: Invalid page requested (${page}). Current: ${this.currentPage}, Total: ${this.totalPages}`,
        );
      }
      return;
    }

    console.log(`Navigating to page ${page}...`);
    this.router
      .navigate([], {
        relativeTo: this.route,
        queryParams: { page: page },
        queryParamsHandling: "merge", // Preserve other query params
      })
      .catch((err) => console.error("Navigation error:", err));
  }

  // --- Event Handlers ---
  onSearchInput(): void {
    // Trigger the RxJS subject for debounced navigation/fetch
    this.searchSubject.next(this.searchTerm);
  }

  // --- UI Interaction ---
  toggleListView(): void {
    this.listView = !this.listView;
  }

  getScoreColor(score: number): string {
    if (score < 2) return "#C6433B"; // Very Low
    if (score < 4) return "#FF5C52"; // Low
    if (score < 7) return "#FFBA52"; // Medium
    if (score < 9) return "#67D67C"; // High
    return "#4BA26E"; // Very High
  }

  chooseProduct(product: FrontendProductModel): void {
    // Prevent interaction if product is dimmed (mixed selection state)
    if (this.isProductDimmed(product)) {
      return;
    }

    const index = this.selectedProducts.findIndex((p) => p.id === product.id);
    if (index === -1) {
      this.selectedProducts.push(product);
      product.isClicked = true;
    } else {
      this.selectedProducts.splice(index, 1);
      product.isClicked = false;
    }
  }

  markAllVisible(): void {
    // Selects all products currently loaded on the *current page*
    // Filters out already selected products to avoid duplicates, then adds remaining
    const selectedIds = new Set(this.selectedProducts.map((p) => p.id));
    const productsToAdd = this.products.filter(
      (p) => !selectedIds.has(p.id) && !p.is_my_product,
    );

    this.selectedProducts.push(...productsToAdd);

    if (this.selectedProducts.length === 0) {
      // in this case all visible products are my products and the select all is probably ment to select all my products
      this.selectedProducts = this.products.filter((p) => p.is_my_product);
    }

    this.updateProductClickedState(); // Update isClicked for all visible products
  }

  clearSelection(): void {
    this.selectedProducts = [];
    this.updateProductClickedState(); // Update isClicked for all visible products
  }

  // Helper to sync the `isClicked` property with the `selectedProducts` array
  updateProductClickedState(): void {
    const selectedIds = new Set(this.selectedProducts.map((p) => p.id));
    this.products.forEach((p) => (p.isClicked = selectedIds.has(p.id)));
  }

  // --- Actions (Add/Remove My Products) ---
  async onAddClick() {
    if (
      !this.canAddSelection ||
      this.isMixedSelection ||
      this.selectedProducts.length === 0
    )
      return;

    this.loader.start();
    this.error = null;
    const productsToAdd = [...this.selectedProducts]; // Copy selection

    try {
      await firstValueFrom(
        this.productService
          .addMyProducts(productsToAdd.map((p) => p.id))
          .pipe(takeUntil(this.destroy$)),
      );
      this.clearSelection();
      this.fetchProducts();
    } catch (err: any) {
      this.loader.stop();
      this.handleFetchError(err, "Failed to add products"); // Use consistent error handling
    }
  }

  async onRemoveClick() {
    if (
      !this.canRemoveSelection ||
      this.isMixedSelection ||
      this.selectedProducts.length === 0
    )
      return;

    this.loader.start();
    this.error = null;
    const productsToRemove = [...this.selectedProducts]; // Copy selection

    try {
      await firstValueFrom(
        this.productService
          .removeMyProducts(productsToRemove.map((p) => p.id))
          .pipe(takeUntil(this.destroy$)),
      );
      this.clearSelection();
      this.fetchProducts();
    } catch (err: any) {
      this.loader.stop();
      this.handleFetchError(err, "Failed to remove products"); // Use consistent error handling
    }
  }

  isProductDimmed(product: FrontendProductModel): boolean {
    // Dims products that cannot be part of the current action based on selection
    if (this.selectedProducts.length === 0) return false;

    const selectionContainsMyProduct = this.selectedProducts.some(
      (p) => p.is_my_product,
    );
    const selectionContainsOtherProduct = this.selectedProducts.some(
      (p) => !p.is_my_product,
    );

    // If selection includes 'My Products', dim 'Other Products'
    if (selectionContainsMyProduct && !product.is_my_product) {
      return true;
    }
    // If selection includes 'Other Products', dim 'My Products'
    if (selectionContainsOtherProduct && product.is_my_product) {
      return true;
    }

    return false; // Not dimmed otherwise
  }

  /**
   * Helper to update the view based on MyProducts changes without full refetch
   */
  updateProductIsMyProductState(): void {
    // This forces Angular to re-evaluate the [ngIf]="isMyProduct(product)" in the template
    // for the products currently in the view.
    this.products = [...this.products];
  }

  // --- Product Creation/Editing (Bulk/Manual) ---
  triggerFileInput(): void {
    this.fileInput.nativeElement.click();
  }

  redirectToAddManually(): void {
    // Close the modal first if using DaisyUI modal methods
    const modal = document.getElementById(
      "create_product_modal",
    ) as HTMLDialogElement | null;
    if (modal && typeof modal.close === "function") {
      modal.close();
    }
    this.router.navigate(["/create-product"]);
  }

  editProduct(productId: number): void {
    // Navigate to the edit product page, passing the ID as a query parameter
    console.log(`Navigating to edit product with ID: ${productId}`);
    this.router.navigate(["/edit-product"], {
      queryParams: { productId: productId },
    });
  }

  // Helper for generating pagination buttons with ellipsis
  getPaginationRange(): (number | string)[] {
    const total = this.totalPages;
    const current = this.currentPage;
    const delta = 1; // How many pages to show around the current page
    const range = [];
    const rangeWithDots: (number | string)[] = [];
    let l: number | undefined;

    range.push(1); // Always show first page

    // Calculate bounds, ensuring they are within [1, totalPages]
    const lowerBound = Math.max(2, current - delta);
    const upperBound = Math.min(total - 1, current + delta);

    for (let i = lowerBound; i <= upperBound; i++) {
      range.push(i);
    }

    if (total > 1) {
      range.push(total); // Always show last page if different from first
    }

    // Add ellipsis ("...") where gaps exist
    for (const i of range) {
      if (l) {
        if (i - l === 2) {
          // Gap of one page
          rangeWithDots.push(l + 1);
        } else if (i - l > 2) {
          // Gap of two or more pages
          rangeWithDots.push("...");
        }
      }
      rangeWithDots.push(i);
      l = i;
    }

    return rangeWithDots;
  }
}
// All references to Brand in this file are filter names or comments, not type/interface usage. No changes needed for ProductBrand interface here.
