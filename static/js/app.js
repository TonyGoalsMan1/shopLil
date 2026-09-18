// Cart logic — FIXED with credentials + premium toasts
let cartCount = 0, cartTotal = 0;
async function updateCartBadge(){
  try{
    const r = await fetch('/api/cart', {credentials:'same-origin'});
    const d = await r.json();
    cartCount = d.count; cartTotal = d.total;
    document.querySelectorAll('.cart-count').forEach(el=>el.textContent=cartCount);
    document.querySelectorAll('.cart-total').forEach(el=>el.textContent='€'+cartTotal+'.00');
    const dot = document.getElementById('cartDot');
    if(dot) dot.style.display = cartCount>0 ? 'block' : 'none';
  }catch(e){ console.log('badge err',e); }
}
async function addToCart(id, btn){
  const orig = btn ? btn.innerHTML : '';
  if(btn){ btn.innerHTML='Adding…'; btn.disabled=true; }
  try{
    const r = await fetch('/api/cart/add',{method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify({id})});
    const d = await r.json();
    if(!d.ok) throw new Error(d.error||'error');
    cartCount=d.count; cartTotal=d.total;
    await updateCartBadge();
    // premium animation
    if(btn){
      btn.innerHTML='✓ Added';
      btn.style.background='linear-gradient(135deg,#0f0f0f,#2a2a2a)';
      btn.style.color='#fff';
      showToast('Добавлено в корзину 🩷 — <a href="/cart" style="color:#fff; text-decoration:underline;">Открыть корзину</a>', true);
      confettiBurst(btn);
      setTimeout(()=>{ btn.innerHTML=orig; btn.disabled=false; btn.style.background=''; btn.style.color=''; }, 1400);
    } else {
      showToast('Добавлено в корзину 🩷');
    }
  }catch(e){
    showToast('Ошибка: '+e.message);
    if(btn){ btn.innerHTML=orig; btn.disabled=false; }
  }
}
async function removeFromCart(id){
  await fetch('/api/cart/remove',{method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify({id})});
  location.reload();
}
async function clearCart(){
  await fetch('/api/cart/clear',{method:'POST', credentials:'same-origin'});
  location.reload();
}
function showToast(msg, isHtml=false){
  let t=document.getElementById('toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; t.className='toast'; document.body.appendChild(t); }
  if(isHtml) t.innerHTML=msg; else t.textContent=msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'), 3200);
}
function confettiBurst(el){
  const rect = el.getBoundingClientRect();
  for(let i=0;i<14;i++){
    const c=document.createElement('div');
    c.className='confetti';
    c.style.left=(rect.left+rect.width/2)+'px';
    c.style.top=(rect.top)+'px';
    c.style.background=['#e85a7a','#ffb3c6','#ffd700','#7b61ff','#00d4ff'][i%5];
    document.body.appendChild(c);
    const dx=(Math.random()-0.5)*220, dy= - (Math.random()*120+40);
    c.animate([{transform:'translate(0,0) scale(1)', opacity:1},{transform:`translate(${dx}px, ${dy+180}px) scale(0.7) rotate(${Math.random()*720}deg)`, opacity:0}],{duration:900+Math.random()*400, easing:'cubic-bezier(0.25,1,0.5,1)'}).onfinish=()=>c.remove();
  }
}
// Filters — FIXED to support gift-card
function filterShop(cat){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  document.querySelector(`[data-filter="${cat}"]`)?.classList.add('active');
  document.querySelectorAll('.gift-card, .card').forEach(c=>{
    const dc = c.dataset.cat || 'all';
    if(cat==='all' || dc===cat) c.style.display='';
    else c.style.display='none';
  });
}
// 3D tilt premium
document.addEventListener('mousemove', e=>{
  document.querySelectorAll('.gift-card, .feature, .about-card').forEach(card=>{
    const rect=card.getBoundingClientRect();
    if(e.clientX<rect.left || e.clientX>rect.right || e.clientY<rect.top || e.clientY>rect.bottom) {
      card.style.transform=''; return;
    }
    const x = (e.clientX - rect.left)/rect.width - 0.5;
    const y = (e.clientY - rect.top)/rect.height - 0.5;
    card.style.transform = `perspective(900px) rotateY(${x*7}deg) rotateX(${-y*7}deg) translateZ(12px)`;
  });
});
async function subscribe(e){
  e.preventDefault();
  const email=e.target.querySelector('input[type="email"]').value;
  const r=await fetch('/api/subscribe',{method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify({email})});
  const d=await r.json();
  if(d.ok) showToast('Подписка оформлена! Добро пожаловать в LYLILI 💌');
  else showToast(d.error||'Ошибка');
  e.target.reset();
}
// --- AI CHAT ---
let chatOpen=false;
function toggleChat(){
  chatOpen=!chatOpen;
  document.getElementById('chatWidget').classList.toggle('open', chatOpen);
  if(chatOpen) document.getElementById('chatInput').focus();
}
async function sendChat(e){
  e.preventDefault();
  const input=document.getElementById('chatInput');
  const msg=input.value.trim();
  if(!msg) return;
  const box=document.getElementById('chatMessages');
  box.innerHTML+=`<div class="chat-msg user">${escapeHtml(msg)}</div>`;
  input.value='';
  box.scrollTop=box.scrollHeight;
  box.innerHTML+=`<div class="chat-msg bot typing">LYLILI печатает…</div>`;
  box.scrollTop=box.scrollHeight;
  try{
    const r=await fetch('/api/chat',{method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify({message:msg})});
    const d=await r.json();
    document.querySelector('.typing')?.remove();
    let reply = d.reply||d.error||'Ошибка';
    // информативно: сохраняем переносы и показываем код
    let html = escapeHtml(reply).replace(/\n/g,'<br>');
    // подсветка diff/code блоков
    html = html.replace(/```([\s\S]*?)```/g,'<pre style="background:#0f0f0f; color:#00ffa3; padding:8px; border-radius:8px; overflow:auto; font-family:JetBrains Mono; font-size:11px; margin:6px 0">$1</pre>');
    html = html.replace(/`([^`]+)`/g,'<code style="background:#f0e6e0; padding:2px 5px; border-radius:4px; font-family:JetBrains Mono; font-size:11px">$1</code>');
    box.innerHTML+=`<div class="chat-msg bot" style="white-space:normal; word-break:break-word; max-width:88%">${html}</div>`;
    // также покажи конкретные изменения в трекинге если есть
    if(reply.includes('Конкретные изменения') || msg.toLowerCase().includes('исправил') || msg.toLowerCase().includes('протестировал')){
      try{
        const cr=await fetch('/api/changes', {cache:'no-store'}); const ch=await cr.json();
        let extra='<div style="margin-top:8px; padding:8px; background:#fff; border:1px solid #e8e0de; border-radius:10px; font-size:11px"><b>📋 Последние коммиты:</b><br>';
        ch.slice(0,3).forEach(c=>{
          extra+=`<div style="margin:4px 0; padding:6px; background:#f7f5f4; border-radius:8px"><b>${escapeHtml(c.title)}</b> <span style="opacity:0.6; font-size:10px">${escapeHtml(c.where)} · ${escapeHtml(c.when)}</span><br><code style="font-size:10px; color:#0f0f0f">${escapeHtml(c.diff.slice(0,140))}</code></div>`;
        });
        extra+='</div>';
        box.innerHTML+=`<div class="chat-msg bot" style="background:#fff; border:1px dashed #d4af37">${extra}</div>`;
      }catch(e){}
    }
  }catch(err){
    document.querySelector('.typing')?.remove();
    box.innerHTML+=`<div class="chat-msg bot">Ошибка сети, попробуй еще раз.</div>`;
  }
  box.scrollTop=box.scrollHeight;
}
function escapeHtml(s){ return s.replace(/[&<>"]/g,c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
// quick chips
function chatChip(t){ document.getElementById('chatInput').value=t; document.getElementById('chatForm').dispatchEvent(new Event('submit')); }

// Three.js 3D background
(function(){
  const canvas=document.getElementById('canvas3d');
  if(!canvas || !window.THREE) return;
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(60, canvas.clientWidth/canvas.clientHeight, 0.1, 100);
  camera.position.z=8;
  const renderer=new THREE.WebGLRenderer({canvas, alpha:true, antialias:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  function resize(){
    const w=canvas.parentElement.clientWidth, h=canvas.parentElement.clientHeight;
    renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize); resize();
  scene.add(new THREE.AmbientLight(0xffffff, 0.9));
  const dir=new THREE.DirectionalLight(0xffb3c6, 0.8); dir.position.set(5,5,5); scene.add(dir);
  const geo1=new THREE.TorusGeometry(0.6,0.18,16,32);
  const geo2=new THREE.SphereGeometry(0.35,24,24);
  const geo3=new THREE.BoxGeometry(0.7,0.7,0.12);
  const matPink=new THREE.MeshStandardMaterial({color:0xe85a7a, roughness:0.4, metalness:0.1});
  const matLight=new THREE.MeshStandardMaterial({color:0xffd6e7, roughness:0.3});
  const matCream=new THREE.MeshStandardMaterial({color:0xfff2cc, roughness:0.4});
  const meshes=[];
  for(let i=0;i<12;i++){
    const g=[geo1,geo2,geo3][i%3];
    const m=[matPink,matLight,matCream][i%3];
    const mesh=new THREE.Mesh(g,m);
    mesh.position.set((Math.random()-0.5)*12, (Math.random()-0.5)*6, (Math.random()-0.5)*4 -1);
    mesh.rotation.set(Math.random()*Math.PI, Math.random()*Math.PI,0);
    mesh.userData={vx:(Math.random()-0.5)*0.008, vy:(Math.random()-0.5)*0.006, rz:(Math.random()-0.5)*0.012};
    scene.add(mesh); meshes.push(mesh);
  }
  let t=0;
  function animate(){
    requestAnimationFrame(animate);
    t+=0.01;
    meshes.forEach((m,i)=>{
      m.rotation.y+=m.userData.rz;
      m.rotation.x+=0.003;
      m.position.y+=Math.sin(t+i)*0.002;
      m.position.x+=m.userData.vx;
      if(Math.abs(m.position.x)>6) m.userData.vx*=-1;
    });
    camera.position.x=Math.sin(t*0.3)*0.6;
    camera.lookAt(0,0,0);
    renderer.render(scene,camera);
  }
  animate();
})();
updateCartBadge();
