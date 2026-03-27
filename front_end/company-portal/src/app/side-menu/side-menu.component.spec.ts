import { ComponentFixture, TestBed } from "@angular/core/testing";
import { SideMenuComponent } from "./side-menu.component";
import { HttpClientTestingModule } from "@angular/common/http/testing"; // Import HttpClientTestingModule to mock HTTP requests
import { FilterService } from "../services/filter.service"; // Import the service
import { of } from "rxjs";

describe("SideMenuComponent", () => {
  let component: SideMenuComponent;
  let fixture: ComponentFixture<SideMenuComponent>;
  let mockFilterService: jasmine.SpyObj<FilterService>;

  beforeEach(async () => {
    // Create spies for the services
    mockFilterService = jasmine.createSpyObj("FilterService", [
      "updateSelectedFilter",
      "getFilters",
    ]);

    // Mock the getFilters method to return an observable
    mockFilterService.getFilters.and.returnValue(of([])); // Mock an empty array for filters

    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, SideMenuComponent], // Use HttpClientTestingModule for HTTP requests
      providers: [
        { provide: FilterService, useValue: mockFilterService }, // Provide mock services
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SideMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });

  it("should call getFilters on init", () => {
    expect(mockFilterService.getFilters).toHaveBeenCalled(); // Verify that getFilters is called during initialization
  });

  it("should toggle filter section visibility", () => {
    expect(component.isFilterExpanded).toBe(false); // Initially false
    component.toggleFilterSection();
    expect(component.isFilterExpanded).toBe(true); // After toggling, it should be true
  });
});
