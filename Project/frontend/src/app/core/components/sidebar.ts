import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="logo">❤️ HeartAI</span>
      </div>
      
      <nav class="sidebar-nav">
        <ul>
          <li>
            <a routerLink="/dashboard" routerLinkActive="active">
              <span class="icon">📊</span>
              <span class="label">Panel General</span>
            </a>
          </li>
          <li>
            <a routerLink="/pacientes" routerLinkActive="active">
              <span class="icon">👥</span>
              <span class="label">Pacientes</span>
            </a>
          </li>
          <li>
            <a routerLink="/triajes" routerLinkActive="active">
              <span class="icon">🩺</span>
              <span class="label">Triajes</span>
            </a>
          </li>
          <li>
            <a routerLink="/alertas" routerLinkActive="active">
              <span class="icon">⚠️</span>
              <span class="label">Alertas Críticas</span>
            </a>
          </li>
          <li>
            <a routerLink="/config" routerLinkActive="active">
              <span class="icon">⚙️</span>
              <span class="label">Configuración</span>
            </a>
          </li>
        </ul>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" (click)="logout()">
          <span class="icon">🚪</span>
          <span class="label">Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      width: var(--sidebar-width);
      height: 100vh;
      background: var(--bg-card);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      position: fixed;
      left: 0;
      top: 0;
      z-index: 100;
      transition: all 0.3s ease;
    }

    .sidebar-header {
      padding: 2rem;
      border-bottom: 1px solid var(--border);
      .logo {
        font-family: 'Outfit', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary);
      }
    }

    .sidebar-nav {
      flex: 1;
      padding: 1.5rem 1rem;
      
      ul {
        list-style: none;
        
        li {
          margin-bottom: 0.5rem;
          
          a {
            display: flex;
            align-items: center;
            padding: 0.875rem 1rem;
            border-radius: var(--radius-md);
            text-decoration: none;
            color: var(--text-muted);
            transition: all 0.2s ease;
            gap: 1rem;

            &:hover {
              background: var(--primary-low);
              color: var(--primary);
            }

            &.active {
              background: var(--primary);
              color: white;
              box-shadow: 0 4px 12px hsla(var(--primary-hue), 90%, 55%, 0.2);
            }
          }
        }
      }
    }

    .sidebar-footer {
      padding: 1.5rem;
      border-top: 1px solid var(--border);
      
      .logout-btn {
        width: 100%;
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        border: none;
        background: transparent;
        color: var(--danger);
        cursor: pointer;
        border-radius: var(--radius-md);
        gap: 1rem;
        font-family: inherit;
        font-weight: 500;

        &:hover {
          background: var(--danger-low);
        }
      }
    }
  `]
})
export class SidebarComponent {
  logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
}
