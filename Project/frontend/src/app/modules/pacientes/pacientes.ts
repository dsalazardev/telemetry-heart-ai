import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../../core/components/sidebar';
import { ApiService } from '../../core/services/api';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-pacientes',
  standalone: true,
  imports: [CommonModule, SidebarComponent, FormsModule, RouterModule],
  templateUrl: './pacientes.html',
  styleUrls: ['./pacientes.scss']
})
export class PacientesComponent implements OnInit {
  pacientes: any[] = [];
  loading = true;
  guardando = false;
  searchTerm = '';
  showModal = false;
  toast: { mensaje: string; tipo: 'success' | 'error' } | null = null;

  isEditing = false;
  nuevoPaciente: any = {
    id: null,
    usuario: {
      documento: '',
      nombres: '',
      apellidos: '',
      correo: '',
      password: 'password123',
      telefono: ''
    },
    fechaNacimiento: ''
  };

  constructor(
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.cargarPacientes();
  }

  cargarPacientes() {
    this.loading = true;
    this.api.get<any[]>('/pacientes')
      .pipe(finalize(() => {
        this.loading = false;
        this.cdr.detectChanges();
      }))
      .subscribe({
        next: (data) => {
          if (data && data.length) {
            this.pacientes = data;
          } else {
            // Mock data fallback
            this.pacientes = [
              { id: 1, usuario: { nombres: 'Carlos', apellidos: 'Pérez', documento: '1053' }, fechaNacimiento: '1959-01-01' },
              { id: 2, usuario: { nombres: 'Marta', apellidos: 'Lucía', documento: '2084' }, fechaNacimiento: '1979-06-15' }
            ];
          }
        },
        error: () => {
          this.pacientes = [
            { id: 1, usuario: { nombres: 'Carlos', apellidos: 'Pérez', documento: '1053' }, fechaNacimiento: '1959-01-01' },
            { id: 2, usuario: { nombres: 'Marta', apellidos: 'Lucía', documento: '2084' }, fechaNacimiento: '1979-06-15' }
          ];
        }
      });
  }

  // Create new patient
  crearPaciente() {
    this.guardando = true;
    this.api.post<any>('/pacientes', this.nuevoPaciente).subscribe({
      next: () => {
        this.showModal = false;
        this.guardando = false;
        this.resetForm();
        this.cargarPacientes();
        this.mostrarToast('Paciente registrado exitosamente', 'success');
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarToast('Error al crear paciente: ' + (err.message || 'Error desconocido'), 'error');
      }
    });
  }

  // Update existing patient
  actualizarPaciente() {
    if (!this.nuevoPaciente.id) return;
    this.guardando = true;
    this.api.put<any>(`/pacientes/${this.nuevoPaciente.id}`, this.nuevoPaciente).subscribe({
      next: () => {
        this.showModal = false;
        this.guardando = false;
        this.resetForm();
        this.cargarPacientes();
        this.mostrarToast('Paciente actualizado exitosamente', 'success');
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarToast('Error al actualizar paciente: ' + (err.message || 'Error desconocido'), 'error');
      }
    });
  }

  cerrarModal() {
    this.showModal = false;
    this.isEditing = false;
    this.resetForm();
  }

  // Open modal for editing a patient
  editar(paciente: any) {
    this.isEditing = true;
    this.nuevoPaciente = {
      id: paciente.id,
      usuario: {
        documento: paciente.usuario.documento,
        nombres: paciente.usuario.nombres,
        apellidos: paciente.usuario.apellidos,
        correo: paciente.usuario.correo,
        password: 'password123',
        telefono: paciente.usuario.telefono
      },
      fechaNacimiento: paciente.fechaNacimiento
    };
    this.showModal = true;
  }

  resetForm() {
    this.nuevoPaciente = {
      usuario: { documento: '', nombres: '', apellidos: '', correo: '', password: 'password123', telefono: '' },
      fechaNacimiento: ''
    };
  }

  mostrarToast(mensaje: string, tipo: 'success' | 'error') {
    this.toast = { mensaje, tipo };
    setTimeout(() => this.toast = null, 4000);
  }

  getRiskClass(riesgo: string) {
    return riesgo?.toLowerCase() || 'bajo';
  }
}
