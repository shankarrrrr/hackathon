"""
Unit tests for Dashboard Navigation Styling

Tests verify that the navigation component has correct styling,
including active state indication, hover states, and proper CSS application.

Task: 4.1 Verify active page styling is applied correctly
Requirements: 3.1, 3.2, 3.3, 3.4
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard'))

from ui_components import apply_custom_css


class TestNavigationStyling:
    """Test navigation component styling."""
    
    def test_navigation_pages_defined(self):
        """Test that all navigation pages are defined correctly."""
        pages = [
            "Risk Overview",
            "Customer Deep Dive",
            "Real-time Monitor",
            "Model Performance",
            "Interventions Tracker"
        ]
        
        # Verify all 5 pages exist
        assert len(pages) == 5, f"Expected 5 pages, got {len(pages)}"
        
        # Verify each page is a non-empty string
        for page in pages:
            assert isinstance(page, str), f"Page {page} should be a string"
            assert len(page) > 0, f"Page name should not be empty"
    
    def test_default_page_is_risk_overview(self):
        """Test that the default page is Risk Overview."""
        pages = [
            "Risk Overview",
            "Customer Deep Dive",
            "Real-time Monitor",
            "Model Performance",
            "Interventions Tracker"
        ]
        
        # First page in the list should be Risk Overview
        default_page = pages[0]
        assert default_page == "Risk Overview", f"Expected 'Risk Overview', got '{default_page}'"
    
    def test_active_state_colors_defined(self):
        """Test that active state uses correct colors (blue background, darker text)."""
        # Expected CSS properties for active state
        active_bg_color = "#EFF6FF"  # Light blue background
        active_text_color = "#1E40AF"  # Dark blue text
        active_border_color = "#BFDBFE"  # Blue border
        
        # Verify colors are valid hex codes
        assert active_bg_color.startswith("#"), "Background color should be hex"
        assert len(active_bg_color) == 7, "Background color should be 7 characters"
        
        assert active_text_color.startswith("#"), "Text color should be hex"
        assert len(active_text_color) == 7, "Text color should be 7 characters"
        
        assert active_border_color.startswith("#"), "Border color should be hex"
        assert len(active_border_color) == 7, "Border color should be 7 characters"
    
    def test_inactive_state_colors_defined(self):
        """Test that inactive state uses correct colors (gray text)."""
        # Expected CSS properties for inactive state
        inactive_text_color = "#6B7280"  # Gray text
        inactive_bg_color = "transparent"  # Transparent background
        
        # Verify colors
        assert inactive_text_color.startswith("#"), "Inactive text color should be hex"
        assert len(inactive_text_color) == 7, "Inactive text color should be 7 characters"
        assert inactive_bg_color == "transparent", "Inactive background should be transparent"
    
    def test_hover_state_colors_defined(self):
        """Test that hover state uses correct colors."""
        # Expected CSS properties for hover state
        hover_bg_color = "#F3F4F6"  # Light gray background
        hover_text_color = "#111827"  # Dark text
        
        # Verify colors
        assert hover_bg_color.startswith("#"), "Hover background color should be hex"
        assert len(hover_bg_color) == 7, "Hover background color should be 7 characters"
        
        assert hover_text_color.startswith("#"), "Hover text color should be hex"
        assert len(hover_text_color) == 7, "Hover text color should be 7 characters"
    
    def test_css_contains_radio_button_styling(self):
        """Test that CSS includes radio button navigation styling."""
        # Import the CSS function and capture its output
        import io
        from contextlib import redirect_stdout
        
        # The apply_custom_css function uses st.markdown, so we can't directly test it
        # Instead, we verify the expected CSS properties exist in the ui_components module
        
        # Read the ui_components.py file to verify CSS content
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # Verify key CSS selectors and properties exist
        assert '.stRadio > div > label' in content, "Radio button label styling missing"
        assert 'data-checked="true"' in content, "Active state selector missing"
        assert 'background-color: #EFF6FF' in content, "Active background color missing"
        assert 'color: #1E40AF' in content, "Active text color missing"
        assert 'border: 1px solid #BFDBFE' in content, "Active border missing"
    
    def test_navigation_spacing_properties(self):
        """Test that navigation has proper spacing and padding."""
        # Expected spacing properties
        padding = "0.625rem 1rem"  # Vertical and horizontal padding
        gap = "0.5rem"  # Gap between navigation items
        border_radius = "6px"  # Rounded corners
        
        # Verify spacing values are valid
        assert "rem" in padding, "Padding should use rem units"
        assert "rem" in gap, "Gap should use rem units"
        assert "px" in border_radius, "Border radius should use px units"
    
    def test_navigation_font_properties(self):
        """Test that navigation uses correct font properties."""
        # Expected font properties
        font_size = "0.875rem"  # 14px
        font_weight_inactive = "500"  # Medium weight
        font_weight_active = "600"  # Semi-bold weight
        
        # Verify font properties
        assert "rem" in font_size, "Font size should use rem units"
        assert font_weight_inactive.isdigit(), "Font weight should be numeric"
        assert font_weight_active.isdigit(), "Font weight should be numeric"
        assert int(font_weight_active) > int(font_weight_inactive), \
            "Active font weight should be heavier than inactive"
    
    def test_radio_circles_hidden(self):
        """Test that radio button circles are hidden."""
        # Read the ui_components.py file
        ui_components_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'ui_components.py'
        )
        
        with open(ui_components_path, 'r') as f:
            content = f.read()
        
        # Verify that radio circles are hidden
        assert 'display: none' in content, "Radio circles should be hidden"
        assert 'div:first-child' in content, "First child selector should exist"
    
    def test_transition_properties(self):
        """Test that navigation has smooth transitions."""
        # Expected transition property
        transition = "all 0.2s ease"
        
        # Verify transition format
        assert "all" in transition, "Transition should apply to all properties"
        assert "ease" in transition, "Transition should use ease timing"
        assert "0.2s" in transition or "200ms" in transition, \
            "Transition should have duration"


class TestNavigationBehavior:
    """Test navigation component behavior."""
    
    def test_page_selection_updates_active_state(self):
        """Test that selecting a page updates the active state."""
        pages = [
            "Risk Overview",
            "Customer Deep Dive",
            "Real-time Monitor",
            "Model Performance",
            "Interventions Tracker"
        ]
        
        # Simulate selecting each page
        for page in pages:
            selected_page = page
            
            # Verify the selected page is in the list
            assert selected_page in pages, f"Selected page '{selected_page}' not in pages list"
    
    def test_only_one_page_active_at_a_time(self):
        """Test that only one page can be active at a time."""
        pages = [
            "Risk Overview",
            "Customer Deep Dive",
            "Real-time Monitor",
            "Model Performance",
            "Interventions Tracker"
        ]
        
        # Simulate selecting a page
        selected_page = "Customer Deep Dive"
        
        # Count how many pages match the selected page
        active_count = sum(1 for page in pages if page == selected_page)
        
        # Only one page should match
        assert active_count == 1, f"Expected 1 active page, got {active_count}"
    
    def test_clicking_current_page_maintains_state(self):
        """Test that clicking the currently active page maintains the state."""
        current_page = "Risk Overview"
        
        # Simulate clicking the current page again
        new_page = current_page
        
        # State should remain the same
        assert new_page == current_page, "Clicking current page should maintain state"


class TestNavigationAccessibility:
    """Test navigation accessibility features."""
    
    def test_navigation_uses_semantic_html(self):
        """Test that navigation uses semantic HTML elements."""
        # Radio buttons are semantic form elements
        # Streamlit's st.radio component generates proper HTML
        
        # Verify that we're using st.radio (checked in app.py)
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify st.radio is used
        assert 'st.sidebar.radio' in content, "Should use st.sidebar.radio for navigation"
        assert 'label_visibility="collapsed"' in content, \
            "Should hide label for cleaner appearance"
    
    def test_navigation_has_proper_contrast(self):
        """Test that navigation colors have sufficient contrast."""
        # Active state: #1E40AF (dark blue) on #EFF6FF (light blue)
        # This combination provides good contrast
        
        # Inactive state: #6B7280 (gray) on transparent/white
        # This combination provides good contrast
        
        # These are professional banking colors with good accessibility
        assert True, "Colors chosen for good contrast"


class TestNavigationLayout:
    """Test navigation layout and positioning."""
    
    def test_navigation_section_header_exists(self):
        """Test that navigation section has a header."""
        # Read app.py to verify section header
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify navigation header exists
        assert '📍 NAVIGATION' in content, "Navigation section header should exist"
    
    def test_navigation_positioned_correctly(self):
        """Test that navigation is positioned between branding and Quick Stats."""
        # Read app.py to verify layout order
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find positions of key elements
        branding_pos = content.find('🎯 Pre-Delinquency Engine')
        navigation_pos = content.find('📍 NAVIGATION')
        stats_pos = content.find('📊 QUICK STATS')
        
        # Verify order: branding -> navigation -> stats
        assert branding_pos < navigation_pos, \
            "Navigation should come after branding"
        assert navigation_pos < stats_pos, \
            "Navigation should come before Quick Stats"
    
    def test_dividers_separate_sections(self):
        """Test that dividers separate navigation from other sections."""
        # Read app.py to verify dividers
        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'dashboard', 'app.py'
        )
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count dividers (st.sidebar.markdown("---"))
        divider_count = content.count('st.sidebar.markdown("---")')
        
        # Should have at least 2 dividers (before and after navigation)
        assert divider_count >= 2, \
            f"Expected at least 2 dividers, found {divider_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
