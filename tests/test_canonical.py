import json
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/guide.json').read_text(encoding='utf-8'))
SITE = 'https://aipmandy.github.io/how-to-survive-unemployment'
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)">')
JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S)
SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# Existing chapter and city pages only. Labels are the site's current nav words.
STAGE_PAGES = {
    'before': ('guides/01-before.html', '失业前'),
    'week': ('guides/02-first-week.html', '前7天'),
    'month3': ('guides/03-three-months.html', '三个月'),
    'month6': ('guides/04-six-months.html', '六个月'),
    'year': ('guides/05-one-year.html', '一年'),
}
CITY_PAGES = {
    'beijing': ('guides/beijing.html', '北京政策'),
    'shanghai': ('guides/shanghai.html', '上海政策'),
    'guangzhou': ('guides/guangzhou.html', '广州政策'),
}


def static_pages():
    pages = [ROOT / 'index.html', ROOT / 'source-audit.html']
    for folder in ('guides', 'playbooks', 'templates'):
        pages.extend(sorted((ROOT / folder).glob('*.html')))
    return pages


def expected_canonical(path):
    rel = path.relative_to(ROOT).as_posix()
    if rel == 'index.html':
        return SITE + '/'
    return SITE + '/' + rel


def visible_html(html):
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
    return re.sub(r'<style\b[^>]*>.*?</style>', '', html, flags=re.S)


class TaskListParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.articles = []
        self.current = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if self.depth:
            self.depth += 1
        classes = (attr.get('class') or '').split()
        if tag == 'article' and 'task' in classes and self.depth == 0:
            self.current = {'id': attr.get('id'), 'hrefs': [], 'text': []}
            self.articles.append(self.current)
            self.depth = 1
        if self.current is not None and tag == 'a' and attr.get('href'):
            self.current['hrefs'].append(attr['href'])

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'].append(data)


def schema_types(node, found):
    if isinstance(node, dict):
        kind = node.get('@type')
        if isinstance(kind, str):
            found.add(kind)
        elif isinstance(kind, list):
            found.update(x for x in kind if isinstance(x, str))
        for value in node.values():
            schema_types(value, found)
    elif isinstance(node, list):
        for value in node:
            schema_types(value, found)


class CanonicalRegressionTests(unittest.TestCase):
    def test_every_static_html_page_has_one_absolute_canonical(self):
        pages = static_pages()
        self.assertEqual(len(pages), 22)
        seen = {}
        for path in pages:
            html = path.read_text(encoding='utf-8')
            found = CANONICAL_RE.findall(html)
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                self.assertEqual(html.count('rel="canonical"'), 1)
                self.assertEqual(found, [expected_canonical(path)])
                parts = urlsplit(found[0])
                self.assertEqual(parts.scheme, 'https')
                self.assertEqual(parts.netloc, 'aipmandy.github.io')
                self.assertEqual(parts.query, '')
                self.assertEqual(parts.fragment, '')
                self.assertFalse(found[0].endswith('index.html'))
                self.assertNotIn('?', found[0])
                seen[found[0]] = path
        self.assertEqual(len(seen), 22)

    def test_sitemap_lists_only_those_canonical_urls(self):
        root = ET.parse(ROOT / 'sitemap.xml').getroot()
        locs = [node.text.strip() for node in root.findall('sm:url/sm:loc', SITEMAP_NS)]
        canonicals = []
        for path in static_pages():
            html = path.read_text(encoding='utf-8')
            canonicals.extend(CANONICAL_RE.findall(html))
        self.assertEqual(locs, list(dict.fromkeys(locs)))
        self.assertEqual(set(locs), set(canonicals))
        self.assertEqual(len(locs), 22)
        self.assertIn(SITE + '/', locs)
        self.assertNotIn(SITE + '/index.html', locs)
        for loc in locs:
            parts = urlsplit(loc)
            self.assertEqual(parts.query, '')
            self.assertEqual(parts.fragment, '')
            self.assertNotIn('2026-11-25', loc)
        lastmods = [node.text.strip() for node in root.findall('sm:url/sm:lastmod', SITEMAP_NS)]
        self.assertEqual(len(lastmods), len(locs))
        self.assertNotIn('2026-11-25', lastmods)
        self.assertIn('2026-11-23', (ROOT / 'sitemap.xml').read_text(encoding='utf-8'))

    def test_home_and_source_audit_schema_match_canonical_identity(self):
        for rel in ('index.html', 'source-audit.html'):
            html = (ROOT / rel).read_text(encoding='utf-8')
            blocks = [json.loads(block) for block in JSONLD_RE.findall(html)]
            self.assertTrue(blocks, rel)
            found = set()
            urls = []
            for block in blocks:
                schema_types(block, found)
                graph = block.get('@graph', [block])
                for node in graph:
                    if isinstance(node, dict) and node.get('url'):
                        urls.append(node['url'])
            with self.subTest(page=rel):
                self.assertNotIn('FAQPage', found)
                self.assertIn(expected_canonical(ROOT / rel), urls)
        home = json.loads(JSONLD_RE.search((ROOT / 'index.html').read_text(encoding='utf-8')).group(1))
        website = next(node for node in home['@graph'] if node['@type'] == 'WebSite')
        person = next(node for node in home['@graph'] if node['@type'] == 'Person')
        self.assertEqual(website['url'], SITE + '/')
        self.assertEqual(person['name'], 'AI酋长Andy')
        self.assertEqual(person['jobTitle'], '流量 AI 联合创始人、星觉 AI 创始人')
        self.assertIn('北京', person['description'])
        audit = (ROOT / 'source-audit.html').read_text(encoding='utf-8')
        self.assertIn('"datePublished":"2026-11-23"', audit)
        self.assertIn('2026-10-30', audit)
        self.assertNotIn('2026-11-25', audit)

    def test_verified_policy_dates_and_boundaries_stay_put(self):
        checks = {
            'guides/beijing.html': ('2026-10-08', 'rsj.beijing.gov.cn'),
            'guides/shanghai.html': ('2026-10-08', 'rsj.sh.gov.cn'),
            'guides/guangzhou.html': ('2026-10-30', 'rsj.gz.gov.cn', '2250', '2680'),
        }
        for rel, parts in checks.items():
            text = (ROOT / rel).read_text(encoding='utf-8')
            for part in parts:
                with self.subTest(page=rel, part=part):
                    self.assertIn(part, text)
            self.assertNotIn('2026-11-25', text)
        home = (ROOT / 'index.html').read_text(encoding='utf-8')
        for part in (
            '不构成个案法律意见',
            '计算器仅用于预算，不存储或上传你的财务信息',
            '2N仅在符合法定违法解除赔偿情形时可能适用',
            '2129',
            '2286',
            '2340',
            '1872',
        ):
            self.assertIn(part, home)
        self.assertNotIn('腾讯优图', home)
        self.assertNotIn('Youtu', home)
        self.assertIsNone(re.search(r'(?i)youtu(?!be)', home))

    def test_home_tasks_have_crawlable_summaries_and_existing_links(self):
        html = visible_html((ROOT / 'index.html').read_text(encoding='utf-8'))
        parser = TaskListParser()
        parser.feed(html)
        by_id = {article['id']: article for article in parser.articles}
        self.assertEqual(len(parser.articles), 53)
        self.assertEqual(len(by_id), 53)
        sources = {source['id']: source for source in DATA['sources']}
        for task in DATA['tasks']:
            article = by_id.get('task-' + task['id'])
            text = ''.join(article['text']) if article else ''
            hrefs = article['hrefs'] if article else []
            with self.subTest(task=task['id']):
                self.assertIsNotNone(article)
                self.assertIn(task['title'], text)
                self.assertIn(task['detail'], text)
                self.assertIn('#task-' + task['id'], hrefs)
                stage_href, stage_label = STAGE_PAGES[task['stage']]
                self.assertIn(stage_href, hrefs)
                self.assertIn(stage_label, text)
                city = CITY_PAGES.get(task['city'])
                if city:
                    self.assertIn(city[0], hrefs)
                    self.assertIn(city[1], text)
                else:
                    for city_href, _label in CITY_PAGES.values():
                        self.assertNotIn(city_href, hrefs)
                for source_id in task['sources']:
                    self.assertIn(sources[source_id]['url'], hrefs)
                for href in hrefs:
                    parts = urlsplit(href)
                    self.assertEqual(parts.query, '')
                    if parts.scheme in ('http', 'https'):
                        self.assertEqual(parts.fragment, '')
        self.assertEqual(len(list(ROOT.rglob('*.html'))), 22)


if __name__ == '__main__':
    unittest.main()
