"""SpecLens: PRD-derived local NLP planning + evidence-based browser verification."""
import argparse, asyncio, hashlib, html, json, re, time, platform
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, expect
from planner import plan

class Agent:
 def __init__(self,args):
    self.a=args; self.out=Path(args.output).resolve(); self.out.mkdir(parents=True,exist_ok=True)
    self.requirements=plan(Path(args.prd).read_text()); self.results=[]; self.started=time.time()
    self.tag='SpecLens-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
 async def nav(self,path):
    self.actions.append('Navigate '+path)
    await self.p.goto(self.a.url.rstrip('/')+path)
    await self.p.locator('h1').first.wait_for()
 async def snapshot(self):
    # Read-only API observations supplement UI evidence; no direct API mutations.
    a=await self.ctx.request.get(self.a.api+'/api/accounts')
    t=await self.ctx.request.get(self.a.api+'/api/transactions')
    if not a.ok or not t.ok: raise RuntimeError('Observation API unavailable')
    return {'accounts':(await a.json())['accounts'],'transactions':(await t.json())['transactions']}
 async def transfer(self,amount,same=False):
    await self.nav('/transfer')
    await expect(self.p.get_by_label('From account')).not_to_have_value('')
    opts=await self.p.get_by_label('From account').locator('option').evaluate_all('(es)=>es.filter(e=>e.value).map(e=>({id:e.value,label:e.textContent}))')
    source=opts[0]['id']; dest=source if same else opts[1]['id']
    await self.p.get_by_label('From account').select_option(source)
    await self.p.get_by_label('To account').select_option(dest)
    await self.p.get_by_label('Amount (USD)').fill(amount)
    await self.p.get_by_label('Memo').fill(self.tag+'-'+str(len(self.results)))
    self.actions.append(f'Submit transfer amount={amount!r}; source={source}; destination={dest}')
    await self.p.get_by_role('button',name='Transfer funds',exact=True).click()
    # Wait for either a validation error or receipt, not a fixed success assumption.
    await self.p.wait_for_function("""()=> document.querySelector('.alert') || [...document.querySelectorAll('.field__error')].some(e=>e.textContent.trim())""")
    return source,dest
 async def check(self,name,group,fn):
    selected=[r for r in self.requirements if r['capability']==group and r['similarity']>0]
    if not selected: return
    ident=f'T{len(self.results)+1:02}'; steps=[]; self.actions=[]
    try:
        observed,steps=await fn(); verdict='passed'
    except AssertionError as e:
        observed=str(e); verdict='failed'
    except Exception as e:
        observed=f'{type(e).__name__}: {str(e)[:500]}'; verdict='unverified'
    if not steps: steps=list(self.actions)+['Compare observed values against the named assertion']
    await self.p.screenshot(path=str(self.out/f'{ident}.png'),full_page=True)
    (self.out/f'{ident}.txt').write_text(await self.p.locator('body').inner_text())
    result={'id':ident,'name':name,'group':group,'verdict':verdict,'observed':observed,'steps':steps,
            'evidence':[f'{ident}.png',f'{ident}.txt'],'candidate_requirements':[r['id'] for r in selected]}
    self.results.append(result); print(f'{ident} {verdict.upper()}: {name}',flush=True)
    self.export()
    if self.a.demo: await asyncio.sleep(4)
 async def run(self):
    async with async_playwright() as pw:
      browser=await pw.chromium.launch(headless=True)
      self.ctx=await browser.new_context(viewport={'width':1280,'height':800},record_video_dir=str(self.out/'video') if self.a.demo else None,record_video_size={'width':1280,'height':800})
      self.p=await self.ctx.new_page(); self.p.set_default_timeout(8000)
      await self.p.goto(self.a.url)
      # Agent-owned briefing is recorded before target execution, never mistaken for target evidence.
      if self.a.demo:
        await self.p.set_content('<html><body style="background:#101c2d;color:white;font:22px system-ui;padding:50px"><h1>SpecLens | Autonomous QA</h1><p>Raashid Shaik · CDF Agentic QA Hackathon</p><h2>1. Ingest the specification</h2><p>Local TF-IDF planner maps PRD bullets to executable capability families.</p><p>2. Execute positive, negative, and boundary scenarios.</p><p>3. Verify balances, records, filters, and session behavior.</p><p>4. Export evidence, uncovered requirements, runtime, and cost.</p><p>No LLM calls. No real financial data. Unverified is never a pass.</p></body></html>')
        await self.p.set_content('<html><body style="background:#101c2d;color:white;font:18px system-ui;padding:36px"><h1>SpecLens | PRD ingestion and plan</h1><p>Raashid Shaik · Local NLP planner · No remote model calls</p><p>Read '+str(len(self.requirements))+' exact requirement bullets from PRD.md</p><p>PRD SHA-256: '+hashlib.sha256(Path(self.a.prd).read_bytes()).hexdigest()+'</p>'+''.join('<p><b>'+r['id']+' → '+r['capability']+' ('+str(r['similarity'])+')</b><br>'+html.escape(r['text'])+'</p>' for r in self.requirements[:5])+'<p>Next: execute browser scenarios, compare evidence, export audit.</p></body></html>')
        await asyncio.sleep(12); await self.p.goto(self.a.url)
      async def session():
        await self.p.get_by_role('button',name='Enter Demo',exact=True).click(); await self.p.wait_for_url('**/dashboard')
        await expect(self.p.get_by_role('button',name='Log out',exact=True)).to_be_visible()
        return 'Demo dashboard opened without credentials; Log out available.',['Open target','Click Enter Demo','Observe dashboard and logout control']
      await self.check('Enter demo without credentials','session',session)
      async def refresh():
        await self.p.reload(); await expect(self.p.get_by_test_id('account-card')).to_have_count(2)
        return 'Session survives refresh and two accounts load.',['Refresh dashboard','Wait for two account cards']
      await self.check('Session persistence after refresh','session',refresh)
      async def accounts():
        await self.nav('/dashboard'); cards=self.p.get_by_test_id('account-card'); await expect(cards).to_have_count(2)
        texts=await cards.all_inner_texts()
        assert all(re.search(r'\$[\d,]+\.\d{2}',t) and ('••' in t or '***' in t) for t in texts),texts
        assert any('Checking' in t for t in texts) and any('Savings' in t for t in texts),texts
        return texts,['Open dashboard','Check names, types, masked numbers, two-decimal USD balances']
      await self.check('Account cards and readable masked balances','accounts',accounts)
      async def detail():
        before=await self.snapshot()
        for a in before['accounts']:
          await self.nav('/accounts/'+a['id']); await expect(self.p.get_by_test_id('transaction-table')).to_be_visible()
          text=await self.p.locator('body').inner_text(); assert f"{Decimal(a['balance']):,.2f}" in text,text
        return before['accounts'],['Open each discovered account detail','Compare balance to read-only account observation','Check history is visible']
      await self.check('Detail balances agree and history exists','accounts',detail)
      for value in ('','0','-1','abc','1.001'):
        async def negative(v=value):
          before=await self.snapshot(); await self.transfer(v); after=await self.snapshot()
          msg=await self.p.locator('body').inner_text()
          assert before==after and 'Transfer complete' not in msg, json.dumps({'input':v,'before':before,'after':after,'ui':msg})
          assert await self.p.locator('[role="alert"],.field__error').count()>0,'No clear validation feedback'
          return {'input':v,'unchanged':True},['Capture balances/history',f'Submit amount {v!r}','Check validation and unchanged balances/history']
        await self.check(f'Reject invalid amount {value!r} without side effects','transfer',negative)
      async def same():
        before=await self.snapshot(); await self.transfer('1.00',True); after=await self.snapshot()
        assert before==after,'Same-account transfer changed balances or history'
        assert 'Transfer complete' not in await self.p.locator('body').inner_text(),'Success shown for rejected transfer'
        return 'Same-account transfer rejected without mutations.',['Choose identical source/destination','Submit 1.00','Compare full balances/history']
      await self.check('Reject same-account transfer','transfer',same)
      async def valid():
        before=await self.snapshot(); source,dest=await self.transfer('1.23'); after=await self.snapshot()
        old={a['id']:Decimal(a['balance']) for a in before['accounts']}; new={a['id']:Decimal(a['balance']) for a in after['accounts']}
        assert new[source]==old[source]-Decimal('1.23') and new[dest]==old[dest]+Decimal('1.23'),str({'before':old,'after':new})
        fresh=[t for t in after['transactions'] if t['id'] not in {x['id'] for x in before['transactions']}]
        assert len(fresh)==1 and fresh[0]['status']=='completed' and fresh[0]['memo'].startswith(self.tag),str(fresh)
        tx=fresh[0]
        for account in (source,dest):
          await self.nav('/accounts/'+account); await expect(self.p.locator(f'[data-transaction-id="{tx["id"]}"]')).to_be_visible()
        await self.nav('/dashboard'); await self.p.reload(); await expect(self.p.get_by_test_id('account-card')).to_have_count(2)
        assert (await self.snapshot())==after,'Transfer state changed after refresh'
        return {'before':before['accounts'],'after':after['accounts'],'transaction':tx},['Submit 1.23 between different accounts with unique memo','Check both balance deltas and exactly one completed record','Find same transaction ID in both histories','Refresh and verify persistence']
      await self.check('Valid transfer conserves funds and persists in both histories','transfer',valid)
      async def insufficient():
        before=await self.snapshot(); amount=str(Decimal(before['accounts'][0]['balance'])+Decimal('1.00'))
        await self.transfer(amount); after=await self.snapshot(); msg=await self.p.locator('body').inner_text()
        assert before==after and 'Transfer complete' not in msg,json.dumps({'amount':amount,'before':before,'after':after,'success_shown':'Transfer complete' in msg})
        return 'Insufficient funds rejected without changes.',['Read source available balance','Submit balance + 1.00','Compare balances/history and success state']
      # This intentionally runs after valid transfer; every case uses a fresh observed baseline.
      await self.check('Reject insufficient funds without mutation or false success','transfer',insufficient)
      async def rows():
        await self.nav('/transactions'); await self.p.get_by_test_id('transaction-row').first.wait_for()
        return await self.p.get_by_test_id('transaction-row').all_inner_texts(),['Open combined transaction history','Capture rendered rows']
      await self.check('Combined history renders transaction rows','history',rows)
      for field,choice,label in [('Type','deposit','Deposit'),('Status','pending','Pending')]:
        async def filt(f=field,c=choice,l=label):
          await self.nav('/transactions'); await self.p.get_by_label(f,exact=True).select_option(c)
          async with self.p.expect_response(lambda r:'/api/transactions?' in r.url):
            await self.p.get_by_role('button',name='Apply filters',exact=True).click()
          await self.p.get_by_test_id('transaction-row').first.wait_for()
          vals=await self.p.locator(f'tbody td[data-label="{f}"]').all_inner_texts()
          assert vals and all(v==l for v in vals),str(vals)
          return vals,[f'Select {f}={c}','Apply filters','Verify every visible row matches']
        await self.check(f'History {field.lower()} filter','history',filt)
      async def combined():
        before=await self.snapshot(); account=before['accounts'][0]['id']
        expected=[t['id'] for t in before['transactions'] if t['type']=='deposit' and t['status']=='completed' and any(d['account_id']==account for d in t['account_deltas'])]
        await self.nav('/transactions'); await self.p.get_by_label('Account',exact=True).select_option(account)
        await self.p.get_by_label('Type',exact=True).select_option('deposit'); await self.p.get_by_label('Status',exact=True).select_option('completed')
        async with self.p.expect_response(lambda r:'/api/transactions?' in r.url):
          await self.p.get_by_role('button',name='Apply filters',exact=True).click()
        await self.p.get_by_test_id('transaction-row').first.wait_for()
        ids=await self.p.get_by_test_id('transaction-row').evaluate_all('(es)=>es.map(e=>e.dataset.transactionId)')
        assert set(ids)==set(expected),json.dumps({'expected':expected,'actual':ids})
        return {'expected':expected,'observed':ids},['Select discovered checking account, Deposit, Completed','Apply all three filters','Compare exact transaction IDs']
      await self.check('Combined account, type and status filters intersect correctly','history',combined)
      async def dates():
        await self.nav('/transactions'); await self.p.get_by_test_id('transaction-row').first.wait_for()
        times=await self.p.locator('tbody time').evaluate_all('(es)=>es.map(e=>e.dateTime)')
        date=datetime.fromisoformat(times[-1].replace('Z','+00:00')).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
        prior=await self.p.locator('tbody tr').evaluate_all('(es)=>es.map(e=>({id:e.dataset.transactionId,time:e.querySelector("time").dateTime}))')
        expected=[r['id'] for r in prior if datetime.fromisoformat(r['time'].replace('Z','+00:00')).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()==date]
        await self.p.get_by_label('Start date',exact=True).fill(date); await self.p.get_by_label('End date',exact=True).fill(date)
        async with self.p.expect_response(lambda r:'/api/transactions?' in r.url):
          await self.p.get_by_role('button',name='Apply filters',exact=True).click()
        await self.p.get_by_role('heading',name='Filtered results').wait_for(); await self.p.wait_for_function("()=>!document.body.innerText.includes('Loading transactions')")
        observed=await self.p.get_by_test_id('transaction-row').evaluate_all('(es)=>es.map(e=>e.dataset.transactionId)')
        assert set(observed)==set(expected),json.dumps({'boundary_date':date,'expected_ids':expected,'observed_ids':observed})
        return {'date':date,'ids':observed},['Observe an existing transaction date in Pacific Time','Set start=end to that date','Compare expected and displayed IDs for inclusive boundaries']
      await self.check('Date filter includes same-day start and end boundaries','history',dates)
      async def empty():
        await self.nav('/transactions'); await self.p.get_by_label('Start date',exact=True).fill('1900-01-01'); await self.p.get_by_label('End date',exact=True).fill('1900-01-02')
        await self.p.get_by_role('button',name='Apply filters',exact=True).click()
        await expect(self.p.get_by_role('heading',name='No transactions match these filters')).to_be_visible()
        return 'Clear empty-state message shown.',['Filter to 1900-01-01 through 1900-01-02','Observe empty-state heading']
      await self.check('Empty filter result displays useful empty state','history',empty)
      async def clear():
        await self.p.get_by_role('button',name='Clear filters',exact=True).first.click(); await self.p.get_by_test_id('transaction-row').first.wait_for()
        expected=len((await self.snapshot())['transactions']); actual=await self.p.get_by_test_id('transaction-row').count()
        assert expected==actual,str({'expected':expected,'actual':actual})
        return {'rows_restored':actual},['Clear filters','Compare visible row count with unfiltered read-only history']
      await self.check('Clear filters restores full history','history',clear)
      async def profile():
        await self.nav('/profile'); text=await self.p.locator('main').inner_text()
        assert re.search(r'[^\s]*\*+[^\s]*@',text),text
        assert not re.search(r'eyJ[A-Za-z0-9_-]{20,}',text),'Token-like string in profile'
        return text,['Open Profile','Check masked email and visible synthetic details; bounded token-pattern scan']
      await self.check('Profile masks synthetic email','profile',profile)
      async def narrow():
        await self.p.set_viewport_size({'width':390,'height':844}); await self.nav('/dashboard'); await self.p.get_by_test_id('account-card').first.wait_for()
        dims=await self.p.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        assert dims['scroll']<=dims['width']+1,str(dims)
        return dims,['Set viewport 390x844','Open dashboard','Check document-level horizontal overflow']
      await self.check('Narrow dashboard has no document overflow','interface',narrow)
      await self.p.set_viewport_size({'width':1280,'height':800})
      async def logout():
        await self.p.get_by_role('button',name='Log out',exact=True).click(); await expect(self.p.get_by_role('button',name='Enter Demo',exact=True)).to_be_visible()
        await self.nav('/dashboard'); await expect(self.p.get_by_role('button',name='Enter Demo',exact=True)).to_be_visible()
        await self.p.reload(); await expect(self.p.get_by_role('button',name='Enter Demo',exact=True)).to_be_visible()
        return 'Logout, direct protected-route navigation, and refresh deny access.',['Click Log out','Navigate directly to /dashboard','Refresh','Verify Enter Demo is required each time']
      await self.check('Logout protects dashboard even after refresh','session',logout)
      self.export()
      if self.a.demo:
        # 3-minute minimum recording includes genuine execution plus generated report review.
        await self.p.goto((self.out/'audit.html').as_uri())
        await asyncio.sleep(max(15,185-(time.time()-self.started)))
      await self.ctx.close(); await browser.close()
      self.export()
 def export(self):
    counts=Counter(r['verdict'] for r in self.results)
    # Exact assertions matter: candidate semantic mapping is NOT a claim of full coverage.
    coverage=[]
    for req in self.requirements:
      related=[r['id'] for r in self.results if req['id'] in r['candidate_requirements']]
      explicit = {
       'The landing page provides': ['Enter demo without credentials'],
       'Logging out returns': ['Logout protects dashboard even after refresh'],
       'Refreshing while in a valid': ['Session persistence after refresh','Logout protects dashboard even after refresh'],
       "The dashboard shows the customer's": ['Account cards and readable masked balances'],
       'Each account displays': ['Account cards and readable masked balances'],
       'The source and destination must': ['Reject same-account transfer'],
       'Amount must be a positive': [f'Reject invalid amount {v!r} without side effects' for v in ('','0','-1','abc','1.001')],
       'The amount must not exceed': ['Reject insufficient funds without mutation or false success'],
       'Refreshing after a successful': ['Valid transfer conserves funds and persists in both histories'],
       'The start and end dates': ['Date filter includes same-day start and end boundaries'],
       'An empty result set': ['Empty filter result displays useful empty state'],
       'Clearing filters restores': ['Clear filters restores full history'],
      }
      required = next((v for k,v in explicit.items() if req['text'].startswith(k)),[])
      checks=[r for r in self.results if r['name'] in required]
      status='unverified';reason='Not every clause was directly tested; candidate mapping is not full coverage.'
      if required and len(checks)==len(required):
       status='failed' if any(r['verdict']=='failed' for r in checks) else ('passed' if all(r['verdict']=='passed' for r in checks) else 'unverified')
       reason='Explicit assertion-to-requirement mapping; see linked evidence. Limited to this local run.'
      coverage.append({**req,'status':status,'reason':reason,'candidate_tests':related,'verified_by':[r['id'] for r in checks]})
    data={'project':'SpecLens','author':'Raashid Shaik','run_utc':datetime.now(timezone.utc).isoformat(),'target':self.a.url,'prd_sha256':hashlib.sha256(Path(self.a.prd).read_bytes()).hexdigest(),'planner':'local TF-IDF + cosine similarity; no LLM','runtime_seconds':round(time.time()-self.started,2),'scenario_counts':dict(counts),'environment':'Official target commit c7b856cc0d7cfb367e96fda0e5c291eba10cbb10, unchanged business logic; PGlite 0.5.10 PostgreSQL WASM, serialized connection pool; Chromium 141; localhost only','requirements':coverage,'scenarios':self.results,'cost':{'external_model_calls':0,'input_tokens':0,'output_tokens':0,'model_api_usd':0,'note':'Local CPU/browser/storage and development assistance excluded; zero inference API cost is not zero total cost.'}}
    (self.out/'results.json').write_text(json.dumps(data,indent=2))
    entries=[]
    for r in self.results:
      entries.append(f'<section><h2>{r["id"]} · {html.escape(r["name"])} <b class="{r["verdict"]}">{r["verdict"].upper()}</b></h2><p>Candidate PRD requirements: {", ".join(r["candidate_requirements"])}</p><pre>{html.escape(json.dumps(r["observed"],indent=2) if not isinstance(r["observed"],str) else r["observed"])}</pre><p>{html.escape(" → ".join(r["steps"]))}</p><a href="{r["id"]}.png">Screenshot</a> · <a href="{r["id"]}.txt">Visible text</a></section>')
    page='''<!doctype html><meta charset="utf-8"><title>SpecLens QA audit</title><style>body{font:16px system-ui;background:#f3f6fa;color:#17263c;max-width:1100px;margin:40px auto;padding:20px}section{background:white;padding:20px;margin:16px 0;border-radius:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px monospace}.passed{color:#187344}.failed{color:#b52828}.unverified{color:#8b6500}b{float:right}h1{font-size:40px}</style>'''
    page+=f'<h1>SpecLens · QA audit</h1><p>Raashid Shaik | Target: {html.escape(self.a.url)} | {data["run_utc"]}</p><h2>{counts["passed"]} passed · {counts["failed"]} failed · {counts["unverified"]} unverified scenarios</h2><p>Local NLP requirement routing. $0 model API inference. Evidence is from an unchanged local official target, not the hosted target. Candidate mappings do not imply complete PRD coverage.</p>'+''.join(entries)
    page+='<h2>PRD coverage</h2>'+''.join(f'<section><strong>{r["id"]} {r["status"].upper()}</strong><p>{html.escape(r["text"])}</p><p>Evidence tests: {", ".join(r["verified_by"]) or "Partial or no direct coverage"}</p></section>' for r in coverage)
    page+='<h2>Coverage limitations</h2><p>Requirements without complete direct assertion coverage remain unverified. Explicit mappings appear in results.json. Scenario results establish only the named assertions. No stress tests, real payments, failure injection, exhaustive accessibility, or hidden-state security audit.</p>'
    (self.out/'audit.html').write_text(page)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://localhost:5173');p.add_argument('--api',default='http://localhost:8000');p.add_argument('--prd',default='../test-website/PRD.md');p.add_argument('--output',default='artifacts');p.add_argument('--demo',action='store_true');p.add_argument('--allow-demo-target',action='store_true');a=p.parse_args()
 if not a.allow_demo_target: p.error('Pass --allow-demo-target only for the authorized synthetic DemoBank target.')
 for u in (a.url,a.api):
  if urlparse(u).scheme not in ('http','https'): p.error('HTTP(S) URLs required')
 asyncio.run(Agent(a).run())
