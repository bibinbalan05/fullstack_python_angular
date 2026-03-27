import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import Papa from 'papaparse';

export interface UploadProduct {
  name: string;
  ean: string;
  productCategory: string;
  productLine: string;
  brand: string;
  image: string;
  isValid: boolean;
  isSelected: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ProductCsvService {

  private productsSubject = new BehaviorSubject<UploadProduct[]>([]);
  public products$: Observable<UploadProduct[]> = this.productsSubject.asObservable();

  constructor() { }

  setProducts(products: UploadProduct[]): void {
    this.productsSubject.next(products);
  }

  getProducts(): UploadProduct[] {
    return this.productsSubject.value;
  }
  
  validateProduct(product: UploadProduct): string[] {
      const missingFields: string[] = [];
      if (!product.ean) missingFields.push('EAN');
      if (!product.name) missingFields.push('Product Name');
      if (!product.productCategory) missingFields.push('Category');
      if (!product.productLine)  missingFields.push('Product Line');
      if (!product.brand) missingFields.push('Brand');
      return missingFields;
  }

  parseCsvFile(file: File): Promise<UploadProduct[]> {
    return new Promise((resolve, reject) => {
      if (!file || file.type !== 'text/csv') {
        reject(new Error('Invalid CSV file'));
        return;
      }

      Papa.parse(file, {
        header: true,          
        skipEmptyLines: true,
        complete: (results: Papa.ParseResult<any>) => {
          try {
            const data: any[] = results.data as any[];
            const products: UploadProduct[] = data.map(row => this.mapRowToProduct(row));
            resolve(products);
          } catch (error) {
            reject(error);
          }
        },
        error: (err: Error) => reject(err)
      });
    });
  }

  private mapRowToProduct(row: any): UploadProduct {
    const product: UploadProduct = {
      productCategory: row['ProductCategory'] ?? '',
      productLine: row['ProductLine'] ?? '',
      brand: row['Brand'] ?? '',
      name: row['Name'] ?? '',
      ean: row['EAN'] ?? '',
      image: row['ImageURL'] ?? '',
      isValid: false,
      isSelected: false
    };

    const missingFields = this.validateProduct(product);
    product.isValid = missingFields.length === 0;
    product.isSelected = product.isValid;

    return product;
  }
}
