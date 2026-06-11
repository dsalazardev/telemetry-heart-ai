import random
import numpy as np
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
import pandas as pd

class Particle:
    """Particle for PSO algorithm"""
    def __init__(self, n_dimensions: int, bounds: List[Tuple[float, float]]):
        self.n_dimensions = n_dimensions
        self.bounds = bounds
        
        # Initialize position and velocity
        self.position = [random.uniform(bounds[i][0], bounds[i][1]) for i in range(n_dimensions)]
        self.velocity = [random.uniform(-1, 1) for _ in range(n_dimensions)]
        
        # Best known position
        self.best_position = self.position.copy()
        self.best_fitness = -float('inf')
    
    def update_velocity(self, global_best: List[float], w: float = 0.7, c1: float = 1.5, c2: float = 1.5):
        """Update velocity using PSO formula"""
        for i in range(self.n_dimensions):
            r1, r2 = random.random(), random.random()
            cognitive = c1 * r1 * (self.best_position[i] - self.position[i])
            social = c2 * r2 * (global_best[i] - self.position[i])
            self.velocity[i] = w * self.velocity[i] + cognitive + social
    
    def update_position(self):
        """Update position and apply bounds"""
        for i in range(self.n_dimensions):
            self.position[i] += self.velocity[i]
            # Apply bounds
            self.position[i] = max(self.bounds[i][0], min(self.bounds[i][1], self.position[i]))

class PSOEngine:
    def __init__(self, n_particles: int = 30, n_iterations: int = 30):
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.swarm = []
        self.global_best_position = None
        self.global_best_fitness = -float('inf')
        self.history = []
        
        # Hyperparameter bounds: [n_estimators, max_depth, min_samples_split, min_samples_leaf]
        self.bounds = [
            (10, 200),   # n_estimators
            (2, 20),     # max_depth
            (2, 10),     # min_samples_split
            (1, 5)       # min_samples_leaf
        ]
        self.n_dimensions = len(self.bounds)
    
    def _evaluate(self, position: List[float], X: pd.DataFrame, y: pd.Series) -> float:
        """Evaluate fitness: F1-score of RandomForest with given hyperparameters"""
        params = {
            'n_estimators': int(position[0]),
            'max_depth': int(position[1]),
            'min_samples_split': int(position[2]),
            'min_samples_leaf': int(position[3])
        }
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(**params, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        return f1_score(y_test, y_pred, average='weighted')
    
    def run(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Run PSO for hyperparameter tuning"""
        # Initialize swarm
        self.swarm = [Particle(self.n_dimensions, self.bounds) for _ in range(self.n_particles)]
        
        # Initial evaluation
        for particle in self.swarm:
            fitness = self._evaluate(particle.position, X, y)
            particle.best_fitness = fitness
            particle.best_position = particle.position.copy()
            
            if fitness > self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best_position = particle.position.copy()
        
        # PSO iterations
        for iteration in range(self.n_iterations):
            for particle in self.swarm:
                particle.update_velocity(self.global_best_position)
                particle.update_position()
                
                fitness = self._evaluate(particle.position, X, y)
                
                if fitness > particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = particle.position.copy()
                
                if fitness > self.global_best_fitness:
                    self.global_best_fitness = fitness
                    self.global_best_position = particle.position.copy()
            
            self.history.append({
                "iteration": iteration,
                "best_fitness": self.global_best_fitness
            })
        
        best_params = {
            'n_estimators': int(self.global_best_position[0]),
            'max_depth': int(self.global_best_position[1]),
            'min_samples_split': int(self.global_best_position[2]),
            'min_samples_leaf': int(self.global_best_position[3])
        }
        
        return {
            "best_params": best_params,
            "best_fitness": self.global_best_fitness,
            "n_iterations": self.n_iterations,
            "n_particles": self.n_particles
        }
