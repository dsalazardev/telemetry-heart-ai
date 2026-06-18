import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';
import { environment } from '../../../environments/environment';
import { finalize, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

@Component({
  selector: 'app-patient-detail',
  standalone: true,
  imports: [CommonModule, SidebarComponent, FormsModule],
  template: `
    <div class="app-container">
      <app-sidebar></app-sidebar>
      <main class="main-content">
        <header class="topbar">
          <div class="view-info">
            <button class="back-btn" (click)="volver()">← Volver</button>
            <h1>Detalle del Paciente</h1>
            <p>Monitoreo Clínico Profundo</p>
          </div>
          <button class="btn btn-primary" (click)="abrirEdicion()" *ngIf="paciente">
            ✏️ Editar Datos
          </button>
        </header>

        <div class="content-body fade-in" *ngIf="!loading && paciente">
          <div class="detail-grid">
            <!-- Perfil del Paciente -->
            <div class="glass-card profile-card">
              <div class="avatar-lg">
                {{ (paciente.usuario?.nombres?.[0] || '') + (paciente.usuario?.apellidos?.[0] || '') }}
              </div>
              <h2>{{ paciente.usuario?.nombres }} {{ paciente.usuario?.apellidos }}</h2>
              <p class="id-doc">CC {{ paciente.usuario?.documento }}</p>
              <hr class="divider">
              <div class="info-list">
                <div class="info-item">
                  <span class="info-label">Correo</span>
                  <span class="info-value">{{ paciente.usuario?.correo }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Teléfono</span>
                  <span class="info-value">{{ paciente.usuario?.telefono }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Nacimiento</span>
                  <span class="info-value">{{ paciente.fechaNacimiento || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Estado</span>
                  <span class="status-active">● Activo</span>
                </div>
              </div>
            </div>

            <!-- Telemetría en Vivo -->
            <div class="glass-card telemetry-card">
              <div class="ai-header">
                <h3>Telemetría en Tiempo Real</h3>
                <span class="ws-badge" [class.live]="wsConnected">
                  {{ wsConnected ? '● En línea' : '○ Sin conexión' }}
                </span>
              </div>
              <div class="metrics-row">
                <div class="metric">
                  <span class="m-val">{{ telemetria ? (telemetria.fc | number:'1.0-0') : '--' }}</span>
                  <span class="m-unit">BPM</span>
                  <span class="m-label">Frec. Cardíaca</span>
                </div>
                <div class="metric">
                  <span class="m-val">{{ telemetria ? (telemetria.spo2 | number:'1.0-0') : '--' }}</span>
                  <span class="m-unit">%</span>
                  <span class="m-label">SpO2</span>
                </div>
              </div>
              <div class="chart-box">
                <span *ngIf="telemetria">Última lectura: {{ telemetria.ts | date:'medium' }}</span>
                <span *ngIf="!telemetria">📡 Esperando lecturas del dispositivo…</span>
              </div>
            </div>

            <!-- Perfil Clínico -->
            <div class="glass-card perfil-card">
              <div class="ai-header">
                <h3>🩺 Perfil Clínico</h3>
                <button class="btn btn-sm" (click)="abrirPerfil()">
                  {{ perfil ? '✏️ Editar' : '➕ Crear' }}
                </button>
              </div>
              <div class="info-list" *ngIf="perfil as pf; else sinPerfil">
                <div class="info-item"><span class="info-label">Edad</span><span class="info-value">{{ pf.edad }} años</span></div>
                <div class="info-item"><span class="info-label">Sexo</span><span class="info-value">{{ pf.sexo }}</span></div>
                <div class="info-item"><span class="info-label">Tipo de sangre</span><span class="info-value">{{ pf.tipoSangre }}</span></div>
                <div class="info-item"><span class="info-label">Alergias</span><span class="info-value">{{ pf.alergias || 'Ninguna' }}</span></div>
              </div>
              <ng-template #sinPerfil>
                <p style="color:var(--text-muted); font-size:0.875rem;">
                  Sin perfil clínico. La IA usa edad y sexo para predecir el riesgo — créalo para mejorar la evaluación.
                </p>
              </ng-template>
            </div>

            <!-- Explicación del Agente AI -->
            <div class="glass-card ai-card">
              <div class="ai-header">
                <h3>🧠 Análisis del Agente AI</h3>
                <span class="ai-badge">Telemetry Heart AI</span>
              </div>

              <!-- Disparador de evaluación -->
              <div class="eval-trigger" *ngIf="eventos.length; else sinEventos">
                <select [(ngModel)]="eventoId" name="eventoId">
                  <option *ngFor="let e of eventos" [ngValue]="e.id">{{ etiquetaEvento(e) }}</option>
                </select>
                <button class="btn btn-primary" (click)="evaluar()" [disabled]="!eventoId || evaluando">
                  {{ evaluando ? 'Evaluando...' : '⚡ Evaluar' }}
                </button>
              </div>
              <ng-template #sinEventos>
                <p class="no-eventos">
                  {{ cargandoEventos ? 'Cargando eventos…' : '📭 Este paciente no tiene eventos de telemetría registrados.' }}
                </p>
              </ng-template>

              <!-- Resultado -->
              <div class="ai-content" *ngIf="prediccion as p">
                <div class="result-row">
                  <span class="result-label">Nivel de riesgo</span>
                  <span class="risk-pill" [ngClass]="'risk-' + (p.risk_level || '')">
                    {{ (p.risk_level || 'N/D') | uppercase }}
                  </span>
                </div>
                <div class="result-row" *ngIf="p.priority">
                  <span class="result-label">Prioridad de triaje (PSO)</span>
                  <span class="priority-badge" [ngClass]="'prio-' + p.priority.toLowerCase()">
                    {{ p.priority }}
                  </span>
                </div>
                <p *ngIf="p.clinical_explanation">
                  <strong>Explicación:</strong> {{ p.clinical_explanation }}
                </p>
                <p *ngIf="p.recommended_action">
                  <strong>Recomendación:</strong> {{ p.recommended_action }}
                </p>
                <p *ngIf="p.dominant_factors?.length">
                  <strong>Factores:</strong> {{ p.dominant_factors.join(', ') }}
                </p>
              </div>

              <!-- Estado por defecto / error -->
              <div class="ai-content" *ngIf="!prediccion">
                <p *ngIf="!evalError"><strong>Estado:</strong> Sin análisis. Ingresa un ID de evento de telemetría y evalúa.</p>
                <p *ngIf="evalError" class="eval-error"><strong>Error:</strong> {{ evalError }}</p>
              </div>
            </div>

            <!-- Historial Clínico -->
            <div class="glass-card historial-card">
              <h3>📋 Historial Clínico</h3>
              <table class="historial-table" *ngIf="historiales.length; else sinHistorial">
                <thead>
                  <tr>
                    <th>Patología</th>
                    <th>Diagnóstico</th>
                    <th>Severidad</th>
                    <th>Estado</th>
                    <th>Tratamiento</th>
                    <th>Última revisión</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let h of historiales">
                    <td class="strong">{{ patologiaNombre(h) }}</td>
                    <td>{{ h.fechaDiagnostico | date:'mediumDate' }}</td>
                    <td>{{ h.nivelSeveridad }}</td>
                    <td>
                      <span class="state" [class.done]="h.controlada">
                        {{ h.controlada ? '✓ Controlada' : '● Activa' }}
                      </span>
                    </td>
                    <td>{{ h.tratamientoActual || '—' }}</td>
                    <td class="muted">{{ h.ultimaRevision | date:'short' }}</td>
                  </tr>
                </tbody>
              </table>
              <ng-template #sinHistorial>
                <p style="color:var(--text-muted); font-size:0.875rem;">Sin antecedentes clínicos registrados.</p>
              </ng-template>
            </div>
          </div>
        </div>

        <!-- Loading state -->
        <div class="content-body" *ngIf="loading">
          <div class="glass-card" style="text-align:center; padding: 4rem;">
            <p style="color: var(--text-muted);">Cargando datos del paciente...</p>
          </div>
        </div>

        <!-- Not found -->
        <div class="content-body" *ngIf="!loading && !paciente">
          <div class="glass-card" style="text-align:center; padding: 4rem;">
            <p style="font-size:2rem;">😔</p>
            <h3>Paciente no encontrado</h3>
            <button class="btn btn-primary" style="margin-top:1rem;" (click)="volver()">Volver al listado</button>
          </div>
        </div>
      </main>
    </div>

    <!-- Modal de edición -->
    <div class="modal-overlay" *ngIf="showEdit" (click)="showEdit = false">
      <div class="glass-card modal-content fade-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h2>Editar Paciente</h2>
          <button class="close-btn" (click)="showEdit = false">×</button>
        </div>
        <form (ngSubmit)="guardarEdicion()" #editForm="ngForm" class="modal-form" *ngIf="editData">
          <div class="form-row">
            <div class="form-group">
              <label>Nombres</label>
              <input type="text" [(ngModel)]="editData.usuario.nombres" name="nombres" required>
            </div>
            <div class="form-group">
              <label>Apellidos</label>
              <input type="text" [(ngModel)]="editData.usuario.apellidos" name="apellidos" required>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Teléfono</label>
              <input type="text" [(ngModel)]="editData.usuario.telefono" name="telefono" required>
            </div>
            <div class="form-group">
              <label>Fecha de Nacimiento</label>
              <input type="date" [(ngModel)]="editData.fechaNacimiento" name="fechaNacimiento" required>
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-outline" (click)="showEdit = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" [disabled]="!editForm.valid || guardando">
              {{ guardando ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal de perfil clínico -->
    <div class="modal-overlay" *ngIf="showPerfil" (click)="showPerfil = false">
      <div class="glass-card modal-content fade-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h2>{{ perfil ? 'Editar' : 'Crear' }} Perfil Clínico</h2>
          <button class="close-btn" (click)="showPerfil = false">×</button>
        </div>
        <form (ngSubmit)="guardarPerfil()" #perfilForm="ngForm" class="modal-form" *ngIf="perfilData">
          <div class="form-row">
            <div class="form-group">
              <label>Edad</label>
              <input type="number" [(ngModel)]="perfilData.edad" name="edad" min="0" max="120" required>
            </div>
            <div class="form-group">
              <label>Sexo</label>
              <select [(ngModel)]="perfilData.sexo" name="sexo" required>
                <option value="" disabled>Seleccionar...</option>
                <option value="M">Masculino</option>
                <option value="F">Femenino</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Tipo de sangre</label>
              <select [(ngModel)]="perfilData.tipoSangre" name="tipoSangre" required>
                <option value="" disabled>Seleccionar...</option>
                <option *ngFor="let t of tiposSangre" [value]="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Alergias</label>
              <input type="text" [(ngModel)]="perfilData.alergias" name="alergias" placeholder="Opcional">
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-outline" (click)="showPerfil = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" [disabled]="!perfilForm.valid || guardandoPerfil">
              {{ guardandoPerfil ? 'Guardando...' : 'Guardar Perfil' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Toast -->
    <div *ngIf="toast" class="toast-detail" [ngClass]="toast.tipo">
      <span>{{ toast.tipo === 'success' ? '✅' : '❌' }}</span>
      <p>{{ toast.mensaje }}</p>
    </div>
  `,
  styles: [`
    .back-btn {
      background: none; border: none; color: var(--text-muted);
      cursor: pointer; font-size: 0.875rem; padding: 0;
      margin-bottom: 0.25rem; display: block;
    }
    .back-btn:hover { color: var(--primary); }

    .detail-grid {
      display: grid;
      grid-template-columns: 320px 1fr;
      grid-template-rows: auto auto;
      gap: 1.5rem;
    }

    .profile-card {
      grid-row: span 2;
      display: flex; flex-direction: column;
      align-items: center; text-align: center; padding: 2.5rem 2rem;
    }
    .avatar-lg {
      width: 90px; height: 90px;
      background: var(--primary-low); color: var(--primary);
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; font-size: 2rem; font-weight: 700;
      margin-bottom: 1.25rem;
    }
    .profile-card h2 { font-size: 1.25rem; margin-bottom: 0.25rem; }
    .id-doc { color: var(--text-muted); font-size: 0.875rem; margin-bottom: 1.25rem; }
    .divider { width: 100%; border: 0; border-top: 1px solid var(--border); margin: 1rem 0; }
    .info-list { width: 100%; text-align: left; }
    .info-item { display: flex; flex-direction: column; margin-bottom: 1rem; }
    .info-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .info-value { font-size: 0.9375rem; font-weight: 500; margin-top: 0.25rem; }
    .status-active { color: var(--success); font-weight: 600; margin-top: 0.25rem; }

    .metrics-row { display: flex; gap: 3rem; margin: 1.5rem 0; }
    .metric { display: flex; flex-direction: column; }
    .m-val { font-size: 2.5rem; font-weight: 700; font-family: 'Outfit'; color: var(--primary); line-height: 1; }
    .m-unit { font-size: 0.875rem; color: var(--text-muted); }
    .m-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

    .chart-box {
      height: 160px; background: var(--bg-main); border-radius: var(--radius-md);
      display: flex; align-items: center; justify-content: center;
      color: var(--text-muted); font-size: 0.9375rem;
      border: 1px dashed var(--border);
    }

    .ai-card { border-left: 4px solid var(--primary); }
    .ai-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .ai-badge { background: var(--primary-low); color: var(--primary); padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.7rem; font-weight: 700; }
    .ai-content p { margin-bottom: 0.75rem; font-size: 0.9375rem; line-height: 1.6; }
    .eval-error { color: var(--danger); }

    .eval-trigger { display: flex; gap: 0.75rem; margin: 1rem 0; }
    .eval-trigger input {
      flex: 1; padding: 0.6rem 0.9rem; border-radius: var(--radius-md);
      border: 1px solid var(--border); font-family: inherit;
    }
    .eval-trigger input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 4px var(--primary-low); }
    .eval-trigger select {
      flex: 1; padding: 0.6rem 0.9rem; border-radius: var(--radius-md);
      border: 1px solid var(--border); font-family: inherit; background: white; min-width: 0;
    }
    .eval-trigger select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 4px var(--primary-low); }
    .no-eventos { font-size: 0.875rem; color: var(--text-muted); margin: 1rem 0; }

    .result-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
    .result-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

    .risk-pill, .priority-badge {
      display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
    }
    .risk-bajo { background: rgba(34,197,94,0.15); color: #16a34a; }
    .risk-medio { background: rgba(245,158,11,0.15); color: #d97706; }
    .risk-alto { background: rgba(239,68,68,0.15); color: #dc2626; }
    .prio-baja { background: rgba(34,197,94,0.15); color: #16a34a; }
    .prio-media { background: rgba(245,158,11,0.15); color: #d97706; }
    .prio-alta { background: rgba(239,68,68,0.15); color: #dc2626; }

    .modal-overlay {
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.4); backdrop-filter: blur(4px);
      display: flex; align-items: center; justify-content: center; z-index: 1000;
    }
    .modal-content { width: 100%; max-width: 580px; background: white; padding: 0; border-radius: var(--radius-lg); overflow: hidden; }
    .modal-header { padding: 1.5rem 2rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
    .modal-header h2 { font-size: 1.25rem; margin: 0; }
    .close-btn { background: none; border: none; font-size: 2rem; cursor: pointer; color: var(--text-muted); }
    .modal-form { padding: 2rem; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    .form-group { margin-bottom: 1.5rem; }
    .form-group label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem; }
    .form-group input { width: 100%; padding: 0.75rem 1rem; border-radius: var(--radius-md); border: 1px solid var(--border); font-family: inherit; }
    .form-group input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 4px var(--primary-low); }
    .modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1rem; }
    .btn-outline { background: white; border: 1px solid var(--border); color: var(--text-muted); padding: 0.75rem 1.5rem; border-radius: var(--radius-md); cursor: pointer; font-family: inherit; font-weight: 600; }
    .btn-sm { padding: 0.35rem 0.9rem; font-size: 0.8rem; border-radius: var(--radius-sm); background: var(--primary-low); color: var(--primary); border: none; cursor: pointer; font-weight: 600; font-family: inherit; }
    .btn-sm:hover { background: var(--primary); color: white; }
    .form-group select { width: 100%; padding: 0.75rem 1rem; border-radius: var(--radius-md); border: 1px solid var(--border); font-family: inherit; background: white; }
    .form-group select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 4px var(--primary-low); }
    .perfil-card .ai-header { margin-bottom: 1rem; }
    .ws-badge { font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.6rem; border-radius: 999px; background: var(--bg-main); color: var(--text-muted); }
    .ws-badge.live { background: rgba(34,197,94,0.15); color: #16a34a; }

    .historial-card { grid-column: 1 / -1; }
    .historial-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
    .historial-table th { text-align: left; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); }
    .historial-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); font-size: 0.875rem; }
    .historial-table tr:last-child td { border-bottom: none; }
    .historial-table .strong { font-weight: 600; }
    .historial-table .muted { color: var(--text-muted); }
    .historial-table .state { font-weight: 600; color: var(--warning); }
    .historial-table .state.done { color: var(--success); }

    .toast-detail {
      position: fixed; bottom: 2rem; right: 2rem;
      display: flex; align-items: center; gap: 0.75rem;
      padding: 1rem 1.5rem; border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg); z-index: 2000; font-weight: 500;
    }
    .toast-detail.success { background: var(--success); color: white; }
    .toast-detail.error { background: var(--danger); color: white; }
  `]
})
export class PatientDetailComponent implements OnInit, OnDestroy {
  paciente: any = null;
  loading = true;
  showEdit = false;
  guardando = false;
  editData: any = null;
  toast: { mensaje: string; tipo: 'success' | 'error' } | null = null;

  eventoId: number | null = null;
  evaluando = false;
  prediccion: any = null;
  evalError: string | null = null;
  eventos: any[] = [];
  cargandoEventos = false;

  perfil: any = null;
  showPerfil = false;
  guardandoPerfil = false;
  perfilData: any = null;
  tiposSangre = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'];

  historiales: any[] = [];
  patologias = new Map<number, string>();

  // Telemetría en vivo (WebSocket)
  telemetria: { fc: number; spo2: number; ts: string } | null = null;
  wsConnected = false;
  private ws?: WebSocket;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      const pid = parseInt(id);
      this.cargarPaciente(pid);
      this.cargarPerfil(pid);
      this.cargarHistoriales(pid);
      this.cargarEventos(pid);
      this.conectarTelemetria(pid);
    } else {
      this.loading = false;
    }
  }

  ngOnDestroy() {
    this.ws?.close();
  }

  cargarHistoriales(pacienteId: number) {
    // Resuelve nombres de patología en paralelo para mostrarlos legibles.
    this.api.get<any[]>('/patologias').pipe(catchError(() => of([]))).subscribe(pats => {
      for (const p of pats || []) { this.patologias.set(p.id, p.nombre); }
      this.cdr.detectChanges();
    });
    this.api.get<any[]>(`/pacientes/${pacienteId}/historiales`).pipe(catchError(() => of([])))
      .subscribe(data => { this.historiales = data || []; this.cdr.detectChanges(); });
  }

  patologiaNombre(historial: any): string {
    return this.patologias.get(historial.patologia_id) ?? `Patología #${historial.patologia_id}`;
  }

  /** Carga los eventos del paciente y preselecciona el más reciente (ya vienen ordenados desc). */
  cargarEventos(pacienteId: number) {
    this.cargandoEventos = true;
    this.api.get<any[]>(`/pacientes/${pacienteId}/eventos`)
      .pipe(finalize(() => { this.cargandoEventos = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: (data) => {
          this.eventos = data || [];
          if (this.eventos.length && this.eventoId == null) {
            this.eventoId = this.eventos[0].id;
          }
        },
        error: () => { this.eventos = []; }
      });
  }

  /** Etiqueta legible para cada opción del desplegable de eventos. */
  etiquetaEvento(e: any): string {
    const fecha = e.ventanaFin ? new Date(e.ventanaFin).toLocaleString() : '';
    const tipo = e.tipo ? e.tipo.replace(/_/g, ' ') : 'evento';
    return `#${e.id} · ${tipo} · ${e.lecturas ?? 0} lecturas · ${fecha}`;
  }

  /** Conecta al WebSocket de telemetría del backend para recibir FC/SpO2 en vivo. */
  private conectarTelemetria(pacienteId: number) {
    const token = localStorage.getItem('token');
    if (!token) { return; }
    const wsBase = environment.apiUrl.replace(/^http/, 'ws');
    try {
      this.ws = new WebSocket(`${wsBase}/telemetria/ws/telemetria/${pacienteId}?token=${token}`);
      this.ws.onopen = () => { this.wsConnected = true; this.cdr.detectChanges(); };
      this.ws.onclose = () => { this.wsConnected = false; this.cdr.detectChanges(); };
      this.ws.onerror = () => { this.wsConnected = false; this.cdr.detectChanges(); };
      this.ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.tipo === 'telemetria') {
            this.telemetria = { fc: msg.fc, spo2: msg.spo2, ts: msg.timestamp };
            this.cdr.detectChanges();
          }
        } catch { /* ignora mensajes no-JSON */ }
      };
    } catch {
      this.wsConnected = false;
    }
  }

  cargarPerfil(pacienteId: number) {
    // El backend devuelve 404 si el paciente aún no tiene perfil clínico.
    this.api.get<any>(`/pacientes/${pacienteId}/perfil`).subscribe({
      next: (data) => { this.perfil = data; this.cdr.detectChanges(); },
      error: () => { this.perfil = null; this.cdr.detectChanges(); }
    });
  }

  abrirPerfil() {
    this.perfilData = {
      edad: this.perfil?.edad ?? null,
      sexo: this.perfil?.sexo ?? '',
      tipoSangre: this.perfil?.tipoSangre ?? '',
      alergias: this.perfil?.alergias ?? ''
    };
    this.showPerfil = true;
  }

  guardarPerfil() {
    if (!this.paciente) { return; }
    this.guardandoPerfil = true;
    const pid = this.paciente.id;
    // Si ya existe perfil -> PUT (actualizar); si no -> POST (crear).
    const req = this.perfil
      ? this.api.put<any>(`/pacientes/${pid}/perfil`, this.perfilData)
      : this.api.post<any>(`/pacientes/${pid}/perfil`, this.perfilData);
    req.pipe(finalize(() => { this.guardandoPerfil = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: (data) => {
          this.perfil = data;
          this.showPerfil = false;
          this.mostrarToast('Perfil clínico guardado.', 'success');
        },
        error: (err) => this.mostrarToast('Error al guardar perfil: ' + (err.message || 'desconocido'), 'error')
      });
  }

  cargarPaciente(id: number) {
    this.api.get<any>(`/pacientes/${id}`)
      .pipe(finalize(() => {
        this.loading = false;
        this.cdr.detectChanges();
      }))
      .subscribe({
        next: (data) => {
          this.paciente = data;
        },
        error: () => {
          this.paciente = null;
        }
      });
  }

  abrirEdicion() {
    this.editData = {
      usuario: {
        nombres: this.paciente.usuario?.nombres || '',
        apellidos: this.paciente.usuario?.apellidos || '',
        telefono: this.paciente.usuario?.telefono || '',
      },
      fechaNacimiento: this.paciente.fechaNacimiento || ''
    };
    this.showEdit = true;
  }

  guardarEdicion() {
    this.guardando = true;
    this.api.put<any>(`/pacientes/${this.paciente.id}`, this.editData).subscribe({
      next: () => {
        this.guardando = false;
        this.showEdit = false;
        this.mostrarToast('Paciente actualizado correctamente', 'success');
        this.cargarPaciente(this.paciente.id);
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarToast('Error al actualizar: ' + (err.message || 'Error desconocido'), 'error');
      }
    });
  }

  evaluar() {
    if (!this.eventoId) { return; }
    this.evaluando = true;
    this.evalError = null;
    this.prediccion = null;
    this.api.evaluarEvento<any>(this.eventoId)
      .pipe(finalize(() => {
        this.evaluando = false;
        this.cdr.detectChanges();
      }))
      .subscribe({
        next: (data) => {
          if (data?.status && data.status !== 'ok') {
            this.evalError = data.detail || data.status;
          } else {
            this.prediccion = data;
          }
        },
        error: (err) => {
          this.evalError = err.message || 'No se pudo evaluar el evento';
        }
      });
  }

  volver() {
    this.router.navigate(['/pacientes']);
  }

  mostrarToast(mensaje: string, tipo: 'success' | 'error') {
    this.toast = { mensaje, tipo };
    setTimeout(() => this.toast = null, 4000);
    this.cdr.detectChanges();
  }
}
