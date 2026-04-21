"""
Dependency Resolver for PromptOps Task Decomposition
====================================================

Graph-based dependency resolution with cycle detection, topological sorting,
and parallelization analysis.

This module validates task dependency graphs and determines optimal execution order.

Author: PromptOps Team - Week 5-6
Date: 2026-04-21
"""

import logging
from typing import Dict, List, Any, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DependencyValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    circular_dependencies: List[List[str]]
    missing_dependencies: List[str]
    orphan_tasks: List[str]


@dataclass
class ExecutionPhase:
    """A phase of execution with parallelizable tasks."""
    phase_number: int
    phase_name: str
    task_ids: List[str]
    execution_mode: str  # "parallel" or "sequential"
    estimated_duration: str


@dataclass
class DependencyAnalysis:
    """Complete dependency analysis result."""
    is_valid: bool
    validation_result: DependencyValidationResult
    topological_order: List[str]
    execution_phases: List[ExecutionPhase]
    critical_path: List[str]
    parallelizable_tasks: Dict[int, List[str]]  # phase_number → task_ids
    total_sequential_time: int  # seconds
    total_parallel_time: int  # seconds


# ============================================================================
# Dependency Resolver
# ============================================================================

class DependencyResolver:
    """
    Resolves task dependencies using graph algorithms.

    Features:
    - Detects circular dependencies (cycles)
    - Validates all dependencies exist
    - Topological sort for execution order
    - Identifies parallelizable tasks
    - Calculates critical path
    - Estimates execution times
    """

    def __init__(self):
        """Initialize resolver."""
        self.task_graph: Dict[str, List[str]] = {}  # task_id → dependencies
        self.reverse_graph: Dict[str, List[str]] = {}  # task_id → dependents
        self.task_durations: Dict[str, int] = {}  # task_id → seconds
        self.task_metadata: Dict[str, Dict] = {}  # task_id → full task object

    def build_graph(self, sub_tasks: List[Dict[str, Any]]) -> None:
        """
        Build dependency graph from sub-tasks.

        Args:
            sub_tasks: List of sub-task dictionaries
        """
        self.task_graph = {}
        self.reverse_graph = defaultdict(list)
        self.task_durations = {}
        self.task_metadata = {}

        for task in sub_tasks:
            task_id = task['task_id']
            dependencies = task.get('dependencies', [])

            self.task_graph[task_id] = dependencies
            self.task_metadata[task_id] = task

            # Parse duration to seconds
            duration_str = task.get('estimated_duration', '0 seconds')
            self.task_durations[task_id] = self._parse_duration(duration_str)

            # Build reverse graph (who depends on this task?)
            for dep in dependencies:
                self.reverse_graph[dep].append(task_id)

        logger.info(f"Built dependency graph with {len(self.task_graph)} tasks")

    def validate(self) -> DependencyValidationResult:
        """
        Validate dependency graph.

        Returns:
            Validation result with errors/warnings
        """
        errors = []
        warnings = []
        circular_dependencies = []
        missing_dependencies = []
        orphan_tasks = []

        # 1. Check for missing dependencies
        all_task_ids = set(self.task_graph.keys())

        for task_id, dependencies in self.task_graph.items():
            for dep in dependencies:
                if dep not in all_task_ids:
                    missing_dependencies.append(f"{task_id} depends on non-existent task: {dep}")
                    errors.append(f"Task {task_id} depends on non-existent task {dep}")

        # 2. Detect circular dependencies
        cycles = self._detect_cycles()
        if cycles:
            circular_dependencies = cycles
            for cycle in cycles:
                cycle_str = " → ".join(cycle + [cycle[0]])
                errors.append(f"Circular dependency detected: {cycle_str}")

        # 3. Identify orphan tasks (no dependencies, no dependents)
        for task_id in all_task_ids:
            has_dependencies = len(self.task_graph[task_id]) > 0
            has_dependents = len(self.reverse_graph.get(task_id, [])) > 0

            if not has_dependencies and not has_dependents:
                orphan_tasks.append(task_id)
                warnings.append(f"Task {task_id} has no dependencies and no dependents (orphan)")

        is_valid = len(errors) == 0

        return DependencyValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            circular_dependencies=circular_dependencies,
            missing_dependencies=missing_dependencies,
            orphan_tasks=orphan_tasks
        )

    def _detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in dependency graph using DFS.

        Returns:
            List of cycles (each cycle is a list of task_ids)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(task_id: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            for dep in self.task_graph.get(task_id, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(task_id)
            return False

        for task_id in self.task_graph:
            if task_id not in visited:
                dfs(task_id)

        return cycles

    def topological_sort(self) -> Optional[List[str]]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of task_ids in execution order, or None if cycles exist
        """
        # Calculate in-degree for each task
        in_degree = {task_id: 0 for task_id in self.task_graph}

        for task_id, dependencies in self.task_graph.items():
            for dep in dependencies:
                if dep in in_degree:  # Skip if dependency doesn't exist
                    in_degree[task_id] += 1

        # Queue of tasks with no dependencies
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])

        sorted_order = []

        while queue:
            # Process task with no remaining dependencies
            task_id = queue.popleft()
            sorted_order.append(task_id)

            # Reduce in-degree of dependent tasks
            for dependent in self.reverse_graph.get(task_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all tasks processed, there's a cycle
        if len(sorted_order) != len(self.task_graph):
            logger.error("Topological sort failed - cycle detected")
            return None

        return sorted_order

    def identify_parallel_tasks(self, topological_order: List[str]) -> Dict[int, List[str]]:
        """
        Identify tasks that can run in parallel (same dependencies).

        Args:
            topological_order: Tasks in sorted order

        Returns:
            Dict mapping phase_number to list of parallelizable task_ids
        """
        phases = {}
        phase_number = 1
        processed = set()

        # Track when each task can start (after all dependencies complete)
        earliest_start_phase = {}

        for task_id in topological_order:
            dependencies = self.task_graph[task_id]

            if not dependencies:
                # No dependencies - can start in phase 1
                earliest_start_phase[task_id] = 1
            else:
                # Can start after all dependencies complete
                max_dep_phase = max(earliest_start_phase.get(dep, 1) for dep in dependencies)
                earliest_start_phase[task_id] = max_dep_phase + 1

        # Group tasks by phase
        for task_id in topological_order:
            phase = earliest_start_phase[task_id]
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(task_id)

        return phases

    def calculate_critical_path(self) -> Tuple[List[str], int]:
        """
        Calculate critical path (longest sequential chain).

        Returns:
            (list of task_ids in critical path, total duration in seconds)
        """
        # Calculate longest path to each task
        longest_path_to = {}
        predecessor = {}

        # Initialize with tasks that have no dependencies
        for task_id in self.task_graph:
            if not self.task_graph[task_id]:
                longest_path_to[task_id] = self.task_durations[task_id]
                predecessor[task_id] = None

        # Topological order ensures we process dependencies before dependents
        topo_order = self.topological_sort()
        if not topo_order:
            return [], 0

        for task_id in topo_order:
            if task_id in longest_path_to:
                # Already initialized
                continue

            # Find longest path through any dependency
            max_path = 0
            best_pred = None

            for dep in self.task_graph[task_id]:
                dep_path = longest_path_to.get(dep, 0)
                if dep_path > max_path:
                    max_path = dep_path
                    best_pred = dep

            longest_path_to[task_id] = max_path + self.task_durations[task_id]
            predecessor[task_id] = best_pred

        # Find task with longest path (end of critical path)
        max_duration = 0
        end_task = None

        for task_id, duration in longest_path_to.items():
            if duration > max_duration:
                max_duration = duration
                end_task = task_id

        # Reconstruct path
        if not end_task:
            return [], 0

        critical_path = []
        current = end_task

        while current:
            critical_path.append(current)
            current = predecessor.get(current)

        critical_path.reverse()

        return critical_path, max_duration

    def analyze(self, sub_tasks: List[Dict[str, Any]]) -> DependencyAnalysis:
        """
        Complete dependency analysis pipeline.

        Args:
            sub_tasks: List of sub-task dictionaries

        Returns:
            Full dependency analysis result
        """
        logger.info("=== Starting Dependency Analysis ===")

        # 1. Build graph
        self.build_graph(sub_tasks)

        # 2. Validate
        validation_result = self.validate()

        if not validation_result.is_valid:
            logger.error(f"Dependency validation failed: {validation_result.errors}")
            return DependencyAnalysis(
                is_valid=False,
                validation_result=validation_result,
                topological_order=[],
                execution_phases=[],
                critical_path=[],
                parallelizable_tasks={},
                total_sequential_time=0,
                total_parallel_time=0
            )

        # 3. Topological sort
        topo_order = self.topological_sort()
        if not topo_order:
            logger.error("Topological sort failed")
            validation_result.is_valid = False
            validation_result.errors.append("Topological sort failed - likely circular dependency")
            return DependencyAnalysis(
                is_valid=False,
                validation_result=validation_result,
                topological_order=[],
                execution_phases=[],
                critical_path=[],
                parallelizable_tasks={},
                total_sequential_time=0,
                total_parallel_time=0
            )

        logger.info(f"Topological order: {topo_order}")

        # 4. Identify parallel tasks
        parallelizable_tasks = self.identify_parallel_tasks(topo_order)

        logger.info(f"Identified {len(parallelizable_tasks)} execution phases")
        for phase, tasks in parallelizable_tasks.items():
            if len(tasks) > 1:
                logger.info(f"  Phase {phase}: {len(tasks)} tasks can run in parallel")

        # 5. Calculate critical path
        critical_path, critical_duration = self.calculate_critical_path()

        logger.info(f"Critical path: {critical_path}")
        logger.info(f"Critical path duration: {critical_duration} seconds")

        # 6. Build execution phases
        execution_phases = self._build_execution_phases(parallelizable_tasks)

        # 7. Calculate total times
        total_sequential_time = sum(self.task_durations.values())
        total_parallel_time = critical_duration

        logger.info(f"Total sequential time: {total_sequential_time} seconds")
        logger.info(f"Total parallel time: {total_parallel_time} seconds")
        logger.info(f"Speedup from parallelization: {total_sequential_time / total_parallel_time:.2f}x")

        return DependencyAnalysis(
            is_valid=True,
            validation_result=validation_result,
            topological_order=topo_order,
            execution_phases=execution_phases,
            critical_path=critical_path,
            parallelizable_tasks=parallelizable_tasks,
            total_sequential_time=total_sequential_time,
            total_parallel_time=total_parallel_time
        )

    def _build_execution_phases(self, parallelizable_tasks: Dict[int, List[str]]) -> List[ExecutionPhase]:
        """
        Build ExecutionPhase objects from parallel task groupings.

        Args:
            parallelizable_tasks: Dict of phase_number → task_ids

        Returns:
            List of ExecutionPhase objects
        """
        phases = []

        for phase_num in sorted(parallelizable_tasks.keys()):
            task_ids = parallelizable_tasks[phase_num]

            # Determine execution mode
            execution_mode = "parallel" if len(task_ids) > 1 else "sequential"

            # Calculate phase duration (max of all parallel tasks)
            if execution_mode == "parallel":
                phase_duration = max(self.task_durations.get(tid, 0) for tid in task_ids)
            else:
                phase_duration = self.task_durations.get(task_ids[0], 0)

            # Generate phase name from task actions
            task_actions = [self.task_metadata[tid].get('action', 'unknown') for tid in task_ids]
            phase_name = self._generate_phase_name(task_actions)

            phases.append(ExecutionPhase(
                phase_number=phase_num,
                phase_name=phase_name,
                task_ids=task_ids,
                execution_mode=execution_mode,
                estimated_duration=self._format_duration(phase_duration)
            ))

        return phases

    def _generate_phase_name(self, task_actions: List[str]) -> str:
        """
        Generate human-readable phase name from task actions.

        Args:
            task_actions: List of task action strings

        Returns:
            Phase name
        """
        if len(task_actions) == 1:
            return task_actions[0].replace('_', ' ').title()

        # Group similar actions
        action_types = set(action.split('_')[0] for action in task_actions)

        if len(action_types) == 1:
            return f"{list(action_types)[0].title()} Phase"
        else:
            return f"Parallel: {', '.join(action_types)}"

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse duration string to seconds.

        Args:
            duration_str: e.g., "30 seconds", "5 minutes", "2 hours"

        Returns:
            Duration in seconds
        """
        parts = duration_str.lower().split()
        if len(parts) != 2:
            return 0

        try:
            value = int(parts[0])
            unit = parts[1]

            if 'second' in unit:
                return value
            elif 'minute' in unit:
                return value * 60
            elif 'hour' in unit:
                return value * 3600
            else:
                return 0
        except (ValueError, IndexError):
            return 0

    def _format_duration(self, seconds: int) -> str:
        """
        Format seconds to human-readable duration.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string like "5 minutes", "2 hours 30 minutes"
        """
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"{minutes} minutes {remaining_seconds} seconds"
            return f"{minutes} minutes"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes > 0:
                return f"{hours} hours {remaining_minutes} minutes"
            return f"{hours} hours"


# ============================================================================
# Utility Functions
# ============================================================================

def validate_dependencies(sub_tasks: List[Dict[str, Any]]) -> DependencyValidationResult:
    """
    Quick validation of dependencies without full analysis.

    Args:
        sub_tasks: List of sub-task dictionaries

    Returns:
        Validation result
    """
    resolver = DependencyResolver()
    resolver.build_graph(sub_tasks)
    return resolver.validate()


def get_execution_order(sub_tasks: List[Dict[str, Any]]) -> Optional[List[str]]:
    """
    Get execution order for sub-tasks.

    Args:
        sub_tasks: List of sub-task dictionaries

    Returns:
        Topologically sorted task_ids, or None if cycles detected
    """
    resolver = DependencyResolver()
    resolver.build_graph(sub_tasks)
    return resolver.topological_sort()


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example sub-tasks for testing
    test_sub_tasks = [
        {
            "task_id": "task-001",
            "action": "validate_version",
            "dependencies": [],
            "estimated_duration": "10 seconds"
        },
        {
            "task_id": "task-002",
            "action": "check_environment",
            "dependencies": [],
            "estimated_duration": "15 seconds"
        },
        {
            "task_id": "task-003",
            "action": "create_backup",
            "dependencies": ["task-001", "task-002"],
            "estimated_duration": "30 seconds"
        },
        {
            "task_id": "task-004",
            "action": "deploy",
            "dependencies": ["task-003"],
            "estimated_duration": "3 minutes"
        },
        {
            "task_id": "task-005",
            "action": "run_health_check",
            "dependencies": ["task-004"],
            "estimated_duration": "20 seconds"
        }
    ]

    print("="*70)
    print("Dependency Resolver Test")
    print("="*70)

    resolver = DependencyResolver()
    analysis = resolver.analyze(test_sub_tasks)

    print(f"\nValidation: {'✓ PASS' if analysis.is_valid else '✗ FAIL'}")

    if analysis.is_valid:
        print(f"\nTopological Order: {analysis.topological_order}")
        print(f"\nCritical Path: {analysis.critical_path}")
        print(f"Critical Path Duration: {analysis.total_parallel_time} seconds")

        print(f"\nExecution Phases:")
        for phase in analysis.execution_phases:
            print(f"  Phase {phase.phase_number}: {phase.phase_name}")
            print(f"    Tasks: {phase.task_ids}")
            print(f"    Mode: {phase.execution_mode}")
            print(f"    Duration: {phase.estimated_duration}")

        print(f"\nTotal Sequential Time: {analysis.total_sequential_time} seconds")
        print(f"Total Parallel Time: {analysis.total_parallel_time} seconds")
        print(f"Speedup: {analysis.total_sequential_time / analysis.total_parallel_time:.2f}x")
    else:
        print(f"\nErrors:")
        for error in analysis.validation_result.errors:
            print(f"  - {error}")

    print("\n" + "="*70)
