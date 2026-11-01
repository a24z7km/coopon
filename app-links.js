/* Official URLs checked 2026-11-01. No guessed app schemes or coupon IDs. */
window.COOPON_APP_LINKS = {
  family: {
    name:'ファミペイ',
    open:'https://famipay.onelink.me/sVp0/gu5iz4el',
    web:'https://www.family.co.jp/famipay.html',
    ios:'https://apps.apple.com/jp/app/id1138196572',
    android:'https://play.google.com/store/apps/details?id=jp.co.family.familymart_app',
    source:'https://www.family.co.jp/content/dam/family/company/news_releases/2023/20231127_newsrelease_03.pdf'
  },
  seven: {
    name:'セブン‐イレブンアプリ',
    open:'https://sej-app.onelink.me/UUyB/ec65d78b',
    web:'https://www.sej.co.jp/products/app.html',
    ios:'https://apps.apple.com/jp/app/id1039171609',
    android:'https://play.google.com/store/apps/details?id=jp.co.sej.app',
    source:'https://www.sej.co.jp/products/app.html'
  },
  skylark: {
    name:'すかいらーくアプリ',
    web:'https://www.skylark.co.jp/cross_brand/coupon/index.html',
    ios:'https://apps.apple.com/jp/app/id906930478',
    android:'https://play.google.com/store/apps/details?id=jp.co.skylark.app.gusto',
    source:'https://www.skylark.co.jp/cross_brand/coupon/index.html'
  },
  tullys: {
    name:'タリーズ公式アプリ',
    web:'https://www.tullys.co.jp/service/app/',
    ios:'https://apps.apple.com/jp/app/id1517333828',
    android:'https://play.google.com/store/apps/details?id=jp.co.tullys.app',
    source:'https://www.tullys.co.jp/service/app/'
  }
};
window.cooponAppDestination = function(brand,userAgent='') {
  const group=['gusto','jonathan','bamiyan','musashino'].includes(brand)?'skylark':brand;
  const app=window.COOPON_APP_LINKS[group];
  if(!app)return null;
  if(app.open)return {...app,url:app.open,mode:'open'};
  if(/Android/i.test(userAgent))return {...app,url:app.android,mode:'store'};
  if(/iPhone|iPad|iPod/i.test(userAgent))return {...app,url:app.ios,mode:'store'};
  return {...app,url:app.web,mode:'web'};
};
