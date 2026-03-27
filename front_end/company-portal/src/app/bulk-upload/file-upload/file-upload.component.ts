import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ProductCsvService, UploadProduct } from '../../services/product-csv.service';

@Component({
  selector: 'app-file-upload',
  imports: [CommonModule],  
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.css']
})
export class FileUploadComponent {

  error: string | null = null;
  file: File | null = null;
  fileName: string | null = null;
  isBulkUploadEnabled = false; 

  constructor(
    private productCsvService: ProductCsvService,
    private router: Router
  ) {}
  
  ngOnInit(): void {
    this.error= null;
    this.file=null;
    this.fileName=null;
  }

  onFileSelected(event: Event): void {
    this.error = null; 
    const input = event.target as HTMLInputElement;
    this.file = input.files?.[0] || null;

    if (this.file) {
      this.fileName = this.file.name;
      this.isBulkUploadEnabled = true;
    } else {
      this.fileName = null;
      this.error = 'No file selected. Please choose a CSV file.';
    }
  }

  async onUpload(): Promise<void> {
    if (!this.file) {
      this.error = 'Please select a file before uploading.';
      return;
    }

    try {
      const products = await this.productCsvService.parseCsvFile(this.file);

      if (!products || products.length === 0) {
        this.error = 'CSV file seems empty or invalid.';
        return;
      }

      this.productCsvService.setProducts(products);
      this.router.navigate(['/uploaded-products']);
    } catch (e) {
      this.error = 'Failed to process CSV file.';
    }
  }
}
