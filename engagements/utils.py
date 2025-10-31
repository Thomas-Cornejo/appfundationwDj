from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def generate_adoption_pdf(engagement, form_data):
    """Generate a PDF with the adoption application data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=30,
        alignment=1
    )
    
    title = Paragraph("SOLICITUD DE ADOPCIÓN", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    animal_title = Paragraph("<b>INFORMACIÓN DEL ANIMAL</b>", styles['Heading2'])
    elements.append(animal_title)
    elements.append(Spacer(1, 0.1*inch))
    
    animal_data = [
        ['Nombre:', engagement.animal.name],
        ['Edad:', f'{engagement.animal.age} años'],
        ['Sexo:', engagement.animal.get_sex_display()],
        ['Raza:', engagement.animal.breed.name],
        ['Color:', engagement.animal.color],
        ['Tamaño:', engagement.animal.get_size_display()],
    ]
    
    animal_table = Table(animal_data, colWidths=[2*inch, 4*inch])
    animal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0E7FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(animal_table)
    elements.append(Spacer(1, 0.3*inch))
    
    user_title = Paragraph("<b>INFORMACIÓN DEL SOLICITANTE</b>", styles['Heading2'])
    elements.append(user_title)
    elements.append(Spacer(1, 0.1*inch))
    
    user_data = [
        ['Nombre completo:', form_data.get('full_name', 'N/A')],
        ['Usuario:', engagement.user.username],
        ['Email:', engagement.user.email],
        ['Teléfono:', form_data.get('phone', 'N/A')],
        ['Ciudad:', form_data.get('city', 'N/A')],
        ['Dirección:', form_data.get('address', 'N/A')],
        ['Ocupación:', form_data.get('occupation', 'N/A')],
    ]
    
    user_table = Table(user_data, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0E7FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 0.3*inch))
    
    additional_title = Paragraph("<b>INFORMACIÓN ADICIONAL</b>", styles['Heading2'])
    elements.append(additional_title)
    elements.append(Spacer(1, 0.1*inch))
    
    additional_data = [
        ['Tipo de vivienda:', form_data.get('housing_type', 'N/A')],
        ['¿Tiene espacio al aire libre?:', 'Sí' if form_data.get('has_outdoor_space') else 'No'],
        ['¿Tiene experiencia con mascotas?:', 'Sí' if form_data.get('has_experience') else 'No'],
        ['¿Tiene otras mascotas?:', 'Sí' if form_data.get('has_other_pets') else 'No'],
    ]
    
    additional_table = Table(additional_data, colWidths=[2.5*inch, 3.5*inch])
    additional_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0E7FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(additional_table)
    elements.append(Spacer(1, 0.2*inch))
    
    if form_data.get('has_other_pets') and form_data.get('other_pets_description'):
        other_pets_title = Paragraph("<b>Descripción de otras mascotas:</b>", styles['Heading3'])
        elements.append(other_pets_title)
        other_pets_text = Paragraph(form_data.get('other_pets_description'), styles['BodyText'])
        elements.append(other_pets_text)
        elements.append(Spacer(1, 0.2*inch))
    
    if form_data.get('reason_for_adoption'):
        reason_title = Paragraph("<b>¿Por qué desea adoptar?</b>", styles['Heading3'])
        elements.append(reason_title)
        reason_text = Paragraph(form_data.get('reason_for_adoption'), styles['BodyText'])
        elements.append(reason_text)
        elements.append(Spacer(1, 0.3*inch))
    
    date_text = Paragraph(
        f"<i>Fecha de solicitud: {engagement.created_at.strftime('%d/%m/%Y %H:%M')}</i>",
        styles['Normal']
    )
    elements.append(date_text)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
