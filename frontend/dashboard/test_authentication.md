# Frontend Authentication Testing
Week 13-15: SECURITY-007

## Test Instructions

### Prerequisites
1. Start API Gateway: `python api_gateway/start_with_mock_db.py`
2. Start Frontend: `cd frontend/dashboard && npm run dev`
3. Open browser: http://localhost:3001

### Test Cases

#### 1. Login Flow
- [ ] Open http://localhost:3001 - should show login page
- [ ] Try invalid credentials - should show error message
- [ ] Login with admin@promptops.com / admin123 - should succeed
- [ ] Should redirect to dashboard
- [ ] User info should appear in navbar (email initial, full name/role)
- [ ] Logout button should be visible

#### 2. Token Storage
- [ ] After login, check localStorage in DevTools:
  - `promptops_token` - JWT token present
  - `promptops_user` - User data present
  - `promptops_token_expiry` - Expiry timestamp present

#### 3. Protected Routes
- [ ] After login, should see dashboard
- [ ] Click logout - should return to login page
- [ ] Refresh page while logged out - should stay on login page
- [ ] Login again - should see dashboard
- [ ] Refresh page while logged in - should stay on dashboard

#### 4. Token Expiry
- [ ] Login successfully
- [ ] In DevTools console, manually set expiry to past:
  ```javascript
  localStorage.setItem('promptops_token_expiry', '0')
  ```
- [ ] Refresh page - should be logged out and see login page

#### 5. Auto-Refresh
- [ ] Login successfully
- [ ] Wait 25 minutes (or modify AuthContext refresh time for testing)
- [ ] Token should auto-refresh before 30-minute expiry
- [ ] User should remain logged in

#### 6. API Integration
- [ ] Login as admin@promptops.com
- [ ] Open DevTools Network tab
- [ ] Interact with dashboard
- [ ] API requests should include `Authorization: Bearer <token>` header

#### 7. Multi-User Testing
- [ ] Login as admin@promptops.com / admin123
  - Should see "System Administrator" or "ADMIN" in navbar
- [ ] Logout
- [ ] Login as pm@promptops.com / pm123
  - Should see "Product Manager" or "PM" in navbar

#### 8. Error Handling
- [ ] Try login without email - should show "Please enter both email and password"
- [ ] Try login without password - should show "Please enter both email and password"
- [ ] Try invalid email format - browser should validate
- [ ] Try wrong password - should show "Incorrect email or password"
- [ ] Try inactive user (if any) - should show "User account is inactive"

#### 9. Loading States
- [ ] During login - button should show "Signing in..." and be disabled
- [ ] Initial page load - should show loading spinner briefly
- [ ] Should not flash login page if already authenticated

#### 10. Browser Compatibility
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Edge
- [ ] Test in Safari (if available)

## Expected Behavior

### Login Page
- Clean, centered login form
- PromptOps logo and branding
- Email and password fields
- Sign in button with loading state
- Error messages displayed clearly
- Test accounts shown at bottom

### Dashboard (After Login)
- Navbar with user info and logout button
- Welcome message
- Command input
- Stats grid
- System status
- All previous functionality intact

### Security Features
- JWT token stored in localStorage
- Token included in all API requests
- Auto-refresh before expiry
- Logout clears all stored data
- Protected routes redirect to login

## Test Results

### Date: ___________
### Tester: ___________

| Test Case | Status | Notes |
|-----------|--------|-------|
| 1. Login Flow | [ ] Pass [ ] Fail | |
| 2. Token Storage | [ ] Pass [ ] Fail | |
| 3. Protected Routes | [ ] Pass [ ] Fail | |
| 4. Token Expiry | [ ] Pass [ ] Fail | |
| 5. Auto-Refresh | [ ] Pass [ ] Fail | |
| 6. API Integration | [ ] Pass [ ] Fail | |
| 7. Multi-User Testing | [ ] Pass [ ] Fail | |
| 8. Error Handling | [ ] Pass [ ] Fail | |
| 9. Loading States | [ ] Pass [ ] Fail | |
| 10. Browser Compatibility | [ ] Pass [ ] Fail | |

## Issues Found

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

## Sign-off

- [ ] All tests passed
- [ ] Issues documented
- [ ] Ready for UAT

Tester Signature: ______________ Date: __________
