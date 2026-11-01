import importlib.util
from pathlib import Path
from datetime import date
import unittest

spec=importlib.util.spec_from_file_location('collector',Path(__file__).parents[1]/'scripts/collect-family-coupons.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

def card(start='10月27日',end='11月23日',asset='2610',amount='50',note='※一部地域を除く'):
    return f'''<div class="item"><div class="use"><dt>クーポン利用期間</dt><dd>{start}〜{end}</dd></div><p class="off_price"><span>{amount}</span> 円引き</p><div class="item_text"><dt class="item_maker">試験メーカー</dt><dd class="item_name">試験商品<br>大</dd><dd class="item_name">試験商品 小</dd></div><img src="/item/{asset}/image.jpg"><div><li>{note}</li></div></div>'''
class CollectorTest(unittest.TestCase):
    def test_preserves_products_conditions_and_stable_identity(self):
        row=collector.parse_items(card(),date(2026,11,1))[0]
        self.assertEqual(row['benefit'],'50円引き')
        self.assertEqual(row['products'],['試験商品 大','試験商品 小'])
        self.assertEqual(row['end'],'2026-11-23')
        self.assertIn('一部地域を除く',row['conditions'])
        self.assertEqual(row['id'],collector.parse_items(card().replace('円引き',' 円引き '),date(2026,11,1))[0]['id'])
    def test_expired_records_are_excluded(self):
        self.assertEqual(collector.parse_items(card(),date(2026,11,24)),[])
        self.assertEqual(len(collector.parse_items(card(),date(2026,11,23))),1)
    def test_new_year_rollover(self):
        row=collector.parse_items(card('12月30日','1月6日','2612'),date(2026,12,31))[0]
        self.assertEqual((row['start'],row['end']),('2026-12-30','2027-01-06'))
    def test_unverified_amount_or_year_rejected(self):
        for html in [card(amount='不明'),card(asset='unknown'),'<div>構造変更</div>']:
            with self.assertRaises(ValueError): collector.parse_items(html,date(2026,11,1))
    def test_one_invalid_card_rejects_whole_source(self):
        with self.assertRaises(ValueError): collector.parse_items(card()+card(amount='不明'),date(2026,11,1))
if __name__=='__main__': unittest.main()
