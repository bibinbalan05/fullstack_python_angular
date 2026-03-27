import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { ProductCategory, ProductLine } from '../../models/questionnaire.model';
import { ProductBrand, CreateProductModel, UpdateProductModel, GetProductResponse } from '../../models/product-entities.model';
import { ProductService } from '../../services/product.service';
import { HttpService } from '../../services/http.service';

export interface ProductFormData {
  productID?: number | null;
  productName: string;
  eans: { ean: string; name?: string; product_model: number }[];
  productCategoryID: string | null;
  productLineID: number | null;
  brandID: number | null;
  image: string;
  imageName?: string | null;
}

export interface ProductFormState {
  isLoading: boolean;
  errorMessage: string | null;
  productCategories: ProductCategory[];
  productLines: ProductLine[];
  filteredProductLines: ProductLine[];
  brands: ProductBrand[];
}

@Injectable({
  providedIn: "root",
})
export class ProductFormService {
  private _state = new BehaviorSubject<ProductFormState>({
    isLoading: false,
    errorMessage: null,
    productCategories: [],
    productLines: [],
    filteredProductLines: [],
    brands: [],
  });

  private _formData = new BehaviorSubject<ProductFormData>({
    productName: "",
    eans: [{ ean: "", name: "", product_model: 0 }],
    productCategoryID: null,
    productLineID: null,
    brandID: null,
    image: '',
    imageName: null
  });

  private _productAnsweredState$ = new BehaviorSubject<boolean>(true);
  public productAnsweredState$ = this._productAnsweredState$.asObservable();

  public state$ = this._state.asObservable();
  public formData$ = this._formData.asObservable();

  constructor(private productService: ProductService, private httpService: HttpService) {}

  get currentState(): ProductFormState {
    return this._state.getValue();
  }

  get currentFormData(): ProductFormData {
    return this._formData.getValue();
  }

  updateFormData(updates: Partial<ProductFormData>): void {
    const current = this._formData.getValue();
    this._formData.next({ ...current, ...updates });
  }

  updateState(updates: Partial<ProductFormState>): void {
    const current = this._state.getValue();
    this._state.next({ ...current, ...updates });
  }

  async loadInitialData(productId?: number): Promise<void> {
    try {
      this.updateState({ isLoading: true, errorMessage: null });

      const promises: Promise<any>[] = [
        this.loadProductCategories(),
        this.loadProductLines(),
        this.loadBrands(),
      ];

      if (productId) {
        promises.push(this.loadProduct(productId));
      }

      const results = await Promise.all(promises);

      if (productId) {
        const product = results[3] as GetProductResponse;
        this.updateFormData({
          productID: product.id,
          productName: product.name,
          eans: product.eans || [{ ean: '', name: '', product_model:0 }],
          image: product.image,
          imageName: null
        });
        let derivedImageName: string | null = null;
        if (product.image) {
          try {
            const url = new URL(product.image);
            const pathname = url.pathname || '';
            const idx = pathname.indexOf('/products/');
            if (idx !== -1) {
              derivedImageName = pathname.substring(idx + 1);
            }
          } catch (e) {
            const s = String(product.image);
            const idx = s.indexOf('products/');
            if (idx !== -1) {
              derivedImageName = s.substring(idx);
            }
          }
        }
        this.updateFormData({
          productID: product.id,
          productName: product.name,
          eans: product.eans || [{ ean: '', name: '', product_model:0 }],
          image: product.image,
          imageName: derivedImageName,
        });
        this.onSelectProductCategory(product.product_category);
        this.onSelectBrand(product.product_line.brand_fk);
        this.onSelectProductLine(product.product_line.id);
        this._productAnsweredState$.next(product.isAnswered);


      } else {
        // For create mode, set defaults
        const state = this.currentState;
        if (state.productCategories.length > 0) {
          this.onSelectProductCategory(state.productCategories[0].name);
        }
        if (state.brands.length > 0) {
          this.onSelectBrand(state.brands[0].id);
        }
      }
    } catch (error) {
      this.updateState({ errorMessage: this.formatError(error) });
    } finally {
      this.updateState({ isLoading: false });
    }
  }

  private loadProductCategories(): Promise<ProductCategory[]> {
    return new Promise((resolve, reject) => {
      this.productService.getProductCategories().subscribe({
        next: data => {
          this.updateState({ productCategories: data });
          resolve(data);
        },
        error: (err) => reject(this.formatError(err)),
      });
    });
  }

  private loadProductLines(): Promise<ProductLine[]> {
    return new Promise((resolve, reject) => {
      this.productService.getProductLines().subscribe({
        next: data => {
          this.updateState({ productLines: data });
          resolve(data);
        },
        error: (err) => reject(this.formatError(err)),
      });
    });
  }

  private loadBrands(): Promise<ProductBrand[]> {
    return new Promise((resolve, reject) => {
      this.productService.getBrands().subscribe({
        next: data => {
          this.updateState({ brands: data });
          resolve(data);
        },
        error: (err) => reject(this.formatError(err)),
      });
    });
  }

  private loadProduct(productId: number): Promise<GetProductResponse> {
    return new Promise((resolve, reject) => {
      this.productService.getProduct(productId).subscribe({
        next: data => resolve(data),
        error: err => reject(this.formatError(err))
      });
    });
  }

  onSelectProductCategory(productCategoryID: string): void {
    this.updateFormData({ productCategoryID });
  }

  onSelectProductLine(productLineID: number | null): void {
    this.updateFormData({ productLineID });
    this.generateFilteredProductLines();
  }

  onSelectBrand(brandID: number | null): void {
    this.updateFormData({ brandID });
    this.generateFilteredProductLines();
  }

  private generateFilteredProductLines(): void {
    const state = this.currentState;
    const formData = this.currentFormData;

    const filteredProductLines = state.productLines.filter(
      (productLine) => productLine.brand_fk === formData.brandID,
    );

    this.updateState({ filteredProductLines });

    // Auto-select first product line if current selection is invalid
    if (!filteredProductLines.find((pl) => pl.id === formData.productLineID)) {
      if (filteredProductLines.length > 0) {
        this.onSelectProductLine(filteredProductLines[0].id);
      } else {
        this.onSelectProductLine(null);
      }
    }
  }

  validateEanUpc(value: string): { isValid: boolean; message: string | null } {
    const eanStr = String(value).trim();
    const baseMessage =
      "Valid EAN-8 (8 digits), UPC-A (12 digits), or EAN-13 (13 digits) code.";

    // 1. Digit check
    if (!/^\d+$/.test(eanStr)) {
      return {
        isValid: false,
        message: `${baseMessage} Must contain only digits. Received: "${eanStr.substring(0, 20)}"`,
      };
    }

    const length = eanStr.length;
    let isValid = false;
    let errorMessage = null;
    let calculatedChecksum = -1;
    let providedChecksum = -1;

    if (length === 13) {
      // Validate as EAN-13
      providedChecksum = parseInt(eanStr.slice(-1), 10);
      const digitsToCheck = eanStr.slice(0, -1);
      calculatedChecksum = this.calculateEanUpcChecksum(digitsToCheck);
      if (calculatedChecksum === providedChecksum) {
        isValid = true;
      } else {
        errorMessage = `Invalid EAN-13 checksum. Calculated ${calculatedChecksum}, expected ${providedChecksum}.`;
      }
    } else if (length === 12) {
      // Validate as UPC-A
      providedChecksum = parseInt(eanStr.slice(-1), 10);
      const digitsToCheck = "0" + eanStr.slice(0, -1);
      calculatedChecksum = this.calculateEanUpcChecksum(digitsToCheck);
      if (calculatedChecksum === providedChecksum) {
        isValid = true;
      } else {
        errorMessage = `Invalid UPC-A checksum. Calculated ${calculatedChecksum} (using EAN-13 method), expected ${providedChecksum}.`;
      }
    } else if (length === 8) {
      // Validate as EAN-8
      providedChecksum = parseInt(eanStr.slice(-1), 10);
      const digitsToCheck = eanStr.slice(0, -1);
      calculatedChecksum = this.calculateEanUpcChecksum(digitsToCheck);
      if (calculatedChecksum === providedChecksum) {
        isValid = true;
      } else {
        errorMessage = `Invalid EAN-8 checksum. Calculated ${calculatedChecksum}, expected ${providedChecksum}.`;
      }
    } else {
      errorMessage = `${baseMessage} Allowed lengths are 8 (EAN-8), 12 (UPC-A), or 13 (EAN-13). You entered ${length}.`;
    }

    return { isValid, message: errorMessage };
  }

  private calculateEanUpcChecksum(digitsStr: string): number {
    if (!/^\d+$/.test(digitsStr)) {
      console.error("Checksum calculation requires digits only.");
      return -1;
    }

    const digits = digitsStr.split("").map(Number);
    const length = digits.length;

    let oddSum = 0;
    let evenSum = 0;

    for (let i = 0; i < length; i++) {
      if (i % 2 === 0) {
        oddSum += digits[i];
      } else {
        evenSum += digits[i];
      }
    }

    const totalSum = oddSum + evenSum * 3;
    const remainder = totalSum % 10;
    const calculatedChecksum = remainder === 0 ? 0 : 10 - remainder;

    return calculatedChecksum;
  }

  validateForm(): { isValid: boolean; message: string | null } {
    const formData = this.currentFormData;

    // Validate all EANs
    for (const eanItem of formData.eans) {
      const eanValidation = this.validateEanUpc(eanItem.ean);
      if (!eanValidation.isValid) {
        return eanValidation;
      }
    }

    // Check if required fields are selected
    if (
      !formData.productLineID ||
      !formData.brandID ||
      !formData.productCategoryID
    ) {
      return {
        isValid: false,
        message: "Please select a product line, brand and product category",
      };
    }

    return { isValid: true, message: null };
  }

  addEan(): void {
    const formData = this.currentFormData;
    this.updateFormData({
      eans: [...formData.eans, { ean: "", name: "", product_model: 0 }],
    });
  }

  removeEan(index: number): void {
    const formData = this.currentFormData;
    if (formData.eans.length > 1) {
      const newEans = [...formData.eans];
      newEans.splice(index, 1);
      this.updateFormData({ eans: newEans });
    }
  }

  updateEan(
    index: number,
    updates: Partial<{ ean: string; name?: string }>,
  ): void {
    const formData = this.currentFormData;
    // Mutate the existing ean object to maintain references for ngModel
    Object.assign(formData.eans[index], updates);
    // Emit the updated formData (same reference, but with updated ean)
    this._formData.next({ ...formData });
  }

  async submitCreate(): Promise<void> {
    const validation = this.validateForm();
    if (!validation.isValid) {
      this.updateState({ errorMessage: validation.message });
      return;
    }

    this.updateState({ isLoading: true, errorMessage: null });

    const formData = this.currentFormData;
    const createProduct: CreateProductModel = {
      name: formData.productName,
      eans: formData.eans,
      image: null,
      productCategoryID: formData.productCategoryID!,
      productLineID: formData.productLineID!,
    };

    return new Promise((resolve, reject) => {
      this.productService.addProductManually(createProduct).subscribe({
        next: () => {
          this.updateState({ isLoading: false });
          resolve();
        },
        error: err => {
          this.updateState({
            isLoading: false,
            errorMessage: this.formatError(err),
          });
          reject(err);
        },
      });
    });
  }

  async submitUpdate(): Promise<void> {
    const validation = this.validateForm();
    if (!validation.isValid) {
      this.updateState({ errorMessage: validation.message });
      return;
    }

    const formData = this.currentFormData;
    if (!formData.productID) {
      this.updateState({ errorMessage: "Product ID is required for update" });
      return;
    }

    this.updateState({ isLoading: true, errorMessage: null });

    // The backend's ImageField expects a relative path from the storage root. We need to extract the path part of the URL.
    // This works for both local URLs ("http://.../media/products/img.png") and production GCS URLs ("https://.../products/img.png").
    let imagePath = formData.imageName ?? formData.image;
    if (imagePath) {
      try {
        const url = new URL(imagePath);
        imagePath = url.pathname.substring(1); // Get path and remove leading '/'
        if (imagePath.startsWith('media/')) {
          imagePath = imagePath.substring('media/'.length);
        }
      } catch (e) {
      }
    }

    const updateProduct: UpdateProductModel = {
      id: formData.productID,
      name: formData.productName,
      eans: formData.eans,
      image: imagePath,
      productCategoryID: formData.productCategoryID!,
      productLineID: formData.productLineID!,
    };

    return new Promise((resolve, reject) => {
      this.productService.updateProductManually(updateProduct).subscribe({
        next: () => {
          this.updateState({ isLoading: false });
          resolve();
        },
        error: err => {
          this.updateState({
            isLoading: false,
            errorMessage: this.formatError(err),
          });
          reject(err);
        },
      });
    });
  }

  private formatError(err: any): string {
    // Backend returns error in `detail` or `error` properties
    if (typeof err?.error?.detail === 'string') {
      return err.error.detail;
    }
    if (typeof err?.error?.error === 'string') {
      return err.error.error;
    }
    // Or it might be a validation error object
    if (typeof err?.error === 'object' && err.error !== null) {
      return this._formatValidationErrorObject(err.error);
    }
    // Fallback for other error types
    return err?.message || String(err);
  }

  /**
   * Parses a Django REST Framework validation error object into a readable string.
   * @param errors The error object, e.g., { name: ['This field is required.'], eans: [...] }
   */
  private _formatValidationErrorObject(errors: any): string {
    const messages: string[] = [];

    for (const key in errors) {
      if (Object.prototype.hasOwnProperty.call(errors, key)) {
        const errorValue = errors[key];

        if (Array.isArray(errorValue)) {
          // Handle nested errors for array fields like 'eans'
          if (key === 'eans' && typeof errorValue[0] === 'object') {
            errorValue.forEach((nestedError, index) => {
              const eanMessages = Object.values(nestedError).flat().join(' ');
              if (eanMessages) {
                messages.push(`EAN #${index + 1}: ${eanMessages}`);
              }
            });
          } else {
            // Handle simple field errors, e.g., name: ['message']
            const fieldName = key.charAt(0).toUpperCase() + key.slice(1);
            messages.push(`${fieldName}: ${errorValue.join(' ')}`);
          }
        }
      }
    }

    return messages.join(' | ');
  }

  setScoreNA(ean: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.httpService.post(`/score/na`, { ean }).subscribe({
        next: () => {
          this._productAnsweredState$.next(false);
          resolve();
        },
        error: (err) => {
          console.error(`Error setting score to NA for EAN ${ean}:`, err);
          reject(err);
        },
      });
    });
  }

  setScoreAnswered(ean: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.httpService.post(`/score/answered`, { ean }).subscribe({
        next: () => {
          this._productAnsweredState$.next(true);
          resolve();
        },
        error: (err) => {
          console.error(`Error setting score to answered for EAN ${ean}:`, err);
          reject(err);
        },
      });
    });
  }

  reset(): void {
    this._formData.next({
      productName: "",
      eans: [{ ean: "", name: "", product_model: 0 }],
      productCategoryID: null,
      productLineID: null,
      brandID: null,
      image: "",
    });
    this._state.next({
      isLoading: false,
      errorMessage: null,
      productCategories: [],
      productLines: [],
      filteredProductLines: [],
      brands: [],
    });
  }
}
