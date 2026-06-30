from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from django.conf import settings
from django.http import HttpResponse
from datetime import datetime

def generate_pdf_receipt(order):
    """Generate a PDF receipt for an order"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Normal text style
    normal_style = styles['Normal']
    
    # 1. Header
    story.append(Paragraph("🧺 ZenClean Laundry", title_style))
    story.append(Paragraph("Quality Dry Cleaning & Laundry", subtitle_style))
    story.append(Paragraph("📍 Nairobi, Kenya | 📞 0712345678", subtitle_style))
    story.append(Spacer(1, 20))
    
    # 2. Receipt Title
    story.append(Paragraph("SALES RECEIPT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2c3e50')))
    story.append(Spacer(1, 10))
    
    # 3. Order Information
    story.append(Paragraph("ORDER INFORMATION", section_style))
    
    order_data = [
        ['Order #:', order.order_number],
        ['Date:', order.created_at.strftime('%Y-%m-%d %H:%M')],
        ['Payment Status:', order.get_payment_status_display()],
    ]
    
    order_table = Table(order_data, colWidths=[100, 300])
    order_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 15))
    
    # 4. Customer Details
    story.append(Paragraph("CUSTOMER DETAILS", section_style))
    
    customer_data = [
        ['Name:', order.customer.name],
        ['Phone:', order.customer.phone],
        ['Location:', order.customer.location or '-'],
        ['Apartment:', order.customer.apartment_name or '-'],
        ['Floor:', order.customer.floor or '-'],
        ['Door/House:', order.customer.door_number or '-'],
    ]
    
    customer_table = Table(customer_data, colWidths=[100, 300])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
        ('ROUND', (0, 0), (-1, -1), 5),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 15))
    
    # 5. Order Details
    story.append(Paragraph("ORDER DETAILS", section_style))
    
    order_details = [
        ['Items:', order.items_description or '-'],
        ['Weight:', f"{order.weight_kg} kg"],
        ['Rate:', f"KSh {order.price_per_kg}/kg"],
        ['Collection Date:', order.collection_date.strftime('%Y-%m-%d') if order.collection_date else 'TBD'],
    ]
    
    details_table = Table(order_details, colWidths=[100, 300])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))
    
    # 6. Payment Summary
    story.append(Paragraph("PAYMENT SUMMARY", section_style))
    
    payment_data = [
        ['Total Amount:', f"KSh {order.total_amount:,}"],
        ['Paid Amount:', f"KSh {order.paid_amount:,}"],
        ['Balance:', f"KSh {order.remaining_balance:,}"],
    ]
    
    # Highlight balance if > 0
    balance_style = ParagraphStyle(
        'BalanceStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#e74c3c') if order.remaining_balance > 0 else colors.HexColor('#27ae60'),
    )
    
    payment_table = Table(payment_data, colWidths=[100, 300])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -2), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor('#e74c3c') if order.remaining_balance > 0 else colors.HexColor('#27ae60')),
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
        ('ROUND', (0, 0), (-1, -1), 5),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 15))
    
    # 7. Status
    story.append(Paragraph(f"Order Status: {order.get_status_display()}", section_style))
    story.append(Spacer(1, 10))
    
    # 8. Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
    story.append(Spacer(1, 10))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
    )
    
    story.append(Paragraph("Thank you for choosing ZenClean! 🙏", footer_style))
    story.append(Paragraph("Your clothes will be ready in 24 hours", footer_style))
    story.append(Paragraph("Follow us: @ZenClean | www.zenclean.com", footer_style))
    story.append(Paragraph("This is a computer-generated receipt", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_whatsapp_receipt(order):
    """Generate PDF and return as base64 for WhatsApp"""
    import base64
    
    pdf_buffer = generate_pdf_receipt(order)
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    return pdf_base64