export interface Questionnaire {
  id: number;
  entityType: string;
  aspect: string;
  questionnaireCategory: QuestionnaireCategory;
  questions: Question[];
}

export interface QuestionnaireCategory {
  name: string;
}

export interface ProductCategory {
  name: string;
  questionnaire_category?: string;
}

export interface ProductLine {
  id: number;
  name: string;
  product_category: string;
  brand_fk: number;
  brand_name: string;
}

export interface Question {
  id: number;
  questionText: string;
  purpose: string | null;
  maxScore: number;
  questionnaireId?: number;
  subAspect: string;
  options: Option[];
  isSingleChoice: boolean;
}

export interface Option {
  id: number;
  optionText: string;
  weight: number;
  definition?: string;
}

export interface Answer {
  id?: number;
  isTrue: boolean;
  isFalse: boolean;
  productEntityId?: number;
  answeredBy: number;
  option: number;
  source?: string | null;
  question?: number;
}

export interface Query {
  id?: number;
  question: number;
  retailUser?: number;
  isHandled?: boolean;
}
