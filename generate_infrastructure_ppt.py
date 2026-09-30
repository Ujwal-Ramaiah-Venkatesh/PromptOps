"""
Generate Platform & Infrastructure Engineer Focused PowerPoint
==============================================================

Creates visual PowerPoint with flow diagrams, explanation diagrams,
and graphs for the Platform & Infrastructure Engineer role.

Author: PromptOps Team
Date: August 2, 2026
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

def add_title_slide(prs, title, subtitle=None):
    """Add slide with title and optional subtitle"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = RGBColor(41, 98, 255)

    # Subtitle if provided
    if subtitle:
        subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(0.5))
        tf = subtitle_box.text_frame
        p = tf.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(18)
        p.font.italic = True
        p.font.color.rgb = RGBColor(100, 100, 100)

    return slide

def add_shape_with_text(slide, shape_type, left, top, width, height, text, font_size=14,
                        fill_color=None, text_color=RGBColor(255, 255, 255)):
    """Add a shape with text"""
    shape = slide.shapes.add_shape(
        shape_type,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height)
    )

    # Fill color
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color

    # Text
    tf = shape.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.font.size = Pt(font_size)
    p.font.bold = True
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER

    # Vertical alignment
    tf.vertical_anchor = 1  # Middle

    return shape

def add_arrow(slide, x1, y1, x2, y2):
    """Add an arrow connector"""
    connector = slide.shapes.add_connector(
        1,  # Straight connector
        Inches(x1), Inches(y1),
        Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = RGBColor(100, 100, 100)
    connector.line.width = Pt(2)
    return connector

def create_presentation():
    """Create the main presentation"""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Define colors
    BRAND_BLUE = RGBColor(41, 98, 255)
    SUCCESS_GREEN = RGBColor(16, 185, 129)
    WARNING_ORANGE = RGBColor(249, 115, 22)
    ERROR_RED = RGBColor(239, 68, 68)
    DARK_GRAY = RGBColor(51, 51, 51)
    LIGHT_BLUE = RGBColor(96, 165, 250)
    PURPLE = RGBColor(168, 85, 247)

    # ========================================================================
    # Slide 1: Title
    # ========================================================================

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = "PromptOps for Platform & Infrastructure Engineers"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = BRAND_BLUE
    p.alignment = PP_ALIGN.CENTER

    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(1))
    tf = subtitle_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Automate Everything • Multiply Your Impact • Scale 1 → 1000 Engineers"
    p.font.size = Pt(20)
    p.font.italic = True
    p.alignment = PP_ALIGN.CENTER

    # ========================================================================
    # Slide 2: The Challenge - Infrastructure Engineer's Daily Reality
    # ========================================================================

    slide = add_title_slide(prs, "The Challenge: Your Daily Reality")

    challenges = [
        ("🔥 Firefighting", "Developers blocked by infra issues", ERROR_RED),
        ("⏰ Time Sink", "Same problems, different teams", WARNING_ORANGE),
        ("🔧 Manual Toil", "Scripts everywhere, no platform", WARNING_ORANGE),
        ("📞 Bottleneck", "You're the single point of contact", ERROR_RED),
        ("🌍 Scale Problem", "Supporting 1000+ engineers globally", ERROR_RED)
    ]

    y_pos = 2.2
    for emoji, description, color in challenges:
        # Box for each challenge
        shape = add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            1, y_pos, 8, 0.7,
            f"{emoji} {description}",
            font_size=18,
            fill_color=color,
            text_color=RGBColor(255, 255, 255)
        )
        y_pos += 0.9

    # ========================================================================
    # Slide 3: The Vision - One-to-Many Thinking
    # ========================================================================

    slide = add_title_slide(prs, "The Vision: One-to-Many Thinking",
                           "Solve once → Nobody ever has this problem again")

    # Before box
    add_shape_with_text(
        slide, MSO_SHAPE.RECTANGLE,
        0.5, 2.5, 4, 1.5,
        "BEFORE\n\nYou: 1 problem\n↓\n1 solution\n↓\n1 person helped",
        font_size=16,
        fill_color=ERROR_RED
    )

    # Arrow
    arrow_shape = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW,
        Inches(4.7), Inches(3), Inches(0.6), Inches(0.6)
    )
    arrow_shape.fill.solid()
    arrow_shape.fill.fore_color.rgb = SUCCESS_GREEN

    # After box
    add_shape_with_text(
        slide, MSO_SHAPE.RECTANGLE,
        5.5, 2.5, 4, 1.5,
        "WITH PROMPTOPS\n\nYou: 1 problem\n↓\nAutomated platform\n↓\n1000 people helped",
        font_size=16,
        fill_color=SUCCESS_GREEN
    )

    # Impact text
    impact_box = slide.shapes.add_textbox(Inches(2), Inches(5.5), Inches(6), Inches(0.8))
    tf = impact_box.text_frame
    p = tf.paragraphs[0]
    p.text = "🚀 Your impact: 1 → 1000x"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.alignment = PP_ALIGN.CENTER

    # ========================================================================
    # Slide 4: Complete Flow Diagram - Commit to Production
    # ========================================================================

    slide = add_title_slide(prs, "Complete DevOps Flow: Commit → Production",
                           "12 Automated Stages in 8-12 Minutes")

    # Row 1: Commit → Build
    stages_row1 = [
        ("1. Commit", BRAND_BLUE, 0.5),
        ("2. CI/CD", BRAND_BLUE, 2.2),
        ("3. Build", LIGHT_BLUE, 3.9),
        ("4. Test", LIGHT_BLUE, 5.6),
        ("5. Scan", PURPLE, 7.3)
    ]

    for stage, color, x_pos in stages_row1:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x_pos, 2.2, 1.5, 0.8,
            stage, font_size=12, fill_color=color
        )
        # Add arrow if not last
        if x_pos < 7:
            add_arrow(slide, x_pos + 1.5, 2.6, x_pos + 1.7, 2.6)

    # Row 2: Docker → Deploy
    stages_row2 = [
        ("6. Docker", PURPLE, 0.5),
        ("7. K8s", SUCCESS_GREEN, 2.2),
        ("8. Cloud", SUCCESS_GREEN, 3.9),
        ("9. Monitor", WARNING_ORANGE, 5.6),
        ("10. Alerts", WARNING_ORANGE, 7.3)
    ]

    for stage, color, x_pos in stages_row2:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x_pos, 3.5, 1.5, 0.8,
            stage, font_size=12, fill_color=color
        )
        # Add arrow if not last
        if x_pos < 7:
            add_arrow(slide, x_pos + 1.5, 3.9, x_pos + 1.7, 3.9)

    # Connector between rows
    add_arrow(slide, 9, 2.6, 9, 3.2)

    # Row 3: Deploy → Monitor
    stages_row3 = [
        ("11. Deploy", SUCCESS_GREEN, 3.25),
        ("12. Production", SUCCESS_GREEN, 5.75)
    ]

    for stage, color, x_pos in stages_row3:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x_pos, 4.8, 2, 0.8,
            stage, font_size=14, fill_color=color
        )

    add_arrow(slide, 5.25, 5.2, 5.75, 5.2)

    # Connector from row 2 to row 3
    add_arrow(slide, 4.25, 4.3, 4.25, 4.8)

    # Time indicator
    time_box = slide.shapes.add_textbox(Inches(2.5), Inches(6), Inches(5), Inches(0.6))
    tf = time_box.text_frame
    p = tf.paragraphs[0]
    p.text = "⏱ Total: 8-12 minutes (was 5h 40min)"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.alignment = PP_ALIGN.CENTER

    # ========================================================================
    # Slide 5: Developer Commit - Stage 1 Detailed
    # ========================================================================

    slide = add_title_slide(prs, "Stage 1: Developer Commit",
                           "The journey begins with git push")

    # Developer
    add_shape_with_text(
        slide, MSO_SHAPE.OVAL,
        1, 2.5, 2, 1,
        "👨‍💻\nDeveloper",
        font_size=16,
        fill_color=BRAND_BLUE
    )

    # Arrow
    add_arrow(slide, 3, 3, 3.5, 3)

    # Git push
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        3.5, 2.5, 2, 1,
        "git push\norigin main",
        font_size=14,
        fill_color=LIGHT_BLUE
    )

    # Arrow
    add_arrow(slide, 5.5, 3, 6, 3)

    # Webhook trigger
    add_shape_with_text(
        slide, MSO_SHAPE.LIGHTNING_BOLT,
        6, 2.5, 2, 1,
        "⚡\nWebhook\nTrigger",
        font_size=14,
        fill_color=WARNING_ORANGE
    )

    # What happens
    info_box = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(2))
    tf = info_box.text_frame

    items = [
        "✓ Commit metadata extracted (author, files, message)",
        "✓ Affected services identified automatically",
        "✓ Environment determined (main → prod, develop → staging)",
        "✓ Pipeline triggered with zero manual intervention"
    ]

    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(16)
        p.space_before = Pt(6)

    # ========================================================================
    # Slide 6: CI/CD Pipeline - Stages 2-4
    # ========================================================================

    slide = add_title_slide(prs, "Stages 2-4: CI/CD → Build → Test",
                           "Automated quality gates")

    # Stage 2: CI/CD
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        1, 2.3, 2.5, 0.8,
        "2. CI/CD Trigger\n<30 sec",
        font_size=13,
        fill_color=BRAND_BLUE
    )

    details_box = slide.shapes.add_textbox(Inches(1), Inches(3.2), Inches(2.5), Inches(0.8))
    tf = details_box.text_frame
    tf.text = "• GitHub Actions\n• GitLab CI\n• Jenkins"
    p = tf.paragraphs[0]
    p.font.size = Pt(11)

    add_arrow(slide, 3.5, 2.7, 4, 2.7)

    # Stage 3: Build
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        4, 2.3, 2.5, 0.8,
        "3. Build\n2-5 min",
        font_size=13,
        fill_color=LIGHT_BLUE
    )

    details_box = slide.shapes.add_textbox(Inches(4), Inches(3.2), Inches(2.5), Inches(0.8))
    tf = details_box.text_frame
    tf.text = "• Dependencies cached\n• Incremental builds\n• Parallel compilation"
    p = tf.paragraphs[0]
    p.font.size = Pt(11)

    add_arrow(slide, 6.5, 2.7, 7, 2.7)

    # Stage 4: Test
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        7, 2.3, 2.5, 0.8,
        "4. Test\n3-8 min",
        font_size=13,
        fill_color=PURPLE
    )

    details_box = slide.shapes.add_textbox(Inches(7), Inches(3.2), Inches(2.5), Inches(0.8))
    tf = details_box.text_frame
    tf.text = "• Unit tests\n• Integration tests\n• E2E tests"
    p = tf.paragraphs[0]
    p.font.size = Pt(11)

    # Quality gates box
    gate_box = slide.shapes.add_textbox(Inches(1.5), Inches(4.5), Inches(7), Inches(1.5))
    tf = gate_box.text_frame

    p = tf.add_paragraph()
    p.text = "🛡️ Quality Gates (Automatic)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN

    gates = [
        "✓ Code coverage >80%",
        "✓ All tests pass",
        "✓ No critical bugs",
        "✓ Performance benchmarks met"
    ]

    for gate in gates:
        p = tf.add_paragraph()
        p.text = gate
        p.font.size = Pt(14)
        p.space_before = Pt(4)

    # ========================================================================
    # Slide 7: Security & Containerization - Stages 5-6
    # ========================================================================

    slide = add_title_slide(prs, "Stages 5-6: Security → Docker",
                           "Multi-layer security + Optimized containers")

    # Left side: Security scanning
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        0.5, 2.2, 4, 0.8,
        "5. Security Scanning (1-2 min)",
        font_size=14,
        fill_color=ERROR_RED
    )

    scan_types = [
        "🔍 SAST - Code vulnerabilities",
        "📦 Dependencies - CVE detection",
        "🐳 Container - Image scanning",
        "☁️ IaC - Terraform security"
    ]

    y_pos = 3.2
    for scan in scan_types:
        box = slide.shapes.add_textbox(Inches(0.8), Inches(y_pos), Inches(3.5), Inches(0.4))
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = scan
        p.font.size = Pt(12)
        y_pos += 0.5

    # Right side: Docker
    add_shape_with_text(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE,
        5.5, 2.2, 4, 0.8,
        "6. Docker Build (2-4 min)",
        font_size=14,
        fill_color=LIGHT_BLUE
    )

    docker_features = [
        "📦 Multi-stage builds",
        "⚡ Layer caching",
        "🎯 200MB → 50MB (75% smaller)",
        "🔒 Security hardening"
    ]

    y_pos = 3.2
    for feature in docker_features:
        box = slide.shapes.add_textbox(Inches(5.8), Inches(y_pos), Inches(3.5), Inches(0.4))
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = feature
        p.font.size = Pt(12)
        y_pos += 0.5

    # Bottom: Result
    result_box = slide.shapes.add_textbox(Inches(2), Inches(5.5), Inches(6), Inches(0.8))
    tf = result_box.text_frame
    p = tf.paragraphs[0]
    p.text = "✅ Secure, Optimized Container Ready for Deployment"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.alignment = PP_ALIGN.CENTER

    # ========================================================================
    # Slide 8: Kubernetes & Cloud - Stages 7-8
    # ========================================================================

    slide = add_title_slide(prs, "Stages 7-8: Kubernetes → Cloud",
                           "Container orchestration + Infrastructure provisioning")

    # Kubernetes section
    k8s_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(4.5), Inches(0.6))
    tf = k8s_box.text_frame
    p = tf.paragraphs[0]
    p.text = "7. Kubernetes Preparation (1-2 min)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = BRAND_BLUE

    k8s_resources = [
        "• Deployment: Pod specs, replicas",
        "• Service: Load balancing",
        "• Ingress: External routing",
        "• HPA: Auto-scaling rules",
        "• ConfigMap: Configuration",
        "• Secrets: Encrypted data"
    ]

    y_pos = 3
    for resource in k8s_resources:
        box = slide.shapes.add_textbox(Inches(0.8), Inches(y_pos), Inches(4), Inches(0.3))
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = resource
        p.font.size = Pt(12)
        y_pos += 0.35

    # Cloud section
    cloud_box = slide.shapes.add_textbox(Inches(5.5), Inches(2.2), Inches(4), Inches(0.6))
    tf = cloud_box.text_frame
    p = tf.paragraphs[0]
    p.text = "8. Cloud Provisioning (3-5 min)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN

    cloud_resources = [
        "☁️ AWS / GCP / Azure",
        "🌐 VPC & Networking",
        "⚖️ Load Balancers",
        "💾 Databases (RDS, etc.)",
        "🗄️ Storage (S3, etc.)",
        "🔧 Terraform automated"
    ]

    y_pos = 3
    for resource in cloud_resources:
        box = slide.shapes.add_textbox(Inches(5.8), Inches(y_pos), Inches(3.5), Inches(0.3))
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = resource
        p.font.size = Pt(12)
        y_pos += 0.35

    # ========================================================================
    # Slide 9: Monitoring Architecture - 5 Layers
    # ========================================================================

    slide = add_title_slide(prs, "5-Layer Monitoring Architecture",
                           "Complete observability from infrastructure to business")

    layers = [
        ("Layer 5: Business", "Deployments, MTTD, MTTR, Revenue", PURPLE, 2),
        ("Layer 4: Cost", "ML anomaly detection, forecasting", WARNING_ORANGE, 2.8),
        ("Layer 3: Security", "CVE, threats, compliance", ERROR_RED, 3.6),
        ("Layer 2: APM", "P95 latency, errors, throughput", LIGHT_BLUE, 4.4),
        ("Layer 1: Infrastructure", "CPU, Memory, Network, Disk", SUCCESS_GREEN, 5.2)
    ]

    for layer, description, color, y_pos in layers:
        # Layer box
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            1, y_pos, 3, 0.6,
            layer,
            font_size=14,
            fill_color=color
        )

        # Description
        desc_box = slide.shapes.add_textbox(Inches(4.2), Inches(y_pos), Inches(5.3), Inches(0.6))
        tf = desc_box.text_frame
        p = tf.paragraphs[0]
        p.text = description
        p.font.size = Pt(13)
        tf.vertical_anchor = 1

    # ========================================================================
    # Slide 10: Predictive Intelligence
    # ========================================================================

    slide = add_title_slide(prs, "Predictive Intelligence: Prevent, Don't React",
                           "Issues detected 7+ days before they occur")

    # Timeline
    timeline_items = [
        ("Day 0", "ML detects\ntrend", SUCCESS_GREEN, 1),
        ("Day 3", "Prediction:\nDisk 90%", WARNING_ORANGE, 3),
        ("Day 7", "Alert:\nAction needed", ERROR_RED, 5),
        ("Day 14", "Would have\nfailed", RGBColor(150, 150, 150), 7)
    ]

    for day, description, color, x_pos in timeline_items:
        # Day marker
        add_shape_with_text(
            slide, MSO_SHAPE.OVAL,
            x_pos, 2.5, 1.5, 0.8,
            day,
            font_size=14,
            fill_color=color
        )

        # Description below
        desc_box = slide.shapes.add_textbox(Inches(x_pos - 0.2), Inches(3.5), Inches(1.9), Inches(0.8))
        tf = desc_box.text_frame
        p = tf.paragraphs[0]
        p.text = description
        p.font.size = Pt(11)
        p.alignment = PP_ALIGN.CENTER
        tf.vertical_anchor = 1

        # Arrow to next (except last)
        if x_pos < 7:
            add_arrow(slide, x_pos + 1.5, 2.9, x_pos + 1.8, 2.9)

    # Predictions list
    predictions_box = slide.shapes.add_textbox(Inches(1.5), Inches(4.8), Inches(7), Inches(1.5))
    tf = predictions_box.text_frame

    p = tf.add_paragraph()
    p.text = "🔮 What We Predict:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = BRAND_BLUE

    predictions = [
        "Disk/Memory exhaustion • Performance degradation • Disk failures",
        "Cost spikes • Security incidents • Scaling needs"
    ]

    for pred in predictions:
        p = tf.add_paragraph()
        p.text = pred
        p.font.size = Pt(13)

    # ========================================================================
    # Slide 11: Automated Remediation
    # ========================================================================

    slide = add_title_slide(prs, "Automated Remediation: Self-Healing Infrastructure",
                           "From detection to fix in seconds")

    # Example workflow
    workflow = [
        ("Issue\nDetected", ERROR_RED, 1),
        ("Validate\nSafe to Fix", WARNING_ORANGE, 3),
        ("Auto\nRemediate", SUCCESS_GREEN, 5),
        ("Verify\nResolved", SUCCESS_GREEN, 7)
    ]

    for step, color, x_pos in workflow:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x_pos, 2.5, 1.5, 1,
            step,
            font_size=13,
            fill_color=color
        )

        if x_pos < 7:
            add_arrow(slide, x_pos + 1.5, 3, x_pos + 1.8, 3)

    # Auto-fix examples
    examples_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(9), Inches(2.2))
    tf = examples_box.text_frame

    p = tf.add_paragraph()
    p.text = "🤖 Auto-Fix Examples:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = BRAND_BLUE

    examples = [
        "High CPU → Auto-scale up • Disk full → Cleanup + expand",
        "Service down → Restart + failover • Memory leak → Rolling restart",
        "High errors → Rollback deployment • Security drift → Revert to baseline",
        "Cost spike → Stop idle resources"
    ]

    for example in examples:
        p = tf.add_paragraph()
        p.text = f"• {example}"
        p.font.size = Pt(12)
        p.space_before = Pt(4)

    # ========================================================================
    # Slide 12: Impact Graph - Before vs After
    # ========================================================================

    slide = add_title_slide(prs, "The Transformation: Before vs. After",
                           "From hours to minutes, from manual to automated")

    # Create bar chart effect using shapes
    metrics = [
        ("Time", "340 min", "10 min", 2),
        ("Steps", "20", "1", 3.5),
        ("Errors", "25%", "<1%", 5)
    ]

    for metric, before, after, y_pos in metrics:
        # Metric label
        label_box = slide.shapes.add_textbox(Inches(0.5), Inches(y_pos), Inches(1.5), Inches(0.4))
        tf = label_box.text_frame
        p = tf.paragraphs[0]
        p.text = metric
        p.font.size = Pt(14)
        p.font.bold = True
        tf.vertical_anchor = 1

        # Before bar (long, red)
        add_shape_with_text(
            slide, MSO_SHAPE.RECTANGLE,
            2.2, y_pos, 3, 0.4,
            f"Before: {before}",
            font_size=12,
            fill_color=ERROR_RED
        )

        # After bar (short, green)
        add_shape_with_text(
            slide, MSO_SHAPE.RECTANGLE,
            5.5, y_pos, 1, 0.4,
            f"After: {after}",
            font_size=12,
            fill_color=SUCCESS_GREEN
        )

        # Improvement
        improve_box = slide.shapes.add_textbox(Inches(6.8), Inches(y_pos), Inches(2.5), Inches(0.4))
        tf = improve_box.text_frame
        p = tf.paragraphs[0]
        if metric == "Time":
            p.text = "97% faster"
        elif metric == "Steps":
            p.text = "95% reduction"
        else:
            p.text = "96% reduction"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = SUCCESS_GREEN
        tf.vertical_anchor = 1

    # ========================================================================
    # Slide 13: Your Impact Multiplied
    # ========================================================================

    slide = add_title_slide(prs, "Your Impact: From 1 to 1000 Engineers",
                           "Build once, serve thousands")

    # Center visualization
    # You in the center
    add_shape_with_text(
        slide, MSO_SHAPE.OVAL,
        4, 3, 2, 1.2,
        "YOU\nPlatform\nEngineer",
        font_size=14,
        fill_color=BRAND_BLUE
    )

    # Arrows radiating out
    positions = [
        (1.5, 2, "200 Devs"),
        (7.5, 2, "200 Devs"),
        (1.5, 5, "200 Devs"),
        (7.5, 5, "200 Devs"),
        (4.5, 1.2, "200 Devs")
    ]

    for x, y, label in positions:
        # Small dev box
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x, y, 1.2, 0.5,
            label,
            font_size=10,
            fill_color=SUCCESS_GREEN
        )

    # Bottom stats
    stats_box = slide.shapes.add_textbox(Inches(1.5), Inches(6.2), Inches(7), Inches(0.6))
    tf = stats_box.text_frame
    p = tf.paragraphs[0]
    p.text = "1 Platform → 1000 Engineers → Zero Manual Intervention"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.alignment = PP_ALIGN.CENTER

    # ========================================================================
    # Slide 14: Technology Stack Match
    # ========================================================================

    slide = add_title_slide(prs, "Perfect Match: Your Skills + PromptOps",
                           "Everything you know, automated and scaled")

    skills = [
        ("🐧 Linux", "Core platform OS", BRAND_BLUE),
        ("📦 Containers", "Docker, K8s, Helm", LIGHT_BLUE),
        ("🔄 CI/CD", "GitHub Actions, GitLab, Jenkins", PURPLE),
        ("☁️ Cloud", "AWS, GCP, Azure", SUCCESS_GREEN),
        ("🔧 IaC", "Terraform, Ansible", WARNING_ORANGE),
        ("🐍 Python", "Automation scripts built-in", ERROR_RED)
    ]

    # Create 2 columns
    col1_skills = skills[:3]
    col2_skills = skills[3:]

    y_pos = 2.5
    for skill, desc, color in col1_skills:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            0.8, y_pos, 4, 0.7,
            f"{skill} {desc}",
            font_size=14,
            fill_color=color
        )
        y_pos += 1

    y_pos = 2.5
    for skill, desc, color in col2_skills:
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            5.2, y_pos, 4, 0.7,
            f"{skill} {desc}",
            font_size=14,
            fill_color=color
        )
        y_pos += 1

    # ========================================================================
    # Slide 15: ROI for Platform Engineers
    # ========================================================================

    slide = add_title_slide(prs, "ROI: What This Means for Platform Engineers")

    benefits = [
        ("⏰ Time Back", "15-20 hrs/week → strategic work", SUCCESS_GREEN),
        ("🚀 Impact", "1 → 1000x engineer productivity", BRAND_BLUE),
        ("🎯 Focus", "Build platforms, not fight fires", PURPLE),
        ("📈 Career", "From firefighter to force multiplier", WARNING_ORANGE),
        ("😊 Life", "On-call alerts: -85%", SUCCESS_GREEN)
    ]

    y_pos = 2.5
    for benefit, description, color in benefits:
        # Benefit box
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            1.5, y_pos, 7, 0.7,
            f"{benefit}: {description}",
            font_size=16,
            fill_color=color
        )
        y_pos += 0.9

    # ========================================================================
    # Slide 16: Getting Started - For Infrastructure Engineers
    # ========================================================================

    slide = add_title_slide(prs, "Getting Started: 3 Steps for Platform Engineers")

    steps = [
        ("1. Deploy\nPromptOps", "30 minutes\nCloudFormation\ntemplate", BRAND_BLUE, 1.5),
        ("2. Connect\nInfrastructure", "15 minutes\nPoint to Terraform\nstate", SUCCESS_GREEN, 4),
        ("3. Multiply\nImpact", "24 hours\nPlatform live for\n1000 engineers", WARNING_ORANGE, 6.5)
    ]

    for step, details, color, x_pos in steps:
        # Step box
        add_shape_with_text(
            slide, MSO_SHAPE.ROUNDED_RECTANGLE,
            x_pos, 2.8, 2, 1.5,
            step,
            font_size=16,
            fill_color=color
        )

        # Details below
        detail_box = slide.shapes.add_textbox(Inches(x_pos), Inches(4.5), Inches(2), Inches(1))
        tf = detail_box.text_frame
        p = tf.paragraphs[0]
        p.text = details
        p.font.size = Pt(12)
        p.alignment = PP_ALIGN.CENTER

        # Arrow (except last)
        if x_pos < 6:
            add_arrow(slide, x_pos + 2, 3.5, x_pos + 2.3, 3.5)

    # ========================================================================
    # Slide 17: Final - Call to Action
    # ========================================================================

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Main message
    msg_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(2))
    tf = msg_box.text_frame

    p = tf.paragraphs[0]
    p.text = "From Firefighter\nto Force Multiplier"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = BRAND_BLUE
    p.alignment = PP_ALIGN.CENTER

    # Stats
    stats_box = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(0.8))
    tf = stats_box.text_frame
    p = tf.paragraphs[0]
    p.text = "1 → 1000x Impact • 97% Time Savings • Self-Service Everything"
    p.font.size = Pt(20)
    p.alignment = PP_ALIGN.CENTER

    # CTA
    cta_box = slide.shapes.add_textbox(Inches(2.5), Inches(5.8), Inches(5), Inches(0.8))
    tf = cta_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Build Once → Serve 1000 Engineers"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.alignment = PP_ALIGN.CENTER

    # Contact
    contact_box = slide.shapes.add_textbox(Inches(1), Inches(6.8), Inches(8), Inches(0.4))
    tf = contact_box.text_frame
    p = tf.paragraphs[0]
    p.text = "team@promptops.io | promptops.io"
    p.font.size = Pt(18)
    p.alignment = PP_ALIGN.CENTER

    return prs

# ============================================================================
# Main
# ============================================================================

def main():
    print("="*70)
    print("Generating Platform & Infrastructure Engineer PowerPoint")
    print("="*70)
    print()
    print("Creating presentation with:")
    print("  • Flow diagrams (12-stage DevOps pipeline)")
    print("  • Explanation diagrams (monitoring, automation)")
    print("  • Visual representations (before/after, impact)")
    print("  • Easy to understand for anyone")
    print()

    prs = create_presentation()
    filename = 'PromptOps_Platform_Infrastructure_Engineer.pptx'
    prs.save(filename)

    print("="*70)
    print("GENERATION COMPLETE!")
    print("="*70)
    print()
    print(f"File: {filename}")
    print(f"Slides: 17 professional slides with visuals")
    print()
    print("SLIDE BREAKDOWN:")
    print("  1. Title Slide")
    print("  2. The Challenge (Infrastructure Engineer Reality)")
    print("  3. The Vision (One-to-Many Thinking)")
    print("  4. Complete Flow Diagram (12 stages)")
    print("  5-8. Detailed Stage Breakdowns with Visuals")
    print("  9. 5-Layer Monitoring Architecture")
    print("  10. Predictive Intelligence (7-day ahead)")
    print("  11. Automated Remediation (Self-Healing)")
    print("  12. Impact Graph (Before vs After)")
    print("  13. Your Impact Multiplied (1 → 1000)")
    print("  14. Technology Stack Match")
    print("  15. ROI for Platform Engineers")
    print("  16. Getting Started (3 Steps)")
    print("  17. Call to Action")
    print()
    print("VISUAL ELEMENTS:")
    print("  ✓ Flow diagrams with arrows")
    print("  ✓ Stage-by-stage breakdowns")
    print("  ✓ Color-coded components")
    print("  ✓ Timeline visualizations")
    print("  ✓ Impact comparisons")
    print("  ✓ Architecture diagrams")
    print()
    print("="*70)
    print("Ready for Platform & Infrastructure Engineer presentations!")
    print("="*70)

if __name__ == '__main__':
    main()
