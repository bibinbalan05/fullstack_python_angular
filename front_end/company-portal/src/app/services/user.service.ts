import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";
import { Company } from "../models/company";
import { LoginResponse } from "../models/user";

@Injectable({
  providedIn: "root",
})
export class UserService {
  private storageKey = "currentUser";
  private isLoggedInSubject = new BehaviorSubject<boolean>(false);

  isLoggedIn$ = this.isLoggedInSubject.asObservable();

  constructor() {
    const user = this.getCurrentUser();
    if (user) {
      this.isLoggedInSubject.next(true);
    } else {
      this.isLoggedInSubject.next(false);
    }
  }

  getCurrentUser(): LoginResponse | null {
    const user = localStorage.getItem(this.storageKey);

    // update isLoggedIn state on each get
    // as the state can get out of sync if the user logged out on an other page
    if (user) {
      this.isLoggedInSubject.next(true);
    } else {
      this.isLoggedInSubject.next(false);
    }

    const parsed = user ? JSON.parse(user) : null;

    // If the stored user is missing the new permission fields, refresh in background
    try {
      const missingCanAnswer = parsed && parsed.user && parsed.user.canAnswerQuestions === undefined;
      const missingRoleName = parsed && parsed.user && parsed.user.profile && parsed.user.profile.roleName === undefined;

      if ((missingCanAnswer || missingRoleName) && typeof fetch === 'function') {
        // Background refresh; do not block. Update localStorage when response arrives.
        fetch('/login/', { credentials: 'include' })
          .then((resp) => resp.json())
          .then((data) => {
            if (data && data.isLoggedIn) {
              try {
                this.setCurrentUser(data as LoginResponse);
              } catch (e) {
                // ignore
              }
            }
          })
          .catch(() => {
            // ignore network errors
          });
      }
    } catch (e) {
      // ignore any errors here
    }

    return parsed;
  }

  setCurrentUser(user: LoginResponse) {
    localStorage.setItem(this.storageKey, JSON.stringify(user));
    this.isLoggedInSubject.next(true);
  }

  removeCurrentUser() {
    localStorage.removeItem(this.storageKey);
    this.isLoggedInSubject.next(false);
  }

  isLoggedIn(): boolean {
    const user = this.getCurrentUser();

    if (!user) {
      this.isLoggedInSubject.next(false);
      return false;
    }

    if (user && user.session_expiry) {
      const expiryDate = new Date(user.session_expiry);
      if (expiryDate < new Date()) {
        this.removeCurrentUser();
        this.isLoggedInSubject.next(false);
        return false;
      }
    }

    this.isLoggedInSubject.next(true);
    return true;
  }

  getCurrentCompany(): Company {
    const user = this.getCurrentUser();
    const company = user?.user.profile.company;

    if (company) {
      return company;
    } else {
      throw new Error("Company is undefined");
    }
  }
}
