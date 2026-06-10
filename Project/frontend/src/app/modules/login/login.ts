import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class LoginComponent {
  usuario = { correo: 'juan@test.com', password: 'clave123' };
  loading = false;

  constructor(private api: ApiService, private router: Router) {}

  onSubmit() {
    this.loading = true;
    this.api.post<any>('/auth/login', this.usuario).subscribe({
      next: (res: any) => {
        console.log('Login exitoso:', res);
        localStorage.setItem('token', res.access_token);
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        console.error('Error en el login:', err);
        this.loading = false;
        alert('Error: ' + (err.message || 'Credenciales incorrectas o servidor no disponible'));
      }
    });
  }

  ngOnInit() {
    this.api.checkHealth().subscribe(res => {
      console.log("¡Conexión exitosa con el Backend!", res);
    });
  }
}