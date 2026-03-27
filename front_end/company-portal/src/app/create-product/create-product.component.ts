import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { LoadingBarService } from '@ngx-loading-bar/core';
import { ProductFormComponent } from '../product-components/components/product-form/product-form.component';
import { ProductFormService } from '../product-components/services/product-form.service';

@Component({
  selector: 'app-create-product',
  imports: [
    CommonModule, ProductFormComponent
  ],
  providers: [ProductFormService],
  templateUrl: './create-product.component.html',
})
export class CreateProductModelComponent {
  loader;

  constructor(
    private router: Router,
    private productFormService: ProductFormService,
    private loadingBar: LoadingBarService,
  ) {
    this.loader = this.loadingBar.useRef();
  }

  async onSubmit(): Promise<void> {
    try {
      this.loader.start();
      await this.productFormService.submitCreate();
      this.loader.stop();
      this.router.navigate(['/']);
    } catch (error) {
      this.loader.stop();
      // Error is already handled by the service
    }
  }
}
