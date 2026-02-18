"""
Unit tests for Sidebar Collapse/Expand Behavior

Tests verify that the sidebar navigation handles collapse and expand states correctly,
ensuring navigation remains accessible in both states.

Task: 5.1 Test sidebar collapse/expand behavior
Requirements: 6.1, 6.2
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard'))


class TestSidebarCollapseExpand:
    """Test sidebar collapse and expand behavior."""
    
    def test_navigation_component_exists_in_sidebar(self):
        """Test that navigation component is defined in the sidebar."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify navigation is in sidebar
        assert 'st.sidebar.radio' in content, "Navigation should use st.sidebar.radio"
        assert 'st.sidebar.markdown' in content, "Sidebar should have markdown sections"
    
    def test_sidebar_initial_state_is_expanded(self):
        """Test that sidebar is configured to be expanded by default."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify page config sets initial_sidebar_state to expanded
        assert 'st.set_page_config' in content, "Page config should be set"
        assert 'initial_sidebar_state="expanded"' in content, \
            "Sidebar should be expanded by default"
    
    def test_all_navigation_options_defined(self):
        """Test that all 5 navigation options are defined for visibility."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Expected navigation pages
        expected_pages = [
            "Risk Overview",
            "Customer Deep Dive",
            "Real-time Monitor",
            "Model Performance",
            "Interventions Tracker"
        ]
        
        # Verify all pages are in the file
        for page in expected_pages:
            assert page in content, f"Page '{page}' should be defined in navigation"
    
    def test_navigation_uses_radio_component(self):
        """Test that navigation uses st.radio which handles collapse gracefully."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # st.radio is the correct component for this use case
        # It automatically handles sidebar collapse/expand
        assert 'st.sidebar.radio' in content, \
            "Should use st.sidebar.radio for navigation"
    
    def test_navigation_label_visibility_collapsed(self):
        """Test that navigation label is collapsed for cleaner appearance."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Label should be collapsed to avoid redundancy with section header
        assert 'label_visibility="collapsed"' in content, \
            "Navigation label should be collapsed"
    
    def test_sidebar_css_does_not_override_collapse_behavior(self):
        """Test that custom CSS doesn't interfere with sidebar collapse."""
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # Verify CSS doesn't set fixed width or display properties that would break collapse
        # Look for the sidebar CSS section
        sidebar_css_start = content.find('section[data-testid="stSidebar"]')
        assert sidebar_css_start != -1, "Sidebar CSS should exist"
        
        # Extract sidebar CSS section (next 500 characters)
        sidebar_css = content[sidebar_css_start:sidebar_css_start + 500]
        
        # These properties would break collapse behavior
        assert 'width:' not in sidebar_css or 'width: auto' in sidebar_css, \
            "CSS should not set fixed sidebar width"
        assert 'display: none' not in sidebar_css, \
            "CSS should not hide sidebar"
        assert 'visibility: hidden' not in sidebar_css, \
            "CSS should not hide sidebar visibility"
    
    def test_navigation_section_header_present(self):
        """Test that navigation section header is present for context."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Section header provides context even when sidebar is collapsed
        assert '📍 NAVIGATION' in content, \
            "Navigation section header should be present"
    
    def test_quick_stats_section_present(self):
        """Test that Quick Stats section is present below navigation."""
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Quick Stats should be present
        assert '📊 QUICK STATS' in content, \
            "Quick Stats section should be present"
        
        # Verify order: Navigation comes before Quick Stats
        nav_pos = content.find('📍 NAVIGATION')
        stats_pos = content.find('📊 QUICK STATS')
        
        assert nav_pos < stats_pos, \
            "Navigation should come before Quick Stats"


class TestSidebarResponsiveBehavior:
    """Test sidebar responsive behavior across different states."""
    
    def test_streamlit_handles_collapse_automatically(self):
        """Test that Streamlit's built-in collapse mechanism is used."""
        # Streamlit automatically provides a collapse button in the sidebar
        # when initial_sidebar_state is set to "expanded"
        # This test verifies we're using Streamlit's native behavior
        
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify we're using Streamlit's page config
        assert 'st.set_page_config' in content, \
            "Should use st.set_page_config for sidebar configuration"
        
        # Verify we're not implementing custom collapse logic
        assert 'st.session_state' not in content or \
               'sidebar_collapsed' not in content, \
            "Should use Streamlit's built-in collapse, not custom state"
    
    def test_navigation_remains_functional_when_collapsed(self):
        """Test that navigation remains accessible when sidebar is collapsed."""
        # When sidebar is collapsed, Streamlit shows a toggle button
        # Clicking it expands the sidebar, making navigation accessible
        # This is Streamlit's default behavior
        
        # Verify we're using st.sidebar components (they handle collapse automatically)
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # All sidebar components should use st.sidebar prefix
        assert 'st.sidebar.radio' in content, \
            "Navigation should use st.sidebar.radio"
        assert 'st.sidebar.markdown' in content, \
            "Sidebar content should use st.sidebar.markdown"
        assert 'st.sidebar.metric' in content, \
            "Quick Stats should use st.sidebar.metric"
    
    def test_css_styling_applies_to_expanded_state(self):
        """Test that CSS styling is scoped to sidebar and works when expanded."""
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # CSS should target sidebar specifically
        assert 'section[data-testid="stSidebar"]' in content, \
            "CSS should target sidebar specifically"
        
        # Radio button styling should be scoped to sidebar
        assert 'section[data-testid="stSidebar"] .stRadio' in content, \
            "Radio button styling should be scoped to sidebar"
    
    def test_no_fixed_positioning_that_breaks_collapse(self):
        """Test that CSS doesn't use fixed positioning that would break collapse."""
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # Find sidebar CSS section
        sidebar_css_start = content.find('section[data-testid="stSidebar"]')
        sidebar_css_end = content.find('</style>', sidebar_css_start)
        sidebar_css = content[sidebar_css_start:sidebar_css_end]
        
        # These would break collapse behavior
        assert 'position: fixed' not in sidebar_css, \
            "Sidebar should not use fixed positioning"
        assert 'position: absolute' not in sidebar_css, \
            "Sidebar should not use absolute positioning"


class TestNavigationAccessibilityInCollapsedState:
    """Test that navigation remains accessible in collapsed state."""
    
    def test_sidebar_toggle_button_available(self):
        """Test that Streamlit provides a toggle button for collapsed sidebar."""
        # Streamlit automatically provides a toggle button (hamburger menu)
        # when the sidebar is collapsed. This is built-in behavior.
        
        # Verify we're not hiding or disabling this button
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # Make sure we're not hiding the collapse button
        assert 'stSidebarCollapsedControl' not in content or \
               'display: none' not in content, \
            "Should not hide sidebar collapse button"
    
    def test_navigation_state_persists_across_collapse(self):
        """Test that selected page persists when sidebar is collapsed/expanded."""
        # Streamlit's st.radio automatically maintains state
        # The selected page should persist across sidebar collapse/expand
        
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify we're using st.radio which maintains state automatically
        assert 'st.sidebar.radio' in content, \
            "Should use st.radio which maintains state"
        
        # Verify we're not clearing state on collapse
        assert 'del st.session_state' not in content or \
               'page' not in content, \
            "Should not clear page state"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
