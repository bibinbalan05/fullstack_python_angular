import { Injectable } from '@angular/core';
import { Subject, BehaviorSubject } from 'rxjs';
import { UploadProduct } from '../models/upload-product-model';

@Injectable({
  providedIn: 'root'
})
export class ProductCsvService {
  private products = new BehaviorSubject<UploadProduct[]>([]);
  private selectedProducts = new BehaviorSubject<UploadProduct[]>([]);
  
  products$ = this.products.asObservable();
  selectedProducts$ = this.selectedProducts.asObservable();

  setProducts(products: UploadProduct[]) {
    console.log('Setting products in service:', products);
    const productsWithSelection = products.map(p => ({
        ...p,
        isSelected: p.isValid ?? false
    }));
    console.log('Products with selection:', productsWithSelection);
    this.products.next(productsWithSelection);
}

  updateSelection(products: UploadProduct[]) {
    this.selectedProducts.next(products.filter(p => p.isSelected));
  }

  validateProduct(product: UploadProduct): string[] {
    const missingFields: string[] = [];
    
    if (!product.ean) missingFields.push('EAN');
    if (!product.name) missingFields.push('Name');
    if (!product.productCategory) missingFields.push('Product Category');
    
    if (product.productLine) {
        if (!product.productLine.name) missingFields.push('Product Line Name');
        if (!product.productLine.brand) missingFields.push('Product Line Brand');
        if (!product.productLine.productCategory) missingFields.push('Product Line Category');
    }
    
    if (product.brand) {
        if (!product.brand.name) missingFields.push('Brand Name');
        if (!product.brand.productCategory) missingFields.push('Brand Category');
    }
    
    return missingFields;
}
}