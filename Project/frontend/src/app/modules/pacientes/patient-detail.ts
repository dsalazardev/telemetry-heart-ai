import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';
import { finalize } from 'rxjs/operators';

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
              <h3>Telemetría en Tiempo Real</h3>
              <div class="metrics-row">
                <div class="metric">
                  <span class="m-val">--</span>
                  <span class="m-unit">BPM</span>
                  <span class="m-label">Frec. Cardíaca</span>
                </div>
                <div class="metric">
                  <span class="m-val">--</span>
                  <span class="m-unit">%</span>
                  <span class="m-label">SpO2</span>
                </div>
              </div>
              <div class="chart-box">
                <span>📡 Sin dispositivo vinculado aún</span>
              </div>
            </div>

            <!-- Explicación del Agente AI -->
            <div class="glass-card ai-card">
              <div class="ai-header">
                <h3>🧠 Análisis del Agente AI</h3>
                <span class="ai-badge">Telemetry Heart AI</span>
              </div>

              <!-- Disparador de evaluación -->
              <div class="eval-trigger">
                <input
                  type="number"
                  [(ngModel)]="eventoId"
                  name="eventoId"
                  placeholder="ID de evento de telemetría"
                  min="1"
                >
                <button class="btn btn-primary" (click)="evaluar()" [disabled]="!eventoId || evaluando">
                  {{ evaluando ? 'Evaluando...' : '⚡ Evaluar' }}
                </button>
              </div>

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
export class PatientDetailComponent implements OnInit {
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

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.cargarPaciente(parseInt(id));
    } else {
      this.loading = false;
    }
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
