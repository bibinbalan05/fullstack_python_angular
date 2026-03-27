import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { Router } from "@angular/router";
import { HttpService } from "./http.service";
import { UserService } from "./user.service";
import {
  CheckRegisterToken,
  LoginRequest,
  LoginResponse,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
} from "../models/user";
import { ɵparseCookieValue } from "@angular/common";
import { HttpClient } from "@angular/common/http";

@Injectable({
  providedIn: "root",
})
export class AuthService extends HttpService {
  constructor(
    http: HttpClient,
    private router: Router,
    private userService: UserService,
  ) {
    super(http);
  }

  login(loginData: LoginRequest): Promise<LoginResponse> {
    return new Promise((resolve, reject) => {
      this.post<LoginResponse>(`/login/`, loginData, {
        withCredentials: true,
      }).subscribe({
        next: (response: LoginResponse) => {
          if (response.isLoggedIn) {
            this.userService.setCurrentUser(response);
          }
          resolve(response);
        },
        error: (error) => reject(error),
      });
    });
  }

  checkLoginStatus(): Observable<any> {
    return this.get(`/login/`, { withCredentials: true });
  }

  async logout() {
    await new Promise<boolean>((resolve, reject) => {
      this.fetchCsrfToken(() => {
        this.post(
          `/logout/`,
          {},
          {
            withCredentials: true,
            headers: {
              "X-CSRFToken":
                ɵparseCookieValue(document.cookie, "csrftoken") ?? "",
            },
          },
        ).subscribe({
          next: () => {
            resolve(true);
          },
          error: (error) => {
            console.error("Logout failed:", error);
            resolve(false);
          },
        });
      });
    }).then((_) => {
      this.userService.removeCurrentUser();
      this.router.navigate(["/login"]);
    });
  }

  requestPasswordReset(payload: PasswordResetRequestPayload): Observable<any> {
    return this.post<any>("/password-reset/request/", payload);
  }

  confirmPasswordReset(payload: PasswordResetConfirmPayload): Observable<any> {
    return this.post<any>("/password-reset/confirm/", payload);
  }
}
