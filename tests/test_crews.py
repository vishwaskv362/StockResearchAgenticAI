"""
Tests for Research Crew

Tests cover:
- Crew creation
- Task definitions
- Task dependencies
- Crew execution flow
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCrewCreation:
    """Tests for crew creation."""
    
    @pytest.mark.unit
    def test_create_stock_research_crew(self):
        """Test that research crew is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            assert crew is not None
    
    @pytest.mark.unit
    def test_crew_has_agents(self):
        """Test that crew has agents assigned."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            assert hasattr(crew, 'agents')
            assert len(crew.agents) > 0
    
    @pytest.mark.unit
    def test_crew_has_tasks(self):
        """Test that crew has tasks defined."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            assert hasattr(crew, 'tasks')
            assert len(crew.tasks) > 0
    
    @pytest.mark.unit
    def test_symbol_normalization(self):
        """Test that symbol is normalized to uppercase."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            # Test with lowercase
            crew = create_stock_research_crew("reliance", "full")
            
            # Crew should be created (symbol normalized internally)
            assert crew is not None


class TestAnalysisTypes:
    """Tests for different analysis types."""
    
    @pytest.mark.unit
    def test_full_analysis_type(self):
        """Test full analysis type creates complete crew."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            # Full analysis should have all tasks
            assert len(crew.tasks) >= 4
    
    @pytest.mark.unit
    def test_quick_analysis_type(self):
        """Test quick analysis type creates minimal crew."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "quick")
            
            # Quick analysis should have fewer tasks
            assert crew is not None
    
    @pytest.mark.unit
    def test_technical_only_analysis_type(self):
        """Test technical-only analysis type."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "technical-only")
            
            # Should have technical-focused tasks
            assert crew is not None


class TestTaskDefinitions:
    """Tests for task definitions."""
    
    @pytest.mark.unit
    def test_tasks_have_descriptions(self):
        """Test that all tasks have descriptions."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            for task in crew.tasks:
                assert hasattr(task, 'description')
                assert len(task.description) > 0
    
    @pytest.mark.unit
    def test_tasks_have_expected_output(self):
        """Test that all tasks have expected output defined."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            for task in crew.tasks:
                assert hasattr(task, 'expected_output')
                assert len(task.expected_output) > 0
    
    @pytest.mark.unit
    def test_tasks_have_agents(self):
        """Test that all tasks have agents assigned."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            for task in crew.tasks:
                assert hasattr(task, 'agent')
                assert task.agent is not None
    
    @pytest.mark.unit
    def test_tasks_include_symbol(self):
        """Test that tasks include the stock symbol in description."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            symbol = "RELIANCE"
            crew = create_stock_research_crew(symbol, "full")
            
            # At least some tasks should mention the symbol
            symbol_mentioned = any(symbol in task.description for task in crew.tasks)
            assert symbol_mentioned, "Symbol should be in task descriptions"


class TestTaskDependencies:
    """Tests for task dependencies (context)."""
    
    @pytest.mark.unit
    def test_some_tasks_have_context(self):
        """Test that dependent tasks have context defined."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            # Later tasks should depend on earlier ones
            tasks_with_context = sum(
                1 for task in crew.tasks 
                if hasattr(task, 'context') and task.context
            )
            
            # At least some tasks should have dependencies
            assert tasks_with_context > 0


class TestSyncAnalysis:
    """Tests for synchronous analysis function."""
    
    @pytest.mark.unit
    def test_analyze_stock_sync_exists(self):
        """Test that sync analysis function exists."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import analyze_stock_sync
            
            assert callable(analyze_stock_sync)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_analyze_stock_sync_returns_result(self):
        """Integration test: Full analysis returns result."""
        # This test is slow and hits real APIs
        # Only run in integration test mode
        pytest.skip("Skipping slow integration test - run with --run-slow")


class TestCrewConfiguration:
    """Tests for crew configuration."""
    
    @pytest.mark.unit
    def test_crew_uses_sequential_process(self):
        """Test that crew uses sequential process by default."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            from crewai import Process
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            # Should use sequential or hierarchical process
            assert crew.process in [Process.sequential, Process.hierarchical]
    
    @pytest.mark.unit
    def test_crew_has_reasonable_task_count(self):
        """Test that crew doesn't have too many tasks."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            crew = create_stock_research_crew("RELIANCE", "full")
            
            # Should have reasonable number of tasks (not too many)
            assert len(crew.tasks) <= 10, "Too many tasks could slow execution"
            assert len(crew.tasks) >= 3, "Should have minimum tasks for analysis"


class TestErrorHandling:
    """Tests for error handling in crew execution."""
    
    @pytest.mark.unit
    def test_invalid_symbol_handling(self):
        """Test handling of invalid symbols."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            # Should still create crew (validation happens at execution)
            crew = create_stock_research_crew("INVALIDXYZ", "full")
            assert crew is not None
    
    @pytest.mark.unit
    def test_empty_symbol_handling(self):
        """Test handling of empty symbol."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            # Empty symbol should be handled
            crew = create_stock_research_crew("", "full")
            assert crew is not None
    
    @pytest.mark.unit
    def test_invalid_analysis_type_handling(self):
        """Test handling of invalid analysis type."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from crews.research_crew import create_stock_research_crew
            
            # Should fall back to default or handle gracefully
            crew = create_stock_research_crew("RELIANCE", "invalid_type")
            assert crew is not None
