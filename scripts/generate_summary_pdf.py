from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

class ProjectSummaryPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(190, 10, 'Fast Transit Line (FTL) - Project Governance', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(190, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(md_path, pdf_path):
    pdf = ProjectSummaryPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        
        # Reset X at the start of each line to avoid horizontal space errors
        pdf.set_x(10)

        if not line:
            pdf.ln(4)
            continue
            
        if line.startswith('|') or line.startswith(':'):
            continue # Skip tables and weird markdown markers
            
        try:
            if line.startswith('# '):
                pdf.set_font('helvetica', 'B', 18)
                pdf.multi_cell(190, 10, line[2:])
                pdf.ln(2)
            elif line.startswith('## '):
                pdf.set_font('helvetica', 'B', 15)
                pdf.multi_cell(190, 10, line[3:])
                pdf.ln(1)
            elif line.startswith('### '):
                pdf.set_font('helvetica', 'B', 13)
                pdf.multi_cell(190, 8, line[4:])
            elif line.startswith('#### '):
                pdf.set_font('helvetica', 'B', 11)
                pdf.multi_cell(190, 7, line[5:])
            elif line.startswith('- '):
                pdf.set_font('helvetica', '', 11)
                pdf.multi_cell(190, 6, f'  - {line[2:]}')
            elif line.startswith('---'):
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(2)
            else:
                pdf.set_font('helvetica', '', 11)
                pdf.multi_cell(190, 6, line)
        except Exception as e:
            print(f"Skipping line due to formatting error: {line[:50]}... ({str(e)})")
            
    pdf.output(pdf_path)
    print(f"PDF successfully generated at: {pdf_path}")

if __name__ == '__main__':
    md_file = r'd:\AXE Global\FTL Demo S1\PROJECT_SUMMARY.md'
    pdf_file = r'd:\AXE Global\FTL Demo S1\FTL_Project_Summary.pdf'
    create_pdf(md_file, pdf_file)
