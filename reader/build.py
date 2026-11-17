"""Build one self-contained HTML from checked local inputs. No network required."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
css=(root/'reader.css').read_text().replace('__BG__','url("'+(root/'research/author-background.txt').read_text().strip()+'")')
data=json.loads((root/'research/reader-data.json').read_text())
page=(root/'template.html').read_text().replace('__CSS__',css).replace('__JS__',(root/'model.js').read_text()+'\n'+(root/'reader.js').read_text()).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
assert not any(x in page for x in ['__CSS__','__JS__','__DATA__','__BG__'])
(root/'dist').mkdir(exist_ok=True)
(root/'dist/index.html').write_text(page)
print(root/'dist/index.html')
