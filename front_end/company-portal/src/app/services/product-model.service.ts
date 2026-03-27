import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";
import { FrontendProduct, FrontendProductLine} from "../models/product-entities.model";
import { AspectTotalScore } from "../models/aspect-total-score.model";
import { ProductCategory } from "../models/questionnaire.model";

@Injectable({
    providedIn: 'root'
})
export class FrontendProductService {
    private frontendProduct = new BehaviorSubject<FrontendProduct>({
        id: 0,
        name: '',
        ean: '',
        overallScore: 0,
        image: '',
        aspectScores: { } as AspectTotalScore[],
        productCategory: { } as ProductCategory,
        productLine: { } as FrontendProductLine,
        is_my_product: false,
    })
    frontendProduct$ = this.frontendProduct.asObservable()

    setEditProduct(frontendProduct: FrontendProduct) {
        this.frontendProduct.next(frontendProduct)
    }
}