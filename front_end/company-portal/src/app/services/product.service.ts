import { Injectable } from "@angular/core";
import { Observable, of } from "rxjs";
import { catchError, filter, map } from "rxjs/operators";
import { HttpService } from "./http.service";
import {
  BackendProductModel,
  FrontendProductModel,
  FrontendProductLine,
  BackendProductLine,
  ProductBrand,
  mapBackendProductToFrontendProductModel,
  mapBackendToFrontendProductLine,
  CreateProductModel,
  GetProductResponse,
  UpdateProductModel,
  BackendPaginatedResult,
} from "../models/product-entities.model";
import { ProductCategory, ProductLine } from "../models/questionnaire.model";
import { ɵparseCookieValue } from "@angular/common";
import { HttpClient } from "@angular/common/http";

@Injectable({
  providedIn: "root",
})
export class ProductService extends HttpService {
  constructor(http: HttpClient) {
    super(http);
  }

  addMyProducts(products: number[]): Observable<any> {
    const payload = { products: products };
    return this.post(`/models/myproducts/`, payload);
  }

  removeMyProducts(products: number[]): Observable<any> {
    return this.delete(`/models/myproducts/`, {
      body: { products: products },
    });
  }

  addProductManually(product: CreateProductModel): Observable<any> {
    return this.post(`/models/products/`, [product]);
  }

  addProductsManually(products: CreateProductModel[]): Observable<any> {
    return this.post(`/models/products/`, products);
  }

  updateProductManually(product: UpdateProductModel) {
    return this.put(`/models/products/${product.id}/`, product).pipe();
  }

  updateProduct(editedProduct: any, productId: number): Observable<any> {
    return this.put(`/models/products/${productId}/`, editedProduct);
  }

  getProduct(productId: number): Observable<GetProductResponse> {
    return this.get<GetProductResponse>(`/models/products/${productId}/`);
  }

  searchProducts(opts: {
    page?: number;
    page_size?: number;
    search?: string | null;
    category_names?: string[] | null;
    questionnaire_category_ids?: number[] | null;
    line_ids?: number[] | null;
    brand_ids?: number[] | null;
    min_score?: number | null;
    max_score?: number | null;
    my_products_filter?: "only" | "others" | null;
  }): Observable<BackendPaginatedResult<FrontendProductModel>> {
    // Build query params for GET request. Arrays are passed as repeated params.
    const params: Record<string, any> = {};
    if (opts.page !== undefined && opts.page !== null)
      params["page"] = opts.page;
    if (opts.page_size !== undefined && opts.page_size !== null)
      params["page_size"] = opts.page_size;
    if (opts.search) params["search"] = opts.search;
    if (opts.category_names && opts.category_names.length > 0)
      params["category_names"] = opts.category_names.join(",");
    if (
      opts.questionnaire_category_ids &&
      opts.questionnaire_category_ids.length > 0
    )
      params["questionnaire_category_ids"] =
        opts.questionnaire_category_ids.join(",");
    if (opts.line_ids && opts.line_ids.length > 0)
      params["line_ids"] = opts.line_ids.join(",");
    if (opts.brand_ids && opts.brand_ids.length > 0)
      params["brand_ids"] = opts.brand_ids.join(",");
    if (opts.min_score !== undefined && opts.min_score !== null)
      params["min_score"] = opts.min_score.toString();
    if (opts.max_score !== undefined && opts.max_score !== null)
      params["max_score"] = opts.max_score.toString();
    if (
      opts.my_products_filter === "only" ||
      opts.my_products_filter === "others"
    )
      params["my_products_filter"] = opts.my_products_filter;

    return this.get<BackendPaginatedResult<BackendProductModel>>(
      `/models/products/search/`,
      {
        params,
      },
    ).pipe(
      map((backendResult) => ({
        ...backendResult,
        results: backendResult.results.map((product) =>
          mapBackendProductToFrontendProductModel(product),
        ),
      })),
      catchError((error) => {
        console.error("Error searching products", error);
        return of({ count: 0, next: null, previous: null, results: [] });
      }),
    );
  }

  getProductCategories(): Observable<ProductCategory[]> {
    return this.get<ProductCategory[]>(`/models/productcategory/`);
  }

  getProductLines(): Observable<ProductLine[]> {
    return this.get<ProductLine[]>(`/models/productlines/`);
  }

  getProductLine(productLineId: number): Observable<FrontendProductLine> {
    return this.get<BackendProductLine>(
      `/models/productlines/${productLineId}/`,
    ).pipe(
      map(mapBackendToFrontendProductLine),
      catchError((error) => {
        console.error("Error loading product", error);
        return of(null);
      }),
      filter(
        (productLine): productLine is FrontendProductLine =>
          productLine !== null,
      ),
    );
  }

  getBrands(): Observable<ProductBrand[]> {
    return this.get<ProductBrand[]>(`/models/brands/`);
  }

  getBrand(brandId: number): Observable<ProductBrand> {
    return this.get<ProductBrand>(`/models/brands/${brandId}/`).pipe(
      catchError((error) => {
        console.error("Error loading brand", error);
        return of(null);
      }),
      filter((brand): brand is ProductBrand => brand !== null),
    );
  }

  uploadSustainabilityReport(productId: number, files: File[]): Observable<any> {
    const formData = new FormData();
    // Append all files to FormData with the same key 'files'
    files.forEach((file) => {
      formData.append("files", file);
    });

    return this.http.post<any>(
      `${this.baseUrl}/models/products/${productId}/sustainability-report/`,
      formData,
      {
        withCredentials: true,
        headers: {
          "X-CSRFToken": ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
        },
      },
    );
  }
}
