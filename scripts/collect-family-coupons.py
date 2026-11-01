#!/usr/bin/env python3
"""Collect only public FamilyMart coupon HTML, preserving products and conditions.
No login, private app API, OCR, third-party aggregation or guessed discounts.
Fetch is explicit/manual; invalid structure leaves the previous feed intact.
"""
import argparse
from datetime import date, datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from zoneinfo import ZoneInfo

URL = 'https://www.family.co.jp/campaign/spot/famipay_again_cp.html'
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self):
        return ' '.join(c.text() if isinstance(c, Node) else c for c in self.children)
    def find(self, tag=None, cls=None):
        result=[]
        for c in self.children:
            if not isinstance(c, Node): continue
            if (tag is None or c.tag==tag) and (cls is None or cls in c.attrs.get('class','').split()): result.append(c)
            result.extend(c.find(tag, cls))
        return result
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root=Node(); self.stack=[self.root]
    def handle_starttag(self, tag, attrs):
        n=Node(tag, attrs); self.stack[-1].children.append(n)
        if tag not in VOID: self.stack.append(n)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)
def clean(value): return re.sub(r'\s+', ' ', value).strip()
def parse_items(html, as_of):
    parser=Parser(); parser.feed(html)
    cards=parser.root.find('div','item')
    if not cards: raise ValueError('No official coupon cards found; previous feed preserved')
    result=[]
    for card in cards:
        uses=card.find('div','use'); prices=card.find('p','off_price'); texts=card.find('div','item_text')
        if not uses or not prices or not texts: raise ValueError('Coupon structure changed')
        dates=re.findall(r'(\d{1,2})月(\d{1,2})日',uses[0].text())
        amount=re.search(r'(\d+)\s*円引',clean(prices[0].text()))
        images=card.find('img')
        year_match=next((m for image in images if (m:=re.search(r'/item/(\d{2})\d{2}/',image.attrs.get('src','')))),None)
        if len(dates)!=2 or not amount or not year_match: raise ValueError('Missing verified dates, amount, or year')
        year=2000+int(year_match[1]); sm,sd=map(int,dates[0]); em,ed=map(int,dates[1])
        start=date(year,sm,sd); end=date(year+(em<sm),em,ed)
        if (end-start).days>180: raise ValueError('Unexpected coupon duration')
        if end<as_of: continue
        if (start-as_of).days>90: raise ValueError('Unexpected future coupon year')
        names=[clean(n.text()) for n in texts[0].find('dd','item_name') if clean(n.text())]
        makers=[clean(n.text()) for n in texts[0].find('dt','item_maker') if clean(n.text())]
        if not names: raise ValueError('Missing target products')
        maker=' '.join(makers)
        title=clean(' '.join(([maker] if maker else [])+names[:2]))+(' ほか' if len(names)>2 else '')
        amount=int(amount[1]); restrictions=[clean(n.text()).lstrip('※').strip() for n in card.find('li') if clean(n.text()) and '掲載画像' not in n.text()]
        key=json.dumps([maker,names,start.isoformat(),end.isoformat(),amount],ensure_ascii=False)
        result.append(dict(id='family-repeat-'+hashlib.sha256(key.encode()).hexdigest()[:12],chain='ファミリーマート',brand='family',category='convenience',title=title,benefit=f'{amount}円引き',summary='対象商品のうち1点。期限内は繰り返し利用できます。',products=names,period=f'{start.year}年{sm}月{sd}日〜{end.year}年{em}月{ed}日',start=start.isoformat(),end=end.isoformat(),kind='app',requirement='ファミペイにクーポンをセット',conditions=['対象商品1点につき1枚、1会計で最大5枚まで。','他のセール・割引券・引換券とは併用できません。','一部地域・店舗や品切れ・取り扱いのない商品は対象外。']+restrictions,how='ファミペイで対象券の枚数を選び「セットする」を押して、ホーム画面のバーコードをレジで提示。',source='familyRepeat',checkedAt=as_of.isoformat()))
    if len({x['id'] for x in result})!=len(result): raise ValueError('Duplicate coupon records')
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path); ap.add_argument('--output',type=Path,default=Path('coupon-feed.js')); ap.add_argument('--date',type=date.fromisoformat); args=ap.parse_args()
    now=datetime.now(ZoneInfo('Asia/Tokyo')); as_of=args.date or now.date()
    if args.input: html=args.input.read_text()
    else:
        req=urllib.request.Request(URL,headers={'User-Agent':'coopon-coupon-collector/1.0 (+https://github.com/a24z7km/coopon)'})
        with urllib.request.urlopen(req,timeout=30) as response:
            if 'text/html' not in response.headers.get('Content-Type',''): raise ValueError('Not HTML')
            html=response.read().decode('utf-8')
    items=parse_items(html,as_of)
    payload=dict(checkedAt=as_of.isoformat(),fetchedAt=now.isoformat(),sources=dict(familyRepeat=dict(name='ファミリーマート公式・何度でも使えるクーポン',url=URL,checkedAt=as_of.isoformat())),items=items)
    # Atomic replacement only after the entire source passed validation.
    temp=args.output.with_suffix('.tmp'); temp.write_text('window.COOPON_FEED = '+json.dumps(payload,ensure_ascii=False,indent=2)+';\n'); temp.replace(args.output)
    print(json.dumps(dict(source=URL,count=len(items),checkedAt=as_of.isoformat()),ensure_ascii=False))
if __name__=='__main__': main()
