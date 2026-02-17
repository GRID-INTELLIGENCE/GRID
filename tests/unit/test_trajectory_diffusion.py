"""
Unit tests for GRID trajectory diffusion module.

Note: These tests require the 'motion' module which is not yet implemented.
Tests are skipped if the module is not available.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add motion module to path
motion_path = Path(__file__).parent.parent.parent / "motion"
if str(motion_path.parent) not in sys.path:
    sys.path.insert(0, str(motion_path.parent))

# Skip entire module if motion is not available
try:
    from motion.trajectory_diffusion import (  # type: ignore[import-not-found]
        BSplineEncoder,
        BSplineTrajectory,
        CostFunction,
        CostGuidedSampler,
        TrajectoryConfig,
        TrajectoryPrior,
    )
except ImportError:
    pytest.skip(
        "motion.trajectory_diffusion module not available - skipping tests",
        allow_module_level=True,
    )

import numpy as np


class TestTrajectoryConfig:
    """Tests for TrajectoryConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TrajectoryConfig()

        assert config.enabled is True
        assert config.bspline_order == 4
        assert config.num_control_points == 16
        assert config.num_samples == 64
        assert config.guidance_scale == 0.7

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TrajectoryConfig(enabled=False, bspline_order=3, num_samples=128, collision_weight=2.0)

        assert config.enabled is False
        assert config.bspline_order == 3
        assert config.num_samples == 128
        assert config.collision_weight == 2.0


class TestBSplineTrajectory:
    """Tests for BSplineTrajectory."""

    def test_trajectory_creation(self):
        """Test creating a B-spline trajectory."""
        control_points: np.ndarray = np.array([[0, 0], [1, 1], [2, 0], [3, 1]])  # type: ignore[assignment]
        traj = BSplineTrajectory(control_points=control_points, order=4)

        assert traj.order == 4
        assert traj.control_points.shape == (4, 2)

    def test_trajectory_evaluation(self):
        """Test evaluating trajectory at parameter values."""
        control_points: np.ndarray = np.array([[0, 0], [1, 1], [2, 0], [3, 1]])  # type: ignore[assignment]
        traj = BSplineTrajectory(control_points=control_points)

        t: np.ndarray = np.array([0.0, 0.5, 1.0])  # type: ignore[assignment]
        result = traj.evaluate(t)

        assert result.shape == (3, 2)
        # Start point
        np.testing.assert_array_almost_equal(result[0], [0, 0])  # type: ignore[attr-defined]
        # End point
        np.testing.assert_array_almost_equal(result[2], [3, 1])  # type: ignore[attr-defined]

    def test_to_dense(self):
        """Test converting to dense representation."""
        control_points: np.ndarray = np.array([[0, 0], [1, 1], [2, 0]])  # type: ignore[assignment]
        traj = BSplineTrajectory(control_points=control_points)

        dense = traj.to_dense(num_points=50)

        assert dense.shape == (50, 2)


class TestBSplineEncoder:
    """Tests for BSplineEncoder."""

    def test_encode_downsample(self):
        """Test encoding a pattern that needs downsampling."""
        encoder = BSplineEncoder(order=4, num_control_points=8)

        # Create a pattern with many points
        pattern: np.ndarray = np.random.randn(100, 2)  # type: ignore[assignment,attr-defined]
        trajectory = encoder.encode(pattern)

        assert isinstance(trajectory, BSplineTrajectory)
        assert trajectory.control_points.shape == (8, 2)

    def test_encode_upsample(self):
        """Test encoding a pattern that needs upsampling."""
        encoder = BSplineEncoder(order=4, num_control_points=16)

        # Create a pattern with few points
        pattern: np.ndarray = np.random.randn(4, 2)  # type: ignore[assignment,attr-defined]
        trajectory = encoder.encode(pattern)

        assert trajectory.control_points.shape == (16, 2)

    def test_decode(self):
        """Test decoding a trajectory to dense points."""
        encoder = BSplineEncoder()

        control_points: np.ndarray = np.random.randn(16, 2)  # type: ignore[assignment,attr-defined]
        trajectory = BSplineTrajectory(control_points=control_points)

        dense = encoder.decode(trajectory, num_points=100)

        assert dense.shape == (100, 2)


class TestTrajectoryPrior:
    """Tests for TrajectoryPrior."""

    def test_prior_creation(self):
        """Test creating a trajectory prior."""
        config = TrajectoryConfig()
        prior = TrajectoryPrior(config)

        assert prior.is_loaded is False

    def test_sample_prior_fallback(self):
        """Test sampling from prior without loaded model."""
        config = TrajectoryConfig()
        prior = TrajectoryPrior(config)

        samples = prior.sample_prior(num_samples=10, trajectory_dim=16)

        assert samples.shape == (10, 16, 2)


class TestCostFunction:
    """Tests for CostFunction."""

    def test_smoothness_cost(self):
        """Test smoothness cost calculation."""
        config = TrajectoryConfig(smoothness_weight=1.0)
        cost_fn = CostFunction(config)

        # Smooth trajectory
        smooth: np.ndarray = np.linspace([0, 0], [10, 10], 100)  # type: ignore[assignment,arg-type,attr-defined]
        smooth_cost = cost_fn.smoothness_cost(smooth)

        # Jerky trajectory
        jerky = smooth.copy()
        jerky[50] += [5, 5]
        jerky_cost = cost_fn.smoothness_cost(jerky)

        assert jerky_cost > smooth_cost

    def test_goal_reaching_cost(self):
        """Test goal-reaching cost calculation."""
        config = TrajectoryConfig(goal_reaching_weight=1.0)
        cost_fn = CostFunction(config)

        trajectory: np.ndarray = np.array([[0, 0], [1, 1], [2, 2]])  # type: ignore[assignment]
        goal: np.ndarray = np.array([2, 2])  # type: ignore[assignment]

        cost = cost_fn.goal_reaching_cost(trajectory, goal)

        assert cost == 0.0  # Final point matches goal

    def test_collision_cost(self):
        """Test collision cost calculation."""
        config = TrajectoryConfig(collision_weight=1.0)
        cost_fn = CostFunction(config)

        trajectory: np.ndarray = np.array([[0, 0], [1, 1], [2, 2]])  # type: ignore[assignment]
        obstacles = [{"center": np.array([1, 1]), "radius": 0.5}]  # type: ignore[arg-type]

        cost = cost_fn.collision_cost(trajectory, obstacles)

        assert cost > 0.0  # Trajectory passes through obstacle


class TestCostGuidedSampler:
    """Tests for CostGuidedSampler."""

    def test_sampler_creation(self):
        """Test creating a cost-guided sampler."""
        config = TrajectoryConfig(num_samples=10)
        prior = TrajectoryPrior(config)
        cost_fn = CostFunction(config)
        sampler = CostGuidedSampler(prior, cost_fn, config)

        assert sampler.config.num_samples == 10

    def test_sample_trajectories(self):
        """Test sampling multiple trajectories."""
        config = TrajectoryConfig(num_samples=5)
        prior = TrajectoryPrior(config)
        cost_fn = CostFunction(config)
        sampler = CostGuidedSampler(prior, cost_fn, config)

        trajectories = sampler.sample(num_samples=5)

        assert len(trajectories) == 5
        assert all(isinstance(t, BSplineTrajectory) for t in trajectories)

    def test_sample_best(self):
        """Test sampling best trajectory."""
        config = TrajectoryConfig(num_samples=10)
        prior = TrajectoryPrior(config)
        cost_fn = CostFunction(config)
        sampler = CostGuidedSampler(prior, cost_fn, config)

        best = sampler.sample_best(goal=np.array([5, 5]))  # type: ignore[arg-type]

        assert isinstance(best, BSplineTrajectory)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
