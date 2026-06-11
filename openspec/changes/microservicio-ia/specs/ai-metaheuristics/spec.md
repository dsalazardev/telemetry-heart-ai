## ADDED Requirements

### Requirement: Genetic algorithm for feature selection
The system SHALL implement a genetic algorithm using DEAP to identify the optimal feature subset for cardiac risk prediction.

#### Scenario: Feature selection execution
- **WHEN** the genetic algorithm is invoked with the heart dataset
- **THEN** the system initializes a population of 50 individuals
- **AND** runs for 20 generations
- **AND** evaluates fitness using F1-score weighted
- **AND** returns the best feature subset, fitness score, and generation history

#### Scenario: Feature selection results
- **WHEN** the genetic algorithm completes
- **THEN** the system stores the selected feature indices in `importanciaVariables` (JSON)
- **AND** updates the `Prediccion` record with the selected features

### Requirement: PSO for hyperparameter tuning
The system SHALL implement a custom Particle Swarm Optimization (PSO) algorithm to optimize RandomForest hyperparameters.

#### Scenario: PSO execution
- **WHEN** the PSO algorithm is invoked with the heart dataset
- **THEN** the system initializes a swarm of 30 particles
- **AND** runs for 30 iterations
- **AND** optimizes the hyperparameters: `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`
- **AND** returns the best hyperparameters and fitness score

#### Scenario: PSO results storage
- **WHEN** the PSO algorithm completes
- **THEN** the system stores the best hyperparameters in `metadataTecnica` (JSON)
- **AND** updates the model configuration

### Requirement: Metaheuristics endpoint
The system SHALL expose a POST endpoint `/agent/train` (reused) to trigger both metaheuristic algorithms.

#### Scenario: Combined execution
- **WHEN** the training endpoint is called with `run_metaheuristics: true`
- **THEN** the system first runs the genetic algorithm for feature selection
- **AND** then runs PSO on the selected features for hyperparameter tuning
- **AND** returns a combined report with both results
