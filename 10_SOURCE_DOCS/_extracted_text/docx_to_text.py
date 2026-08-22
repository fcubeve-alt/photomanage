import sys, zipfile, re, os
def conv(p, out):
    z = zipfile.ZipFile(p)
    xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<w:tab[^>]*/>', '\t', xml)
    xml = re.sub(r'<w:br[^>]*/>', '\n', xml)
    txt = re.sub(r'<[^>]+>', '', xml)
    txt = txt.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&#39;',"'")
    txt = re.sub(r'\n{3,}', '\n\n', txt)
    open(out,'w',encoding='utf-8').write(txt)
    return len(txt.split('\n')), len(txt)
for f in sys.argv[1:]:
    base = os.path.basename(f)
    out = os.path.join(os.path.dirname(sys.argv[0]),'txt', re.sub(r'[^A-Za-z0-9._-]','_',base)+'.txt')
    try:
        l,c = conv(f,out)
        print(f"{base} -> {os.path.basename(out)} | lines={l} chars={c}")
    except Exception as e:
        print(f"{base} FAILED {e}")
