import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { HttpService } from "./http.service";
import { Suggestion } from "../models/suggestion";
import { Query } from "../models/questionnaire.model";
import { HttpClient, HttpParams } from "@angular/common/http";
import { environment } from '../../environments/environment';


@Injectable({
  providedIn: "root",
})
export class SuggestionService extends HttpService {
  private apiUrl = `${environment.apiUrl}/queries`; 
  constructor(http: HttpClient) {
    super(http);
  }

  addSuggestion(suggestion: Suggestion): Observable<Suggestion> {
    return this.post<Suggestion>(`/models/suggestion/`, { suggestion });
  }

  raiseConcern(questionId: number, suggestionText?: string): Observable<Query> {
    return this.post<Query>(`/models/query/`, {
      question: questionId,
      suggestion_text: suggestionText,
    });
  }

  getQueries(productEntityId: number): Observable<Query[]> {
    return this.get<Query[]>(`/models/query/`, {
      params: { product_entity: productEntityId },
    });
  }

  /**
   * Retract a concern previously raised by the current user for the given question.
   * Sends a DELETE to `/models/query/` with body { question }
   */
  retractConcern(questionId: number): Observable<any> {
    return this.delete<any>(`/models/query/`, { body: { question: questionId } });
  }

  /**
   * Dismiss a concern (mark it handled). Requires an authorized user on the backend.
   */
  dismissConcern(concernId: number): Observable<any> {
    return this.put<any>(`/models/query/${concernId}/`, { is_handled: true });
  }

  /**
   * Send AI prediction feedback to the backend for logging.
   * Expects an object with fields matching the backend serializer (productEntityId, optionId, predictedValue, correctedValue, predictedOptionId, modelName, userId)
   */
  addAIFeedback(feedback: any): Observable<any> {
    return this.post<any>(`/models/ai-feedback/`, { feedback });
  }
}
