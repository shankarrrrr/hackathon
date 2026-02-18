# Manual Keyboard Navigation Verification

**Task:** 5.2 Test keyboard navigation  
**Requirements:** 7.1, 7.3  
**Date:** 2024  

## Purpose

This document provides a manual testing checklist for keyboard navigation functionality in the dashboard sidebar. While automated tests verify the logic, manual testing ensures the actual user experience meets accessibility standards.

## Prerequisites

- Dashboard is running (`streamlit run dashboard/app.py`)
- Browser is open (Chrome, Firefox, Safari, or Edge)
- Keyboard is the primary input device for testing

## Test Procedures

### 1. Tab Key Navigation

**Objective:** Verify Tab key navigates through radio buttons sequentially

**Steps:**
1. Open the dashboard in a browser
2. Click in the browser address bar, then press Tab repeatedly
3. Observe focus moving through page elements
4. When focus reaches the sidebar navigation, continue pressing Tab

**Expected Results:**
- [ ] Focus moves to the first navigation option (Risk Overview)
- [ ] Pressing Tab again moves focus to the next option (Customer Deep Dive)
- [ ] Focus continues through all 5 navigation options in order
- [ ] Focus indicators are clearly visible on each option
- [ ] After the last navigation option, Tab moves focus to the next element (Quick Stats or main content)

**Actual Results:**
```
[Record observations here]
```

---

### 2. Shift+Tab Reverse Navigation

**Objective:** Verify Shift+Tab navigates backwards through radio buttons

**Steps:**
1. Tab to the last navigation option (Interventions Tracker)
2. Press Shift+Tab repeatedly
3. Observe focus moving backwards through options

**Expected Results:**
- [ ] Focus moves backwards through navigation options
- [ ] Order is: Interventions Tracker → Model Performance → Real-time Monitor → Customer Deep Dive → Risk Overview
- [ ] Focus indicators remain visible during reverse navigation
- [ ] Shift+Tab from first option moves focus to previous element (branding or browser UI)

**Actual Results:**
```
[Record observations here]
```

---

### 3. Arrow Key Selection - Down Arrow

**Objective:** Verify Arrow Down key selects next option

**Steps:**
1. Tab to the navigation section (focus on any option)
2. Press Arrow Down key repeatedly
3. Observe selection changing

**Expected Results:**
- [ ] Arrow Down moves selection to the next option
- [ ] Visual selection indicator (blue background) moves with each press
- [ ] At the last option (Interventions Tracker), Arrow Down either stays on last option or wraps to first
- [ ] Main content area updates to show the selected page

**Actual Results:**
```
[Record observations here]
```

---

### 4. Arrow Key Selection - Up Arrow

**Objective:** Verify Arrow Up key selects previous option

**Steps:**
1. Tab to the navigation section
2. Press Arrow Down to move to a middle option (e.g., Real-time Monitor)
3. Press Arrow Up key repeatedly
4. Observe selection changing

**Expected Results:**
- [ ] Arrow Up moves selection to the previous option
- [ ] Visual selection indicator moves backwards
- [ ] At the first option (Risk Overview), Arrow Up either stays on first option or wraps to last
- [ ] Main content area updates to show the selected page

**Actual Results:**
```
[Record observations here]
```

---

### 5. Enter Key Activation

**Objective:** Verify Enter key activates the focused option

**Steps:**
1. Tab to the navigation section
2. Use Arrow keys to focus on a different option (don't select it yet)
3. Press Enter key
4. Observe page change

**Expected Results:**
- [ ] Enter key activates the focused option
- [ ] Main content area updates to show the selected page
- [ ] Visual selection indicator (blue background) appears on the activated option
- [ ] Page title in main content matches the selected navigation option

**Actual Results:**
```
[Record observations here]
```

---

### 6. Space Key Activation

**Objective:** Verify Space key activates the focused option

**Steps:**
1. Tab to the navigation section
2. Use Arrow keys to focus on a different option
3. Press Space key
4. Observe page change

**Expected Results:**
- [ ] Space key activates the focused option
- [ ] Main content area updates to show the selected page
- [ ] Visual selection indicator appears on the activated option
- [ ] Behavior is identical to Enter key activation

**Actual Results:**
```
[Record observations here]
```

---

### 7. Focus Indicator Visibility

**Objective:** Verify focus indicators are clearly visible

**Steps:**
1. Tab through all navigation options slowly
2. Observe the visual feedback for each focused element
3. Test in both light and dark browser themes (if applicable)

**Expected Results:**
- [ ] Focused option has visible hover state (light gray background: #F3F4F6)
- [ ] Selected option has distinct active state (blue background: #EFF6FF, blue text: #1E40AF, blue border)
- [ ] Focus indicators have sufficient contrast ratio (WCAG AA: 3:1 minimum)
- [ ] Focus indicators are visible in all browser themes
- [ ] No confusion between focused and selected states

**Actual Results:**
```
[Record observations here]
```

---

### 8. Keyboard Navigation State Persistence

**Objective:** Verify selection persists after keyboard navigation

**Steps:**
1. Use keyboard to navigate to "Customer Deep Dive"
2. Press Enter or Space to select it
3. Tab away from navigation to main content
4. Tab back to navigation section
5. Observe which option is selected

**Expected Results:**
- [ ] "Customer Deep Dive" remains selected (blue background)
- [ ] Main content still shows Customer Deep Dive page
- [ ] Selection persists across focus changes
- [ ] Selection persists after interacting with other page elements

**Actual Results:**
```
[Record observations here]
```

---

### 9. No Keyboard Trap

**Objective:** Verify users can navigate away from radio buttons

**Steps:**
1. Tab to the navigation section
2. Continue pressing Tab
3. Verify focus moves to next section (Quick Stats)
4. Continue tabbing through entire page
5. Verify you can return to navigation via Shift+Tab

**Expected Results:**
- [ ] Tab moves focus out of navigation to Quick Stats section
- [ ] No keyboard trap - user is never stuck in navigation
- [ ] Can return to navigation via Shift+Tab
- [ ] Can navigate through entire page using only keyboard

**Actual Results:**
```
[Record observations here]
```

---

### 10. Screen Reader Compatibility

**Objective:** Verify keyboard navigation works with screen readers

**Steps:**
1. Enable screen reader (NVDA on Windows, VoiceOver on Mac, JAWS, etc.)
2. Tab to navigation section
3. Listen to screen reader announcements
4. Use Arrow keys to navigate options
5. Press Enter to select an option

**Expected Results:**
- [ ] Screen reader announces "Navigation" or similar section label
- [ ] Each option is announced with its text (e.g., "Risk Overview")
- [ ] Screen reader indicates which option is selected
- [ ] Screen reader announces state changes when selection changes
- [ ] Radio button role is properly announced

**Actual Results:**
```
[Record observations here]
```

---

### 11. Browser Compatibility

**Objective:** Verify keyboard navigation works across browsers

**Browsers to Test:**
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on Mac)

**For Each Browser:**
1. Test Tab navigation
2. Test Arrow key navigation
3. Test Enter/Space activation
4. Verify focus indicators are visible

**Expected Results:**
- [ ] Keyboard navigation works identically in all browsers
- [ ] Focus indicators are visible in all browsers
- [ ] No browser-specific issues or quirks

**Actual Results:**
```
Browser: Chrome
[Record observations]

Browser: Firefox
[Record observations]

Browser: Safari
[Record observations]
```

---

### 12. Rapid Key Press Handling

**Objective:** Verify system handles rapid keyboard input gracefully

**Steps:**
1. Tab to navigation section
2. Rapidly press Arrow Down key 10-15 times
3. Observe behavior
4. Rapidly press Arrow Up key 10-15 times
5. Observe behavior

**Expected Results:**
- [ ] System handles rapid key presses without errors
- [ ] Selection stops at last option when pressing Arrow Down rapidly
- [ ] Selection stops at first option when pressing Arrow Up rapidly
- [ ] No visual glitches or flickering
- [ ] Page remains responsive

**Actual Results:**
```
[Record observations here]
```

---

## Summary

**Total Tests:** 12  
**Tests Passed:** ___  
**Tests Failed:** ___  
**Issues Found:** ___  

### Issues Identified

```
[List any issues found during manual testing]
```

### Recommendations

```
[List any recommendations for improvements]
```

### Sign-off

**Tester Name:** _______________  
**Date:** _______________  
**Status:** [ ] PASS [ ] FAIL [ ] PASS WITH ISSUES  

---

## Notes

- This manual verification complements the automated tests in `test_keyboard_navigation.py`
- Requirements 7.1 (keyboard controls) and 7.3 (visible focus indicators) are validated through these tests
- WCAG 2.1 Level AA compliance is verified through these procedures
- Any failures should be documented and addressed before marking task 5.2 as complete
