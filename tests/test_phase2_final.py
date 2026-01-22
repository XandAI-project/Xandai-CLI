"""
Tests for Phase 2 Final Components

Tests for Agent, Web, and File Watching systems.
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

# Agent tests
from xandai.agent import AgentManager, TaskExecutor, TaskPlanner, TaskStatus
from xandai.agent.task_planner import StepType


class TestAgentManager:
    """Test Agent Manager"""

    def test_create_task(self):
        """Test creating a task"""
        manager = AgentManager()
        task = manager.create_task("Build a REST API")

        assert task is not None
        assert task.description == "Build a REST API"
        assert task.status == TaskStatus.PENDING

    def test_list_tasks(self):
        """Test listing tasks"""
        manager = AgentManager()
        task1 = manager.create_task("Task 1")
        task2 = manager.create_task("Task 2")

        tasks = manager.list_tasks()
        assert len(tasks) >= 2

    def test_update_task_status(self):
        """Test updating task status"""
        manager = AgentManager()
        task = manager.create_task("Test task")

        manager.update_task_status(task.id, TaskStatus.RUNNING)
        assert task.status == TaskStatus.RUNNING

    def test_cancel_task(self):
        """Test canceling a task"""
        manager = AgentManager()
        task = manager.create_task("Cancelable task")

        cancelled = manager.cancel_task(task.id)
        assert cancelled is True
        assert task.status == TaskStatus.CANCELLED


class TestTaskPlanner:
    """Test Task Planner"""

    def test_plan_code_task(self):
        """Test planning a code task"""
        planner = TaskPlanner()
        steps = planner.plan_task("Create a Python web scraper")

        assert len(steps) > 0
        assert any(s.step_type == StepType.CODE for s in steps)

    def test_plan_test_task(self):
        """Test planning with tests"""
        planner = TaskPlanner()
        steps = planner.plan_task("Build API and test it")

        assert any(s.step_type == StepType.TEST for s in steps)

    def test_get_next_steps(self):
        """Test getting executable steps"""
        planner = TaskPlanner()
        steps = planner.plan_task("Simple task")

        next_steps = planner.get_next_steps(steps)
        assert len(next_steps) > 0

    def test_calculate_progress(self):
        """Test progress calculation"""
        planner = TaskPlanner()
        steps = planner.plan_task("Test progress")

        progress = planner.calculate_progress(steps)
        assert progress == 0.0

        steps[0].completed = True
        progress = planner.calculate_progress(steps)
        assert progress > 0.0


class TestTaskExecutor:
    """Test Task Executor"""

    def test_execute_step_success(self):
        """Test successful step execution"""
        executor = TaskExecutor()
        planner = TaskPlanner()
        steps = planner.plan_task("Test")

        def simple_exec(step):
            return "Success"

        result = executor.execute_step(steps[0], simple_exec)
        assert result.success is True
        assert steps[0].completed is True

    def test_execute_step_failure(self):
        """Test failed step execution"""
        executor = TaskExecutor(max_retries=2)
        planner = TaskPlanner()
        steps = planner.plan_task("Test")

        def failing_exec(step):
            raise Exception("Failed")

        result = executor.execute_step(steps[0], failing_exec)
        assert result.success is False
        assert result.error is not None


# Web tests
from xandai.web import ContentExtractor


class TestContentExtractor:
    """Test Content Extractor"""

    def test_extract_code_blocks(self):
        """Test extracting code blocks"""
        extractor = ContentExtractor()
        html = """
        <pre><code class="language-python">
        def hello():
            print("Hello")
        </code></pre>
        """

        blocks = extractor.extract_code_blocks(html)
        assert len(blocks) > 0
        assert blocks[0]["language"] == "python"

    def test_extract_tables(self):
        """Test extracting tables"""
        extractor = ContentExtractor()
        html = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>John</td><td>30</td></tr>
        </table>
        """

        tables = extractor.extract_tables(html)
        assert len(tables) > 0
        assert len(tables[0]) == 2  # 2 rows

    def test_extract_lists(self):
        """Test extracting lists"""
        extractor = ContentExtractor()
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """

        lists = extractor.extract_lists(html)
        assert len(lists["unordered"]) > 0

    def test_extract_headings(self):
        """Test extracting headings"""
        extractor = ContentExtractor()
        html = """
        <h1>Title</h1>
        <h2>Subtitle</h2>
        """

        headings = extractor.extract_headings(html)
        assert "h1" in headings
        assert "h2" in headings


# File Watcher tests
from xandai.file_watcher import EventType, FileWatcher, ProjectWatcher


class TestFileWatcher:
    """Test File Watcher"""

    def test_watch_directory(self):
        """Test watching a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(polling_interval=0.1)
            watcher.watch(tmpdir)

            assert tmpdir in [os.path.abspath(p) for p in watcher.watched_paths.keys()]

            watcher.stop()

    def test_detect_file_creation(self):
        """Test detecting file creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = []

            watcher = FileWatcher(polling_interval=0.1)
            watcher.on(EventType.CREATED, lambda e: events.append(e))
            watcher.watch(tmpdir)
            watcher.start()

            # Create a file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello")

            time.sleep(0.3)  # Wait for detection

            watcher.stop()

            assert len(events) > 0
            assert any(e.event_type == EventType.CREATED for e in events)

    def test_detect_file_modification(self):
        """Test detecting file modification"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Initial")

            events = []

            watcher = FileWatcher(polling_interval=0.1)
            watcher.on(EventType.MODIFIED, lambda e: events.append(e))
            watcher.watch(tmpdir)
            watcher.start()

            time.sleep(0.2)

            # Modify file
            test_file.write_text("Modified")

            time.sleep(0.3)

            watcher.stop()

            assert len(events) > 0


class TestProjectWatcher:
    """Test Project Watcher"""

    def test_ignore_patterns(self):
        """Test file ignoring"""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = ProjectWatcher(tmpdir)

            # Should ignore
            assert watcher._should_ignore(f"{tmpdir}/__pycache__/test.pyc")
            assert watcher._should_ignore(f"{tmpdir}/file.pyc")

            # Should not ignore
            assert not watcher._should_ignore(f"{tmpdir}/main.py")

    def test_get_watched_files(self):
        """Test getting watched files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "main.py").write_text("# main")
            Path(tmpdir, "test.txt").write_text("test")
            Path(tmpdir, "__pycache__").mkdir()
            Path(tmpdir, "__pycache__", "cache.pyc").write_text("")

            watcher = ProjectWatcher(tmpdir)
            files = watcher.get_watched_files()

            # Should include .py and .txt but not .pyc
            assert any("main.py" in f for f in files)
            assert any("test.txt" in f for f in files)
            assert not any(".pyc" in f for f in files)
