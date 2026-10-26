"""Write an offline human review tool; pending teacher labels are never auto-accepted."""
import json


def write_review(directory,records,limit):
    buckets={}
    for r in records:buckets.setdefault((r['split'],r['kind']),[]).append(r)
    for items in buckets.values():items.sort(key=lambda r:r['sample_id'])
    selected=[]
    while any(buckets.values()) and len(selected)<limit:
        for key in sorted(buckets):
            if buckets[key] and len(selected)<limit:selected.append(buckets[key].pop(0))
    (directory/'queue.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')
    data=json.dumps(selected,ensure_ascii=False).replace('</','<\\/')
    html=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>关键点人工复核</title>
<style>
body{font:16px system-ui;margin:24px;color:#18222f;background:#f4f6f9}h1{font-size:24px}
.grid{display:flex;gap:24px;flex-wrap:wrap}.card{background:white;padding:18px;border-radius:10px}
canvas{width:512px;height:512px;max-width:100%;background:#111;cursor:crosshair}img{max-width:480px;max-height:360px}
button,select,input{font:inherit;padding:7px;margin:5px}button{cursor:pointer}#meta{max-width:1000px;overflow-wrap:anywhere}
#notice{color:#9c3c00;font-weight:600}label{display:block;margin:8px 0}.toolbar{margin:12px 0}
</style><h1>关键点人工复核 · 本地工具</h1>
<p>教师点只是初始建议。逐点检查并修正可见点；遮挡点取消可见。未知区域须先判断有无手。
未保存的帧不进入人工标签；导出的 JSONL 需作为训练参数 --reviews 显式导入。</p>
<div class="toolbar"><button id="prev">上一帧</button><button id="next">下一帧</button>
<button id="download">导出已复核 JSONL</button><input type="file" id="import" accept=".jsonl,.json">
<span id="count"></span></div><p id="meta"></p>
<div class="grid"><div class="card"><canvas id="canvas" width="512" height="512"></canvas>
<p>先选点号，再点画面修正；可点击已有点切换选中点。</p>
<select id="point"></select><label><input type="checkbox" id="visible">所选点可见</label></div>
<div class="card"><img id="context" alt="原始帧上下文"><p id="source"></p>
<label>复核者 <input id="reviewer" placeholder="姓名或稳定标识"></label>
<label>有无手 <select id="presence"><option value="">待判断</option><option value="1">有手</option><option value="0">无手</option></select></label>
<label>解剖学侧别 <select id="handedness"><option value="">未核实</option><option value="0">左手</option><option value="1">右手</option></select></label>
<label>场景 <select id="scenario"><option value="general">一般动作</option><option value="static">静止</option>
<option value="fast_motion">快速运动</option><option value="crossing">交叉</option><option value="occlusion">遮挡/恢复</option></select></label>
<label><input type="checkbox" id="presenceOnly">只审核有无手，不提交关键点真值</label>
<label><input type="checkbox" id="checked">我已核对本帧，不是自动批准教师输出</label>
<button id="save">保存此帧复核</button><p id="notice"></p>
</div></div><script>
const queue=__DATA__,saved=new Map(),$=id=>document.getElementById(id);
let index=0,points=[],visible=[],active=0,bitmap=new Image();
const edges=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
for(let i=0;i<21;i++)$('point').add(new Option(i===0?'0 腕点':String(i),String(i)));
function draw(){const c=$('canvas').getContext('2d');c.clearRect(0,0,512,512);c.drawImage(bitmap,0,0,512,512);
 c.lineWidth=2;c.strokeStyle='#36e09a';for(const [a,b] of edges)if(points[a]&&points[b]&&visible[a]&&visible[b]){
 c.beginPath();c.moveTo(points[a][0]*511,points[a][1]*511);c.lineTo(points[b][0]*511,points[b][1]*511);c.stroke();}
 points.forEach((p,i)=>{if(!p||!visible[i])return;c.fillStyle=i===active?'#ffb000':'#22dd88';c.beginPath();c.arc(p[0]*511,p[1]*511,i===active?6:4,0,Math.PI*2);c.fill();c.fillStyle='white';c.fillText(String(i),p[0]*511+5,p[1]*511-5);});}
function show(){if(!queue.length){$('notice').textContent='复核队列为空';return;}
 const r=queue[index],s=saved.get(r.sample_id);points=structuredClone(s?.landmarks_xy??r.initial_xy??Array(21).fill(null));
 visible=s?.visible?.slice()??points.map(p=>p!==null);active=0;$('point').value='0';$('visible').checked=visible[0];
 $('presence').value=s?String(Number(s.presence)):(r.kind==='teacher_positive'?'1':'');
 $('handedness').value=s?.handedness===null||s?.handedness===undefined?'':String(s.handedness);
 $('scenario').value=s?.scenario??'general';$('presenceOnly').checked=!!s&&s.landmarks_xy===null&&s.presence;
 $('checked').checked=!!s;if(s?.reviewer)$('reviewer').value=s.reviewer;
 $('meta').textContent=`${index+1}/${queue.length} | ${r.sample_id} | ${r.split} | ${r.split_group} | ${r.kind}`;
 $('source').textContent=`源帧 ${r.source_frame}, 时间 ${r.source_timestamp_s.toFixed(3)}s。框仅是候选，不是人工真值。`;
 $('context').src=r.context;bitmap=new Image();bitmap.onload=draw;bitmap.src=r.image;
 $('count').textContent=`已保存 ${saved.size} 帧`;$('notice').textContent='';}
$('point').onchange=()=>{active=Number($('point').value);$('visible').checked=visible[active];draw();};
$('visible').onchange=()=>{visible[active]=$('visible').checked;if(visible[active]&&!points[active])visible[active]=false;draw();};
$('canvas').onclick=e=>{const box=$('canvas').getBoundingClientRect(),p=[Math.max(0,Math.min(1,(e.clientX-box.left)/box.width*512/511)),Math.max(0,Math.min(1,(e.clientY-box.top)/box.height*512/511))];
 let nearest=-1,dist=.025;points.forEach((q,i)=>{if(q&&visible[i]){let d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<dist){nearest=i;dist=d;}}});
 if(nearest>=0&&nearest!==active){active=nearest;$('point').value=String(active);}else{points[active]=p;visible[active]=true;}
 $('visible').checked=visible[active];draw();};
$('prev').onclick=()=>{index=(index+queue.length-1)%queue.length;show();};$('next').onclick=()=>{index=(index+1)%queue.length;show();};
$('save').onclick=()=>{const reviewer=$('reviewer').value.trim(),value=$('presence').value,presence=value==='1',only=$('presenceOnly').checked;
 if(!reviewer||value===''||!$('checked').checked){$('notice').textContent='请填写复核者、判断有无手并确认已核对。';return;}
 if(presence&&!only&&visible.filter(Boolean).length<2){$('notice').textContent='关键点真值至少需要两个可见点，或选择只审核有无手。';return;}
 saved.set(queue[index].sample_id,{sample_id:queue[index].sample_id,status:'accepted',annotation_origin:'human',human_verified:true,reviewer,presence,
 handedness:presence&&$('handedness').value!==''?Number($('handedness').value):null,scenario:$('scenario').value,
 landmarks_xy:presence&&!only?points.map((p,i)=>visible[i]?p:null):null,visible:presence&&!only?visible.slice():Array(21).fill(false)});
 $('notice').textContent='此帧已存到内存；离开前请导出 JSONL。';$('count').textContent=`已保存 ${saved.size} 帧`;};
$('download').onclick=()=>{if(!saved.size){$('notice').textContent='还没有已复核帧';return;}const blob=new Blob([[...saved.values()].map(v=>JSON.stringify(v)).join('\n')+'\n'],{type:'application/x-ndjson'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='hand_review_annotations.jsonl';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('import').onchange=async e=>{try{const ids=new Set(queue.map(r=>r.sample_id));for(const line of (await e.target.files[0].text()).split(/\r?\n/)){if(!line.trim())continue;const r=JSON.parse(line);if(!ids.has(r.sample_id)||r.status!=='accepted')throw Error('ID 或状态不匹配');saved.set(r.sample_id,r);}show();}catch(error){$('notice').textContent=String(error);}};
show();
</script></html>'''.replace('__DATA__',data)
    (directory/'index.html').write_text(html,encoding='utf-8')
    return len(selected)
