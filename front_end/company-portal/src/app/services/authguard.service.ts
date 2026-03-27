import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { UserService } from './user.service';
import { ɵparseCookieValue } from '@angular/common';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private router: Router, private userService: UserService) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot,
  ): boolean | UrlTree {
    const isLoggedIn = this.userService.isLoggedIn()
    // console.debug("[AUTHGUARD] isLoggedIn", isLoggedIn)
    if (isLoggedIn) {
      return true; // User is logged in, allow access
    } else {
      this.router.navigate(['/login']);
      return false;
    }
  }
}