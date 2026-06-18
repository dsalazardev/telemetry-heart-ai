import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('token');
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'Ha ocurrido un error desconocido';
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Código de error: ${error.status}\nMensaje: ${error.message}`;
    }
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  checkHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`).pipe(catchError(this.handleError));
  }

  get<T>(endpoint: string): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${endpoint}`, { headers: this.getHeaders() })
      .pipe(catchError(this.handleError));
  }

  post<T>(endpoint: string, data: any): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, data, { headers: this.getHeaders() })
      .pipe(catchError(this.handleError));
  }

  put<T>(endpoint: string, data: any): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${endpoint}`, data, { headers: this.getHeaders() })
      .pipe(catchError(this.handleError));
  }

  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${endpoint}`, { headers: this.getHeaders() })
      .pipe(catchError(this.handleError));
  }

  /** Dispara la evaluación IA de un evento de telemetría y devuelve la predicción (riesgo + prioridad de triaje). */
  evaluarEvento<T>(eventoId: number): Observable<T> {
    return this.post<T>(`/eventos/${eventoId}/evaluar`, {});
  }

  /** Genera un evento + telemetría de demo (nivel bajo/medio/alto) para poder evaluar desde la UI. */
  simularTelemetria<T>(pacienteId: number, nivel: 'bajo' | 'medio' | 'alto' = 'alto'): Observable<T> {
    return this.post<T>(`/pacientes/${pacienteId}/simular-telemetria`, { nivel });
  }

  /** Decodifica el payload del JWT guardado en localStorage (sin verificar firma). */
  private decodeToken(): any | null {
    const token = localStorage.getItem('token');
    if (!token) { return null; }
    try {
      const payload = token.split('.')[1];
      const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(json);
    } catch {
      return null;
    }
  }

  /** Id del usuario autenticado (claim `sub` del JWT). Ojo: NO es el medico_id. */
  getCurrentUserId(): number | null {
    const sub = this.decodeToken()?.sub;
    return sub != null ? Number(sub) : null;
  }

  /** Tipo del usuario autenticado (claim `tipo`: 'medico' | 'paciente' | ...). */
  getCurrentUserTipo(): string | null {
    return this.decodeToken()?.tipo ?? null;
  }
}