"""
Test layout preservation for dashboard sidebar navigation.

This test verifies that:
1. Navigation section header remains in place
2. Divider is positioned correctly
3. Quick Stats section appears below navigation
4. Sidebar width and overall layout are maintained

Requirements: 5.1, 5.2, 5.3, 5.4, 1.4
"""

import re


def test_sidebar_structure():
    """
    Verify the sidebar maintains correct structure with navigation and Quick Stats.
    
    This test reads the app.py file and verifies:
    - Navigation section header exists
    - Divider separates navigation from Quick Stats
    - Quick Stats section appears after navigation
    - Proper ordering is maintained
    """
    with open('dashboard/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the sidebar section
    sidebar_start = content.find('# SIDEBAR NAVIGATION')
    assert sidebar_start != -1, "Sidebar navigation section not found"
    
    # Extract sidebar section (up to MAIN CONTENT AREA)
    sidebar_end = content.find('# MAIN CONTENT AREA')
    sidebar_content = content[sidebar_start:sidebar_end]
    
    # Verify branding is at the top
    branding_match = re.search(r'st\.sidebar\.markdown.*🎯 Pre-Delinquency Engine', sidebar_content)
    assert branding_match is not None, "Dashboard branding not found"
    branding_pos = branding_match.start()
    
    # Verify first divider after branding
    first_divider = sidebar_content.find('st.sidebar.markdown("---")', branding_pos)
    assert first_divider != -1, "First divider not found after branding"
    assert first_divider > branding_pos, "First divider should come after branding"
    
    # Verify navigation section header
    nav_header_match = re.search(r'st\.sidebar\.markdown.*📍 NAVIGATION', sidebar_content)
    assert nav_header_match is not None, "Navigation section header not found"
    nav_header_pos = nav_header_match.start()
    assert nav_header_pos > first_divider, "Navigation header should come after first divider"
    
    # Verify radio button navigation
    radio_match = re.search(r'st\.sidebar\.radio\(', sidebar_content)
    assert radio_match is not None, "Radio button navigation not found"
    radio_pos = radio_match.start()
    assert radio_pos > nav_header_pos, "Radio navigation should come after navigation header"
    
    # Verify second divider after navigation
    second_divider = sidebar_content.find('st.sidebar.markdown("---")', first_divider + 1)
    assert second_divider != -1, "Second divider not found after navigation"
    assert second_divider > radio_pos, "Second divider should come after radio navigation"
    
    # Verify Quick Stats section header
    stats_header_match = re.search(r'st\.sidebar\.markdown.*📊 QUICK STATS', sidebar_content)
    assert stats_header_match is not None, "Quick Stats section header not found"
    stats_header_pos = stats_header_match.start()
    assert stats_header_pos > second_divider, "Quick Stats header should come after second divider"
    
    # Verify metrics are present after Quick Stats header
    metric_match = re.search(r'st\.sidebar\.metric\(', sidebar_content[stats_header_pos:])
    assert metric_match is not None, "Metrics not found in Quick Stats section"
    
    print("✅ Sidebar structure verification passed:")
    print("  - Dashboard branding at top")
    print("  - First divider after branding")
    print("  - Navigation section header present")
    print("  - Radio button navigation present")
    print("  - Second divider after navigation")
    print("  - Quick Stats section header present")
    print("  - Metrics present in Quick Stats")


def test_css_no_width_override():
    """
    Verify CSS styling doesn't override sidebar width.
    
    This test ensures the custom CSS doesn't include width properties
    that would change the default Streamlit sidebar width.
    """
    with open('dashboard/ui_components.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the sidebar CSS section
    sidebar_css_start = content.find('section[data-testid="stSidebar"]')
    assert sidebar_css_start != -1, "Sidebar CSS not found"
    
    # Extract CSS up to the next major section
    sidebar_css_end = content.find('/* Tables */', sidebar_css_start)
    sidebar_css = content[sidebar_css_start:sidebar_css_end]
    
    # Verify no width property is set
    assert 'width:' not in sidebar_css.lower(), "CSS should not override sidebar width"
    assert 'min-width:' not in sidebar_css.lower(), "CSS should not override sidebar min-width"
    assert 'max-width:' not in sidebar_css.lower(), "CSS should not override sidebar max-width"
    
    print("✅ CSS width verification passed:")
    print("  - No width override in sidebar CSS")
    print("  - No min-width override in sidebar CSS")
    print("  - No max-width override in sidebar CSS")


def test_navigation_options_complete():
    """
    Verify all five navigation options are present.
    
    This ensures the navigation component displays all required pages.
    """
    with open('dashboard/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the radio button section
    radio_start = content.find('page = st.sidebar.radio(')
    assert radio_start != -1, "Radio button navigation not found"
    
    # Extract the radio button definition (next 300 characters should contain all options)
    radio_section = content[radio_start:radio_start + 400]
    
    # Verify all five page options are present
    required_pages = [
        "Risk Overview",
        "Customer Deep Dive",
        "Real-time Monitor",
        "Model Performance",
        "Interventions Tracker"
    ]
    
    for page in required_pages:
        assert page in radio_section, f"Page '{page}' not found in navigation options"
    
    print("✅ Navigation options verification passed:")
    print("  - All 5 page options present")
    for page in required_pages:
        print(f"    ✓ {page}")


def test_label_visibility_collapsed():
    """
    Verify radio button label is collapsed for clean appearance.
    """
    with open('dashboard/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the radio button section
    radio_start = content.find('page = st.sidebar.radio(')
    radio_section = content[radio_start:radio_start + 400]
    
    # Verify label_visibility is set to collapsed
    assert 'label_visibility="collapsed"' in radio_section, \
        "Radio button should have label_visibility='collapsed'"
    
    print("✅ Label visibility verification passed:")
    print("  - label_visibility set to 'collapsed'")


if __name__ == '__main__':
    print("Testing layout preservation for dashboard sidebar navigation...\n")
    
    try:
        test_sidebar_structure()
        print()
        test_css_no_width_override()
        print()
        test_navigation_options_complete()
        print()
        test_label_visibility_collapsed()
        print()
        print("=" * 60)
        print("✅ ALL LAYOUT PRESERVATION TESTS PASSED")
        print("=" * 60)
        print("\nVerified:")
        print("  ✓ Navigation section header remains in place")
        print("  ✓ Divider positioned correctly between sections")
        print("  ✓ Quick Stats section appears below navigation")
        print("  ✓ Sidebar width and layout maintained (no CSS overrides)")
        print("  ✓ All navigation options present and visible")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        exit(1)
