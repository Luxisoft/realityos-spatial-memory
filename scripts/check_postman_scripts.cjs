const fs=require('node:fs'); const vm=require('node:vm');const assert=require('node:assert/strict');
const c=JSON.parse(fs.readFileSync('docs/postman/RealityOS.postman_collection.json'));
const all=c.item.flatMap(f=>f.item);
function execute(item,listen,values={},code=200,body={}) {
 let skipped=false;const environment={...values};const failures=[];
 const pm={environment:{get:k=>environment[k],set:(k,v)=>environment[k]=v},execution:{skipRequest:()=>{skipped=true;}},response:{code,json:()=>body},test:(name,fn)=>{try{fn();}catch(e){failures.push(name);}},expect:v=>({to:{be:{below:n=>assert(v<n)},eql:n=>assert.equal(v,n)}})};
 for(const e of item.event||[])if(e.listen===listen)vm.runInNewContext(e.script.exec.join('\n'),{pm,console:{warn:()=>{}}});
 return {environment,skipped,failures};
}
let guards=0;
for(const i of all){
 for(const e of i.event||[])new vm.Script(e.script.exec.join('\n'));
 if(JSON.stringify(i.event).includes('enable_write_requests')){
  assert(execute(i,'prerequest').skipped);assert(!execute(i,'prerequest',{enable_write_requests:'true'}).skipped);guards++;
 }
 if(/POST \/v1\/auth\/(login|refresh|local-login)$/.test(i.name)){
  const ok=execute(i,'test',{},200,{access_token:'test-access',refresh_token:'test-refresh'});
  assert.equal(ok.environment.access_token,'test-access');assert.equal(ok.environment.refresh_token,'test-refresh');assert.equal(ok.failures.length,0);
  const fail=execute(i,'test',{access_token:'previous'},401,{});assert.equal(fail.environment.access_token,'previous');assert(fail.failures.length);
 }
}
const q=c.item[0].item.at(-1);assert.throws(()=>execute(q,'prerequest'),/workspace_id/);assert(!execute(q,'prerequest',{workspace_id:'test-workspace'}).skipped);
console.log(`PASS: ${all.length} request scripts parsed; ${guards} write guards; login/refresh success and failure; explicit workspace selection. No HTTP requests.`);
