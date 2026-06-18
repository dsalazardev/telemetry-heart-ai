import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';

interface AlertaApi {
  id: number;
  tipo: string;
  mensaje: string;
  leida: boolean;
  atendida: boolean;
  fechaEmision: string;
  paciente_id: number;
  medico_id: number | null;
  triaje_id: number | null;
}

interface PacienteApi {
  id: number;
  usuario?: { nombres?: string; apellidos?: string };
}

interface AlertaView extends AlertaApi {
  paciente: string;
}

@Component({
  selector: 'app-alertas',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  template: `
    <div class="app-container">
      <app-sidebar></app-sidebar>
      <main class="main-content">
        <header class="topbar">
          <div class="view-info">
            <h1>Alertas Críticas</h1>
            <p>Notificaciones de riesgo generadas por el sistema</p>
          </div>
        </header>

        <div class="content-body fade-in">
          <div class="load-error" *ngIf="loadError && !loading">
            ⚠️ No se pudieron cargar los datos desde el backend. Mostrando la información disponible.
          </div>

          <div class="toolbar">
            <div class="filters">
              <button class="chip" [class.active]="filtro === 'pendientes'" (click)="setFiltro('pendientes')">
                Pendientes <span class="count">{{ totalPendientes }}</span>
              </button>
              <button class="chip" [class.active]="filtro === 'todas'" (click)="setFiltro('todas')">
                Todas <span class="count">{{ totalTodas }}</span>
              </button>
            </div>
          </div>

          <div *ngIf="!loading; else loader">
            <div class="alert-list" *ngIf="visibles.length; else vacio">
              <div *ngFor="let a of visibles" class="glass-card alert-item" [ngClass]="(a.tipo || '').toLowerCase()">
                <div class="alert-status"></div>
                <div class="alert-content">
                  <div class="alert-header">
                    <span class="paciente-name">{{ a.paciente }}</span>
                    <span class="risk-pill" [ngClass]="'risk-' + (a.tipo || '').toLowerCase()">{{ (a.tipo || 'N/D') | uppercase }}</span>
                    <span class="badge" *ngIf="!a.leida">No leída</span>
                    <span class="badge done" *ngIf="a.atendida">Atendida</span>
                    <span class="alert-time">{{ a.fechaEmision | date:'short' }}</span>
                  </div>
                  <p class="alert-msg">{{ a.mensaje }}</p>
                </div>
                <div class="alert-actions">
                  <button class="btn-mini" *ngIf="!a.leida" [disabled]="busy.has(a.id)" (click)="marcarLeida(a)">Marcar leída</button>
                  <button class="btn-mini" *ngIf="medicoId && !a.medico_id" [disabled]="busy.has(a.id)" (click)="asignarme(a)">Asignarme</button>
                  <button class="btn-mini primary" *ngIf="!a.atendida" [disabled]="busy.has(a.id)" (click)="atender(a)">Atender</button>
                </div>
              </div>
            </div>

            <ng-template #vacio>
              <div class="glass-card empty-state">
                <p style="font-size:2rem;">✅</p>
                <p>No hay alertas {{ filtro === 'pendientes' ? 'pendientes' : 'registradas' }}.</p>
              </div>
            </ng-template>
          </div>

          <ng-template #loader>
            <div class="glass-card" style="text-align:center; padding:4rem; color:var(--text-muted);">Cargando alertas...</div>
          </ng-template>
        </div>
      </main>
    </div>

    <div *ngIf="toast" class="toast-detail" [ngClass]="toast.tipo">
      <span>{{ toast.tipo === 'success' ? '✅' : '❌' }}</span>
      <p>{{ toast.mensaje }}</p>
    </div>
  `,
  styles: [`
    .load-error { display:flex; align-items:center; gap:0.5rem; padding:0.75rem 1rem; margin-bottom:1.5rem;
      background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25);
      border-radius:var(--radius-md); color:var(--danger); font-size:0.875rem; }
    .toolbar { display:flex; margin-bottom:1.25rem; }
    .filters { display:flex; gap:0.5rem; }
    .chip { display:inline-flex; align-items:center; gap:0.5rem; padding:0.5rem 1rem;
      border:1px solid var(--border); background:white; border-radius:999px; cursor:pointer;
      font-family:inherit; font-weight:600; font-size:0.875rem; color:var(--text-muted); }
    .chip.active { background:var(--primary); color:white; border-color:var(--primary); }
    .chip .count { background:rgba(0,0,0,0.08); padding:0.05rem 0.5rem; border-radius:999px; font-size:0.75rem; }
    .chip.active .count { background:rgba(255,255,255,0.25); }

    .alert-list { display:flex; flex-direction:column; gap:0.75rem; }
    .alert-item { display:flex; align-items:center; gap:1rem; padding:1rem 1.25rem; border-left:4px solid var(--border); }
    .alert-status { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
    .alert-item.alto { border-left-color:var(--danger); } .alert-item.alto .alert-status { background:var(--danger); }
    .alert-item.medio { border-left-color:var(--warning); } .alert-item.medio .alert-status { background:var(--warning); }
    .alert-item.bajo { border-left-color:var(--success); } .alert-item.bajo .alert-status { background:var(--success); }

    .alert-content { flex:1; }
    .alert-header { display:flex; align-items:center; gap:0.6rem; margin-bottom:0.25rem; flex-wrap:wrap; }
    .paciente-name { font-weight:600; font-size:0.9375rem; }
    .alert-time { font-size:0.75rem; color:var(--text-muted); margin-left:auto; }
    .alert-msg { font-size:0.875rem; color:var(--text-muted); margin:0; }

    .risk-pill { display:inline-block; padding:0.1rem 0.6rem; border-radius:999px; font-size:0.65rem; font-weight:700; letter-spacing:0.05em; }
    .risk-bajo { background:rgba(34,197,94,0.15); color:#16a34a; }
    .risk-medio { background:rgba(245,158,11,0.15); color:#d97706; }
    .risk-alto { background:rgba(239,68,68,0.15); color:#dc2626; }
    .badge { font-size:0.65rem; font-weight:700; padding:0.1rem 0.55rem; border-radius:999px; background:var(--primary-low); color:var(--primary); }
    .badge.done { background:rgba(34,197,94,0.15); color:#16a34a; }

    .alert-actions { display:flex; gap:0.5rem; flex-shrink:0; }
    .btn-mini { padding:0.35rem 0.8rem; font-size:0.78rem; font-weight:600; border-radius:var(--radius-sm);
      border:1px solid var(--border); background:white; color:var(--text-muted); cursor:pointer; }
    .btn-mini:hover:not(:disabled) { border-color:var(--primary-mid); color:var(--primary); }
    .btn-mini.primary { background:var(--primary); color:white; border-color:var(--primary); }
    .btn-mini:disabled { opacity:0.5; cursor:default; }

    .empty-state { text-align:center; padding:4rem; color:var(--text-muted); }
    .toast-detail { position:fixed; bottom:2rem; right:2rem; display:flex; align-items:center; gap:0.75rem;
      padding:1rem 1.5rem; border-radius:var(--radius-md); box-shadow:var(--shadow-lg); z-index:2000; font-weight:500; }
    .toast-detail.success { background:var(--success); color:white; }
    .toast-detail.error { background:var(--danger); color:white; }
  `]
})
export class AlertasComponent implements OnInit {
  todas: AlertaView[] = [];
  pendientes: AlertaView[] = [];
  visibles: AlertaView[] = [];
  filtro: 'todas' | 'pendientes' = 'pendientes';
  loading = true;
  loadError = false;
  medicoId: number | null = null;
  busy = new Set<number>();
  toast: { mensaje: string; tipo: 'success' | 'error' } | null = null;

  get totalTodas() { return this.todas.length; }
  get totalPendientes() { return this.pendientes.length; }

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.resolverMedico();
    this.cargar();
  }

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
    this.loadError = false;
    forkJoin({
      alertas: this.api.get<AlertaApi[]>('/alertas').pipe(catchError(() => { this.loadError = true; return of([] as AlertaApi[]); })),
      pacientes: this.api.get<PacienteApi[]>('/pacientes').pipe(catchError(() => { this.loadError = true; return of([] as PacienteApi[]); }))
    })
      .pipe(finalize(() => { this.loading = false; this.cdr.detectChanges(); }))
      .subscribe(({ alertas, pacientes }) => {
        const nombrePorId = new Map<number, string>();
        for (const p of pacientes) {
          const n = `${p.usuario?.nombres ?? ''} ${p.usuario?.apellidos ?? ''}`.trim();
          nombrePorId.set(p.id, n || `Paciente #${p.id}`);
        }
        this.todas = alertas
          .map(a => ({ ...a, paciente: nombrePorId.get(a.paciente_id) ?? `Paciente #${a.paciente_id}` }))
          .sort((a, b) => +new Date(b.fechaEmision) - +new Date(a.fechaEmision));
        this.pendientes = this.todas.filter(a => !a.atendida);
        this.aplicarFiltro();
      });
  }

  setFiltro(f: 'todas' | 'pendientes') { this.filtro = f; this.aplicarFiltro(); }
  private aplicarFiltro() { this.visibles = this.filtro === 'pendientes' ? this.pendientes : this.todas; }

  marcarLeida(a: AlertaView) {
    this.accion(a, this.api.put(`/alertas/${a.id}/leer`, {}), 'Alerta marcada como leída.');
  }

  asignarme(a: AlertaView) {
    if (!this.medicoId) { return; }
    this.accion(a, this.api.put(`/alertas/${a.id}/asignar?medico_id=${this.medicoId}`, {}), 'Alerta asignada a ti.');
  }

  atender(a: AlertaView) {
    this.accion(a, this.api.put(`/alertas/${a.id}/atender`, {}), 'Alerta atendida.');
  }

  /** Aplica el resultado de la acción sobre la alerta en memoria, sin recargar todo. */
  private accion(a: AlertaView, obs: any, okMsg: string) {
    this.busy.add(a.id);
    obs.pipe(finalize(() => { this.busy.delete(a.id); this.cdr.detectChanges(); }))
      .subscribe({
        next: (updated: AlertaApi) => {
          Object.assign(a, updated);
          this.pendientes = this.todas.filter(x => !x.atendida);
          this.aplicarFiltro();
          this.mostrarToast(okMsg, 'success');
        },
        error: (err: any) => this.mostrarToast('Error: ' + (err.message || 'desconocido'), 'error')
      });
  }

  mostrarToast(mensaje: string, tipo: 'success' | 'error') {
    this.toast = { mensaje, tipo };
    setTimeout(() => { this.toast = null; this.cdr.detectChanges(); }, 4000);
    this.cdr.detectChanges();
  }
}
