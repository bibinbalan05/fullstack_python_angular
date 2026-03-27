import { Injectable } from '@angular/core';
import { CanActivate } from '@angular/router';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { UserService } from './user.service';

@Injectable({
  providedIn: 'root',
})
export class NoAuthGuard implements CanActivate {
  constructor(private userService: UserService) { }

  canActivate(): Observable<boolean> {

    // only allow to login if logged out
    return this.userService.isLoggedIn$.pipe(
      map((isLoggedIn) => {
        if (isLoggedIn) {
          return false;
        } else {
          return true;
        }
      })
    )
  }
}
