import { Component } from "@angular/core";
import { NavigationEnd, Router, RouterOutlet } from "@angular/router";
import { SideMenuComponent } from "./side-menu/side-menu.component";
import { HttpClient, HttpClientModule } from "@angular/common/http";
import { CommonModule } from "@angular/common";
import { LoadingBarModule } from "@ngx-loading-bar/core";

@Component({
  selector: "app-root",
  imports: [
    RouterOutlet,
    SideMenuComponent,
    HttpClientModule,
    CommonModule,
    LoadingBarModule,
  ], // Import SideMenuComponent
  templateUrl: "./app.component.html",
})
export class AppComponent {
  title = "company-portal";
  showSideMenu: boolean = true;

  constructor(private router: Router) {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        // Check the current route and decide whether to show or hide the component
        this.checkRoute(event.urlAfterRedirects);
      }
    });
  }

  checkRoute(url: string) {
    // Set `showComponent` to false only for a specific route
    if (
      url.startsWith("/nopermission") ||
      url.startsWith("/login") ||
      url.startsWith("/password-reset")
    ) {
      this.showSideMenu = false;
    } else {
      this.showSideMenu = true;
    }
  }
}
