import { Routes } from '@angular/router';
import { LoginComponent } from './modules/login/login'; 
import { DashboardComponent } from './modules/dashboard/dashboard';
import { PacientesComponent } from './modules/pacientes/pacientes';
import { PatientDetailComponent } from './modules/pacientes/patient-detail';
import { authGuard } from './core/guards/auth';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { 
    path: 'dashboard', 
    component: DashboardComponent,
    canActivate: [authGuard] 
  },
  { 
    path: 'pacientes', 
    component: PacientesComponent,
    canActivate: [authGuard] 
  },
  { 
    path: 'pacientes/:id', 
    component: PatientDetailComponent,
    canActivate: [authGuard] 
  },
  { 
    path: 'alertas', 
    component: PacientesComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'config', 
    component: DashboardComponent, 
    canActivate: [authGuard] 
  },
  { path: '', redirectTo: '/login', pathMatch: 'full' }
];