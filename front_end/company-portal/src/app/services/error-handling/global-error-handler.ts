import { ErrorHandler, Injectable, NgZone } from "@angular/core";
import { MatSnackBar } from "@angular/material/snack-bar";

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
    constructor(private snackBar: MatSnackBar, private zone: NgZone) {}

    handleError(error: any): void {
        this.snackBar.open('Error: ' + error.message, 'Close', {
            duration: 3000,
        })
    }
}