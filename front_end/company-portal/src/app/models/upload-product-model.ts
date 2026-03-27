export interface UploadProduct {
    ean: string;
    name: string;
    productCategory: string;
    productLine: {
        name: string;
        brand: string;
        productCategory: string;
    };
    brand: {
        name: string;
        productCategory: string;
    };
    image?: string;
    isValid?: boolean;
    isSelected?: boolean;
    validationErrors?: string[];
}