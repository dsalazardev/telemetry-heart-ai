import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
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
}

interface PacienteApi {
  id: number;
  usuario?: { nombres?: string; apellidos?: string };
}

interface AlertaView {
  id: number;
  tipo: string;
  paciente: string;
  mensaje: string;
  fecha: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss']
})
export class DashboardComponent implements OnInit {
  resumen = {
    pacientesTotales: 0,
    alertasCriticas: 0,
    triajesPendientes: 0
  };

  alertas: AlertaView[] = [];
  loading = true;
  loadError = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.loadError = false;

    // Datos reales del backend. Cada stream cae a un valor seguro si falla,
    // de modo que un endpoint caído no oculta los demás (sin datos simulados).
    forkJoin({
      pacientes: this.api.get<PacienteApi[]>('/pacientes').pipe(
        catchError(() => { this.loadError = true; return of([] as PacienteApi[]); })
      ),
      pendientes: this.api.get<any[]>('/triajes/pendientes').pipe(
        catchError(() => { this.loadError = true; return of([] as any[]); })
      ),
      alertas: this.api.get<AlertaApi[]>('/alertas').pipe(
        catchError(() => { this.loadError = true; return of([] as AlertaApi[]); })
      )
    }).subscribe(({ pacientes, pendientes, alertas }) => {
      // Mapa paciente_id -> nombre completo para resolver el autor de cada alerta.
      const nombrePorId = new Map<number, string>();
      for (const p of pacientes) {
        const nombre = `${p.usuario?.nombres ?? ''} ${p.usuario?.apellidos ?? ''}`.trim();
        nombrePorId.set(p.id, nombre || `Paciente #${p.id}`);
      }

      this.resumen.pacientesTotales = pacientes.length;
      this.resumen.triajesPendientes = pendientes.length;
      // El backend emite el nivel de riesgo del microservicio: 'bajo' | 'medio' | 'alto'.
      this.resumen.alertasCriticas = alertas.filter(a => a.tipo === 'alto').length;

      this.alertas = alertas
        .sort((a, b) => +new Date(b.fechaEmision) - +new Date(a.fechaEmision))
        .map(a => ({
          id: a.id,
          tipo: a.tipo,
          paciente: nombrePorId.get(a.paciente_id) ?? `Paciente #${a.paciente_id}`,
          mensaje: a.mensaje,
          fecha: a.fechaEmision
        }));

      this.loading = false;
    });
  }
}
