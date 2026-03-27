import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { LoadingBarService } from '@ngx-loading-bar/core';
import { Subscription } from 'rxjs';
import { ProductFormComponent } from '../product-components/components/product-form/product-form.component';
import { ProductFormData, ProductFormService } from '../product-components/services/product-form.service';
import { QuestionnaireSectionsComponent } from "./questionnaire-sections/questionnaire-sections.component";

@Component({
  selector: 'app-edit-product',
  imports: [
    CommonModule, ProductFormComponent, QuestionnaireSectionsComponent
  ],
  providers: [ProductFormService],
  templateUrl: './edit-product.component.html',
})
export class EditProductModelComponent implements OnInit, OnDestroy {
  productId?: number;
  loader;

  // Properties needed for questionnaire sections
  productID: number | null = null;
  brandID: number | null = null;
  productLineID: number | null = null;
  productCategoryID: string | null = null;

  private subscriptions: Subscription[] = [];

  constructor(
    private route: ActivatedRoute,
    private productFormService: ProductFormService,
    private loadingBar: LoadingBarService,
  ) {
    this.loader = this.loadingBar.useRef();
  }

  ngOnInit(): void {
    // Get product ID from route params
    this.subscriptions.push(
      this.route.queryParams.subscribe(params => {
        this.productId = params['productId'] ? parseInt(params['productId']) : undefined;
      })
    );

    // Subscribe to form data changes to update questionnaire section properties
    this.subscriptions.push(
      this.productFormService.formData$.subscribe((data: ProductFormData) => {
        this.productID = data.productID || null;
        this.brandID = data.brandID;
        this.productLineID = data.productLineID;
        this.productCategoryID = data.productCategoryID;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  get showQuestionnaireSections(): boolean {
    return !!(this.brandID && this.productID && this.productLineID && this.productCategoryID);
  }

  async onSubmit(): Promise<void> {
    try {
      this.loader.start();
      await this.productFormService.submitUpdate();
      this.loader.stop();
      // Reload data to refresh the form and questionnaire sections
      if (this.productId) {
        await this.productFormService.loadInitialData(this.productId);
      }
    } catch (error) {
      this.loader.stop();
      // Error is already handled by the service
    }
  }
}
