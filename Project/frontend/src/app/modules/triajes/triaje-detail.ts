import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';

@Component({
  selector: 'app-triaje-detail',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  template: `
    <div class="app-container">
      <app-sidebar></app-sidebar>
      <main class="main-content">
        <header class="topbar">
          <div class="view-info">
            <button class="back-btn" (click)="volver()">← Volver a triajes</button>
            <h1>Detalle de Triaje</h1>
            <p>Evaluación cardiovascular #{{ triajeId }}</p>
          </div>
          <button
            class="btn btn-primary"
            *ngIf="triaje && !triaje.atendida"
            [disabled]="!medicoId || atendiendo"
            [title]="!medicoId ? 'Solo un médico autenticado puede atender' : ''"
            (click)="atender()">
            {{ atendiendo ? 'Atendiendo...' : '✓ Marcar como atendido' }}
          </button>
        </header>

        <div class="content-body fade-in" *ngIf="!loading && triaje as t">
          <div class="detail-grid">
            <!-- Resumen clínico -->
            <div class="glass-card">
              <h3>Resultado de la IA</h3>
              <div class="kv">
                <span class="k">Nivel de urgencia</span>
                <span class="risk-pill" [ngClass]="'risk-' + (t.nivelUrgencia || '').toLowerCase()">
                  {{ (t.nivelUrgencia || 'N/D') | uppercase }}
                </span>
              </div>
              <div class="kv">
                <span class="k">Probabilidad de riesgo</span>
                <span class="v">{{ (t.probabilidadRiesgo * 100) | number:'1.0-1' }}%</span>
              </div>
              <div class="kv">
                <span class="k">Estado</span>
                <span class="state" [class.done]="t.atendida">
                  {{ t.atendida ? '✓ Atendido' : '● Pendiente' }}
                </span>
              </div>
              <div class="kv">
                <span class="k">Notificado por Telegram</span>
                <span class="v">{{ t.telegramEnviado ? 'Sí' : 'No' }}</span>
              </div>
              <div class="kv" *ngIf="t.diagnosticoConfirmado != null">
                <span class="k">Diagnóstico confirmado</span>
                <span class="v">{{ t.diagnosticoConfirmado ? 'Sí' : 'No' }}</span>
              </div>
            </div>

            <!-- Tiempos y vínculos -->
            <div class="glass-card">
              <h3>Trazabilidad</h3>
              <div class="kv"><span class="k">Emitido</span><span class="v">{{ t.fechaEmision | date:'medium' }}</span></div>
              <div class="kv"><span class="k">Atendido</span><span class="v">{{ t.fechaAtencion ? (t.fechaAtencion | date:'medium') : '—' }}</span></div>
              <div class="kv"><span class="k">Paciente</span><span class="v">#{{ t.paciente_id }}</span></div>
              <div class="kv"><span class="k">Médico</span><span class="v">{{ t.medico_id ? ('#' + t.medico_id) : '—' }}</span></div>
              <div class="kv"><span class="k">Alerta asociada</span><span class="v">{{ t.alerta_id ? ('#' + t.alerta_id) : '—' }}</span></div>
            </div>

            <!-- Factores críticos -->
            <div class="glass-card span-2" *ngIf="factores.length">
              <h3>Factores críticos</h3>
              <div class="chips">
                <span class="factor" *ngFor="let f of factores">{{ f }}</span>
              </div>
            </div>

            <!-- Explicación clínica -->
            <div class="glass-card span-2" *ngIf="t.explicacionClinica">
              <h3>🧠 Explicación clínica del agente</h3>
              <p class="explanation">{{ t.explicacionClinica }}</p>
            </div>

            <!-- Logs -->
            <div class="glass-card span-2">
              <h3>Registro de eventos (logs)</h3>
              <table class="logs" *ngIf="logs.length; else sinLogs">
                <thead><tr><th>Hora</th><th>Evento</th><th>Detalle</th><th>OK</th></tr></thead>
                <tbody>
                  <tr *ngFor="let l of logs">
                    <td class="muted">{{ l.timestamp | date:'short' }}</td>
                    <td>{{ l.tipoEvento }}</td>
                    <td>{{ l.detalle }}{{ l.errorMsg ? ' — ' + l.errorMsg : '' }}</td>
                    <td>{{ l.exitoso ? '✅' : '❌' }}</td>
                  </tr>
                </tbody>
              </table>
              <ng-template #sinLogs><p class="muted">Sin eventos registrados.</p></ng-template>
            </div>
          </div>
        </div>

        <div class="content-body" *ngIf="loading">
          <div class="glass-card" style="text-align:center; padding:4rem; color:var(--text-muted);">Cargando triaje...</div>
        </div>

        <div class="content-body" *ngIf="!loading && !triaje">
          <div class="glass-card" style="text-align:center; padding:4rem;">
            <p style="font-size:2rem;">😔</p>
            <h3>Triaje no encontrado</h3>
            <button class="btn btn-primary" style="margin-top:1rem;" (click)="volver()">Volver</button>
          </div>
        </div>
      </main>
    </div>

    <div *ngIf="toast" class="toast-detail" [ngClass]="toast.tipo">
      <span>{{ toast.tipo === 'success' ? '✅' : '❌' }}</span>
      <p>{{ toast.mensaje }}</p>
    </div>
  `,
  styles: [`
    .back-btn { background:none; border:none; color:var(--text-muted); cursor:pointer;
      font-size:0.875rem; padding:0; margin-bottom:0.25rem; display:block; }
    .back-btn:hover { color:var(--primary); }

    .detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
    .span-2 { grid-column:1 / -1; }
    .glass-card h3 { margin-bottom:1rem; font-size:1.05rem; }

    .kv { display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0;
      border-bottom:1px solid var(--border); }
    .kv:last-child { border-bottom:none; }
    .k { font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
    .v { font-weight:500; font-size:0.9375rem; }

    .risk-pill { display:inline-block; padding:0.15rem 0.7rem; border-radius:999px;
      font-size:0.7rem; font-weight:700; letter-spacing:0.05em; }
    .risk-bajo { background:rgba(34,197,94,0.15); color:#16a34a; }
    .risk-medio { background:rgba(245,158,11,0.15); color:#d97706; }
    .risk-alto { background:rgba(239,68,68,0.15); color:#dc2626; }

    .state { font-weight:600; color:var(--warning); }
    .state.done { color:var(--success); }

    .chips { display:flex; flex-wrap:wrap; gap:0.5rem; }
    .factor { background:var(--primary-low); color:var(--primary); padding:0.3rem 0.8rem;
      border-radius:999px; font-size:0.8rem; font-weight:600; }

    .explanation { font-size:0.9375rem; line-height:1.7; color:var(--text-main); }

    .logs { width:100%; border-collapse:collapse; }
    .logs th { text-align:left; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em;
      color:var(--text-muted); padding:0.6rem 0.75rem; border-bottom:1px solid var(--border); }
    .logs td { padding:0.6rem 0.75rem; border-bottom:1px solid var(--border); font-size:0.875rem; }
    .logs tr:last-child td { border-bottom:none; }
    .muted { color:var(--text-muted); }

    .toast-detail { position:fixed; bottom:2rem; right:2rem; display:flex; align-items:center;
      gap:0.75rem; padding:1rem 1.5rem; border-radius:var(--radius-md);
      box-shadow:var(--shadow-lg); z-index:2000; font-weight:500; }
    .toast-detail.success { background:var(--success); color:white; }
    .toast-detail.error { background:var(--danger); color:white; }
  `]
})
export class TriajeDetailComponent implements OnInit {
  triajeId = 0;
  triaje: any = null;
  logs: any[] = [];
  factores: string[] = [];
  medicoId: number | null = null;
  loading = true;
  atendiendo = false;
  toast: { mensaje: string; tipo: 'success' | 'error' } | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    this.triajeId = id ? parseInt(id, 10) : 0;
    this.resolverMedico();
    this.cargar();
  }

  /** El JWT trae el id de Usuario; el endpoint atender necesita el id de Médico. */
  private resolverMedico() {
    if (this.api.getCurrentUserTipo() !== 'medico') { return; }
    const usuarioId = this.api.getCurrentUserId();
    if (usuarioId == null) { return; }
    this.api.get<any[]>('/medicos').pipe(catchError(() => of([]))).subscribe(medicos => {
      const m = (medicos || []).find(med => med.usuario?.id === usuarioId);
      this.medicoId = m ? m.id : null;
      this.cdr.detectChanges();
    });
  }

  cargar() {
    this.loading = true;
    this.api.get<any>(`/triajes/${this.triajeId}`)
      .pipe(finalize(() => { this.loading = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: (data) => {
          this.triaje = data;
          this.factores = this.parseFactores(data?.factoresCriticos);
          this.cargarLogs();
        },
        error: () => { this.triaje = null; }
      });
  }

  private cargarLogs() {
    this.api.get<any[]>(`/triajes/${this.triajeId}/logs`)
      .pipe(catchError(() => of([])))
      .subscribe(data => { this.logs = data || []; this.cdr.detectChanges(); });
  }

  /** factoresCriticos se persiste como string JSON; tolera texto plano. */
  private parseFactores(raw: string | null | undefined): string[] {
    if (!raw) { return []; }
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) { return parsed.map(String); }
      return [String(parsed)];
    } catch {
      return [raw];
    }
  }

  atender() {
    if (!this.medicoId) {
      this.mostrarToast('No se pudo identificar al médico autenticado.', 'error');
      return;
    }
    this.atendiendo = true;
    this.api.put<any>(`/triajes/${this.triajeId}/atender?medico_id=${this.medicoId}`, {})
      .pipe(finalize(() => { this.atendiendo = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: (data) => {
          this.triaje = data;
          this.mostrarToast('Triaje marcado como atendido.', 'success');
        },
        error: (err) => this.mostrarToast('Error al atender: ' + (err.message || 'desconocido'), 'error')
      });
  }

  volver() { this.router.navigate(['/triajes']); }

  mostrarToast(mensaje: string, tipo: 'success' | 'error') {
    this.toast = { mensaje, tipo };
    setTimeout(() => { this.toast = null; this.cdr.detectChanges(); }, 4000);
    this.cdr.detectChanges();
  }
}
