import random
import numpy as np
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from deap import base, creator, tools, algorithms
import pandas as pd

class GeneticEngine:
    def __init__(self, n_features: int = 13, population_size: int = 50, generations: int = 20):
        self.n_features = n_features
        self.population_size = population_size
        self.generations = generations
        self.best_individual = None
        self.best_fitness = 0
        self.history = []
        
        # Setup DEAP
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 1)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attr_bool, n=self.n_features)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self._evaluate)
        self.toolbox.register("mate", tools.cxUniform, indpb=0.8)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.2)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _evaluate(self, individual: List[int]) -> Tuple[float]:
        """Evaluate fitness: F1-score of RandomForest on selected features"""
        if not hasattr(self, 'X') or not hasattr(self, 'y'):
            return (0.0,)
        
        # Get selected features
        selected = [i for i, val in enumerate(individual) if val == 1]
        if len(selected) == 0:
            return (0.0,)
        
        X_selected = self.X.iloc[:, selected]
        X_train, X_test, y_train, y_test = train_test_split(X_selected, self.y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        f1 = f1_score(y_test, y_pred, average='weighted')
        return (f1,)
    
    def run(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Run genetic algorithm for feature selection"""
        self.X = X
        self.y = y
        
        pop = self.toolbox.population(n=self.population_size)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        pop, log = algorithms.eaSimple(
            pop, self.toolbox,
            cxpb=0.7, mutpb=0.2,
            ngen=self.generations,
            stats=stats,
            halloffame=hof,
            verbose=False
        )
        
        self.best_individual = hof[0]
        self.best_fitness = hof[0].fitness.values[0]
        self.history = log
        
        selected_features = [i for i, val in enumerate(self.best_individual) if val == 1]
        
        return {
            "selected_features": selected_features,
            "feature_names": [X.columns[i] for i in selected_features],
            "n_selected": len(selected_features),
            "best_fitness": self.best_fitness,
            "generations": self.generations
        }
