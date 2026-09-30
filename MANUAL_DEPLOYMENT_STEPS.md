# 📹 Manual Deployment Recording Guide

## Screen Recording Setup

### Software Recommendations:
1. **Windows Game Bar** (Built-in)
   - Press `Win + G` to open
   - Click "Capture" button
   - Select "Record window" for PromptOps only

2. **OBS Studio** (Free, Professional)
   - Download: https://obsproject.com/
   - Create window capture for browser only
   - Set output to 1920x1080

3. **ShareX** (Free, Simple)
   - Download: https://getsharex.com/
   - Screen recording with easy editing

---

## 🎬 Recording Script

### Pre-Recording Checklist:
- [ ] Browser open at http://localhost:3000
- [ ] Logged in as admin@promptops.com
- [ ] Screen recorder ready
- [ ] Audio ON (optional for narration)
- [ ] Browser zoom at 100%
- [ ] Close unnecessary tabs/windows

---

## Recording Sequence (5 Minutes)

### Scene 1: Login (30 seconds)
```
[START RECORDING]

Action: Show login page
Say: "Welcome to PromptOps. Let me log in."

Action: Type admin@promptops.com
Action: Type password (don't show it)
Action: Click Login

Result: Dashboard appears
```

### Scene 2: Home Dashboard Tour (30 seconds)
```
Action: Pan around the dashboard
Say: "This is the PromptOps home dashboard."

Show:
- Navigation menu (Home, Autonomy, Discovery, etc.)
- Main content area
- User profile
- Quick action cards

Say: "Let's deploy a web application to AWS."
```

### Scene 3: Initiate Deployment (15 seconds)
```
Action: Look for deployment option

Options:
A) Click "Deploy App" button/card
B) Type in command box: "Deploy application to AWS"
C) Navigate to deployment page

Say: "I'll deploy a React e-commerce application."
```

### Scene 4: Fill Deployment Form (45 seconds)
```
Form Fields:

1. Application Name
   Type: jewelry-vault-demo
   Say: "This is our jewelry e-commerce demo."

2. GitHub Repository URL
   Type: https://github.com/ashi100sh/jewelry-vault
   Say: "The source code is on GitHub."

3. Branch
   Type: main
   Say: "Deploying from the main branch."

4. Deployment Target
   Select: AWS S3 Static Hosting
   Say: "We'll use S3 for static hosting."

5. Region
   Select: us-east-1
   Say: "Deploying to US East region."

6. Options
   Check: CloudFront CDN
   Check: Enable HTTPS
   Check: Enable Monitoring
   Say: "Enabling CDN, HTTPS, and monitoring."
```

### Scene 5: Start Deployment (15 seconds)
```
Action: Review form
Say: "Everything looks good. Let's deploy!"

Action: Click "Deploy Now" button
Say: "Deployment starting..."
```

### Scene 6: Progress Monitoring (90 seconds)
```
Watch deployment progress:

Step 1/8: ✓ Cloning repository
Say: "First, it's cloning the GitHub repo."

Step 2/8: ✓ Installing dependencies
Say: "Installing npm packages."

Step 3/8: ✓ Building application
Say: "Building the React production bundle."

Step 4/8: ✓ Creating S3 bucket
Say: "Creating the S3 bucket on AWS."

Step 5/8: ✓ Uploading files
Say: "Uploading the built files to S3."

Step 6/8: ✓ Configuring CloudFront
Say: "Setting up CloudFront CDN for faster delivery."

Step 7/8: ✓ Setting up monitoring
Say: "Configuring real-time monitoring."

Step 8/8: ✓ Verification
Say: "Final verification... and done!"
```

### Scene 7: Deployment Success (30 seconds)
```
Show success modal:

Elements visible:
- ✓ Deployment Successful!
- Website URL
- CloudFront URL
- Deployment stats

Say: "Perfect! The application is now live on AWS."

Action: Hover over the URL
Say: "Here's the live website URL."
```

### Scene 8: View Deployed Application (30 seconds)
```
Action: Click "View Application"

Result: Embedded iframe or new tab opens
Say: "Let's see the deployed jewelry store."

Show:
- The website loading
- Homepage with jewelry items
- Navigation working
- Responsive design

Say: "The site is fully functional and hosted on AWS."
```

### Scene 9: Security Monitoring (45 seconds)
```
Action: Navigate to "Security Monitor" tab
Say: "Now let's check the security and performance."

Action: Enter deployed URL in form
Action: Enter bucket name

Action: Click "Security Scan"
Say: "Running a comprehensive security scan."

Wait: 30 seconds

Show results:
- System metrics (CPU, Memory, Disk)
- Alert count
- Security findings

Say: "The scan found [X] issues. Let's review them."

Action: Click "Alerts" tab
Show: List of security findings
```

### Scene 10: Load Testing (30 seconds)
```
Action: Click "Run Load Test"
Say: "Let's test how it handles traffic."

Show progress:
- Requests counter
- Response time graph
- Error rate

Wait for completion

Show results:
- Total requests: 6000
- Error rate: 0.2%
- Avg response time: 145ms

Say: "Excellent! The application handles load very well."
```

### Scene 11: Wrap Up (15 seconds)
```
Action: Show dashboard overview
Say: "In just 5 minutes, we deployed a production-ready 
     e-commerce site with security scanning and monitoring."

Say: "That's PromptOps - AI-powered DevOps automation."

[STOP RECORDING]
```

---

## 🎤 Narration Script (Full)

```
[INTRO]
"Welcome to PromptOps, the AI-powered DevOps platform that 
makes cloud deployment as simple as clicking a button."

[LOGIN]
"Let me start by logging into the platform."

[DASHBOARD]
"This is the PromptOps dashboard where we can manage all our
deployments, monitor infrastructure, and automate DevOps tasks."

[START DEPLOYMENT]
"Today, I'll deploy a real e-commerce jewelry store to AWS. 
Let me click on Deploy Application."

[FORM - APP NAME]
"First, I'll name this deployment 'jewelry-vault-demo'."

[FORM - GITHUB]
"The source code is hosted on GitHub at this repository."

[FORM - SETTINGS]
"I'm deploying to AWS S3 for static hosting in the US East region,
with CloudFront CDN for global delivery, HTTPS for security, and
built-in monitoring."

[DEPLOY]
"Let's deploy! Watch as PromptOps handles everything automatically."

[PROGRESS - CLONE]
"It's starting by cloning the repository from GitHub..."

[PROGRESS - BUILD]
"Now installing dependencies and building the React application..."

[PROGRESS - AWS]
"Creating the S3 bucket, uploading files, and configuring CloudFront
CDN for fast global delivery..."

[PROGRESS - MONITOR]
"Setting up real-time monitoring and security scanning..."

[SUCCESS]
"And we're done! The application is live on AWS with a CloudFront
URL for optimal performance."

[VIEW APP]
"Let's view the deployed site. Here's the jewelry store running 
live on AWS infrastructure."

[SECURITY]
"PromptOps doesn't just deploy - it continuously monitors. Let's
run a security scan to check for vulnerabilities."

[SCAN RESULTS]
"The scan completed and found a few minor security recommendations.
With one click, we can auto-remediate these issues."

[LOAD TEST]
"Now let's test performance under load. I'm simulating 100 users
per second hitting the site..."

[RESULTS]
"Perfect! The application handled 6,000 requests with only 0.2%
errors and sub-200ms response times. This is production-ready!"

[CONCLUSION]
"In just 5 minutes, we went from source code to a production
deployment on AWS with security scanning, performance monitoring,
and CDN delivery. That's the power of PromptOps - making DevOps
accessible to everyone."
```

---

## Post-Recording Checklist

After recording:
- [ ] Review the video
- [ ] Check audio quality
- [ ] Trim beginning/ending
- [ ] Add captions (optional)
- [ ] Export in 1080p
- [ ] Add title slide (optional)

---

## Editing Tips

### Simple Edits:
1. Trim dead space at start/end
2. Speed up slow parts (1.5x)
3. Add arrows/highlights on key clicks
4. Add text overlays for URLs
5. Add background music (optional)

### Professional Edits:
1. Add intro/outro slides
2. Picture-in-picture for narration
3. Zoom effects on important UI elements
4. Transition effects between scenes
5. Lower-third text for descriptions

---

## File Naming
```
PromptOps_Deployment_Demo_v1.mp4
PromptOps_5min_Demo_Final.mp4
PromptOps_Jewelry_Vault_Deployment.mp4
```

---

## Sharing Options

1. **YouTube** (Public/Unlisted)
2. **Vimeo** (Password protected)
3. **Google Drive** (Shared link)
4. **Loom** (Quick sharing)
5. **Internal server** (Company only)

---

## Troubleshooting During Recording

### Issue: Form doesn't appear
- Refresh page (F5)
- Check console for errors (F12)
- Restart backend/frontend

### Issue: Deployment fails
- Check AWS credentials
- Verify GitHub URL accessible
- Check S3 bucket name is unique
- Review backend logs

### Issue: Monitoring shows empty
- Wait 10 seconds and refresh
- Check backend API running
- Verify endpoints responding

### Issue: Screen recorder lags
- Close other applications
- Reduce recording quality
- Record smaller window area
- Use hardware acceleration

---

## Quick Re-Record Scenarios

If you need to re-record a specific part:

**Scenario 1: Just the deployment**
- Start recording at deployment form
- Skip login/dashboard tour
- Focus only on deployment progress

**Scenario 2: Just the monitoring**
- Pre-deploy the application
- Start recording at Security Monitor tab
- Show scans and tests only

**Scenario 3: Just the results**
- Complete deployment beforehand
- Record only the success screen
- Show deployed app working

---

## Time Stamps for Video Chapters

```
00:00 - Introduction
00:15 - Login to PromptOps
00:30 - Dashboard Overview
01:00 - Start Deployment
01:30 - Configure Deployment Settings
02:15 - Deployment Progress
04:00 - Deployment Success
04:30 - View Deployed Application
05:00 - Security Scanning
05:45 - Load Testing
06:30 - Results & Conclusion
```

---

## Alternative: Demo Without Real Deployment

If AWS permissions are blocking real deployment:

1. **Mock the deployment**
   - Fill form but don't submit
   - Show progress UI (pre-recorded or simulated)
   - Show pre-deployed app

2. **Focus on monitoring**
   - Use pre-deployed jewelry-vault
   - Show security scanning
   - Show load testing
   - Emphasize monitoring features

3. **Use test environment**
   - Deploy to local MinIO (S3 compatible)
   - Show UI flow without AWS
   - Demonstrate process only

---

## Ready to Record!

Follow this script and you'll have a professional demo video showing the complete PromptOps deployment workflow!

**Remember:** 
- Keep it smooth and confident
- Speak clearly
- Pause between major steps
- Smile! (if doing webcam overlay)

Good luck! 🎥🚀
