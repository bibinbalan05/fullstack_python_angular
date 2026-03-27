import { Component, Input } from "@angular/core";
import * as bibtexParse from "bibtex-parse-js";
import {
  Questionnaire,
  Option,
  Answer,
  ProductCategory,
  Question,
} from "../../models/questionnaire.model";
import { UserService } from "../../services/user.service";
import { firstValueFrom } from "rxjs";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { NgIcon, provideIcons } from "@ng-icons/core";
import {
  matCloseRound,
  matErrorRound,
  matAutoAwesomeRound,
  matInfoRound,
  matLinkRound,
} from "@ng-icons/material-icons/round";
import { matInfoOutline } from "@ng-icons/material-icons/outline";
import { matHelpOutlineOutline } from "@ng-icons/material-icons/outline";
import { QuestionnaireService } from "../../services/questionnaire.service";
import { ProductService } from "../../services/product.service";
import { SuggestionService } from "../../services/suggestion.service";

@Component({
  selector: "app-questionnaire-sections",
  imports: [CommonModule, FormsModule, NgIcon],
  templateUrl: "./questionnaire-sections.component.html",
  providers: [
    provideIcons({
      matErrorRound,
      matCloseRound,
      matInfoOutline,
      matInfoRound,
      matLinkRound,
      matHelpOutlineOutline,
      matAutoAwesomeRound,
    }),
  ],
})
export class QuestionnaireSectionsComponent {
  // Returns the selected option id for a single-choice question
  getSelectedOptionId(question: any): number | null {
    for (const opt of question.options) {
      const ans = this.answers.find((a) => a.option === opt.id);
      if (ans && (ans.isTrue || ans.isFalse)) {
        return opt.id;
      }
    }
    return null;
  }
  // Display all BibTeX fields as key-value pairs
  formatBibtex(source: string): string {
    if (!source || !source.trim().startsWith("@")) return source;
    try {
      const entries = bibtexParse.toJSON(source);
      if (!entries.length) return source;
      const entry = entries[0].entryTags || {};
      const fields = Object.entries(entry)
        .map(([key, value]) => `${key}: ${value}`)
        .join("; ");
      return fields || source;
    } catch (e) {
      return source;
    }
  }

  showSourceDialog: boolean = false;
  sourceDialogOption: Option | null = null;
  sourceDialogValue: string = "";
  @Input() productCategory!: ProductCategory;
  @Input() brandId: number = 0;
  @Input() productLineId: number = 0;
  @Input() productId: number = 0;

  brandQuestionnaires: Questionnaire[] = [];
  productLineQuestionnaires: Questionnaire[] = [];
  productQuestionnaires: Questionnaire[] = [];

  brandIsActive: boolean = true;
  productLineIsActive: boolean = false;
  productIsActive: boolean = false;
  aspectName: string = "";

  selectedFiles: File[] = [];

  answers: Answer[] = [];
  concerns: any[] = []; // To store full concern objects
  queries: Set<number> = new Set(); // Keep this for quick lookups in hasConcern()
  pendingAIAnswers: Map<
    number,
    { isTrue: boolean; isFalse: boolean; source?: string }
  > = new Map();
  isLoading = false;
  errorMessage: string | null = null;
  loadingQuestionnaires = false;
  uploadingFile = false;
  concernsForSelectedQuestion: any[] = []; // To hold the list of concerns for the modal

  // Properties for prefill modal
  showPrefillModal = false;
  availableSourceModels: any[] = [];
  selectedSourceModelId: number | null = null;
  isCopyingAnswers = false;

  // Properties for the concern suggestion modal
  showConcernModal = false;
  selectedQuestionForConcern: Question | null = null;
  concernSuggestionText: string = "";

  openSourceDialog(option: Option) {
    this.sourceDialogOption = option;
    this.sourceDialogValue = this.getAnswerSource(option);
    this.showSourceDialog = true;
  }

  closeSourceDialog() {
    this.showSourceDialog = false;
    this.sourceDialogOption = null;
    this.sourceDialogValue = "";
  }

  ensureBibtex(source: string): string {
    if (!source || !source.trim()) return "";
    const trimmed = source.trim();
    if (trimmed.startsWith("@")) return source;

    const safeContent = source.replace(/}/g, '\\}');
    return `@misc{manual_entry,\n  note = {${safeContent}}\n}`;
  }

  async saveSourceDialog() {
    if (this.sourceDialogOption) {
      const answer = this.answers.find(
        (ans) => ans.option === this.sourceDialogOption!.id,
      );
      if (answer) {
        answer.source = this.ensureBibtex(this.sourceDialogValue);
        const success = await this.submitAnswer(answer);
        if (!success) {
          return;
        }
      }
    }
    this.closeSourceDialog();
  }

  constructor(
    private userService: UserService,
    private questionnaireService: QuestionnaireService,
    private productService: ProductService,
    private suggestionService: SuggestionService
  ) { }

  clearError() {
    this.errorMessage = null;
  }

  ngOnInit() {
    if (this.activeEntityId) {
      this.loadAnswers();
      this.loadQuestionnaires();
      this.loadQueries();
    } else {
      console.warn("Skipping loadAnswers: No valid active entity ID.");
    }
  }

  get activeEntityId(): number {
    if (this.productIsActive && this.productId) return this.productId;
    if (this.productLineIsActive && this.productLineId)
      return this.productLineId;
    if (this.brandIsActive && this.brandId) return this.brandId;

    console.warn("No valid active entity found.");
    return 0; // Consider handling this case properly
  }

  private async loadQuestionnaires() {
    this.loadingQuestionnaires = true;
    try {
      // Load questionnaires for all available entities in parallel
      const requests = [];

      if (this.brandId) {
        console.log(
          `Loading brand questionnaires for brandId=${this.brandId} with productCategory=${this.productCategory?.name}`,
        );

        // First try loading without filter to see if any questionnaires exist at all
        firstValueFrom(this.questionnaireService.getEntityQuestionnaires(this.brandId))
          .then((allQuestionnaires) => {
            console.log(
              `All questionnaires for brand ${this.brandId} without filter:`,
              allQuestionnaires,
            );
          })
          .catch((error) => {
            console.error(
              "Error loading unfiltered brand questionnaires:",
              error,
            );
          });

        // Now try with the filter as before
        requests.push(
          firstValueFrom(
            this.questionnaireService.getEntityQuestionnaires(
              this.brandId,
              this.productCategory?.name,
            ),
          )
            .then((questionnaires) => {
              console.log(
                `Filtered questionnaires received for brand ${this.brandId}:`,
                questionnaires,
              );
              this.brandQuestionnaires = questionnaires;
            })
            .catch((error) => {
              console.error("Error loading brand questionnaires:", error);
              this.brandQuestionnaires = [];
            }),
        );
      }

      if (this.productLineId) {
        requests.push(
          firstValueFrom(
            this.questionnaireService.getEntityQuestionnaires(this.productLineId),
          )
            .then(
              (questionnaires) =>
                (this.productLineQuestionnaires = questionnaires),
            )
            .catch((error) => {
              console.error(
                "Error loading product line questionnaires:",
                error,
              );
              this.productLineQuestionnaires = [];
            }),
        );
      }

      if (this.productId) {
        requests.push(
          firstValueFrom(
            this.questionnaireService.getEntityQuestionnaires(this.productId),
          )
            .then(
              (questionnaires) => (this.productQuestionnaires = questionnaires),
            )
            .catch((error) => {
              console.error("Error loading product questionnaires:", error);
              this.productQuestionnaires = [];
            }),
        );
      }

      await Promise.all(requests);
    } catch (error) {
      console.error("Error in loadQuestionnaires:", error);
    } finally {
      this.loadingQuestionnaires = false;
      this.initAspectName();
    }
  }

  onFileSelected(event: any) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      return;
    }

    const newFiles: File[] = Array.from(input.files);

    // Filter PDF files
    const validFiles = newFiles.filter(file => {
      if (file.type !== "application/pdf") {
        console.warn(`Skipped non-PDF file: ${file.name}`);
        return false;
      }
      return true;
    });

    if (validFiles.length !== newFiles.length) {
      alert("Some files were skipped because they are not PDFs.");
    }

    if (validFiles.length === 0) {
      alert("Please select valid PDF files.");
      this.selectedFiles = [];
      return;
    }

    this.selectedFiles = validFiles;
  }

  async onUpload() {
    if (!this.selectedFiles || this.selectedFiles.length === 0) {
      this.errorMessage = "Please select at least one file first!";
      return;
    }

    if (!this.productId) {
      this.errorMessage =
        "No product model selected. Please ensure you have a product model to upload for.";
      return;
    }

    this.uploadingFile = true;
    this.errorMessage = null;

    try {
      const response = await firstValueFrom(
        this.productService.uploadSustainabilityReport(
          this.productId,
          this.selectedFiles,
        ),
      );

      if (response.responses && response.responses.length > 0) {
        await this.processAIResponses(response.responses);
        this.errorMessage = null;
        console.log(
          `Successfully processed ${response.responses.length} AI responses`,
        );
      } else {
        this.errorMessage =
          "No AI responses received. The file(s) may not contain relevant information.";
      }

      this.selectedFiles = [];
      // Reset file input if possible (optional, but requires ViewChild or direct DOM access)
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (error: any) {
      this.errorMessage =
        error?.error?.error ||
        error?.error?.detail ||
        "Failed to process sustainability report(s).";
      console.error("Error uploading sustainability report:", error);
    } finally {
      this.uploadingFile = false;
    }
  }

  private async loadAnswers() {
    const id = this.activeEntityId;
    if (id) {
      try {
        this.isLoading = true;
        this.answers = await firstValueFrom(this.questionnaireService.getAnswers(id));
      } catch (error) {
        console.error("Error loading answers:", error);
      } finally {
        this.isLoading = false;
      }
    } else {
      console.warn("No active entity id provided to load answers.");
    }
  }

  private async loadQueries() {

    const entityIds = [this.brandId, this.productLineId, this.productId].filter(id => id > 0);
    if (entityIds.length === 0) {
      return;
    }

    try {
      const queryRequests = entityIds.map(id =>
        firstValueFrom(this.suggestionService.getQueries(id))
      );
      const results = await Promise.all(queryRequests);

      // Flatten the results and remove duplicates (a concern for the same question could appear in multiple entities)
      const allConcerns = results.flat();
      const uniqueConcerns = Array.from(new Map(allConcerns.map(c => [c.id, c])).values());

      this.concerns = uniqueConcerns;
      this.queries = new Set(this.concerns.map((c) => c.question));

    } catch (error) {
      console.error("Error loading queries for one or more entities:", error);
      this.concerns = [];
      this.queries = new Set();
    }
  }

  handleClick(entityType: string) {
    this.brandIsActive = entityType === "brand";
    this.productLineIsActive = entityType === "productLine";
    this.productIsActive = entityType === "product";

    this.loadAnswers();
    this.initAspectName();
  }

  handleSelection(categoryName: string) {
    this.aspectName = categoryName;
  }

  initAspectName() {
    if (
      !this.getActiveQuestionnaires ||
      this.getActiveQuestionnaires.length === 0
    ) {
      console.warn("No questionnaires found for the active entity.");
      return;
    }
    this.aspectName = this.getActiveQuestionnaires[0].aspect;
  }

  get getActiveFilteredQuestionnaires(): Questionnaire[] {
    return this.getActiveQuestionnaires.filter(
      (questionnaire) => questionnaire.aspect === this.aspectName,
    );
  }

  // Get answer state for the given option
  getAnswerState(option: Option): "true" | "false" | "unknown" {
    const pendingAnswer = this.pendingAIAnswers.get(option.id);
    if (pendingAnswer) {
      if (pendingAnswer.isTrue) return "true";
      if (pendingAnswer.isFalse) return "false";
      return "unknown";
    }

    const answer = this.answers.find((ans) => ans.option === option.id);
    if (!answer) return "unknown";
    if (answer.isTrue) return "true";
    if (answer.isFalse) return "false";
    return "unknown";
  }

  getAnswerSource(option: Option): string {
    const answer = this.answers.find((ans) => ans.option === option.id);
    return answer?.source ?? "";
  }

  setAnswerSource(option: Option, event: any) {
    const sourceText = (event.target as HTMLTextAreaElement).value;
    const answer = this.answers.find((ans) => ans.option === option.id);

    if (answer) {
      answer.source = sourceText;
    }
  }

  async saveAnswerSource(option: Option) {
    const answer = this.answers.find((ans) => ans.option === option.id);
    // Only submit if the answer actually exists
    if (answer) {
      await this.submitAnswer(answer);
    }
  }

  // Set answer state for the given option
  async setAnswerState(
    option: Option,
    state: "true" | "false" | "unknown",
    question?: any,
  ) {
    this.pendingAIAnswers.delete(option.id);

    let answer = this.answers.find((ans) => ans.option === option.id);
    // Find the question if not provided
    if (!question) {
      question = this.getActiveFilteredQuestionnaires
        .flatMap((qn) => qn.questions)
        .find((q) => q.options.some((opt) => opt.id === option.id));
    }

    if (
      question &&
      question.isSingleChoice &&
      (state === "true" || state === "false")
    ) {
      // For single-choice, set all other options to unknown and disable them
      for (const opt of question.options) {
        if (opt.id !== option.id) {
          this.pendingAIAnswers.delete(opt.id);
          let otherAnswer = this.answers.find((ans) => ans.option === opt.id);
          if (!otherAnswer) {
            otherAnswer = {
              answeredBy: this.userService.getCurrentUser()?.user.id ?? 0,
              option: opt.id,
              productEntityId: this.activeEntityId,
              isTrue: false,
              isFalse: false,
            };
            this.answers.push(otherAnswer);
          }
          otherAnswer.isTrue = false;
          otherAnswer.isFalse = false;
          // Optionally, submit the change for other options as well
          if (this.activeEntityId) {
            await this.submitAnswer(otherAnswer);
          }
        }
      }
    }

    if (answer) {
      // Update existing answer
      answer.isTrue = state === "true";
      answer.isFalse = state === "false";
    } else {
      // Create new answer
      answer = {
        answeredBy: this.userService.getCurrentUser()?.user.id ?? 0,
        option: option.id,
        productEntityId: this.activeEntityId,
        isTrue: state === "true",
        isFalse: state === "false",
        source: "", // Initialize with empty source
      };
      this.answers.push(answer);
    }

    // Only submit if we have a valid ID
    if (this.activeEntityId) {
      await this.submitAnswer(answer);
    }
  }

  async submitAnswer(answer: Answer): Promise<boolean> {
    try {
      const id = this.activeEntityId;
      if (!answer.id) {
        // Create new answer
        const result = await firstValueFrom(
          this.questionnaireService.addAnswers([answer], id),
        );
        if (result && result.length > 0) {
          const updatedAnswer = result[0];
          // Update the local answer with the one from the server (which includes the new ID)
          const index = this.answers.findIndex(
            (ans) => ans.option === updatedAnswer.option,
          );
          if (index > -1) this.answers[index] = updatedAnswer;
        }
      } else {
        // Update existing answer
        const updatedAnswer = await firstValueFrom(
          this.questionnaireService.updateAnswer(answer, id),
        );
        // Replace the local answer with the updated one from the server
        const index = this.answers.findIndex(
          (ans) => ans.option === updatedAnswer.option,
        );
        if (index > -1) this.answers[index] = updatedAnswer;
      }

      // Successfully persisted
      return true;
    } catch (err: any) {
      let errorMsg = err?.message || "Failed to submit answer";

      if (err?.error) {
        if (typeof err.error === "string") {
          errorMsg = err.error;
        } else if (err.error.error) {
          errorMsg = err.error.error;
        } else if (err.error.detail) {
          errorMsg = err.error.detail;
        } else if (typeof err.error === "object") {
          const parts = Object.entries(err.error).map(([k, v]) => {
            let val = v;
            if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
              val = Object.entries(v).map(([sk, sv]) => `${sk}: ${Array.isArray(sv) ? sv.join(", ") : sv}`).join(", ");
            } else if (Array.isArray(v)) {
              val = v.join(", ");
            }
            return `${k}: ${val}`;
          });
          if (parts.length > 0) errorMsg = parts.join("; ");
        }
      }
      this.errorMessage = errorMsg;
      console.error("Error submitting answer:", err);
      return false;
    }
  }

  get getActiveQuestionnaires(): Questionnaire[] {
    if (this.brandIsActive) return this.brandQuestionnaires;
    if (this.productLineIsActive) return this.productLineQuestionnaires;
    if (this.productIsActive) return this.productQuestionnaires;
    return [];
  }

  private async processAIResponses(responses: any[]) {
    for (const response of responses) {
      const questionId = response.question_id;
      const aiAnswers = response.answers;

      for (const aiAnswer of aiAnswers) {
        const optionId = aiAnswer.option_id;
        const isTrue = aiAnswer.is_true;
        const isFalse = aiAnswer.is_false;
        const source = (aiAnswer as any).source ?? "";

        this.pendingAIAnswers.set(optionId, { isTrue, isFalse, source });
      }
    }
  }

  hasPendingAIAnswer(option: Option): boolean {
    return this.pendingAIAnswers.has(option.id);
  }

  async acceptAIAnswer(option: Option) {
    const pendingAnswer = this.pendingAIAnswers.get(option.id);
    if (!pendingAnswer) return;

    let answer = this.answers.find((ans) => ans.option === option.id);

    // Find the question for this option
    let questionId: number | undefined;
    for (const qn of this.getActiveFilteredQuestionnaires.flatMap(qn => qn.questions)) {
      if (qn.options.some(opt => opt.id === option.id)) {
        questionId = qn.id;
        break;
      }
    }

    if (answer) {
      answer.isTrue = pendingAnswer.isTrue;
      answer.isFalse = pendingAnswer.isFalse;
      (answer as any).source = (pendingAnswer as any).source || (answer as any).source || "";
      if (questionId !== undefined) (answer as any).question = questionId;
      this.answers.push(answer);
    } else if (questionId !== undefined) {
      answer = {
        answeredBy: this.userService.getCurrentUser()?.user.id ?? 0,
        option: option.id,
        productEntityId: this.activeEntityId,
        isTrue: pendingAnswer.isTrue,
        isFalse: pendingAnswer.isFalse,
        source: (pendingAnswer as any).source || "",
        question: questionId,
      };
      this.answers.push(answer);
    } else {
      // If questionId is undefined, do not proceed
      return;
    }

    this.pendingAIAnswers.delete(option.id);

    if (this.activeEntityId) {
      const saved = await this.submitAnswer(answer);
      if (!saved) {
        // If save failed (e.g., invalid BibTeX), open source editor so user can correct it
        this.openSourceDialog(option);
        return;
      }

      // Log AI feedback: what the model predicted and what the user accepted as corrected value
      try {
        const feedback = {
          productEntityId: this.activeEntityId,
          optionId: option.id,
          predictedValue: pendingAnswer.isTrue,
          correctedValue: answer.isTrue ?? null,
          predictedOptionId: option.id,
          modelName: 'Gemini POC',
          userId: this.userService.getCurrentUser()?.user.id ?? null,
        };
        await firstValueFrom(this.suggestionService.addAIFeedback(feedback));
      } catch (err) {
        console.error('Failed to log AI feedback (accept):', err);
      }
    }
  }

  rejectAIAnswer(option: Option) {
    const pendingAnswer = this.pendingAIAnswers.get(option.id);
    const existingAnswer = this.answers.find((ans) => ans.option === option.id);
    this.pendingAIAnswers.delete(option.id);

    // Log AI feedback for rejection: model prediction vs user-corrected (if any)
    if (pendingAnswer) {
      try {
        const feedback = {
          productEntityId: this.activeEntityId,
          optionId: option.id,
          predictedValue: pendingAnswer.isTrue,
          correctedValue: existingAnswer ? (existingAnswer.isTrue ?? null) : null,
          predictedOptionId: option.id,
          modelName: 'Gemini POC',
          userId: this.userService.getCurrentUser()?.user.id ?? null,
        };
        void firstValueFrom(this.suggestionService.addAIFeedback(feedback)).catch((err) => {
          console.error('Failed to log AI feedback (reject):', err);
        });
      } catch (err) {
        console.error('Failed to prepare AI feedback (reject):', err);
      }
    }
  }

  getOptionSource(option: Option): string | undefined {
    const pendingAnswer = this.pendingAIAnswers.get(option.id);
    return (pendingAnswer as any)?.source;
  }

  hasSource(option: Option): boolean {
    const source = this.getOptionSource(option);
    return Boolean(source && typeof source === 'string' && source.trim());
  }

  isArchrUser(): boolean {
    try {
      const current = this.userService.getCurrentUser();
      // Prefer the backend-provided single source-of-truth flag
      if (current?.user?.canAnswerQuestions !== undefined) {
        return current.user.canAnswerQuestions === true;
      }

      // Fallback for older login objects: derive from profile roleName and company flag
      const profile = current?.user?.profile;
      const roleName = profile?.roleName ?? null;
      const company = profile?.company ?? null;
      return (
        (roleName === 'Admin' || roleName === 'ManufacturingUser') &&
        company?.canEditQuestionAnswers === true
      );
    } catch {
      return false;
    }
  }

  openConcernModal(question: Question) {
    this.selectedQuestionForConcern = question;
    this.showConcernModal = true;
    this.concernSuggestionText = ""; // Reset text
  }

  closeConcernModal() {
    this.showConcernModal = false;
    this.selectedQuestionForConcern = null;
    this.concernSuggestionText = "";
  }

  async submitConcern() {
    if (!this.selectedQuestionForConcern) return;

    if (this.isArchrUser()) {
      this.errorMessage = "Archr users should submit answers, not concerns.";
      this.closeConcernModal();
      return;
    }

    try {
      const newConcern: any = await firstValueFrom(
        this.suggestionService.raiseConcern(
          this.selectedQuestionForConcern.id,
          this.concernSuggestionText
        )
      );
      this.errorMessage = null;
      // Add the new concern to our local state to update the UI instantly
      if (newConcern && newConcern.id) {
        this.concerns.push({
          id: newConcern.id,
          question: newConcern.question,
          suggestion_text: newConcern.suggestion_text,
          retailUser: newConcern.retailUser,
          retailUserUsername: newConcern.retailUserUsername,
          isHandled: newConcern.isHandled,
        });
        this.queries.add(this.selectedQuestionForConcern.id);
      }
      this.closeConcernModal();
    } catch (err: any) {
      this.errorMessage = `${err?.error?.error ?? err?.error?.detail ?? "Failed to raise concern"}`;
      console.error("Error raising concern:", err);
    }
  }

  async retractConcern(question: Question) {
    if (this.isArchrUser()) {
      this.errorMessage = "This action is not available for your user role.";
      return;
    }
    try {
      await firstValueFrom(this.suggestionService.retractConcern(question.id));
      this.errorMessage = null;
      // Remove the concern from our local state to update the UI instantly
      const currentUser = this.userService.getCurrentUser();
      this.concerns = this.concerns.filter(c => !(c.question === question.id && c.retailUser === currentUser?.user.id));
      this.queries.delete(question.id);
    } catch (err: any) {
      this.errorMessage = `${err?.error?.error ?? err?.error?.detail ?? "Failed to retract concern"}`;
      console.error("Error retracting concern:", err);
    }
  }

  hasConcern(question: Question): boolean {
    return this.queries.has(question.id);
  }

  hasUserRaisedConcern(question: Question): boolean {
    const currentUser = this.userService.getCurrentUser();
    if (!currentUser) {
      return false;
    }
    return this.concerns.some(c => c.question === question.id && c.retailUser === currentUser.user.id);
  }

  getConcernCount(question: Question): number {
    return this.concerns.filter(c => c.question === question.id).length;
  }

  showConcernDetails(question: Question): void {
    // Find all concern objects that match the question ID
    this.concernsForSelectedQuestion = this.concerns.filter(c => c.question === question.id);
  }

  closeConcernDetails(): void {
    this.concernsForSelectedQuestion = [];
  }

  async dismissConcern(concernId: number): Promise<void> {
    try {
      await firstValueFrom(this.suggestionService.dismissConcern(concernId));
      this.errorMessage = null;
      // Remove the dismissed concern from our local state to update the UI instantly
      this.concerns = this.concerns.filter(c => c.id !== concernId);
      // Update the concerns for selected question to reflect the dismissal
      this.concernsForSelectedQuestion = this.concernsForSelectedQuestion.filter(c => c.id !== concernId);
    } catch (err: any) {
      this.errorMessage = `${err?.error?.error ?? err?.error?.detail ?? "Failed to dismiss concern"}`;
      console.error("Error dismissing concern:", err);
    }
  }

  async openPrefillModal() {
    if (!this.productId || !this.productLineId) {
      this.errorMessage = "Product model or product line information is missing.";
      return;
    }

    try {
      this.availableSourceModels = await firstValueFrom(
        this.questionnaireService.getAnswerableModels(this.productLineId)
      );
      this.availableSourceModels = this.availableSourceModels.filter(
        (m) => m.id !== this.productId
      );
      this.showPrefillModal = true;
      this.selectedSourceModelId = null;
      this.errorMessage = null;
    } catch (error: any) {
      this.errorMessage =
        error?.error?.error ||
        error?.error?.detail ||
        "Failed to load available models.";
      console.error("Error loading answerable models:", error);
    }
  }

  closePrefillModal() {
    this.showPrefillModal = false;
    this.selectedSourceModelId = null;
    this.availableSourceModels = [];
  }

  async confirmPrefill() {
    if (!this.selectedSourceModelId || !this.productId) {
      this.errorMessage = "Please select a source model.";
      return;
    }

    this.isCopyingAnswers = true;
    this.errorMessage = null;

    try {
      const response = await firstValueFrom(
        this.questionnaireService.copyAnswersFromModel(
          this.selectedSourceModelId,
          this.productId
        )
      );

      // Reload answers to show the prefilled data
      await this.loadAnswers();
      this.closePrefillModal();

      // Optional: Show success message
      console.log("Successfully prefilled answers:", response);
    } catch (error: any) {
      this.errorMessage =
        error?.error?.error ||
        error?.error?.detail ||
        "Failed to copy answers.";
      console.error("Error copying answers:", error);
    } finally {
      this.isCopyingAnswers = false;
    }
  }
}

