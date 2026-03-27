import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuestionnaireSectionsComponent } from './questionnaire-sections.component';

describe('QuestionnaireSectionsComponent', () => {
  let component: QuestionnaireSectionsComponent;
  let fixture: ComponentFixture<QuestionnaireSectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuestionnaireSectionsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(QuestionnaireSectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
