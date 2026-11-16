import test from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../src/api.ts';

test('DELETE accepts an empty HTTP 204 response',async()=>{
 const original=globalThis.fetch;
 let request;
 globalThis.fetch=async(url,options)=>{request={url,options};return new Response(null,{status:204})};
 try{assert.equal(await api('/students/example','DELETE'),undefined);assert.equal(request.options.method,'DELETE');assert.equal(request.url,'/api/students/example')}finally{globalThis.fetch=original}
});
test('failed deletion reports an error instead of success',async()=>{
 const original=globalThis.fetch;
 globalThis.fetch=async()=>new Response(JSON.stringify({detail:'failed'}),{status:500});
 try{await assert.rejects(()=>api('/students/example','DELETE'),/Сервис временно недоступен/)}finally{globalThis.fetch=original}
});
