import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';

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

  alertas: any[] = [];
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    // En una implementación real, cargaríamos estos datos del backend
    // Por ahora simulamos la carga para el diseño premium
    
    // Simulación de alertas críticas
    this.api.get<any[]>('/alertas').subscribe({
      next: (data) => {
        this.alertas = data || [];
        this.resumen.alertasCriticas = this.alertas.filter(a => a.tipo === 'CRITICA').length;
        this.loading = false;
      },
      error: () => {
        // Fallback para demo si el backend no tiene datos aún
        this.alertas = [
          { id: 1, paciente: 'Carlos Pérez', tipo: 'CRITICA', mensaje: 'Frecuencia cardíaca > 120 bpm', fecha: new Date() },
          { id: 2, paciente: 'Marta Lucía', tipo: 'ADVERTENCIA', mensaje: 'SpO2 < 90%', fecha: new Date() }
        ];
        this.resumen.alertasCriticas = 1;
        this.resumen.pacientesTotales = 12;
        this.resumen.triajesPendientes = 5;
        this.loading = false;
      }
    });
  }
}
