import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule], // Simulamos el módulo HTTP
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('debería ser creado', () => {
    expect(service).toBeTruthy();
  });

  it('debería realizar una petición GET a /health', () => {
    const dummyResponse = { status: 'ok' };
    
    service.checkHealth().subscribe(res => {
      expect(res).toEqual(dummyResponse);
    });

    const req = httpMock.expectOne('http://localhost:8000/health');
    expect(req.request.method).toBe('GET');
    req.flush(dummyResponse); // Simulamos la respuesta del backend
  });
});