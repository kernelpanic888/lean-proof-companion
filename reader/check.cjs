const fs=require('fs'),vm=require('vm'),path=require('path');
const root=__dirname;
const context={};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'model.js'),'utf8'),context);
const data=JSON.parse(fs.readFileSync(path.join(root,'research/reader-data.json'),'utf8'));
const result=context.PC01Model.compareAll(data.oracle);
if(result.status!=='PASS'||result.checks!==106496)throw Error('differential failed');
for(const [mask,category] of [[-1,0],[8192,0],[0,13],[0,-1],[0.5,1]]){let rejected=false;try{context.PC01Model.transition(mask,category)}catch{rejected=true}if(!rejected)throw Error('range accepted');}
const page=fs.readFileSync(path.join(root,'dist/index.html'),'utf8');
const ids=[...page.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);if(new Set(ids).size!==ids.length)throw Error('duplicate HTML id');
for(const id of ['purpose','chat','pipeline','lab','scorecard','capsule','statuses','installation','model','evidence','passport','trust','reference'])if(!ids.includes(id))throw Error('missing chapter '+id);
for(const match of page.matchAll(/href="#([^"]+)"/g))if(!ids.includes(match[1]))throw Error('broken anchor '+match[1]);
if(/<script[^>]+src=|<link[^>]+(?:stylesheet|preload)|<iframe|XMLHttpRequest|WebSocket|https:\/\/fonts\./i.test(page))throw Error('external runtime');
for(const raw of page.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){
 if(raw[0].includes('type="application/json"'))continue;
 new vm.Script(raw[1]);
}
if(page.includes('/Users/')||page.includes('art_v2_')||page.includes('�'))throw Error('private path/token/encoding damage');
fs.writeFileSync(path.join(root,'research/differential.json'),JSON.stringify({...result,range_rejections:5,html_anchors:'PASS',external_runtime:'NONE'},null,2)+'\n');
console.log(JSON.stringify(result));

const publicPage=fs.readFileSync(path.join(root,'dist/public-reader.html'),'utf8');
if(/\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(|<meta name="lpc-session"/i.test(publicPage))throw Error('public reader must not connect to local service or contain a session');
