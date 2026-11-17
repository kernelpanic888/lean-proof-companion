/* PC-01 finite scorecard implementation. Reference rows are exported by Lean. */
(function(root){
  'use strict';
  function transition(mask,category){
    if(!Number.isInteger(mask)||mask<0||mask>=8192||!Number.isInteger(category)||category<0||category>=13) throw new RangeError('scorecard range');
    return (mask & (1<<category))!==0 ? null : mask | (1<<category);
  }
  function compareAll(oracle){
    if(!Array.isArray(oracle)||oracle.length!==8192) throw new Error('Lean oracle must contain 8192 states');
    let checks=0;
    for(let mask=0;mask<8192;mask++){
      const row=oracle[mask];
      if(!Array.isArray(row)||row.length!==13) throw new Error('Lean oracle row length');
      for(let category=0;category<13;category++){
        const actual=transition(mask,category),expected=row[category];
        if(actual!==expected) throw new Error('Mismatch at '+mask+'/'+category+': '+actual+' != '+expected);
        checks++;
      }
    }
    return {status:'PASS',states:8192,categories:13,checks};
  }
  root.PC01Model=Object.freeze({transition,compareAll});
})(globalThis);
