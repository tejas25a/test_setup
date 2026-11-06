/* ---------- Backend hook ----------
   Set API to your endpoint, e.g. "https://your-server.com/api/trends".
   Request:  GET API?metric=temp|rain&type=annual|monthly&year=2025&month=3   (month 1-12, monthly only)
   Response: JSON { "Delhi": 0.9, "Mumbai": 0.6, ... }  one number per region name below.
   While API is empty, illustrative demo values are generated locally. */
const API="";
async function getData(metric,type,year,month){
  if(API){const q=new URLSearchParams({metric,type,year,...(type==="monthly"?{month}:{})});
    const r=await fetch(API+"?"+q);if(!r.ok)throw 0;const j=await r.json();return R.map(x=>+j[x[0]])}
  const f=(year-1990)/35,o={};
  return R.map((x,i)=>{const b=metric==="temp"?x[3]:x[4];let s=1;
    if(type==="monthly")s=metric==="temp"?1+.3*Math.cos(2*Math.PI*(month-1.5)/12):(month>=6&&month<=9?1.5:.6);
    const n=Math.sin((i+1)*12.9898+year*78.233+(month||0)*37.7)*43758.5453,e=n-Math.floor(n)-.5;
    return b*f*s+e*(metric==="temp"?.15:2.5)})}

const R=[
["Srinagar",74.8,34.1,1.1,-6],["Delhi",77.2,28.6,.9,-4],["Jaipur",75.8,26.9,.8,3],["Lucknow",80.9,26.8,.9,-5],
["Guwahati",91.7,26.1,.8,-9],["Ahmedabad",72.6,23.0,.7,8],["Kolkata",88.4,22.6,.6,-2],["Nagpur",79.1,21.1,.8,-1],
["Bhubaneswar",85.8,20.3,.7,-3],["Mumbai",72.9,19.1,.6,5],["Hyderabad",78.5,17.4,.7,3],["Chennai",80.3,13.1,.6,4],
["Bengaluru",77.6,13.0,.7,2],["Kochi",76.3,10.0,.5,-7]];
const OUT=[[74.6,36.9],[76.8,35.6],[79,34.3],[78.9,32.5],[80.2,30.8],[81,30.2],[80.1,28.8],[82,27.8],[84.1,27.4],[88.1,26.5],[88.2,27.9],[88.9,27.3],[89.8,26.7],[92,26.9],[94,27.6],[96.1,29],[97.3,28.2],[96,27.2],[95.2,26],[94.6,24],[93.4,22.9],[92.4,23.2],[92.3,24.1],[92,25.1],[90.5,25.1],[89.8,25.3],[89,26.2],[88.5,25.2],[88.9,24.2],[88.6,23.2],[89,22.2],[88.1,21.6],[87,21.5],[86.4,20.2],[85,19.3],[84,18.3],[82.3,16.6],[80.9,15.7],[80.2,13.5],[80.3,12.3],[79.8,10.3],[78.9,9.3],[77.5,8.1],[76.5,8.8],[75.5,11.8],[74.8,13],[73.8,15.5],[72.8,19],[72.8,21],[72,21.1],[70.2,20.8],[69,22.3],[70,22.9],[68.2,23.7],[68.8,24.3],[70,24.2],[71,24.5],[70.5,25.7],[69.5,26.7],[70.3,28],[71.9,27.9],[73,29.9],[74.5,31],[74.6,32.4],[74.3,34],[73.5,35]];
const key=(p,q)=>OUT.findIndex(z=>z[0]===p&&z[1]===q);
const LAND=[[60,40],[102,40],[102,14],[98.5,15.6],[97.6,16.6],[95.4,15.8],[94.3,16],[94.4,18.8],[93,20.3],[92.3,21.4],[91.6,22.5],[90.5,22],[89.2,21.8],...OUT.slice(key(89,22.2),key(68.2,23.7)+1),[67.2,24.7],[66.5,25.4],[64.5,25.2],[62.3,25.2],[60,25.3]];
const LANKA=[[80.1,9.8],[80.9,9.3],[81.8,7.6],[81.6,6.5],[80.6,5.9],[79.9,6.9],[79.8,8.5]];
const S=12,X=l=>(l-60)*S,Y=a=>(40-a)*S;
const inside=(P,x,y)=>{let c=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const[a,b]=P[i],[p,q]=P[j];if((b>y)!=(q>y)&&x<(p-a)*(y-b)/(q-b)+a)c=!c}return c};
const M={t:{n:"Temperature",k:"temp",f:v=>(v>=0?"+":"")+v.toFixed(1)+"°C",cap:"warming vs 1990 baseline",div:0},
         r:{n:"Rainfall",k:"rain",f:v=>(v>=0?"+":"")+Math.round(v)+"%",cap:"rainfall change vs 1990 baseline",div:1}};
const P={annual:"Annual",monthly:"Monthly"},MN=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
let m="t",type="annual",year=2025,month=new Date().getMonth()+1,sel=null,vs=R.map(()=>0),tok=0;
const svg=document.getElementById("svg"),NS="http://www.w3.org/2000/svg",$=id=>document.getElementById(id);
const el=(n,a,par)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);(par||svg).appendChild(e);return e};
const dots=[];
for(let la=40;la>=4;la-=.5)for(let lo=60;lo<=102;lo+=.5){
  if(inside(OUT,lo,la))dots.push({lo,la,e:el("circle",{cx:X(lo),cy:Y(la),r:2.4,class:"dot"})});
  else if(inside(LAND,lo,la)||inside(LANKA,lo,la))el("circle",{cx:X(lo),cy:Y(la),r:1.7,class:"ctx"})}
el("polygon",{points:OUT.map(p=>X(p[0])+","+Y(p[1])).join(" "),class:"edge"});
const pins=R.map((r,i)=>{const g=el("g",{class:"pin",tabindex:0,role:"button","aria-label":r[0]});
 el("circle",{class:"hit",cx:X(r[1]),cy:Y(r[2]),r:12},g);el("circle",{class:"c",cx:X(r[1]),cy:Y(r[2]),r:4},g);
 el("text",{x:X(r[1])+9,y:Y(r[2])+4},g).textContent=r[0];
 g.onclick=()=>pick(i);g.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();pick(i)}};return g});
function color(v,lo,hi){
 if(M[m].div){const a=Math.min(1,Math.abs(v)/Math.max(Math.abs(lo),Math.abs(hi),1e-6));const dk=matchMedia("(prefers-color-scheme:dark)").matches;
  return `hsl(${v<0?28:205} ${25+55*a}% ${dk?(28+30*a):(88-42*a)}%)`}
 const a=(v-lo)/((hi-lo)||1);return `hsl(${50-44*a} ${60+25*a}% ${84-36*a}%)`}
function paint(){
 const lo=Math.min(...vs),hi=Math.max(...vs),f=M[m].f;
 dots.forEach(d=>{let n=0,w=0;R.forEach((r,i)=>{const q=Math.hypot(d.lo-r[1],(d.la-r[2])*1.05)+.4,k=1/Math.pow(q,2.5);n+=vs[i]*k;w+=k});d.e.style.fill=color(n/w,lo,hi)});
 $("lo").textContent=f(lo);$("hi").textContent=f(hi);
 $("bar").style.background=`linear-gradient(90deg,${[0,.5,1].map(t=>color(lo+(hi-lo)*t,lo,hi)).join(",")})`;
 summary()}
function label(){return type==="monthly"?MN[month-1]+" "+year:String(year)}
function summary(){
 const f=M[m].f,avg=vs.reduce((a,b)=>a+b)/vs.length,order=vs.map((v,i)=>i).sort((a,b)=>vs[b]-vs[a]);
 pins.forEach((g,i)=>g.classList.toggle("on",i===sel));
 $("reset").style.visibility=sel===null?"hidden":"visible";
 $("k").textContent=M[m].n+" · "+label();
 if(sel===null){$("t").textContent="All India";$("v").textContent=f(avg);$("c").textContent="average · "+M[m].cap}
 else{const r=R[sel],d=vs[sel]-avg;$("t").textContent=r[0];$("v").textContent=f(vs[sel]);
  $("c").textContent=`${M[m].cap} · #${order.indexOf(sel)+1} of ${R.length}, ${d>=0?"above":"below"} the national average`}
 const list=(h,ix)=>`<h4>${h}</h4>`+ix.map(i=>`<div class="row" data-i="${i}"><span>${R[i][0]}</span><b>${f(vs[i])}</b></div>`).join("");
 $("top").innerHTML=list("Highest",order.slice(0,3));$("low").innerHTML=list("Lowest",order.slice(-3).reverse());
 document.querySelectorAll(".row").forEach(r=>r.onclick=()=>pick(+r.dataset.i))}
function pick(i){sel=sel===i?null:i;summary()}
async function load(){
 const t=++tok;$("mapbox").classList.add("load");
 try{const d=await getData(M[m].k,type,year,month);if(t!==tok)return;vs=d.map(Number)}catch(e){if(t!==tok)return}
 $("mapbox").classList.remove("load");paint()}
function ui(){
 const seg=(id,o,cur,set)=>{const c=$(id);c.innerHTML="";for(const k in o){const b=document.createElement("button");b.textContent=o[k].n||o[k];b.className=k===cur?"on":"";b.onclick=()=>{set(k);ui();load()};c.appendChild(b)}};
 seg("m",M,m,k=>m=k);seg("p",P,type,k=>type=k);
 $("mo").style.display=type==="monthly"?"":"none";
}
$("mo").innerHTML=MN.map((n,i)=>`<option value="${i+1}">${n}</option>`).join("");
$("yr").innerHTML=Array.from({length:35},(_,i)=>2025-i).map(y=>`<option>${y}</option>`).join("");
$("mo").value=month;$("yr").value=year;
$("mo").onchange=e=>{month=+e.target.value;load()};$("yr").onchange=e=>{year=+e.target.value;load()};
$("reset").onclick=()=>{sel=null;summary()};
ui();load();