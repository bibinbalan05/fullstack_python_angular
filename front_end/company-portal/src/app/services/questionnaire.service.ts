import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { HttpService } from "./http.service";
import {
  Answer,
  ProductCategory,
  Questionnaire,
} from "../models/questionnaire.model";
import { HttpClient } from "@angular/common/http";

@Injectable({
  providedIn: "root",
})
export class QuestionnaireService extends HttpService {
  constructor(http: HttpClient) {
    super(http);
  }

  getQuestionnaireBrand(
    productCategory: ProductCategory,
  ): Observable<Questionnaire[]> {
    return this.get<Questionnaire[]>(
      `/models/questionnaire/brand/${productCategory.name}`,
    );
  }

  getQuestionnaireProductLine(
    productCategory: ProductCategory,
  ): Observable<Questionnaire[]> {
    return this.get<Questionnaire[]>(
      `/models/questionnaire/productline/${productCategory.name}`,
    );
  }

  getQuestionnaireProduct(
    productCategory: ProductCategory,
  ): Observable<Questionnaire[]> {
    return this.get<Questionnaire[]>(
      `/models/questionnaire/product/${productCategory.name}`,
    );
  }

  getEntityQuestionnaires(
    entityId: number,
    productCategory?: string,
  ): Observable<Questionnaire[]> {
    let params = {};
    if (productCategory) {
      params = { product_category: productCategory };
    }
    return this.get<Questionnaire[]>(
      `/models/questionnaire-entity/${entityId}/`,
      { params },
    );
  }

  addAnswers(answers: Answer[], productEntity: number): Observable<Answer[]> {
    return this.post<Answer[]>(`/models/answer/${productEntity}`, { answers });
  }

  updateAnswer(answer: Answer, productEntity: number): Observable<Answer> {
    return this.put<Answer>(
      `/models/answer/${productEntity}/${answer.id}`,
      answer,
    );
  }

  getAnswers(productEntity: number): Observable<Answer[]> {
    return this.get<Answer[]>(`/models/answer/${productEntity}`);
  }

  getAnswerableModels(productLineId: number): Observable<any[]> {
    return this.get<any[]>(
      `/models/productlines/${productLineId}/answerable-models/`,
    );
  }

  copyAnswersFromModel(sourceModelId: number, targetModelId: number): Observable<any> {
    return this.post<any>(`/models/answers/copy/`, {
      source_model_id: sourceModelId,
      target_model_id: targetModelId,
    });
  }
}
