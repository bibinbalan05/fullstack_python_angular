import { AspectTotalScore } from "./aspect-total-score.model";
import { ProductCategory } from "./questionnaire.model";

export interface EAN {
  id: number;
  ean: string;
  name: string;
  product_model: number;
}

export interface BackendProductModel {
  id: number;
  name: string;
  product_category: string;
  eans: EAN[];
  product_line: {
    id: number;
    name: string;
    product_category: string;
    brand_fk: number;
    brand_name: string;
  };
  product_line_name: string;
  overall_score: number;
  aspect_scores: AspectTotalScore[];
  image: string;
  is_my_product: boolean;
  concern_count: number;
  isAnswered?: boolean;
}

export interface BackendPaginatedResult<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FrontendProductModel {
  id: number;
  name: string;
  eans: EAN[];
  overallScore: number;
  image: string;
  aspectScores: AspectTotalScore[];
  productCategory: ProductCategory;
  productLine: FrontendProductLine;
  isHovered?: boolean;
  isClicked?: boolean;
  is_my_product: boolean;
  concernCount: number;
  isAnswered?: boolean;
}

export interface GetProductResponse {
  id: number;
  name: string;
  product_category: string;
  eans: EAN[];
  product_line: {
    id: number;
    name: string;
    product_category: string;
    brand_fk: number;
    brand_name: string;
  };
  product_line_name: string;
  overall_score: string;
  aspect_scores: AspectTotalScore[];
  image: string;
  isAnswered: boolean;
}

export interface CreateProductModel {
  productCategoryID: string;
  name: string;
  eans: { ean: string; name?: string; product_model: number }[];
  image?: File | null;
  productLineID: number;
}

export interface UpdateProductModel {
  id: number;
  name: string;
  eans: { ean: string; name?: string }[];
  image: string;
  productCategoryID: string;
  productLineID: number;
}

export interface BackendProductLine {
  id: number;
  name: string;
  product_category: string;
  brand_fk: number;
  brand_name: string;
}

export interface FrontendProductLine {
  id: number;
  name: string;
  productCategory: ProductCategory;
  brand: ProductBrand;
}

export interface ProductBrand {
  id: number;
  name: string;
  product_category_name: string;
}

export function mapBackendProductToFrontendProductModel(
  backendProduct: BackendProductModel,
): FrontendProductModel {
  return {
    id: backendProduct.id,
    name: backendProduct.name,
    eans: backendProduct.eans,
    overallScore: backendProduct.overall_score,
    image: backendProduct.image,
    aspectScores: backendProduct.aspect_scores,
    productCategory: {
      name: backendProduct.product_category,
    } as ProductCategory,
    productLine: {
      id: backendProduct.product_line.id,
      name: backendProduct.product_line.name,
      productCategory: {
        name: backendProduct.product_category,
      } as ProductCategory,
      brand: {
        id: backendProduct.product_line.brand_fk,
        name: backendProduct.product_line.brand_name,
        product_category_name: backendProduct.product_line.product_category,
      },
    },
    isHovered: false,
    isClicked: false,
    is_my_product: backendProduct.is_my_product,
    concernCount: backendProduct.concern_count || 0,
    isAnswered: backendProduct.isAnswered,
  };
}

export function mapFrontendProductToBackendProductModel(
  frontendProduct: FrontendProductModel,
) {
  return {
    id: frontendProduct.id,
    name: frontendProduct.name,
    overall_score: frontendProduct.overallScore,
    image: frontendProduct.image,
    aspect_scores: frontendProduct.aspectScores,
    product_category_name: frontendProduct.productCategory.name,
    product_line: frontendProduct.productLine.id,
    product_line_name: frontendProduct.productLine.name,
    brand_name: frontendProduct.productLine.brand.name,
    eans: frontendProduct.eans,
  };
}

export function mapBackendToFrontendProductLine(
  backendProductLine: BackendProductLine,
): FrontendProductLine {
  return {
    id: backendProductLine.id,
    name: backendProductLine.name,
    productCategory: {
      name: backendProductLine.product_category,
    } as ProductCategory,
    brand: {
      id: backendProductLine.brand_fk,
      name: backendProductLine.brand_name,
      product_category_name: backendProductLine.product_category,
    },
  };
}

export function mapFrontendToBackendProductLine(
  frontendProductLine: FrontendProductLine,
): BackendProductLine {
  return {
    id: frontendProductLine.id,
    name: frontendProductLine.name,
    product_category: frontendProductLine.productCategory.name,
    brand_fk: frontendProductLine.brand.id,
    brand_name: frontendProductLine.brand.name,
  };
}
