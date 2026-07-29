from pathlib import Path

root = Path(r'd:\Visual code editor\Learning Hub\templates\phy-ol')
patch = 'href="{{ url_for(\'render_html_template\', template_name=\'courses\') }}"'
count = 0
for p in sorted(root.rglob('*.html')):
    text = p.read_text(encoding='utf-8')
    new = text.replace('href="courses.html"', patch).replace('href="templates/courses.html"', patch)
    if new != text:
        p.write_text(new, encoding='utf-8')
        print(f'patched: {p}')
        count += 1
print(f'total patched files: {count}')
