## Bug Report: [Test] Application fails to load due to locator issue

- **Test Case:** TC-001
- **Severity:** P1
- **Component:** Application Load
- **Application URL:** https://dev.dmerocket.com/insurance
- **Environment:** Windows_NT, Chrome
- **Test Data Used:** Username: admin@selectortho.net, Password: Password123!

### Steps to Reproduce
1. 1. Navigate to https://dev.dmerocket.com/insurance
1. 2. Enter valid login credentials.
1. 3. Verify landing on the application dashboard.

### Expected Result
User lands on the application dashboard.

### Actual Result
Application fails to load due to locator issue.

### Error Log
```
Error: toBeVisible can be only used with Locator object, was called with _Page
```

---
## Bug Report: [Test] Application fails to load with invalid URL

- **Test Case:** TC-002
- **Severity:** P0
- **Component:** Login
- **Application URL:** https://dev-otl8xt3f1rt2o3gd.us.auth0.com/u/login?state=hKFo2SBTTzBOUDE3bG5qUnBLY1lOeG1kc19ITHRtWW9zWmNHeKFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIC1xdVg0LXpqaGFiRHplLVRjejJUR1pBNFpGMFFLT1oto2NpZNkgU2xxYzZTc1JBVVNZeUx3bk1USHNVdVJEVmllbzRPdFg
- **Environment:** Browser: Chrome, OS: Windows 10
- **Test Data Used:** Invalid URL: https://dev.dmerocket.com/invalid-url

### Steps to Reproduce
1. 1. Navigate to an invalid URL.

### Expected Result
Application fails to load.

### Actual Result
Application navigated to a login page instead of showing a 404 error.

### Error Log
```
expect(page).toHaveURL(expected) failed. Expected pattern: /.*404/. Received string: "https://dev-otl8xt3f1rt2o3gd.us.auth0.com/u/login?state=hKFo2SBTTzBOUDE3bG5qUnBLY1lOeG1kc19ITHRtWW9zWmNHeKFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIC1xdVg0LXpqaGFiRHplLVRjejJUR1pBNFpGMFFLT1oto2NpZNkgU2xxYzZTc1JBVVNZeUx3bk1USHNVdVJEVmllbzRPdFg"
```

---
## Bug Report: [Test] Application Load with Invalid Credentials fails due to timeout

- **Test Case:** TC-003
- **Severity:** P0
- **Component:** Login
- **Application URL:** http://example.com/login
- **Environment:** Chrome on Windows 10
- **Test Data Used:** Username: invalidUser, Password: invalidPass

### Steps to Reproduce
1. 1. Navigate to the application load page.
1. 2. Enter invalid login credentials.

### Expected Result
User receives an authentication error.

### Actual Result
Test timeout of 30000ms exceeded.

### Error Log
```
Test timeout of 30000ms exceeded.
```

---
## Bug Report: [Test] Application Load with No Credentials fails to prompt for credentials

- **Test Case:** TC-004
- **Severity:** P0
- **Component:** Login
- **Application URL:** http://example.com/login
- **Environment:** Chrome on Windows 10
- **Test Data Used:** No credentials provided

### Steps to Reproduce
1. 1. Navigate to the application load page.
1. 2. Leave the login fields empty.
1. 3. Observe the behavior after 30 seconds.

### Expected Result
User receives a prompt to enter credentials.

### Actual Result
No prompt received; test timed out.

### Error Log
```
Test timeout of 30000ms exceeded.
```

---
## Bug Report: [Test] Admin user login test timed out

- **Test Case:** TC-005
- **Severity:** P1
- **Component:** Login
- **Application URL:** http://example.com/login
- **Environment:** Chrome on Windows 10
- **Test Data Used:** Username: admin@selectortho.net, Password: Password123!

### Steps to Reproduce
1. 1. Navigate to the login page.
1. 2. Enter username 'admin@selectortho.net'.
1. 3. Enter password 'Password123!'.
1. 4. Click on the 'Login' button.

### Expected Result
Admin user logs in successfully.

### Actual Result
Test timed out before login could complete.

### Error Log
```
Test timeout of 30000ms exceeded.
```

---
## Bug Report: [Test] Admin User Login with Incorrect Password timed out

- **Test Case:** TC-006
- **Severity:** P0
- **Component:** Login
- **Application URL:** https://example.com/login
- **Environment:** Chrome on Windows 10
- **Test Data Used:** Username: admin@selectortho.net, Password: incorrect_password

### Steps to Reproduce
1. 1. Navigate to the login page.
1. 2. Enter username 'admin@selectortho.net'.
1. 3. Enter incorrect password.
1. 4. Submit the login form.

### Expected Result
User receives an authentication error.

### Actual Result
Test timed out without receiving an authentication error.

### Error Log
```
Test timeout of 30000ms exceeded.
```

---
## Bug Report: [Test] Admin User Login with Incorrect Username fails due to timeout

- **Test Case:** TC-007
- **Severity:** P1
- **Component:** Login
- **Application URL:** http://example.com/login
- **Environment:** Chrome on Windows 10
- **Test Data Used:** Username: invalidUser, Password: validPassword123

### Steps to Reproduce
1. 1. Navigate to the login page.
1. 2. Enter incorrect username and valid password.
1. 3. Click on the login button.

### Expected Result
User receives an authentication error.

### Actual Result
Test timeout of 30000ms exceeded.

### Error Log
```
Test timeout of 30000ms exceeded.
```

---
