import { Component } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../services/auth.service';
@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    imports: [CommonModule, FormsModule, RouterModule],
    providers: [AuthService]
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;

  constructor(private authService: AuthService, private router: Router) { }

  async onLogin() {
    this.isLoading = true;
    const loginData = { email: this.email, password: this.password };

    try {
      const response = await this.authService.login(loginData);

      if (response.isLoggedIn) {
        this.router.navigate(['/']); // Navigate to the dashboard
      } else {
        this.errorMessage = 'Invalid email or password. Please try again.';
      }
    } catch (err: any) {
      console.error('Error during login:', err);
      this.errorMessage = `${err?.error?.error ?? err?.error?.detail ?? err}`;
    } finally {
      this.isLoading = false;
    }
  }
  
}
