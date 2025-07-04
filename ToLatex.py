import os
import re
import subprocess

def md_to_latex(md_file, tex_file, pdf_file):
    output_dir = os.path.dirname(tex_file)
    os.makedirs(output_dir, exist_ok=True)

    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.readlines()

    tex_content = [
        "\\documentclass{article}\n",
        "\\usepackage[a4paper, margin=1in]{geometry}\n",
        "\\usepackage{enumitem}\n",
        "\\begin{document}\n",
        "\\begin{center}\n",
        "\\textbf{Question Paper}\n",
        "\\vspace{0.5cm}\n",
        "\\end{center}\n"
    ]

    title = None
    current_section = None
    for line in md_content:
        line = line.strip().replace("&", "\\&")
        if line.startswith("# "):
            title = line[2:]
            tex_content.append(f"\\noindent \\textbf{{{title}}}\n")
        elif line.startswith("## "):
            if current_section:
                tex_content.append("\\end{enumerate}\n")
            current_section = line[3:]
            tex_content.append(f"\\section*{{{current_section}}}\n")
            tex_content.append("\\begin{enumerate}\n")
        elif re.match(r"^\d+\.", line):
            tex_content.append(f"\\item {line.split('.', 1)[1].strip()}\n")
        else:
            tex_content.append(f"{line}\n")

    if current_section:
        tex_content.append("\\end{enumerate}\n")
    tex_content.append("\\end{document}\n")

    with open(tex_file, 'w', encoding='utf-8') as f:
        f.writelines(tex_content)

    print(f"LaTeX file saved as {tex_file}")

    subprocess.run(["pdflatex", "-output-directory", output_dir, tex_file])
    subprocess.run(["pdflatex", "-output-directory", output_dir, tex_file])

    print(f"PDF generated: {pdf_file}")