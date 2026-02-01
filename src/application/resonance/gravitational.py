import numpy as np


class GravitationalPoint:
    def __init__(self, position: np.ndarray):
        self.position = position


class AttractionForce:
    def __init__(self, strength: float = 1.0):
        self.strength = strength

    def calculate_force(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        direction = p2 - p1
        distance = np.linalg.norm(direction)
        if distance == 0:
            return np.zeros_like(p1)
        return self.strength * direction / (distance**2)


class OrbitPath:
    def __init__(self):
        self.path: list[np.ndarray] = []

    def add_position(self, position: np.ndarray):
        self.path.append(position)


class EquilibriumState:
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def is_in_equilibrium(self, force: np.ndarray) -> bool:
        return np.linalg.norm(force) < self.tolerance


class GravitationalSystem:
    def __init__(self, gravitational_point: GravitationalPoint, attraction_force: AttractionForce):
        self.gravitational_point = gravitational_point
        self.attraction_force = attraction_force

    def apply_gravity(self, parameter_vector: np.ndarray) -> np.ndarray:
        force = self.attraction_force.calculate_force(parameter_vector, self.gravitational_point.position)
        return parameter_vector + force
