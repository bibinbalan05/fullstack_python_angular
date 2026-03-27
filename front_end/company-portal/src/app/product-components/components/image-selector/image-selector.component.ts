import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MediaService, MediaImage } from '../../services/media.service';
import { HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-image-selector',
  templateUrl: './image-selector.component.html',
  standalone: true,
  imports: [CommonModule]
})
export class ImageSelectorComponent {
  images: MediaImage[] = [];
  isLoading = false;
  uploading = false;
  uploadProgress = 0;
  uploadError: string | null = null;
  successMessage: string | null = null;
  @Output() select = new EventEmitter<MediaImage>();

  constructor(private mediaService: MediaService) {
    this.reload();
  }

  reload(): void {
    this.isLoading = true;
    this.mediaService.listImages().subscribe({
      next: data => this.images = data.images || [],
      error: err => {
        console.error('Failed loading images', err);
        this.images = [];
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  choose(img: MediaImage): void {
    this.select.emit(img);
  }

  onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    this.uploading = true;
    this.uploadProgress = 0;
    this.uploadError = null;
    this.successMessage = null;

    this.mediaService.uploadImage(file).subscribe({
      next: (event: any) => {
        if (event.type === HttpEventType.UploadProgress) {
          if (event.total) this.uploadProgress = Math.round((100 * event.loaded) / event.total);
        } else if (event.type === HttpEventType.Response) {
          const body = event.body || {};
          this.successMessage = 'Upload successful';
          // If API returns the created image record, auto-select it
          if (body && body.url) {
            this.select.emit({ name: body.name || file.name, url: body.url });
          } else {
            // Refresh after small delay for consistency
            setTimeout(() => this.reload(), 300);
          }
        }
      },
      error: (err) => {
        console.error('Upload failed', err);
        this.uploadError = err?.error?.detail || 'Upload failed';
        this.uploading = false;
      },
      complete: () => {
        setTimeout(() => {
          this.successMessage = null;
        }, 3000); // Clear message after 3 seconds
        this.uploading = false;
      }
    });
  }
}
