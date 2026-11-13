import { chromium } from 'playwright';
const sites = ['https://gba.karnataka.gov.in/home','https://bbmptax.karnataka.gov.in/','https://bwssb.karnataka.gov.in/','https://bswml.karnataka.gov.in/','https://sakala.kar.nic.in/','https://www.ghmc.gov.in/','https://igs.ghmc.gov.in/','https://www.ghmc.gov.in/PropertyTax.aspx','https://www.hyderabadwater.gov.in/en/','https://ts.meeseva.telangana.gov.in/meeseva/home.htm'];
const KW=/complaint|grievance|sahaaya|property.?tax|birth|death|certificate|sanitation|garbage|waste|swm|ration|track|status|health|hospital|clinic|tanker|bill|payment|mycure|whatsapp|app\b/i;
const b=await chromium.launch({channel:'chrome',headless:true});
for(const s of sites){const p=await (await b.newContext()).newPage();try{await p.goto(s,{waitUntil:'domcontentloaded',timeout:45000});await p.waitForTimeout(3000);
const l=await p.evaluate(()=>[...document.querySelectorAll('a[href]')].map(a=>[(a.textContent||'').trim().replace(/\s+/g,' ').slice(0,60),a.href]));
const seen=new Set();console.log('##',s);for(const [t,h] of l){if((KW.test(t)||KW.test(h))&&!seen.has(h)&&!h.startsWith('javascript')){seen.add(h);console.log('  ',t,'|',h.slice(0,110));if(seen.size>14)break}}}catch(e){console.log('##',s,'ERR',String(e.message).slice(0,80))}await p.close()}
await b.close();
