import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';

interface TriajeApi {
  id: number;
  probabilidadRiesgo: number;
  nivelUrgencia: string;
  atendida: boolean;
  telegramEnviado: boolean;
  fechaEmision: string;
  paciente_id: number;
  medico_id: number | null;
}

interface PacienteApi {
  id: number;
  usuario?: { nombres?: string; apellidos?: string };
}

interface TriajeView extends TriajeApi {
  paciente: string;
}

@Component({
  selector: 'app-triajes',
  standalone: true,
  imports: [CommonModule, SidebarComponent, RouterModule],
  template: `
    <div class="app-container">
      <app-sidebar></app-sidebar>
      <main class="main-content">
        <header class="topbar">
          <div class="view-info">
            <h1>Triajes</h1>
            <p>Priorización cardiovascular asistida por IA</p>
          </div>
        </header>

        <div class="content-body fade-in">
          <div class="load-error" *ngIf="loadError && !loading">
            ⚠️ No se pudieron cargar los datos desde el backend. Mostrando la información disponible.
          </div>

          <!-- Filtros -->
          <div class="toolbar">
            <div class="filters">
              <button class="chip" [class.active]="filtro === 'todos'" (click)="setFiltro('todos')">
                Todos <span class="count">{{ totalTodos }}</span>
              </button>
              <button class="chip" [class.active]="filtro === 'pendientes'" (click)="setFiltro('pendientes')">
                Pendientes <span class="count">{{ totalPendientes }}</span>
              </button>
            </div>
          </div>

          <!-- Tabla -->
          <div class="glass-card table-card" *ngIf="!loading; else loader">
            <table class="data-table" *ngIf="visibles.length; else vacio">
              <thead>
                <tr>
                  <th>Paciente</th>
                  <th>Urgencia</th>
                  <th>Riesgo</th>
                  <th>Estado</th>
                  <th>Telegram</th>
                  <th>Fecha</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let t of visibles">
                  <td class="paciente">{{ t.paciente }}</td>
                  <td>
                    <span class="risk-pill" [ngClass]="'risk-' + (t.nivelUrgencia || '').toLowerCase()">
                      {{ (t.nivelUrgencia || 'N/D') | uppercase }}
                    </span>
                  </td>
                  <td>{{ (t.probabilidadRiesgo * 100) | number:'1.0-0' }}%</td>
                  <td>
                    <span class="state" [class.done]="t.atendida">
                      {{ t.atendida ? '✓ Atendido' : '● Pendiente' }}
                    </span>
                  </td>
                  <td>{{ t.telegramEnviado ? '📨' : '—' }}</td>
                  <td class="muted">{{ t.fechaEmision | date:'short' }}</td>
                  <td>
                    <a class="btn btn-sm" [routerLink]="['/triajes', t.id]">Ver</a>
                  </td>
                </tr>
              </tbody>
            </table>

            <ng-template #vacio>
              <div class="empty-state">
                <p style="font-size:2rem;">🩺</p>
                <p>No hay triajes {{ filtro === 'pendientes' ? 'pendientes' : 'registrados' }}.</p>
              </div>
            </ng-template>
          </div>

          <ng-template #loader>
            <div class="glass-card" style="text-align:center; padding:4rem; color:var(--text-muted);">
              Cargando triajes...
            </div>
          </ng-template>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .content-body { padding-top: 0; }
    .load-error {
      display:flex; align-items:center; gap:0.5rem; padding:0.75rem 1rem; margin-bottom:1.5rem;
      background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25);
      border-radius:var(--radius-md); color:var(--danger); font-size:0.875rem;
    }
    .toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem; }
    .filters { display:flex; gap:0.5rem; }
    .chip {
      display:inline-flex; align-items:center; gap:0.5rem; padding:0.5rem 1rem;
      border:1px solid var(--border); background:white; border-radius:999px;
      cursor:pointer; font-family:inherit; font-weight:600; font-size:0.875rem; color:var(--text-muted);
    }
    .chip.active { background:var(--primary); color:white; border-color:var(--primary); }
    .chip .count {
      background:rgba(0,0,0,0.08); padding:0.05rem 0.5rem; border-radius:999px; font-size:0.75rem;
    }
    .chip.active .count { background:rgba(255,255,255,0.25); }

    .table-card { padding:0; overflow:hidden; }
    .data-table { width:100%; border-collapse:collapse; }
    .data-table thead th {
      text-align:left; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em;
      color:var(--text-muted); padding:1rem 1.25rem; border-bottom:1px solid var(--border);
    }
    .data-table tbody td { padding:1rem 1.25rem; border-bottom:1px solid var(--border); font-size:0.9375rem; }
    .data-table tbody tr:last-child td { border-bottom:none; }
    .data-table tbody tr:hover { background:var(--bg-main); }
    .paciente { font-weight:600; }
    .muted { color:var(--text-muted); font-size:0.875rem; }

    .risk-pill {
      display:inline-block; padding:0.15rem 0.7rem; border-radius:999px;
      font-size:0.7rem; font-weight:700; letter-spacing:0.05em;
    }
    .risk-bajo { background:rgba(34,197,94,0.15); color:#16a34a; }
    .risk-medio { background:rgba(245,158,11,0.15); color:#d97706; }
    .risk-alto { background:rgba(239,68,68,0.15); color:#dc2626; }

    .state { font-weight:600; font-size:0.875rem; color:var(--warning); }
    .state.done { color:var(--success); }

    .empty-state { text-align:center; padding:4rem; color:var(--text-muted); }
    .btn-sm { padding:0.35rem 0.9rem; font-size:0.8rem; border-radius:var(--radius-sm);
      background:var(--primary-low); color:var(--primary); text-decoration:none; font-weight:600; }
    .btn-sm:hover { background:var(--primary); color:white; }
  `]
})
export class TriajesComponent implements OnInit {
  todos: TriajeView[] = [];
  pendientes: TriajeView[] = [];
  visibles: TriajeView[] = [];
  filtro: 'todos' | 'pendientes' = 'todos';
  loading = true;
  loadError = false;

  get totalTodos() { return this.todos.length; }
  get totalPendientes() { return this.pendientes.length; }

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.loading = true;
    this.loadError = false;
    forkJoin({
      triajes: this.api.get<TriajeApi[]>('/triajes').pipe(
        catchError(() => { this.loadError = true; return of([] as TriajeApi[]); })
      ),
      pacientes: this.api.get<PacienteApi[]>('/pacientes').pipe(
        catchError(() => { this.loadError = true; return of([] as PacienteApi[]); })
      )
    })
      .pipe(finalize(() => { this.loading = false; this.cdr.detectChanges(); }))
      .subscribe(({ triajes, pacientes }) => {
        const nombrePorId = new Map<number, string>();
        for (const p of pacientes) {
          const n = `${p.usuario?.nombres ?? ''} ${p.usuario?.apellidos ?? ''}`.trim();
          nombrePorId.set(p.id, n || `Paciente #${p.id}`);
        }

        this.todos = triajes
          .map(t => ({ ...t, paciente: nombrePorId.get(t.paciente_id) ?? `Paciente #${t.paciente_id}` }))
          .sort((a, b) => +new Date(b.fechaEmision) - +new Date(a.fechaEmision));
        this.pendientes = this.todos.filter(t => !t.atendida);
        this.aplicarFiltro();
      });
  }

  setFiltro(f: 'todos' | 'pendientes') {
    this.filtro = f;
    this.aplicarFiltro();
  }

  private aplicarFiltro() {
    this.visibles = this.filtro === 'pendientes' ? this.pendientes : this.todos;
  }
}
