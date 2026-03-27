import { ApplicationConfig, ErrorHandler, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import {
  provideHttpClient,
  withXsrfConfiguration,
  withInterceptors,
  withInterceptorsFromDi
} from '@angular/common/http';
import { GlobalErrorHandler } from './services/error-handling/global-error-handler';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideHttpClient(
      withInterceptorsFromDi(),
      withXsrfConfiguration({
        cookieName: 'csrftoken',
        headerName: 'X-CSRFToken',
      }),
      withInterceptors([
        (req, next) => {
          const cloned = req.clone({ withCredentials: true });
          return next(cloned);
        }
      ])
    ),
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
  ],
};
