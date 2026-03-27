import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { matInfoRound } from '@ng-icons/material-icons/round';
import { CreateProductModel, EAN } from '../models/product-entities.model';
import { combineLatest, forkJoin } from 'rxjs';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { ProductFormService, ProductFormState } from '../product-components/services/product-form.service';
import { ProductCsvService, UploadProduct } from '../services/product-csv.service';
import { ProductService } from '../services/product.service';


export interface UploadedProduct {   
  name: string;
  ean: string | number;
  productCategory: {
    label: string; 
    value: string | number; 
  };
  productLine: {
    label: string;
    value: string | number;
  };
  brand: {
    label: string;
    value: string | number;
  };
  isValid: boolean;
  isSelected: boolean;
}

@Component({
    selector: 'app-uploaded-products',
    templateUrl: './uploaded-products.component.html',
    standalone: true,
    imports: [
      CommonModule,
      FormsModule,
      NgIcon
    ],
    providers: [
      provideIcons({ matInfoRound })
    ]
  })
export class UploadedProductsComponent implements OnInit {
  uploadedProducts: UploadedProduct[] = [];
  successMessage = '';
  errorMessage = '';
  
  state: ProductFormState = {
      isLoading: false,
      errorMessage: null,
      productCategories: [],
      productLines: [],
      filteredProductLines: [],
      brands: []
    };
  private subscriptions: Subscription[] = [];

  constructor(
    private productCsvService: ProductCsvService,  
    private router: Router,
    private productFormService: ProductFormService,
    private productService: ProductService
  ) {}

  ngOnInit(): void {
    
  this.productFormService.loadInitialData();

  this.subscriptions.push(
    combineLatest([
      this.productFormService.state$,
      this.productCsvService.products$
    ]).subscribe(([state, products]) => {
      this.state = state;
      this.uploadedProducts = this.mapToUploadedProductModel(products, state);
    })
    );
  }

  getMissingFields(uploadedProduct: UploadedProduct): string[] {
     const missingFields: string[] = [];
      if (!uploadedProduct.ean.toString()) missingFields.push('EAN');
      if (!uploadedProduct.name) missingFields.push('Product Name');
      if (!uploadedProduct.productCategory.value) missingFields.push('Category');
      if (!uploadedProduct.productLine.value)  missingFields.push('Product Line');
      if (!uploadedProduct.brand.value) missingFields.push('Brand');
      return missingFields;
  }

  hasSelectedProducts(): boolean {
    return this.uploadedProducts.some(product => product.isSelected && product.isValid);
  }

  handleAddToMyProducts(): void {
    const selectedProducts = this.uploadedProducts.filter(
      p => p.isSelected && p.isValid
    );

    const requests = selectedProducts.map(product =>
      this.productService.addProductManually(this.mapToCreateModel(product))
    );

    forkJoin(requests).subscribe({
      next: results => {
         this.showToast('Products added successfully!');
          setTimeout(() => {
            this.router.navigate(['']);
          }, 3000);
      },
      error: err => {
        this.showToast('Failed to add some products.', true);
      }
    });
  }

  mapToCreateModel(product: UploadedProduct): CreateProductModel {
    return {
      name: product.name,
      eans: [
        {
          ean: product.ean.toString(),
          name: product.ean.toString(),
          product_model: 10
        }
      ],
      image: null,
      productCategoryID: product.productCategory.value.toString(),
      productLineID: product.productLine.value as number
    };
  }
  
  showToast(message: string, isError = false) {
    if (isError) {
      this.errorMessage = message;
      setTimeout(() => (this.errorMessage = ''), 3000);
    } else {
      this.successMessage = message;
      setTimeout(() => (this.successMessage = ''), 3000);
    }
  }
  validate(message: string, isError = false) {
    if (isError) {
      this.errorMessage = message;
      setTimeout(() => (this.errorMessage = ''), 3000);
    } else {
      this.successMessage = message;
      setTimeout(() => (this.successMessage = ''), 3000);
    }
  }
 mapToUploadedProductModel(products: UploadProduct[],state: ProductFormState): UploadedProduct[] {
    return products.map(product => {
      const category = state.productCategories.find(
        c => c.name === product.productCategory
      );
      const productLine = state.productLines.find(
        pl => pl.name === product.productLine
      );
      const brand = state.brands.find(
        b => b.name === product.brand
      );

      const mapped = {
        name: product.name ?? '',
        ean: product.ean ?? '',
        productCategory: {
          label: category?.name ?? product.productCategory ?? '',
          value: category?.name ?? 0
        },
        productLine: {
          label: productLine?.name ?? product.productLine ?? '',
          value: productLine?.id ?? 0
        },
        brand: {
          label: brand?.name ?? product.brand ?? '',
          value: brand?.id ?? 0
        },
        isSelected: true,
        isValid: true 
      };

      if (
        !mapped.name ||
        !mapped.ean ||
        !mapped.productCategory.label ||
        !mapped.productCategory.value ||
        !mapped.productLine.label ||
        !mapped.productLine.value ||
        !mapped.brand.label ||
        !mapped.brand.value
      ) {
        mapped.isValid = false;
        mapped.isSelected = false;
      }

      return mapped;
    });
  }
}