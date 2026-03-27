import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import '@archr-se/score-card';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { matErrorRound } from '@ng-icons/material-icons/round';
import { Subscription, Observable, firstValueFrom } from 'rxjs';
import {
  ProductFormData,
  ProductFormService,
  ProductFormState,
} from '../../services/product-form.service';
import { ImageSelectorComponent } from '../image-selector/image-selector.component';

@Component({
  selector: 'app-product-form',
  imports: [CommonModule, FormsModule, NgIcon, ImageSelectorComponent],
  providers: [provideIcons({ matErrorRound })],
  templateUrl: "./product-form.component.html",
})
export class ProductFormComponent implements OnInit, OnDestroy {
  @Input() title: string = "Product Form";
  @Input() submitButtonText: string = "Submit";
  @Input() productId?: number;
  @Output() formSubmit = new EventEmitter<void>();

  formData: ProductFormData = {
    productName: "",
    eans: [{ ean: "", name: "", product_model: 0 }],
    productCategoryID: null,
    productLineID: null,
    brandID: null,
    image: "",
  };

  state: ProductFormState = {
    isLoading: false,
    errorMessage: null,
    productCategories: [],
    productLines: [],
    filteredProductLines: [],
    brands: [],
  };

  private subscriptions: Subscription[] = [];

  isProductAnswered$!: Observable<boolean>;
  showImageSelector = false;

  constructor(public productFormService: ProductFormService) {}

  onImageSelected(img: { name: string; url: string }): void {
    // Save both the preview URL and the storage name returned by the media API.
    this.productFormService.updateFormData({ image: img.url, imageName: img.name });
    this.showImageSelector = false;
  }

  ngOnInit(): void {
    this.isProductAnswered$ = this.productFormService.productAnsweredState$;

    this.subscriptions.push(
      this.productFormService.formData$.subscribe((data) => {
        this.formData = data;
      }),
    );

    this.subscriptions.push(
      this.productFormService.state$.subscribe((state) => {
        this.state = state;
      }),
    );

    this.productFormService.loadInitialData(this.productId);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  onProductNameChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.productFormService.updateFormData({ productName: target.value });
  }

  onImageChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    // If user types/pastes a URL manually, clear any previously stored storage name
    // so that the backend will receive either a relative path (if supplied) or
    // the component will try to parse the URL.
    this.productFormService.updateFormData({ image: target.value, imageName: null });
  }

  trackByIndex(index: number, item: any): number {
  return index;
}

onEanChange(index: number, field: "ean" | "name", event: Event): void {
  const target = event.target as HTMLInputElement;
  const updates = { [field]: target.value };
  this.productFormService.updateEan(index, updates);
}

  onSelectProductCategory(productCategoryID: string): void {
    this.productFormService.onSelectProductCategory(productCategoryID);
  }

  onSelectBrand(brandID: number): void {
    this.productFormService.onSelectBrand(brandID);
  }

  onSelectProductLine(productLineID: number): void {
    this.productFormService.onSelectProductLine(productLineID);
  }

  async toggleProductAnswered(): Promise<void> {
    const firstEan = this.formData.eans[0]?.ean;
    if (!firstEan) {
      console.warn("No EAN available, cannot update score");
      return;
    }

    try {
      const currentState = await firstValueFrom(this.isProductAnswered$);
      const newState = !currentState;

      if (newState) {
        await this.productFormService.setScoreAnswered(firstEan);
      } else {
        await this.productFormService.setScoreNA(firstEan);
      }

      // Update UI Score-Elemente
      this.formData.eans.forEach((eanItem) => {
        const scoreElement = document.querySelector<any>(
          `product-score[ean="${eanItem.ean}"]`,
        );
        if (scoreElement) {
          if (newState) {
            scoreElement.restoreScore();
          } else {
            scoreElement.setScoreNA();
          }
        }
      });
    } catch (error) {
      console.error("Failed to update score state:", error);
    }
  }

  addEan(): void {
    this.productFormService.addEan();
  }

  removeEan(index: number): void {
    this.productFormService.removeEan(index);
  }

  async onSubmit(event: Event): Promise<void> {
    event.preventDefault();
    this.formSubmit.emit();
  }
}
