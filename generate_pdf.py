import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(output_path="data/password_reset_guide.pdf"):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Document Setup
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Color Palette (Corporate Blue Theme)
    primary_color = HexColor("#1A365D")
    secondary_color = HexColor("#2B6CB0")
    text_color = HexColor("#2D3748")
    light_bg = HexColor("#EDF2F7")
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=text_color,
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=6
    )

    story = []
    
    # Header / Title
    story.append(Paragraph("Adsparkx AI Platform Security", title_style))
    story.append(Paragraph("Official Guide: Password Security, Recovery, and Multi-Factor Authentication", subtitle_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Section 1: Standard Password Policy
    story.append(Paragraph("1. Password Complexity Requirements", h1_style))
    story.append(Paragraph("To protect your account and our developer platform, passwords must comply with the following complexity rules:", body_style))
    story.append(Paragraph("• <b>Minimum Length:</b> Must be at least 12 characters long.", bullet_style))
    story.append(Paragraph("• <b>Character Diversity:</b> Must contain at least one uppercase letter, one lowercase letter, one numeric digit, and one special character (e.g., !, @, #, $, %, etc.).", bullet_style))
    story.append(Paragraph("• <b>History Restriction:</b> You cannot reuse any of your last five (5) previously set passwords.", bullet_style))
    story.append(Paragraph("• <b>Common Words Block:</b> Simple words or sequential sequences (e.g., 'password123', 'admin2026') are blocked by our verification service.", bullet_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Section 2: Password Reset Steps
    story.append(Paragraph("2. How to Reset Your Password", h1_style))
    story.append(Paragraph("If you forgot your password or your credentials are no longer working, follow these exact recovery steps:", body_style))
    story.append(Paragraph("1. Navigate to the Adsparkx platform login interface and click the <b>'Forgot Password?'</b> link.", bullet_style))
    story.append(Paragraph("2. Input your registered account email address and click 'Send Recovery Email'.", bullet_style))
    story.append(Paragraph("3. Check your inbox for a verification message with the subject line 'Reset Your Adsparkx Password'.", bullet_style))
    story.append(Paragraph("4. Click the secure link inside the email. <i>Note: For security reasons, this recovery link is valid for exactly 15 minutes</i>. If you do not click it within this window, you must request a new reset link.", bullet_style))
    story.append(Paragraph("5. Enter your new password confirming to the complexity requirements and click 'Update Password'.", bullet_style))
    story.append(Paragraph("6. Log in using your new credentials. You will be prompted to complete Multi-Factor Authentication (MFA) validation if it is configured for your account.", bullet_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Section 3: Locked Accounts
    story.append(Paragraph("3. Locked Accounts & Anti-Brute-Force Policies", h1_style))
    story.append(Paragraph("Our system implements an automatic brute-force mitigation lock to block unauthorized login attempts:", body_style))
    story.append(Paragraph("• <b>Failed Attempts Threshold:</b> An account is automatically locked after <b>five (5) consecutive failed login attempts</b> within a 10-minute window.", bullet_style))
    story.append(Paragraph("• <b>Auto-Unlock Window:</b> Once locked, the account will remain disabled for <b>exactly 30 minutes</b>. You can wait for this window to expire to try logging in again.", bullet_style))
    story.append(Paragraph("• <b>Immediate Recovery:</b> To bypass the 30-minute lock window, check your email for the 'Suspicious Login Attempt & Lockout' notification. Click the 'Immediate Unlock' link in that email, which will prompt you to verify your identity through your registered MFA device.", bullet_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Section 4: Contacting Support
    story.append(Paragraph("4. Escalation Policy & Sensitive Accounts", h1_style))
    story.append(Paragraph("If you are still unable to recover your account or bypass the lockout, contact the customer support team immediately. Because password resets and account modifications are highly sensitive procedures, our support agents will follow these verification rules:", body_style))
    
    # Visual Table for Escalation
    data = [
        [Paragraph("<b>Scenario</b>", body_style), Paragraph("<b>Action Required</b>", body_style)],
        [Paragraph("MFA Device Lost", body_style), Paragraph("Support agent must verify identity via corporate domain check and manual video call.", body_style)],
        [Paragraph("Compromised Account", body_style), Paragraph("Account will be temporarily frozen. A password reset link will be sent to the backup email.", body_style)],
        [Paragraph("Email Access Lost", body_style), Paragraph("Escalate immediately to Tier 2 Security Team for manual review. Require document uploads.", body_style)]
    ]
    
    t = Table(data, colWidths=[2.0 * inch, 4.0 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E0")),
    ]))
    
    story.append(t)
    
    # Build Document
    doc.build(story)
    print(f"Generated PDF successfully at {output_path}")

if __name__ == "__main__":
    generate_pdf()
