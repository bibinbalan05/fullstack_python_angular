import { bootstrapApplication } from "@angular/platform-browser";
import {
  provideRouter,
  withDebugTracing,
  withRouterConfig,
} from "@angular/router";
import { AppComponent } from "./app/app.component";
import { HomeComponent } from "./app/home/home.component";
import { UploadedProductsComponent } from "./app/uploaded-products/uploaded-products.component";
import { LoginComponent } from "./app/login/login.component";
import { AuthGuard } from "./app/services/authguard.service";
import { HttpClientModule } from "@angular/common/http";
import { Component, importProvidersFrom } from "@angular/core";
import { NotFoundComponent } from "./app/not.found/not.found.component";
import { CreateProductModelComponent } from "./app/create-product/create-product.component";
import { EditProductModelComponent } from "./app/edit-product/edit-product.component";
import { PasswordResetComponent } from "./app/password-reset/password-reset.component";
import { NoAuthGuard } from "./app/services/noauthguard.service";
import { provideLoadingBar } from "@ngx-loading-bar/core";

const routes = [
  { path: "", component: HomeComponent, canActivate: [AuthGuard] }, // Default route for Home
  {
    path: "uploaded-products",
    component: UploadedProductsComponent,
    canActivate: [AuthGuard],
  },
  {
    path: "create-product",
    component: CreateProductModelComponent,
    canActivate: [AuthGuard],
  },
  {
    path: "edit-product",
    component: EditProductModelComponent,
    canActivate: [AuthGuard],
  },
  { path: "login", component: LoginComponent, canActivate: [NoAuthGuard] },
  { path: "password-reset", component: PasswordResetComponent },
  { path: "password-reset/:uid/:token", component: PasswordResetComponent },
  { path: "**", component: NotFoundComponent },
];

bootstrapApplication(AppComponent, {
  providers: [
    importProvidersFrom(HttpClientModule),
    provideRouter(
      routes,
      withDebugTracing(), // Optional: enables detailed tracing of route events
      withRouterConfig({ paramsInheritanceStrategy: "always" }), // Example of extra router configuration
    ),
    provideLoadingBar({ latencyThreshold: 0 }),
  ],
});
