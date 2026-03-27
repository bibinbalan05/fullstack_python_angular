import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { Location } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { matHelpOutlineRound, matArrowBackRound, matHomeRound } from '@ng-icons/material-icons/round';

@Component({
  selector: 'app-not.found',
  imports: [
    RouterModule,
    NgIcon
  ],
  templateUrl: './not.found.component.html',
  providers: [
    provideIcons({ matHelpOutlineRound, matArrowBackRound, matHomeRound })
  ]
})
export class NotFoundComponent {
  // Inject the Location service in the constructor
  constructor(private location: Location) { }

  /**
   * Navigates back to the previous location in the browser history.
   */
  goBack(): void {
    this.location.back();
  }
}