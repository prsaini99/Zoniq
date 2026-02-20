import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

from src.config.manager import settings


# Service class responsible for generating PDF e-tickets using ReportLab
class TicketService:
    """
    Service for generating PDF tickets.
    """

    # Load the JWT secret key from settings (used if ticket signing were needed)
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY

    # Generate a complete PDF ticket containing event, ticket, and booking details
    def generate_ticket_pdf(
        self,
        ticket_data: dict[str, Any],
        event_data: dict[str, Any],
        booking_data: dict[str, Any],
    ) -> bytes:
        """
        Generate a PDF ticket with all details.

        Args:
            ticket_data: Dict with ticket_number, category_name, seat_label, price
            event_data: Dict with title, event_date, venue_name, venue_address
            booking_data: Dict with booking_number, contact_email

        Returns:
            PDF file as bytes
        """
        # Create an in-memory buffer to write the PDF into
        buffer = io.BytesIO()
        # Configure A4 page size with custom margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        # Define custom paragraph styles for various sections of the ticket
        styles = getSampleStyleSheet()
        # Main title style — large, centered, branded purple color
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6366F1'),
        )
        # Section heading style — medium size, dark gray text
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#1F2937'),
        )
        # Ticket number style — bold, centered, branded purple
        ticket_number_style = ParagraphStyle(
            'TicketNumber',
            parent=styles['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6366F1'),
        )

        # Story list holds all flowable elements (paragraphs, tables, spacers) for the PDF
        story = []

        # Add the ZONIQ brand header and subtitle
        story.append(Paragraph("ZONIQ", title_style))
        story.append(Paragraph("E-Ticket", ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=30,
        )))

        # Display the unique ticket number prominently
        story.append(Paragraph(f"Ticket: {ticket_data['ticket_number']}", ticket_number_style))
        story.append(Spacer(1, 30))

        # Event Details section — title, date, venue, and optional address
        story.append(Paragraph("Event Details", heading_style))

        # Build event info rows for the table
        event_table_data = [
            ["Event:", event_data.get('title', 'N/A')],
            ["Date:", self._format_date(event_data.get('event_date'))],
            ["Venue:", event_data.get('venue_name', 'N/A')],
        ]
        # Append venue address row only if it exists
        if event_data.get('venue_address'):
            event_table_data.append(["Address:", event_data.get('venue_address')])

        # Create and style the event details table
        event_table = Table(event_table_data, colWidths=[100, 350])
        event_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(event_table)
        story.append(Spacer(1, 20))

        # Ticket Details section — category, seat, and price information
        story.append(Paragraph("Ticket Details", heading_style))

        # Build ticket info rows including formatted price in INR
        ticket_table_data = [
            ["Category:", ticket_data.get('category_name', 'N/A')],
            ["Seat:", ticket_data.get('seat_label', 'General Admission')],
            ["Price:", f"₹{ticket_data.get('price', 0):,.2f}"],
        ]

        # Create and style the ticket details table
        ticket_table = Table(ticket_table_data, colWidths=[100, 350])
        ticket_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(ticket_table)
        story.append(Spacer(1, 20))

        # Booking Information section — booking reference number and contact email
        story.append(Paragraph("Booking Information", heading_style))

        booking_table_data = [
            ["Booking #:", booking_data.get('booking_number', 'N/A')],
            ["Email:", booking_data.get('contact_email', 'N/A')],
        ]

        # Create and style the booking info table
        booking_table = Table(booking_table_data, colWidths=[100, 350])
        booking_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(booking_table)
        story.append(Spacer(1, 30))

        # Terms and conditions footer — small, muted text at the bottom
        terms_style = ParagraphStyle(
            'Terms',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER,
        )
        story.append(Paragraph(
            "This ticket is valid for one-time entry only. Please present this ticket at the venue entrance. "
            "Ticket is non-transferable unless transferred through the official ZONIQ platform.",
            terms_style
        ))

        # Build the final PDF document from the story elements
        doc.build(story)
        # Reset the buffer position to the beginning so it can be read
        buffer.seek(0)

        # Return the raw PDF bytes for attachment or download
        return buffer.getvalue()

    # Format an ISO date string into a human-readable display format
    def _format_date(self, date_str: str | None) -> str:
        """Format date string for display."""
        if not date_str:
            return "N/A"
        try:
            # Parse ISO format date, handling the 'Z' UTC suffix
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            # Fallback: return the raw string if parsing fails
            return str(date_str)


# Singleton instance — reused across the application for PDF generation
ticket_service = TicketService()
