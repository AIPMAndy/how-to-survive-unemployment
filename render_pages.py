#!/usr/bin/env python3
"""Zero-dependency build of standalone offline HTML from trusted repo-authored Markdown.
Not a general purpose Markdown engine: authoring subset documented in CONTRIBUTING.
"""
import re
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NAV=[('开始这里','guides/00-start-here.html'),('失业前','guides/01-before.html'),('前7天','guides/02-first-week.html'),('三个月','guides/03-three-months.html'),('六个月','guides/04-six-months.html'),('一年','guides/05-one-year.html'),('北京政策','guides/beijing.html'),('上海政策','guides/shanghai.html')]
LINK=re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def inline(line):
    # Link labels / destinations escaped; protocols not interpolated from user-generated data.
    tokens=[]
    def take(m):
        label,url=m.group(1),m.group(2)
        if url.startswith(('https://','http://','#')) or not re.match(r'^[a-z]+:',url,re.I):
            url=url.replace('.md','.html')
            tokens.append(f'<a href="{escape(url,quote=True)}">{escape(label)}</a>')
        else: tokens.append(escape(label))
        return f'ZZLINKTOKEN{len(tokens)-1}ZZ'
    safe=escape(LINK.sub(take,line))
    safe=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',safe)
    safe=re.sub(r'`([^`]+)`',r'<code>\1</code>',safe)
    for i,token in enumerate(tokens):safe=safe.replace(f'ZZLINKTOKEN{i}ZZ',token)
    return safe

def render(md):
    lines=md.splitlines(); out=[]; i=0; state=None
    def close():
        nonlocal state
        if state:out.append('</'+state+'>');state=None
    while i<len(lines):
        line=lines[i]; stripped=line.strip()
        if not stripped:close();i+=1;continue
        if stripped.startswith('```'):
            close();lang=escape(stripped[3:]); code=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):code.append(lines[i]);i+=1
            out.append('<pre><code>'+escape('\n'.join(code))+'</code></pre>');i+=1;continue
        if stripped.startswith('|') and i+1<len(lines) and re.fullmatch(r'\|[\s:\-|]+\|?',lines[i+1].strip()):
            close();hdr=[v.strip() for v in stripped.strip('|').split('|')];out.append('<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+inline(v)+'</th>' for v in hdr)+'</tr></thead><tbody>');i+=2
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[v.strip() for v in lines[i].strip().strip('|').split('|')];out.append('<tr>'+''.join('<td>'+inline(v)+'</td>' for v in cells)+'</tr>');i+=1
            out.append('</tbody></table></div>');continue
        if stripped.startswith('#') and (m:=re.match(r'^(#{1,6})\s+(.+)$',stripped)):
            close();level=len(m.group(1));out.append(f'<h{level}>{inline(m.group(2))}</h{level}>');i+=1;continue
        if stripped=='---':close();out.append('<hr>');i+=1;continue
        if stripped.startswith('> '):close();out.append('<blockquote>'+inline(stripped[2:])+'</blockquote>');i+=1;continue
        if re.match(r'^[-*]\s+',stripped) or re.match(r'^\d+[.)]\s+',stripped):
            kind='ol' if re.match(r'^\d+[.)]\s+',stripped) else 'ul'
            if state!=kind:close();out.append('<'+kind+'>');state=kind
            text=re.sub(r'^(?:[-*]|\d+[.)])\s+','',stripped)
            if text.startswith('[ ] '):text='☐ '+text[4:]
            if text.startswith('[x] '):text='☑ '+text[4:]
            out.append('<li>'+inline(text)+'</li>');i+=1;continue
        close();out.append('<p>'+inline(stripped)+'</p>');i+=1
    close();return '\n'.join(out)

def write_all():
    files=[p for parent in ('guides','playbooks','templates') for p in (ROOT/parent).glob('*.md')]
    count=0
    for path in files:
        title=next((l.strip('# ').strip() for l in path.read_text(encoding='utf-8').splitlines() if l.startswith('# ')),path.stem)
        prefix='../'; topnav='<a href="https://metaver.vip/" target="_blank" rel="noopener noreferrer">Andy 官网 ↗</a> ' + ' '.join(f'<a href="{prefix+url}">{escape(label)}</a>' for label,url in NAV)
        content=render(path.read_text(encoding='utf-8'))
        html=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} · 失业了咋办</title><meta name="description" content="按真实步骤操作的失业自救指南：{escape(title)}"><style>body{{margin:0;background:#f6f7f8;color:#242b32;font:16px/1.9 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft Yahei",sans-serif}}.wrap{{max-width:780px;margin:auto;padding:24px 18px 80px}}header{{background:white;position:sticky;top:0;box-shadow:0 1px 8px #0001;z-index:2}}header nav{{max-width:1000px;margin:auto;padding:10px 18px;display:flex;gap:15px;overflow:auto;white-space:nowrap}}a{{color:#187184;text-decoration:none}}a:hover{{text-decoration:underline}}article{{background:white;border:1px solid #e4e7eb;border-radius:14px;padding:30px 34px}}h1{{font-size:31px;line-height:1.4;margin:0 0 26px}}h2{{font-size:23px;line-height:1.4;margin-top:38px}}h3{{font-size:19px}}p{{margin:14px 0}}li{{margin:7px 0}}strong{{color:#14232c}}blockquote{{border-left:3px solid #8aa5ae;background:#f2f5f7;margin:18px 0;padding:10px 18px}}.table-scroll{{overflow:auto;margin:24px 0}}table{{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}}th,td{{border:1px solid #d6dde3;padding:9px;vertical-align:top}}th{{background:#f0f3f5}}pre{{overflow:auto;background:#17252d;color:white;padding:14px;border-radius:8px}}code{{background:#eef3f5;padding:2px 4px}}pre code{{background:none;padding:0}}.back{{display:inline-block;margin:15px 0 20px}}footer{{text-align:center;color:#65737d;font-size:13px;margin-top:24px}}@media(max-width:650px){{article{{padding:19px 18px}}h1{{font-size:25px}}h2{{font-size:20px}}}}</style></head><body><header><nav aria-label="文档目录"><a href="../index.html"><strong>失业了咋办 ↗</strong></a>{topnav}</nav></header><div class="wrap"><a class="back" href="../index.html">← 返回互动行动清单</a><article>{content}</article><footer>AI酋长 Andy 发起 · 2026-10-08核验 · 重大决策以当地官方政策与个案为准<p>求职、职业转型、AI 应用等咨询，可联系微信 <strong>AIPMAndy</strong> · <a href="https://metaver.vip/" target="_blank" rel="noopener noreferrer">Andy 个人官网 ↗</a></p></footer></div></body></html>'''
        # EDITORIAL-2026: shared reader styling for generated pages
        html = html.replace('</style>', "\n/* EDITORIAL-2026 */body{background:#f8f7f4;color:#17191c;font:16px/1.85 -apple-system,BlinkMacSystemFont,\"PingFang SC\",\"Noto Sans CJK SC\",\"Microsoft YaHei\",sans-serif}header{background:rgba(248,247,244,.95);border-bottom:1px solid #dedfd9;box-shadow:none;backdrop-filter:blur(14px)}header nav{max-width:1120px;gap:18px}header a,a{color:#315f52}.wrap{max-width:900px}article{border-color:#dedfd9;border-radius:18px;padding:clamp(22px,4vw,48px)}h1{font-size:clamp(30px,4vw,46px);letter-spacing:-.05em;line-height:1.22}h2{font-size:clamp(23px,3vw,30px)}p,li{line-height:1.85}p{max-width:72ch}blockquote{background:#edf2ec;border-left-color:#315f52}th{background:#edf2ec}th,td{border-color:#dedfd9}code{background:#edf2ec}pre code{background:none}:where(a,button,input):focus-visible{outline:3px solid #315f52;outline-offset:3px}@media(max-width:650px){.wrap{padding:18px 16px 60px}article{padding:22px 18px}.table-scroll{overflow-x:auto}header nav{overflow-x:auto}}\n" + '</style>', 1)
        # FIELD NOTES / READER V2: keep generated standalone pages visually aligned.
        html = html.replace('</style>', "\n/* FIELD NOTES / READER V2 — quiet editorial reading surface */\nbody{background:#f8f7f2;color:#21372a;font:16px/1.9 -apple-system,BlinkMacSystemFont,\"PingFang SC\",\"Noto Sans CJK SC\",\"Microsoft YaHei\",sans-serif;letter-spacing:-.009em}\nheader{background:rgba(248,247,242,.93);border-bottom:1px solid #dce5d8;box-shadow:none;backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}\nheader nav{max-width:1160px;min-height:68px;gap:24px;align-items:center;scrollbar-width:thin}\nheader nav a{font-size:12px;color:#536b59;flex:none}\nheader nav a:first-child{padding:9px 16px;background:#244b38;border-radius:99px;color:#fff;font-size:13px}\nheader nav a:first-child strong{color:#fff}\n.wrap{max-width:1100px;padding:28px 32px 80px}\n.back{color:#43664e;font-size:13px;font-weight:650;margin:13px 0 24px}\narticle{position:relative;max-width:850px;margin:auto;background:#fffefa;border:1px solid #dee8dc;border-radius:24px;padding:clamp(30px,6vw,78px);box-shadow:0 20px 55px rgba(22,62,39,.045)}\narticle::before{content:\"FIELD NOTES  /  OPEN KNOWLEDGE\";display:block;font:750 10px/1.5 Arial,sans-serif;color:#70947b;letter-spacing:.2em;margin-bottom:28px}\nh1{font-size:clamp(34px,4.4vw,55px);line-height:1.25;letter-spacing:-.065em;color:#1c422d;margin-bottom:32px}\nh2{font-size:clamp(25px,3vw,32px);line-height:1.35;color:#235039;letter-spacing:-.045em;margin-top:52px;padding-top:14px;border-top:1px solid #e6ebe3}\nh3{font-size:21px;color:#30573e;letter-spacing:-.025em}\np,li{line-height:1.95;color:#526456}strong{color:#204735}\narticle a{color:#2b6848;text-decoration:underline;text-underline-offset:3px}\narticle a:hover{color:#14432a}\nblockquote{border-left:3px solid #6caa77;background:#eef4ec;border-radius:0 12px 12px 0;padding:18px 23px}\n.table-scroll{border:1px solid #dce5d8;border-radius:12px;overflow-x:auto}\ntable{background:#fffefa}\nth{background:#eaf0e7;color:#244d37}\nth,td{border:1px solid #dee7da;padding:12px 13px}\npre{background:#193d2c;color:#eaf5e7;border-radius:13px;padding:23px}\ncode{background:#e8eee6;color:#1a4830;border-radius:5px}\npre code{background:none;color:inherit}\nhr{border:0;border-top:1px solid #dce5d8;margin:36px 0}\nfooter{max-width:850px;margin:0 auto;padding:60px 0 0;text-align:left;color:#617867;font-size:12px}\nfooter::before{content:\"重新开始，也是人生的一部分。\";display:block;border-top:1px solid #d8e3d6;padding-top:37px;margin-bottom:16px;font-size:clamp(24px,3vw,37px);line-height:1.4;font-weight:740;letter-spacing:-.06em;color:#244a34}\nfooter strong{color:#2b6144}\n:where(a,button,input):focus-visible{outline:3px solid #4e9570;outline-offset:4px}\n@media(max-width:700px){header nav{padding:12px 18px;min-height:60px;gap:16px}.wrap{padding:20px 17px 60px}article{padding:34px 22px;border-radius:18px}article::before{font-size:9px}h1{font-size:clamp(30px,8vw,43px)}h2{font-size:clamp(23px,6vw,29px)}table{min-width:520px}footer{padding-top:40px}}\n@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}\n" + '</style>', 1)
        path.with_suffix('.html').write_text(html,encoding='utf-8');count+=1
    return count
if __name__=='__main__':print('Generated',write_all(),'reader pages')
