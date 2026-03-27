import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
// HttpClient removed, HttpErrorResponse is still needed for error handling
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { finalize } from 'rxjs/operators';

// Import NgIcons stuff
import { NgIconComponent, provideIcons } from '@ng-icons/core';

// Import payload types (assuming they are defined in user models)
import { PasswordResetConfirmPayload, PasswordResetRequestPayload } from '../models/user'; // Adjust path if needed
import { matCheckCircleRound } from '@ng-icons/material-icons/round';
import { AuthService } from '../services/auth.service';

type ResetStage = 'request' | 'request-sent' | 'confirm' | 'confirm-error' | 'complete' | 'error';

@Component({
  selector: 'app-password-reset',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule,
    NgIconComponent
  ],
  templateUrl: './password-reset.component.html',
  viewProviders: [provideIcons({ matCheckCircleRound })],
})
export class PasswordResetComponent implements OnInit {
  // --- Dependencies ---
  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private authService = inject(AuthService);

  // --- State ---
  stage: ResetStage = 'request';
  isLoading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  // --- Forms ---
  requestForm!: FormGroup;
  confirmForm!: FormGroup;

  // --- URL Params ---
  uid: string | null = null;
  token: string | null = null;

  ngOnInit(): void {
    this.initializeForms();

    this.route.paramMap.subscribe(params => {
      this.uid = params.get('uid');
      this.token = params.get('token');

      if (this.uid && this.token) {
        this.stage = 'confirm';
      } else {
        this.stage = 'request';
      }
    });
  }

  private initializeForms(): void {
    this.requestForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });

    this.confirmForm = this.fb.group({
      new_password1: ['', [Validators.required, Validators.minLength(8)]],
      new_password2: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });
  }

  private passwordMatchValidator(form: FormGroup) {
    const password = form.get('new_password1')?.value;
    const confirmPassword = form.get('new_password2')?.value;
    return password === confirmPassword ? null : { passwordMismatch: true };
  }

  onRequestSubmit(): void {
    if (this.requestForm.invalid || this.isLoading) {
      return;
    }
    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    const payload: PasswordResetRequestPayload = { // Use the type
      email: this.requestForm.value.email
    };

    this.authService.requestPasswordReset(payload)
      .pipe(finalize(() => this.isLoading = false))
      .subscribe({
        next: () => {
          this.stage = 'request-sent';
          this.requestForm.reset();
        },
        error: (err: HttpErrorResponse) => {
          this.errorMessage = this.extractErrorMessage(err, 'Failed to send reset email. Please try again.');
        }
      });
  }

  onConfirmSubmit(): void {
    if (this.confirmForm.invalid || this.isLoading || !this.uid || !this.token) {
      if (this.confirmForm.errors?.['passwordMismatch']) {
        this.errorMessage = 'Passwords do not match.';
      } else if (this.confirmForm.controls['new_password1']?.errors || this.confirmForm.controls['new_password2']?.errors) {
        this.errorMessage = 'Please fill in both password fields correctly (min 8 characters).';
      } else {
        this.errorMessage = 'An unexpected validation error occurred.';
      }
      return;
    }
    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    // Ensure uid and token are definitely strings here before creating payload
    if (!this.uid || !this.token) {
      this.errorMessage = 'Missing required information from URL.';
      this.isLoading = false;
      return;
    }

    const payload: PasswordResetConfirmPayload = { // Use the type
      uid: this.uid,
      token: this.token,
      new_password1: this.confirmForm.value.new_password1,
      new_password2: this.confirmForm.value.new_password2
    };

    this.authService.confirmPasswordReset(payload)
      .pipe(finalize(() => this.isLoading = false))
      .subscribe({
        next: () => {
          this.stage = 'complete';
        },
        error: (err: HttpErrorResponse) => {
          if (err.status === 400 && err.error?.token) {
            this.errorMessage = 'This password reset link is invalid or has expired.';
          } else if (err.status === 400 && err.error?.password) {
            this.errorMessage = `Password error: ${err.error.password.join(', ')}`;
          } else if (err.status === 400 && err.error?.detail) {
            this.errorMessage = err.error.detail;
          } else {
            this.errorMessage = this.extractErrorMessage(err, 'Failed to reset password. The link may be invalid or expired.');
          }
          this.stage = 'confirm';
        }
      });
  }

  // --- Utility ---
  private extractErrorMessage(error: HttpErrorResponse, defaultMessage: string): string {
    if (error.error && typeof error.error === 'object') {
      return error.error.detail || error.error.message || error.error.error || JSON.stringify(error.error) || defaultMessage;
    } else if (error.error && typeof error.error === 'string') {
      return error.error;
    }
    return defaultMessage;
  }

  // Method to navigate back to request stage or login
  navigateTo(path: string): void {
    if (path === 'request') {
      this.stage = 'request';
      this.errorMessage = null;
      this.successMessage = null;
      this.uid = null;
      this.token = null;
      this.confirmForm.reset();
      this.router.navigate(['/request-reset']);
    } else {
      this.router.navigate([path]);
    }
  }
}