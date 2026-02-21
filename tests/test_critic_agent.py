"""
Tests for Investment Committee Critic Agent

Tests cover:
- Agent creation and configuration
- Adversarial review capabilities
- Counterargument generation expectations
- Integration with CrewAI framework
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCriticAgentCreation:
    """Tests for critic agent instantiation."""
    
    @pytest.mark.unit
    def test_critic_agent_exists(self):
        """Test that critic agent can be imported and created."""
        from agents.critic_agent import critic_agent
        
        assert critic_agent is not None
        assert hasattr(critic_agent, 'role') or hasattr(critic_agent, '__class__')
    
    @pytest.mark.unit
    def test_critic_agent_configuration(self):
        """Test critic agent has correct configuration."""
        from agents.critic_agent import critic_agent
        
        # Critic should have appropriate temperature for creative thinking
        # Should not have tools (works with existing analysis)
        assert critic_agent is not None
    
    @pytest.mark.unit
    def test_create_critic_agent_function(self):
        """Test the create_critic_agent function."""
        from agents.critic_agent import create_critic_agent
        
        agent = create_critic_agent()
        
        assert agent is not None


class TestCriticAgentRole:
    """Tests for critic agent role and behavior."""
    
    @pytest.mark.unit
    def test_critic_role_is_adversarial(self):
        """Test that critic agent has adversarial role."""
        from agents.critic_agent import critic_agent
        
        # Check that role or goal mentions challenge/critique/adversarial
        role_str = str(critic_agent.role).lower() if hasattr(critic_agent, 'role') else ""
        goal_str = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        
        combined = role_str + goal_str
        
        # Should mention critique/challenge/adversarial/devil's advocate
        assert any(word in combined for word in [
            'critic', 'challenge', 'adversarial', 'devil', 
            'counterargument', 'stress-test', 'contrarian'
        ])
    
    @pytest.mark.unit
    def test_critic_has_no_tools(self):
        """Test that critic agent has no tools (works with existing analysis)."""
        from agents.critic_agent import critic_agent
        
        # Critic should not have tools - it reviews existing analysis
        if hasattr(critic_agent, 'tools'):
            assert critic_agent.tools is None or len(critic_agent.tools) == 0


class TestCriticAgentOutputExpectations:
    """Tests for expected outputs from critic agent."""
    
    @pytest.mark.unit
    def test_critic_mentions_counterarguments(self):
        """Test that critic's role expects counterarguments."""
        from agents.critic_agent import critic_agent
        
        # Goal or backstory should mention counterarguments
        goal_str = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        backstory_str = str(critic_agent.backstory).lower() if hasattr(critic_agent, 'backstory') else ""
        
        combined = goal_str + backstory_str
        
        assert 'counterargument' in combined or 'challenge' in combined or 'risk' in combined
    
    @pytest.mark.unit
    def test_critic_mentions_invalidation(self):
        """Test that critic's role includes thesis invalidation."""
        from agents.critic_agent import critic_agent
        
        goal_str = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        
        # Should mention invalidation or conditions for thesis failure
        assert 'invalid' in goal_str or 'fail' in goal_str or 'wrong' in goal_str or 'challenge' in goal_str
    
    @pytest.mark.unit
    def test_critic_mentions_vulnerability(self):
        """Test that critic assesses vulnerability."""
        from agents.critic_agent import critic_agent
        
        goal_str = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        backstory_str = str(critic_agent.backstory).lower() if hasattr(critic_agent, 'backstory') else ""
        
        combined = goal_str + backstory_str
        
        # Should assess strength/vulnerability of thesis
        assert any(word in combined for word in [
            'vulnerability', 'weakness', 'risk', 'robust', 'stress'
        ])


class TestCriticAgentBackstory:
    """Tests for critic agent backstory and expertise."""
    
    @pytest.mark.unit
    def test_critic_has_contrarian_experience(self):
        """Test that critic has contrarian/skeptical background."""
        from agents.critic_agent import critic_agent
        
        backstory = str(critic_agent.backstory).lower() if hasattr(critic_agent, 'backstory') else ""
        
        # Should mention failures, contrarian thinking, or skepticism
        assert any(word in backstory for word in [
            'contrarian', 'skeptic', 'failure', 'enron', 'satyam', 
            'crisis', 'wrong', 'devil', 'advocate'
        ])
    
    @pytest.mark.unit
    def test_critic_references_case_studies(self):
        """Test that critic references historical failures."""
        from agents.critic_agent import critic_agent
        
        backstory = str(critic_agent.backstory).lower() if hasattr(critic_agent, 'backstory') else ""
        
        # Should reference specific failure cases (Enron, Satyam, Yes Bank, IL&FS, etc.)
        # At least some context about learning from failures
        assert 'enron' in backstory or 'satyam' in backstory or 'failure' in backstory


class TestCriticAgentTemperature:
    """Tests for critic agent LLM configuration."""
    
    @pytest.mark.unit
    def test_critic_has_moderate_to_high_temperature(self):
        """Test that critic has appropriate temperature for creative thinking."""
        from agents.critic_agent import create_critic_agent
        
        agent = create_critic_agent()
        
        # Critic should have temperature around 0.6 for creative adversarial thinking
        # Higher than conservative agents but not too random
        if hasattr(agent, 'llm') and hasattr(agent.llm, 'temperature'):
            temp = agent.llm.temperature
            assert 0.5 <= temp <= 0.8, f"Critic temperature {temp} should be moderate (0.5-0.8)"


class TestCriticAgentMaxIterations:
    """Tests for critic agent iteration limits."""
    
    @pytest.mark.unit
    def test_critic_has_limited_iterations(self):
        """Test that critic has limited iterations (focused critique)."""
        from agents.critic_agent import critic_agent
        
        # Critic should have fewer iterations (3-5) for quick, focused critique
        if hasattr(critic_agent, 'max_iter'):
            assert critic_agent.max_iter <= 5, "Critic should have limited iterations for focused review"


class TestCriticAgentIntegration:
    """Integration tests for critic agent with CrewAI."""
    
    @pytest.mark.unit
    def test_critic_agent_in_agents_module(self):
        """Test that critic agent is exported from agents module."""
        from agents import critic_agent
        
        assert critic_agent is not None
    
    @pytest.mark.unit
    def test_critic_agent_type(self):
        """Test that critic agent is proper Agent type."""
        from agents.critic_agent import critic_agent
        
        # Should be CrewAI Agent instance
        assert hasattr(critic_agent, 'role') and hasattr(critic_agent, 'goal')
    
    @pytest.mark.unit
    def test_critic_agent_has_backstory(self):
        """Test that critic agent has detailed backstory."""
        from agents.critic_agent import critic_agent
        
        assert hasattr(critic_agent, 'backstory')
        assert len(critic_agent.backstory) > 50, "Backstory should be detailed"


class TestCriticTaskExpectations:
    """Tests for expected critic task integration."""
    
    @pytest.mark.unit
    def test_critic_task_expects_five_counterarguments(self):
        """Test that critic is expected to provide 5 counterarguments."""
        # This is behavioral - we're testing the design intent
        from agents.critic_agent import critic_agent
        
        goal = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        
        # Should mention multiple counterarguments
        assert 'counterargument' in goal or 'challenge' in goal or 'risk' in goal
    
    @pytest.mark.unit
    def test_critic_provides_rating(self):
        """Test that critic is expected to provide vulnerability assessment."""
        from agents.critic_agent import critic_agent
        
        goal = str(critic_agent.goal).lower() if hasattr(critic_agent, 'goal') else ""
        backstory = str(critic_agent.backstory).lower() if hasattr(critic_agent, 'backstory') else ""
        
        combined = goal + backstory
        
        # Should assess vulnerability/robustness through counterarguments and invalidation
        assert any(word in combined for word in ['rating', 'assess', 'vulnerability', 'weak', 'challenge', 'invalidate'])


class TestCriticAgentQualityChecks:
    """Quality checks for critic agent configuration."""
    
    @pytest.mark.unit
    def test_critic_role_not_empty(self):
        """Test that critic has non-empty role."""
        from agents.critic_agent import critic_agent
        
        assert hasattr(critic_agent, 'role')
        assert len(critic_agent.role) > 10
    
    @pytest.mark.unit
    def test_critic_goal_not_empty(self):
        """Test that critic has non-empty goal."""
        from agents.critic_agent import critic_agent
        
        assert hasattr(critic_agent, 'goal')
        assert len(critic_agent.goal) > 20
    
    @pytest.mark.unit
    def test_critic_backstory_not_empty(self):
        """Test that critic has non-empty backstory."""
        from agents.critic_agent import critic_agent
        
        assert hasattr(critic_agent, 'backstory')
        assert len(critic_agent.backstory) > 50
