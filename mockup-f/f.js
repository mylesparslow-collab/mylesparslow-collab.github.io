(function(){
  var b=document.body;
  document.addEventListener('keydown',function(e){
    var t=e.target;
    if(e.key==='Escape'&&b.dataset.home&&!(t.closest&&t.closest('input,textarea,select,video')))location.href=b.dataset.home;
  });
  Array.prototype.forEach.call(document.querySelectorAll('.compare'),function(c){
    var r=c.querySelector('input');if(!r)return;
    var s=function(){c.style.setProperty('--pos',r.value+'%')};
    r.addEventListener('input',s);s();
  });
  var w=document.getElementById('weight');
  if(w){
    var t=0,g=function(e){return e.transferSize||e.encodedBodySize||0};
    performance.getEntriesByType('resource').forEach(function(e){t+=g(e)});
    var n=performance.getEntriesByType('navigation')[0];if(n)t+=g(n);
    var k=t>0?Math.max(1,Math.round(t/1024))+' KB':'under 60 KB';
    w.firstChild.nodeValue='This page: '+k+' · 0 trackers · 0 frameworks · last updated '+w.dataset.u+'.';
  }
})();
