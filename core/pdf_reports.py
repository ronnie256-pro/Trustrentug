"""
PDF Reports Generator for TRUST Protocol Admin
Supports generating downloadable, beautifully-styled PDF reports with:
1. Centered Official PDF Logo at the top
2. Category of the report (e.g. Residential Property Report)
3. Name/Title of the property/subject with:
   REF: #<id>
   Issued: <Date, Time EAT>
   underneath it
4. Followed by remaining comprehensive details, specifications, compliance, and metrics
"""
import os
from io import BytesIO
from PIL import Image as PILImage
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_report_styles():
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#022416')
    emerald_color = colors.HexColor('#047857')
    gold_color = colors.HexColor('#b45309')
    slate_dark = colors.HexColor('#0f172a')
    slate_muted = colors.HexColor('#475569')

    custom_styles = {
        'brand_title_center': ParagraphStyle(
            'BrandTitleCenter',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=primary_color,
            alignment=1,
            spaceAfter=2,
            leading=26
        ),
        'category_heading_center': ParagraphStyle(
            'CategoryHeadingCenter',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=emerald_color,
            alignment=1,
            spaceBefore=6,
            spaceAfter=3,
            leading=20
        ),
        'property_title_center': ParagraphStyle(
            'PropertyTitleCenter',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=slate_dark,
            alignment=1,
            spaceBefore=4,
            spaceAfter=3,
            leading=18
        ),
        'meta_underneath_center': ParagraphStyle(
            'MetaUnderneathCenter',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=slate_muted,
            alignment=1,
            spaceBefore=2,
            spaceAfter=12,
            leading=14
        ),
        'section_title': ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=primary_color,
            spaceBefore=10,
            spaceAfter=6,
            leading=14
        ),
        'body': ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=slate_dark,
            leading=13
        ),
        'label': ParagraphStyle(
            'ReportLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            textColor=colors.HexColor('#0f172a'),
            leading=11
        ),
        'value': ParagraphStyle(
            'ReportValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=slate_dark,
            leading=12
        ),
        'value_bold': ParagraphStyle(
            'ReportValueBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=slate_dark,
            leading=12
        ),
        'badge_green': ParagraphStyle(
            'BadgeGreen',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#047857'),
            leading=10
        ),
        'badge_gold': ParagraphStyle(
            'BadgeGold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#b45309'),
            leading=10
        ),
        'badge_blue': ParagraphStyle(
            'BadgeBlue',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#1d4ed8'),
            leading=10
        ),
        'th': ParagraphStyle(
            'THStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.white,
            alignment=1,
            leading=10
        ),
        'td': ParagraphStyle(
            'TDStyle',
            fontName='Helvetica',
            fontSize=8,
            textColor=slate_dark,
            alignment=0,
            leading=11
        ),
        'td_bold': ParagraphStyle(
            'TDBoldStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=slate_dark,
            alignment=0,
            leading=11
        ),
        'footer': ParagraphStyle(
            'ReportFooter',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            textColor=slate_muted,
            alignment=1,
            leading=10
        ),
        'footer_address': ParagraphStyle(
            'ReportFooterAddress',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#334155'),
            alignment=1,
            leading=12
        ),
    }
    return custom_styles


def add_centered_report_header(elements, styles, category_title, subject_name, reference_id, site_settings=None):
    """
    Renders the exact requested hierarchy:
    1. PDF Logo at the top center (larger size, aspect ratio preserved)
    2. Category of the report (e.g. Residential Property Report)
    3. Name of the property with:
       REF: #<id>
       Issued: <Date, Time EAT>
       underneath it
    """
    # 1. Centered Logo
    logo_file = None
    if site_settings:
        if site_settings.pdf_logo and hasattr(site_settings.pdf_logo, 'path') and os.path.exists(site_settings.pdf_logo.path):
            logo_file = site_settings.pdf_logo.path
        elif site_settings.site_logo and hasattr(site_settings.site_logo, 'path') and os.path.exists(site_settings.site_logo.path):
            logo_file = site_settings.site_logo.path

    if logo_file:
        try:
            # Measure original image dimensions to preserve aspect ratio and make logo bigger
            with PILImage.open(logo_file) as p_img:
                orig_w, orig_h = p_img.size

            target_w = 230
            target_h = int(target_w * (orig_h / orig_w))
            # Bound height to max 72 to prevent pushing content off first page
            if target_h > 72:
                target_h = 72
                target_w = int(target_h * (orig_w / orig_h))

            img = RLImage(logo_file, width=target_w, height=target_h)
            img.hAlign = 'CENTER'
            t_logo = Table([[img]], colWidths=[535])
            t_logo.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            elements.append(t_logo)
        except Exception:
            site_name = (site_settings.site_name if site_settings and site_settings.site_name else "TRUST PROTOCOL").upper()
            elements.append(Paragraph(f"<b>{site_name}</b>", styles['brand_title_center']))
    else:
        site_name = (site_settings.site_name if site_settings and site_settings.site_name else "TRUST PROTOCOL").upper()
        elements.append(Paragraph(f"<b>{site_name}</b>", styles['brand_title_center']))

    elements.append(Spacer(1, 2))

    # 2. Category of the report
    elements.append(Paragraph(category_title, styles['category_heading_center']))

    # 3. Name of the property
    elements.append(Paragraph(subject_name, styles['property_title_center']))

    # Underneath: REF and Issued date/time
    now_str = timezone.localtime(timezone.now()).strftime('%d %B %Y, %H:%M EAT')
    meta_html = f"REF: #{reference_id}<br/>Issued: {now_str}"
    elements.append(Paragraph(meta_html, styles['meta_underneath_center']))

    # Divider line
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#047857'), spaceBefore=2, spaceAfter=10))


def add_footer(elements, styles):
    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=6))
    
    # Bottom center physical address & web contact
    address_html = (
        "Kigowa 1, Bukoto II, Nakawa Division, Kampala<br/>"
        "P. O. Box 213047, Kampala GPO<br/>"
        "<b>trustrentug.com</b>"
    )
    elements.append(Paragraph(address_html, styles['footer_address']))
    elements.append(Spacer(1, 4))

    footer_text = "This document is an official digital record generated by TRUST Protocol Systems. Verified via physical field inspections and digital escrow verification."
    elements.append(Paragraph(footer_text, styles['footer']))


# ==========================================
# 1. HOUSE (RESIDENTIAL PROPERTY) REPORT
# ==========================================
def generate_house_pdf(prop, site_settings=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = get_report_styles()
    elements = []

    ref_id = prop.property_id or f"{prop.id:06d}"
    add_centered_report_header(
        elements=elements,
        styles=styles,
        category_title="Residential Property Report",
        subject_name=prop.title,
        reference_id=ref_id,
        site_settings=site_settings
    )

    # 4. Remaining Property Details
    owner_name = prop.owner.get_full_name() or prop.owner.username if prop.owner else "Independent Platform Listing"
    owner_phone = getattr(prop.owner, 'phone', 'N/A') if prop.owner else 'N/A'
    owner_email = prop.owner.email if prop.owner and prop.owner.email else 'N/A'
    
    price_disp = f"UGX {prop.price:,.0f}" if prop.price else "Negotiable / Contact"
    monthly_disp = f"UGX {prop.price_per_month:,.0f}/month" if prop.price_per_month else "N/A"
    loc_disp = prop.location or f"{prop.district.name if prop.district else ''}, {prop.division.name if prop.division else ''}"

    overview_data = [
        [Paragraph("Property ID", styles['label']), Paragraph(ref_id, styles['value_bold']), Paragraph("Listing Status", styles['label']), Paragraph(prop.get_status_display().upper(), styles['badge_green'])],
        [Paragraph("Property Title", styles['label']), Paragraph(prop.title, styles['value']), Paragraph("Category", styles['label']), Paragraph(prop.get_category_display() if hasattr(prop, 'get_category_display') and prop.category else (prop.category or 'Residential'), styles['value'])],
        [Paragraph("Listing Type", styles['label']), Paragraph(prop.get_listing_type_display().upper(), styles['value']), Paragraph("Bedrooms", styles['label']), Paragraph(str(prop.bedrooms or 'N/A'), styles['value'])],
        [Paragraph("Monthly Rate", styles['label']), Paragraph(monthly_disp, styles['value_bold']), Paragraph("Total Price", styles['label']), Paragraph(price_disp, styles['value_bold'])],
        [Paragraph("Location", styles['label']), Paragraph(loc_disp, styles['value']), Paragraph("Coordinates", styles['label']), Paragraph(f"{prop.latitude or 'N/A'}, {prop.longitude or 'N/A'}", styles['value'])],
        [Paragraph("Registered Landlord", styles['label']), Paragraph(owner_name, styles['value']), Paragraph("Contact Info", styles['label']), Paragraph(f"{owner_phone} | {owner_email}", styles['value'])],
        [Paragraph("Rent Collection", styles['label']), Paragraph("TRUST Escrow System" if prop.collect_rent_by_trust else "Direct Landlord", styles['value']), Paragraph("Multi-unit", styles['label']), Paragraph("Yes" if prop.is_multi_unit else "Single Unit", styles['value'])],
    ]
    t_overview = Table(overview_data, colWidths=[95, 172, 95, 173])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_overview)
    elements.append(Spacer(1, 10))

    # Description Section
    if prop.description:
        elements.append(Paragraph("Property Description & Specifications", styles['section_title']))
        desc_data = [[Paragraph(prop.description, styles['body'])]]
        t_desc = Table(desc_data, colWidths=[535])
        t_desc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_desc)
        elements.append(Spacer(1, 10))

    # Amenities Section
    elements.append(Paragraph("Verified Amenities & Features", styles['section_title']))
    amenities = list(prop.amenities.all())
    if amenities:
        amenity_names = [f"• {a.name}" for a in amenities]
        rows = [amenity_names[i:i+3] for i in range(0, len(amenity_names), 3)]
        for r in rows:
            while len(r) < 3:
                r.append("")
        table_rows = [[Paragraph(cell, styles['body']) for cell in r] for r in rows]
        t_amen = Table(table_rows, colWidths=[178, 178, 179])
        t_amen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_amen)
    else:
        elements.append(Paragraph("Standard residential utilities verified on site inspection.", styles['body']))
    elements.append(Spacer(1, 10))

    # Legal & Compliance Section
    elements.append(Paragraph("Compliance & Verification Checklist", styles['section_title']))
    docs_data = [
        [Paragraph("Building Plans Uploaded", styles['label']), Paragraph("Verified on File" if prop.building_plans else "Pending Submission", styles['body']), Paragraph("Occupancy Permit", styles['label']), Paragraph("Verified on File" if prop.occupancy_permit else "Pending Submission", styles['body'])],
        [Paragraph("LC1 Chairman Letter", styles['label']), Paragraph("Verified on File" if prop.lc1_letter else "Pending Submission", styles['body']), Paragraph("Standard Tenancy Agreement", styles['label']), Paragraph("Attached & Registered" if prop.tenancy_agreement else "Standard Digital Draft", styles['body'])],
    ]
    t_docs = Table(docs_data, colWidths=[120, 147, 120, 148])
    t_docs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_docs)

    add_footer(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 2. OFFICE (COMMERCIAL PROPERTY) REPORT
# ==========================================
def generate_office_pdf(prop, site_settings=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = get_report_styles()
    elements = []

    ref_id = prop.property_id or f"{prop.id:06d}"
    add_centered_report_header(
        elements=elements,
        styles=styles,
        category_title="Commercial Office Property Report",
        subject_name=prop.title,
        reference_id=ref_id,
        site_settings=site_settings
    )

    # 4. Remaining Details
    owner_name = prop.owner.get_full_name() or prop.owner.username if prop.owner else "Corporate Management / Landlord"
    owner_phone = getattr(prop.owner, 'phone', 'N/A') if prop.owner else 'N/A'
    price_disp = f"UGX {prop.price:,.0f}" if prop.price else "Contact for Quote"
    pricing_unit = prop.get_office_pricing_unit_display() if hasattr(prop, 'get_office_pricing_unit_display') and prop.office_pricing_unit else "Per Month"

    overview_data = [
        [Paragraph("Office ID", styles['label']), Paragraph(ref_id, styles['value_bold']), Paragraph("Listing Status", styles['label']), Paragraph(prop.get_status_display().upper(), styles['badge_green'])],
        [Paragraph("Office Title", styles['label']), Paragraph(prop.title, styles['value']), Paragraph("Office Category", styles['label']), Paragraph(prop.get_category_display() if hasattr(prop, 'get_category_display') and prop.category else "Commercial Workspace", styles['value'])],
        [Paragraph("Floor / Suite", styles['label']), Paragraph(prop.floor or "Main Floor / Ground", styles['value']), Paragraph("Pricing Structure", styles['label']), Paragraph(pricing_unit, styles['value'])],
        [Paragraph("Rent Rate", styles['label']), Paragraph(price_disp, styles['value_bold']), Paragraph("Rent Escrowed", styles['label']), Paragraph("TRUST Secured" if prop.collect_rent_by_trust else "Direct Landlord", styles['value'])],
        [Paragraph("Building Location", styles['label']), Paragraph(prop.location or "Kampala Commercial District", styles['value']), Paragraph("Coordinates", styles['label']), Paragraph(f"{prop.latitude or 'N/A'}, {prop.longitude or 'N/A'}", styles['value'])],
        [Paragraph("Managing Landlord", styles['label']), Paragraph(owner_name, styles['value']), Paragraph("Landlord Phone", styles['label']), Paragraph(owner_phone, styles['value'])],
    ]
    t_overview = Table(overview_data, colWidths=[95, 172, 95, 173])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_overview)
    elements.append(Spacer(1, 10))

    # Utilities & Overhead Cost Structure
    elements.append(Paragraph("Commercial Utility & Infrastructure Specifications", styles['section_title']))
    util_data = [
        [Paragraph("High-Speed WiFi / Internet", styles['label']), Paragraph(prop.wifi_cost or "Included in Rent / Dedicated Fiber", styles['value']), Paragraph("Power / Electricity", styles['label']), Paragraph(prop.electricity_cost or "Separate Yaka Meter / Backup Generator", styles['value'])],
        [Paragraph("Water Supply & Sanitation", styles['label']), Paragraph(prop.water_cost or "Included / Metered", styles['value']), Paragraph("Security Agreement", styles['label']), Paragraph("Verified 24/7 Guarded Premise" if prop.security_agreement else "Standard Access Control", styles['value'])],
    ]
    t_util = Table(util_data, colWidths=[120, 147, 120, 148])
    t_util.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_util)
    elements.append(Spacer(1, 10))

    if prop.description:
        elements.append(Paragraph("Office Space & Workspace Description", styles['section_title']))
        desc_data = [[Paragraph(prop.description, styles['body'])]]
        t_desc = Table(desc_data, colWidths=[535])
        t_desc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_desc)

    add_footer(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 3. CONSTRUCTION PROJECT REPORT
# ==========================================
def generate_construction_pdf(project, site_settings=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = get_report_styles()
    elements = []

    ref_id = project.property_id or f"{project.id:06d}"
    add_centered_report_header(
        elements=elements,
        styles=styles,
        category_title="Construction Project Progress Report",
        subject_name=project.title,
        reference_id=ref_id,
        site_settings=site_settings
    )

    prog_text = f"{project.progress_percentage}% COMPLETED"

    overview_data = [
        [Paragraph("Project ID", styles['label']), Paragraph(ref_id, styles['value_bold']), Paragraph("Construction Status", styles['label']), Paragraph(project.get_status_display().upper(), styles['badge_blue'])],
        [Paragraph("Project Title", styles['label']), Paragraph(project.title, styles['value_bold']), Paragraph("Progress Rating", styles['label']), Paragraph(prog_text, styles['badge_green'])],
        [Paragraph("Site Location", styles['label']), Paragraph(project.location or "Kampala Metropolitan", styles['value']), Paragraph("Supervising Body", styles['label']), Paragraph(project.supervisor_name or "TRUST Engineering Unit", styles['value'])],
        [Paragraph("Diaspora / Client", styles['label']), Paragraph(project.client_name or "Registered Owner", styles['value']), Paragraph("Owner Contact", styles['label']), Paragraph(f"{project.owner_phone or 'N/A'} | {project.owner_email or 'N/A'}", styles['value'])],
        [Paragraph("Commencement Date", styles['label']), Paragraph(str(project.start_date) if project.start_date else "Recorded at Inception", styles['value']), Paragraph("Target Completion", styles['label']), Paragraph(str(project.expected_completion) if project.expected_completion else "On Schedule", styles['value'])],
    ]
    t_overview = Table(overview_data, colWidths=[95, 172, 95, 173])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_overview)
    elements.append(Spacer(1, 10))

    # Milestones Progress Table
    elements.append(Paragraph("Construction Milestones Audit", styles['section_title']))
    completed_milestones = project.completed_milestones or []
    milestone_names = [
        "1. Site Survey & Clearing", "2. Excavation & Foundation Trenching", "3. Concrete Substructure & Footings",
        "4. Plinth Wall Construction", "5. Damp Proof Course (DPC) & Hardcore", "6. Ground Slab Casting",
        "7. Superstructure Wall Framing", "8. Lintel Casting & Reinforced Columns", "9. Ring Beam Completion",
        "10. Roof Truss Fabrication", "11. Roofing Sheet/Tile Installation", "12. Electrical Rough-in Piping",
        "13. Plumbing Rough-in Piping", "14. Internal Wall Plastering", "15. Ceiling Installation (Gypsum/Board)",
        "16. External Wall Plaster & Facade", "17. Window Frame & Glazing Install", "18. Door Framing & Shutter Fixing",
        "19. Floor Screeding & Tile Laying", "20. Painting - Undercoat Layer", "21. Electrical Wiring & Light Fixtures",
        "22. Sanitary Ware & Bathroom Fitting", "23. Final Coat Painting & Polish", "24. Compound Paving & Landscaping",
        "25. Final Handover & Quality Snagging"
    ]

    m_rows = []
    for idx, name in enumerate(milestone_names, start=1):
        is_done = idx in completed_milestones
        status_badge = Paragraph("<font color='#047857'><b>[DONE] VERIFIED</b></font>" if is_done else "<font color='#94a3b8'>[PENDING]</font>", styles['body'])
        m_rows.append([Paragraph(name, styles['body']), status_badge])

    t_milestones = Table(m_rows, colWidths=[385, 150])
    t_milestones.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_milestones)
    elements.append(Spacer(1, 10))

    if project.short_description or project.full_description:
        elements.append(Paragraph("Scope of Work Summary", styles['section_title']))
        scope_text = project.full_description or project.short_description
        elements.append(Table([[Paragraph(scope_text, styles['body'])]], colWidths=[535], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))

    add_footer(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 4. TENANT REPORT
# ==========================================
def generate_tenant_pdf(tenant, site_settings=None):
    from core.models import TenantBooking, TenantRental, MaintenanceRequest
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = get_report_styles()
    elements = []

    ref_id = f"{tenant.id:06d}"
    full_name = tenant.get_full_name() or tenant.username
    add_centered_report_header(
        elements=elements,
        styles=styles,
        category_title="Tenant Verification & Lease Portfolio Report",
        subject_name=full_name,
        reference_id=ref_id,
        site_settings=site_settings
    )

    phone = getattr(tenant, 'phone', 'N/A')
    date_joined = tenant.date_joined.strftime('%B %d, %Y') if tenant.date_joined else "Recorded"

    rentals = TenantRental.objects.filter(tenant=tenant).select_related('property').order_by('-created_at')
    bookings = TenantBooking.objects.filter(tenant=tenant).select_related('property').order_by('-booked_at')

    overview_data = [
        [Paragraph("Tenant ID", styles['label']), Paragraph(f"TNT-{ref_id}", styles['value_bold']), Paragraph("Account Status", styles['label']), Paragraph("ACTIVE" if tenant.is_active else "SUSPENDED", styles['badge_green'])],
        [Paragraph("Full Name", styles['label']), Paragraph(full_name, styles['value_bold']), Paragraph("Username", styles['label']), Paragraph(tenant.username, styles['value'])],
        [Paragraph("Email Address", styles['label']), Paragraph(tenant.email or "N/A", styles['value']), Paragraph("Phone Contact", styles['label']), Paragraph(str(phone), styles['value'])],
        [Paragraph("Registration Date", styles['label']), Paragraph(date_joined, styles['value']), Paragraph("Total Active Leases", styles['label']), Paragraph(str(rentals.filter(status='active').count()), styles['value_bold'])],
    ]
    t_overview = Table(overview_data, colWidths=[95, 172, 95, 173])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_overview)
    elements.append(Spacer(1, 10))

    # Rental Records Table
    elements.append(Paragraph("Lease Agreements & Property Tenancy", styles['section_title']))
    if rentals.exists():
        r_rows = [[
            Paragraph("Property", styles['th']),
            Paragraph("Monthly Rent", styles['th']),
            Paragraph("Period", styles['th']),
            Paragraph("Lease Status", styles['th'])
        ]]
        for r in rentals:
            p_title = r.property.title if r.property else "Property Record"
            rent_val = r.property.price_per_month if (r.property and r.property.price_per_month) else (r.property.price if r.property else None)
            rent_str = f"UGX {rent_val:,.0f}" if rent_val else (f"Total: UGX {r.total_amount:,.0f}" if r.total_amount else "N/A")
            period_str = f"Started: {r.start_date.strftime('%Y-%m-%d') if r.start_date else 'Recorded'}"
            status_badge = Paragraph(r.get_status_display().upper() if hasattr(r, 'get_status_display') else r.status.upper(), styles['td_bold'])
            r_rows.append([
                Paragraph(p_title, styles['td']),
                Paragraph(rent_str, styles['td']),
                Paragraph(period_str, styles['td']),
                status_badge
            ])
        t_rentals = Table(r_rows, colWidths=[205, 100, 130, 100])
        t_rentals.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#022416')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_rentals)
    else:
        elements.append(Paragraph("No formal signed leases recorded yet.", styles['body']))
    elements.append(Spacer(1, 10))

    # Recent Bookings Table
    elements.append(Paragraph("Booking & Verification Applications", styles['section_title']))
    if bookings.exists():
        b_rows = [[
            Paragraph("Property", styles['th']),
            Paragraph("Booking Date", styles['th']),
            Paragraph("Fee Paid", styles['th']),
            Paragraph("Status", styles['th'])
        ]]
        for b in bookings[:8]:
            p_title = b.property.title if b.property else "Property"
            b_date = b.booked_at.strftime('%Y-%m-%d') if b.booked_at else "N/A"
            b_fee = f"UGX {b.booking_fee:,.0f}" if b.booking_fee else "Free/Waived"
            b_rows.append([
                Paragraph(p_title, styles['td']),
                Paragraph(b_date, styles['td']),
                Paragraph(b_fee, styles['td']),
                Paragraph(b.status.upper(), styles['td_bold'])
            ])
        t_bookings = Table(b_rows, colWidths=[205, 100, 110, 120])
        t_bookings.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#047857')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_bookings)
    else:
        elements.append(Paragraph("No previous property viewing applications recorded.", styles['body']))

    add_footer(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 5. LANDLORD REPORT
# ==========================================
def generate_landlord_pdf(landlord, site_settings=None):
    from core.models import Property
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = get_report_styles()
    elements = []

    ref_id = f"{landlord.id:06d}"
    full_name = landlord.get_full_name() or landlord.username
    add_centered_report_header(
        elements=elements,
        styles=styles,
        category_title="Landlord Portfolio & Verification Report",
        subject_name=full_name,
        reference_id=ref_id,
        site_settings=site_settings
    )

    phone = getattr(landlord, 'phone', 'N/A')
    date_joined = landlord.date_joined.strftime('%B %d, %Y') if landlord.date_joined else "Recorded"

    properties = Property.objects.filter(owner=landlord).order_by('-id')
    tot_count = properties.count()
    avail_count = properties.filter(status='available').count()
    rented_count = properties.filter(status='rented').count()
    gross_val = sum(float(p.price or 0) for p in properties)

    overview_data = [
        [Paragraph("Landlord ID", styles['label']), Paragraph(f"LLD-{ref_id}", styles['value_bold']), Paragraph("Verification Status", styles['label']), Paragraph("VERIFIED LANDLORD", styles['badge_green'])],
        [Paragraph("Full Name", styles['label']), Paragraph(full_name, styles['value_bold']), Paragraph("Username", styles['label']), Paragraph(landlord.username, styles['value'])],
        [Paragraph("Email Address", styles['label']), Paragraph(landlord.email or "N/A", styles['value']), Paragraph("Phone Contact", styles['label']), Paragraph(str(phone), styles['value'])],
        [Paragraph("Total Properties", styles['label']), Paragraph(f"{tot_count} units", styles['value_bold']), Paragraph("Active Leased / Rented", styles['label']), Paragraph(f"{rented_count} units", styles['badge_green'])],
        [Paragraph("Units Available", styles['label']), Paragraph(f"{avail_count} units", styles['value']), Paragraph("Portfolio Valuation", styles['label']), Paragraph(f"UGX {gross_val:,.0f}", styles['value_bold'])],
    ]
    t_overview = Table(overview_data, colWidths=[95, 172, 95, 173])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_overview)
    elements.append(Spacer(1, 10))

    # Portfolio Itemization Table
    elements.append(Paragraph("Owned Real Estate Assets & Listings", styles['section_title']))
    if properties.exists():
        p_rows = [[
            Paragraph("Property ID / Title", styles['th']),
            Paragraph("Category", styles['th']),
            Paragraph("Monthly Rent", styles['th']),
            Paragraph("Location", styles['th']),
            Paragraph("Status", styles['th'])
        ]]
        for p in properties:
            p_code = p.property_id or f"PROP-{p.id}"
            title_text = f"<b>{p_code}</b><br/>{p.title}"
            cat_text = p.get_category_display() if hasattr(p, 'get_category_display') and p.category else (p.category or 'Property')
            rent_str = f"UGX {p.price_per_month:,.0f}" if p.price_per_month else (f"UGX {p.price:,.0f}" if p.price else "Contact")
            loc_str = p.location or "Kampala"
            status_badge = Paragraph(p.get_status_display().upper(), styles['td_bold'])

            p_rows.append([
                Paragraph(title_text, styles['td']),
                Paragraph(cat_text, styles['td']),
                Paragraph(rent_str, styles['td']),
                Paragraph(loc_str, styles['td']),
                status_badge
            ])
        t_props = Table(p_rows, colWidths=[155, 90, 95, 105, 90])
        t_props.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#022416')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_props)
    else:
        elements.append(Paragraph("No properties registered under this landlord account yet.", styles['body']))

    add_footer(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer
