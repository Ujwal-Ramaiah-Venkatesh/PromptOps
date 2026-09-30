"""
Automated PromptOps Demo Recording Script
==========================================

This script automatically:
1. Opens PromptOps UI
2. Logs in
3. Navigates through deployment
4. Fills forms
5. Shows monitoring
6. Records video of the entire process

Author: PromptOps Team
Date: 2026-06-03
"""

import asyncio
import time
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright, expect
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.system('chcp 65001 >nul 2>&1')

# Configuration
PROMPTOPS_URL = "http://localhost:3000"
LOGIN_EMAIL = "admin@promptops.com"
LOGIN_PASSWORD = "admin123"
OUTPUT_DIR = Path("demo_recordings")
VIDEO_FILE = OUTPUT_DIR / f"promptops_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

# Deployment Configuration
DEPLOYMENT_CONFIG = {
    "app_name": "jewelry-vault-demo",
    "repo_url": "https://github.com/ashi100sh/jewelry-vault",
    "branch": "main",
    "region": "us-east-1",
    "bucket_name": "jewelry-vault-demo"
}

# Speed settings (in seconds)
TYPING_DELAY = 100  # milliseconds between keystrokes
WAIT_SHORT = 2  # short wait
WAIT_MEDIUM = 5  # medium wait
WAIT_LONG = 10  # long wait


class PromptOpsDemoRecorder:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def setup(self):
        """Initialize Playwright and browser"""
        print("🎬 Setting up browser automation...")
        OUTPUT_DIR.mkdir(exist_ok=True)

        self.playwright = await async_playwright().start()

        # Launch browser with video recording
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Show browser window
            slow_mo=500,  # Slow down actions for visibility
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create context with video recording
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={'width': 1920, 'height': 1080}
        )

        self.page = await self.context.new_page()

        print(f"✅ Browser ready. Video will be saved to: {OUTPUT_DIR}")

    async def navigate_to_login(self):
        """Navigate to PromptOps login page"""
        print(f"\n📍 Step 1: Navigating to {PROMPTOPS_URL}")
        await self.page.goto(PROMPTOPS_URL, wait_until='networkidle')
        await asyncio.sleep(WAIT_SHORT)

        # Take screenshot
        await self.page.screenshot(path=OUTPUT_DIR / "01_login_page.png")
        print("✅ Login page loaded")

    async def perform_login(self):
        """Fill login form and submit"""
        print("\n🔐 Step 2: Logging in...")

        try:
            # Wait for login form
            await self.page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)

            # Fill email
            print(f"   Typing email: {LOGIN_EMAIL}")
            email_input = await self.page.query_selector('input[type="email"], input[name="email"]')
            await email_input.click()
            await email_input.type(LOGIN_EMAIL, delay=TYPING_DELAY)
            await asyncio.sleep(1)

            # Fill password
            print(f"   Typing password...")
            password_input = await self.page.query_selector('input[type="password"], input[name="password"]')
            await password_input.click()
            await password_input.type(LOGIN_PASSWORD, delay=TYPING_DELAY)
            await asyncio.sleep(1)

            # Click login button
            print("   Clicking login button...")
            login_button = await self.page.query_selector('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
            await login_button.click()

            # Wait for navigation to dashboard
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(WAIT_MEDIUM)

            await self.page.screenshot(path=OUTPUT_DIR / "02_dashboard.png")
            print("✅ Login successful!")

        except Exception as e:
            print(f"❌ Login failed: {e}")
            await self.page.screenshot(path=OUTPUT_DIR / "error_login.png")
            raise

    async def show_dashboard(self):
        """Show the home dashboard"""
        print("\n🏠 Step 3: Exploring Dashboard...")

        # Scroll to show different sections
        await self.page.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(WAIT_SHORT)

        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(WAIT_SHORT)

        await self.page.screenshot(path=OUTPUT_DIR / "03_home_dashboard.png")
        print("✅ Dashboard explored")

    async def navigate_to_security_monitor(self):
        """Navigate to Security Monitor tab"""
        print("\n🛡️ Step 4: Opening Security Monitor...")

        try:
            # Look for Security Monitor button/tab
            security_button = await self.page.query_selector('button:has-text("Security Monitor"), a:has-text("Security Monitor")')

            if security_button:
                await security_button.click()
                await asyncio.sleep(WAIT_MEDIUM)
                await self.page.screenshot(path=OUTPUT_DIR / "04_security_monitor.png")
                print("✅ Security Monitor opened")
            else:
                print("⚠️  Security Monitor tab not found, continuing...")

        except Exception as e:
            print(f"⚠️  Could not navigate to Security Monitor: {e}")

    async def show_system_metrics(self):
        """Display system metrics"""
        print("\n📊 Step 5: Showing System Metrics...")

        await asyncio.sleep(WAIT_MEDIUM)

        # Scroll to metrics section
        await self.page.evaluate("window.scrollTo(0, 200)")
        await asyncio.sleep(WAIT_SHORT)

        await self.page.screenshot(path=OUTPUT_DIR / "05_system_metrics.png")
        print("✅ System metrics displayed")

    async def fill_deployment_form(self):
        """Fill deployment configuration"""
        print("\n📝 Step 6: Configuring Deployment...")

        try:
            # Look for input fields
            await asyncio.sleep(WAIT_SHORT)

            # Try to find target URL input
            url_input = await self.page.query_selector('input[placeholder*="URL"], input[placeholder*="url"], input[type="url"]')
            if url_input:
                print("   Filling Target URL...")
                await url_input.click()
                await url_input.fill(f"https://{DEPLOYMENT_CONFIG['bucket_name']}.s3-website-{DEPLOYMENT_CONFIG['region']}.amazonaws.com")
                await asyncio.sleep(1)

            # Try to find bucket name input
            bucket_input = await self.page.query_selector('input[placeholder*="bucket"], input[placeholder*="Bucket"]')
            if bucket_input:
                print("   Filling Bucket Name...")
                await bucket_input.click()
                await bucket_input.type(DEPLOYMENT_CONFIG['bucket_name'], delay=TYPING_DELAY)
                await asyncio.sleep(1)

            await self.page.screenshot(path=OUTPUT_DIR / "06_deployment_form.png")
            print("✅ Deployment form filled")

        except Exception as e:
            print(f"⚠️  Form filling partial: {e}")

    async def run_security_scan(self):
        """Run security scan"""
        print("\n🔒 Step 7: Running Security Scan...")

        try:
            # Look for security scan button
            scan_button = await self.page.query_selector('button:has-text("Security Scan"), button:has-text("security")')

            if scan_button:
                await scan_button.click()
                print("   Security scan initiated...")
                await asyncio.sleep(WAIT_LONG)

                # Click Tests tab to see progress
                tests_tab = await self.page.query_selector('button:has-text("Tests")')
                if tests_tab:
                    await tests_tab.click()
                    await asyncio.sleep(WAIT_MEDIUM)

                await self.page.screenshot(path=OUTPUT_DIR / "07_security_scan.png")
                print("✅ Security scan completed")
            else:
                print("⚠️  Security scan button not found")

        except Exception as e:
            print(f"⚠️  Security scan failed: {e}")

    async def run_load_test(self):
        """Run load test"""
        print("\n🚀 Step 8: Running Load Test...")

        try:
            # Go back to Overview tab
            overview_tab = await self.page.query_selector('button:has-text("Overview")')
            if overview_tab:
                await overview_tab.click()
                await asyncio.sleep(WAIT_SHORT)

            # Look for load test button
            load_button = await self.page.query_selector('button:has-text("Load Test"), button:has-text("load")')

            if load_button:
                await load_button.click()
                print("   Load test initiated...")
                await asyncio.sleep(WAIT_MEDIUM)

                # Switch to Tests tab
                tests_tab = await self.page.query_selector('button:has-text("Tests")')
                if tests_tab:
                    await tests_tab.click()
                    await asyncio.sleep(WAIT_MEDIUM)

                await self.page.screenshot(path=OUTPUT_DIR / "08_load_test.png")
                print("✅ Load test running")
            else:
                print("⚠️  Load test button not found")

        except Exception as e:
            print(f"⚠️  Load test failed: {e}")

    async def show_alerts(self):
        """Show alerts tab"""
        print("\n⚠️  Step 9: Checking Alerts...")

        try:
            alerts_tab = await self.page.query_selector('button:has-text("Alerts")')
            if alerts_tab:
                await alerts_tab.click()
                await asyncio.sleep(WAIT_MEDIUM)

                await self.page.screenshot(path=OUTPUT_DIR / "09_alerts.png")
                print("✅ Alerts displayed")

        except Exception as e:
            print(f"⚠️  Could not show alerts: {e}")

    async def show_remediation(self):
        """Show remediation tab"""
        print("\n🔧 Step 10: Showing Remediation...")

        try:
            remediation_tab = await self.page.query_selector('button:has-text("Remediation")')
            if remediation_tab:
                await remediation_tab.click()
                await asyncio.sleep(WAIT_MEDIUM)

                await self.page.screenshot(path=OUTPUT_DIR / "10_remediation.png")
                print("✅ Remediation displayed")

        except Exception as e:
            print(f"⚠️  Could not show remediation: {e}")

    async def final_overview(self):
        """Show final overview"""
        print("\n📊 Step 11: Final Overview...")

        # Go back to Overview
        overview_tab = await self.page.query_selector('button:has-text("Overview")')
        if overview_tab:
            await overview_tab.click()
            await asyncio.sleep(WAIT_MEDIUM)

        # Scroll to show all metrics
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(WAIT_SHORT)

        await self.page.screenshot(path=OUTPUT_DIR / "11_final_overview.png")
        print("✅ Final overview captured")

    async def cleanup(self):
        """Close browser and save video"""
        print("\n🎬 Finishing recording...")

        # Wait a bit before closing
        await asyncio.sleep(WAIT_SHORT)

        # Close page and context to save video
        await self.page.close()
        video_path = await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

        print(f"\n✅ Recording complete!")
        print(f"📹 Video saved in: {OUTPUT_DIR}")
        print(f"📸 Screenshots saved in: {OUTPUT_DIR}")
        print(f"\n🎉 Demo recording finished successfully!")

    async def run_demo(self):
        """Main demo execution"""
        try:
            await self.setup()
            await self.navigate_to_login()
            await self.perform_login()
            await self.show_dashboard()
            await self.navigate_to_security_monitor()
            await self.show_system_metrics()
            await self.fill_deployment_form()
            await self.run_security_scan()
            await self.run_load_test()
            await self.show_alerts()
            await self.show_remediation()
            await self.final_overview()

        except Exception as e:
            print(f"\n❌ Error during demo: {e}")
            if self.page:
                await self.page.screenshot(path=OUTPUT_DIR / "error_final.png")

        finally:
            await self.cleanup()


async def main():
    """Entry point"""
    print("=" * 60)
    print("  PROMPTOPS AUTOMATED DEMO RECORDING")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Open PromptOps UI in browser")
    print("  2. Automatically navigate and interact")
    print("  3. Record video of the entire process")
    print("  4. Take screenshots at each step")
    print()
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print()
    print("Starting in 3 seconds...")
    await asyncio.sleep(3)
    print()

    recorder = PromptOpsDemoRecorder()
    await recorder.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
