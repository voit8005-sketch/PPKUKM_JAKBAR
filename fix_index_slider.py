from pathlib import Path

path = Path('templates/index.html')
text = path.read_text(encoding='utf-8')
lines = text.splitlines()
# Replace the broken Jinja chunk around slider button style
start = 322
end = 331
lines[start] = '          {% if i == 1 %}style="background: rgb(37 99 235 / 0.1); border-color: rgb(37 99 235 / 0.5); color: rgb(37 99 235)"{% endif %}'
for i in range(start + 1, end):
    lines[i] = ''
path.write_text('\r\n'.join(lines), encoding='utf-8')
print('fixed', path)
