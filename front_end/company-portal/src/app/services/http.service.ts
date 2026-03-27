import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpContext,
  HttpHeaders,
  HttpParams,
} from "@angular/common/http";
import { environment } from "../../environments/environment";
import { Observable } from "rxjs";
import { ɵparseCookieValue } from "@angular/common";

@Injectable({
  providedIn: "root",
})
export class HttpService {
  protected baseUrl = environment.apiUrl + "/api";

  constructor(protected http: HttpClient) {}

  get<T>(
    path: string,
    options?: {
      headers?: HttpHeaders | Record<string, string | string[]>;
      context?: HttpContext;
      observe?: "body";
      params?:
        | HttpParams
        | Record<
            string,
            string | number | boolean | ReadonlyArray<string | number | boolean>
          >;
      reportProgress?: boolean;
      responseType?: "json";
      withCredentials?: boolean;
      transferCache?:
        | {
            includeHeaders?: string[];
          }
        | boolean;
    },
  ): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${path}`, {
      ...options,
      withCredentials: true,
      headers: {
        "X-CSRFToken": ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
      },
    });
  }

  post<T>(
    path: string,
    data: any,
    options?: {
      headers?: HttpHeaders | Record<string, string | string[]>;
      context?: HttpContext;
      observe?: "body";
      params?:
        | HttpParams
        | Record<
            string,
            string | number | boolean | ReadonlyArray<string | number | boolean>
          >;
      reportProgress?: boolean;
      responseType?: "json";
      withCredentials?: boolean;
      transferCache?:
        | {
            includeHeaders?: string[];
          }
        | boolean;
    },
  ): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, data, {
      ...options,
      withCredentials: true,
      headers: {
        "X-CSRFToken": ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
      },
    });
  }

  put<T>(
    path: string,
    data: any,
    options?: {
      headers?: HttpHeaders | Record<string, string | string[]>;
      context?: HttpContext;
      observe?: "body";
      params?:
        | HttpParams
        | Record<
            string,
            string | number | boolean | ReadonlyArray<string | number | boolean>
          >;
      reportProgress?: boolean;
      responseType?: "json";
      withCredentials?: boolean;
      transferCache?:
        | {
            includeHeaders?: string[];
          }
        | boolean;
    },
  ): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, data, {
      ...options,
      withCredentials: true,
      headers: {
        "X-CSRFToken": ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
      },
    });
  }

  delete<T>(
    path: string,
    options?: {
      headers?: HttpHeaders | Record<string, string | string[]>;
      context?: HttpContext;
      observe?: "body";
      params?:
        | HttpParams
        | Record<
            string,
            string | number | boolean | ReadonlyArray<string | number | boolean>
          >;
      reportProgress?: boolean;
      responseType?: "json";
      withCredentials?: boolean;
      body?: any | null;
    },
  ): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`, {
      ...options,
      withCredentials: true,
      headers: {
        "X-CSRFToken": ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
      },
    });
  }

  fetchCsrfToken(callback?: () => void): void {
    this.get(`/csrf/`, { withCredentials: true }).subscribe({
      next: (value) => {
        console.log("CSRF cookie potentially set/refreshed.", value);
        if (callback) {
          callback();
        }
      },
      error: (err) => {
        console.error("Failed to fetch CSRF token:", err);
      },
    });
  }
}
