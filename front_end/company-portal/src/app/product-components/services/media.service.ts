import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface MediaImage {
  name: string;
  url: string;
}

@Injectable({ providedIn: 'root' })
export class MediaService {
  constructor(private http: HttpClient) {}

  listImages(): Observable<{ images: MediaImage[] }> {
    return this.http.get<{ images: MediaImage[] }>(`/api/media/images/`);
  }

  // Returns an HttpEvent stream so callers can track progress
  uploadImage(file: File): Observable<HttpEvent<any>> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    // Add CSRF token header so Django's CSRF middleware accepts the POST when using session auth.
    const csrf = this.getCookie('csrftoken') || this.getCookie('CSRF-TOKEN') || '';
    const headers = new HttpHeaders({ 'X-CSRFToken': csrf });
    return this.http.post(`/api/media/images/`, fd, { reportProgress: true, observe: 'events' as const, headers, withCredentials: true });
  }

  // Helper to read a cookie by name (simple parser)
  private getCookie(name: string): string | null {
    if (typeof document === 'undefined' || !document.cookie) return null;
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop() as string) : null;
  }
}
