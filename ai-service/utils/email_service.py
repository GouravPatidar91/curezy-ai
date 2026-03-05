import os
import resend
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize Resend with API Key
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "Curezy AI Lab <noreply@curezyai.in>")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@curezy.in")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

class EmailService:
    @staticmethod
    def send_email(to: str, subject: str, html_content: str):
        if not RESEND_API_KEY:
            print(f"[EmailService] Skipping send (No API Key). To: {to}, Subject: {subject}")
            return False
            
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": to,
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"[EmailService] Email sent successfully to {to}. Response: {response}")
            return True
        except Exception as e:
            print(f"[EmailService] Error sending email to {to}: {str(e)}")
            return False

    @staticmethod
    def notify_waitlist_join(user_email: str, user_name: str):
        """Sends a welcome email to the user and a notification to the admin."""
        
        # 1. Welcome email to User
        user_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #111;">
            <h2 style="color: #4D4DFF;">Welcome to the Future of Medicine</h2>
            <p>Hi {user_name},</p>
            <p>Thank you for requesting early access to <b>Curezy AI</b>. We've added you to our exclusive waitlist.</p>
            <p>Our medical board is currently reviewing applications to ensure a safe and high-quality experience for all beta users. You'll receive another email the moment your account is approved.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">Curezy AI Lab — Clinical Intelligence Engine</p>
        </div>
        """
        EmailService.send_email(user_email, "You're on the Waitlist! — Curezy AI", user_html)
        
        # 2. Notification to Admin
        admin_html = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h3>New Waitlist Signup</h3>
            <p><b>Name:</b> {user_name}</p>
            <p><b>Email:</b> {user_email}</p>
            <p><b>Time:</b> {os.popen('date /t').read().strip()}</p>
        </div>
        """
        EmailService.send_email(ADMIN_EMAIL, f"New Waitlist: {user_name}", admin_html)

    @staticmethod
    def send_analysis_report(user_email: str, diagnosis: str, confidence: str):
        """Sends a summary of the AI Analysis to the user."""
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 40px; border-radius: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <span style="font-size: 40px;">🩺</span>
                <h2 style="margin-top: 10px; color: #4D4DFF;">Clinical Analysis Report</h2>
            </div>
            
            <p>Your Curezy AI consultation report is ready.</p>
            
            <div style="background: #f9f9f9; padding: 20px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0; font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase;">Primary Indication</p>
                <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold;">{diagnosis}</p>
            </div>
            
            <div style="background: #f9f9f9; padding: 20px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0; font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase;">Council Confidence</p>
                <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold;">{confidence}%</p>
            </div>
            
            <p style="font-size: 14px; color: #444; line-height: 1.6;">
                The full report with evidence, reasoning, and next clinical steps is available in your Curezy Chat dashboard.
            </p>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="https://curezy-ai.com/chat" style="background: #4D4DFF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 10px; font-weight: bold;">View Full Report</a>
            </div>
            
            <p style="font-size: 10px; color: #999; margin-top: 40px; text-align: center;">
                DISCLAIMER: This is an AI-generated report for informational purposes only. It is not a clinical diagnosis. Always consult a doctor.
            </p>
        </div>
        """
        EmailService.send_email(user_email, "Your Clinical Analysis Report is Ready", html)

    @staticmethod
    def notify_approval(user_email: str):
        """Notifies the user that their beta access has been approved."""
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; text-align: center; padding: 40px;">
            <div style="font-size: 50px; margin-bottom: 20px;">✨</div>
            <h2 style="color: #4D4DFF;">Access Granted</h2>
            <p style="font-size: 16px; color: #333;">Your request for early access to Curezy AI has been approved by our medical board.</p>
            <p style="color: #666; margin-bottom: 30px;">You can now log in and start using the Curezy clinical engine.</p>
            <a href="https://curezy-ai.com/chat" style="background: #000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; font-weight: bold;">Enter Clinical Engine</a>
        </div>
        """
        EmailService.send_email(user_email, "Welcome to Curezy AI — Your Access is Ready", html)
