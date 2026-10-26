"""Write an offline human review tool; pending teacher labels are never auto-accepted."""
import json


def write_review(directory,records,limit,policy=None,annotations=None,preserve_order=False):
    buckets={}
    for r in records:buckets.setdefault((r['split'],r['kind']),[]).append(r)
    for items in buckets.values():items.sort(key=lambda r:r['sample_id'])
    selected=[]
    while any(buckets.values()) and len(selected)<limit:
        for key in sorted(buckets):
            if buckets[key] and len(selected)<limit:selected.append(buckets[key].pop(0))
    if preserve_order:selected=list(records[:limit])
    if policy is not None:
        from .review_sampling import select_clear_review
        selected,report=select_clear_review(records,limit,policy)
        (directory/'selection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'queue.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')
    data=json.dumps(selected,ensure_ascii=False).replace('</','<\\/')
    annotations=annotations or []
    ids={r['sample_id'] for r in selected}
    if any(r['sample_id'] not in ids for r in annotations) or len({r['sample_id'] for r in annotations})!=len(annotations):
        raise ValueError('Prefilled annotations must bind unique IDs in this queue')
    saved_data=json.dumps(annotations,ensure_ascii=False).replace('</','<\\/')
    html=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>关键点人工复核</title>
<style>
body{font:16px system-ui;margin:24px;color:#18222f;background:#f4f6f9}h1{font-size:24px}
.grid{display:flex;gap:24px;flex-wrap:wrap}.card{background:white;padding:18px;border-radius:10px}
canvas{width:512px;height:512px;max-width:100%;background:#111;cursor:crosshair}img{max-width:480px;max-height:360px}
button,select,input{font:inherit;padding:7px;margin:5px}button{cursor:pointer}#meta{max-width:1000px;overflow-wrap:anywhere}
#notice{color:#9c3c00;font-weight:600}label{display:block;margin:8px 0}.toolbar{margin:12px 0}
</style><h1>关键点人工复核 · 本地工具</h1>
<p>绿色点来自自动标注模型，只是初始建议。逐点检查并修正可见点；遮挡点取消可见。未知区域须先判断有无手。
未保存的帧不进入人工标签；导出的 JSONL 需作为训练参数 --reviews 显式导入。</p>
<p><strong>“有无手”只判断左侧ROI裁剪内，不判断右侧整幅原图。</strong>右侧红框只标出当前这一项。
随机候选区可能本来就没有手；它不是手检测结果。图像看不清时标为“无法判断”，不要当作无手。</p>
<div class="toolbar"><button id="prev">上一帧</button><button id="next">下一帧（不保存则跳过）</button>
<button id="download">导出已复核 JSONL</button><input type="file" id="import" accept=".jsonl,.json">
<span id="count"></span></div><p id="meta"></p><p id="purpose"></p><p id="audit" style="color:#a53b00"></p>
<div class="grid"><div class="card"><canvas id="canvas" width="512" height="512"></canvas>
<p>先选点号，再点画面修正；可点击已有点切换选中点。</p>
<label><input type="checkbox" id="overlay" checked>显示自动建议 / 已保存关键点（取消后看原图）</label>
<select id="point"></select><label><input type="checkbox" id="visible">所选点可见</label></div>
<div class="card"><img id="context" alt="原始帧上下文"><p id="source"></p>
<label>复核者 <input id="reviewer" placeholder="姓名或稳定标识"></label>
<label>ROI范围 <select id="roi"><option value="">待审核范围</option><option value="usable">范围可用（也可为无手候选）</option>
<option value="partial">只含部分手，按实际可见部分审核</option><option value="wrong">裁剪错误 / 目标手不对</option></select></label>
<label>有无手 <select id="presence"><option value="">待判断</option><option value="1">有手</option><option value="0">无手</option></select></label>
<label>解剖学侧别 <select id="handedness"><option value="">未核实</option><option value="0">左手</option><option value="1">右手</option></select></label>
<label>场景 <select id="scenario"><option value="general">一般动作</option><option value="static">静止</option>
<option value="fast_motion">快速运动</option><option value="crossing">交叉</option><option value="occlusion">遮挡/恢复</option></select></label>
<label><input type="checkbox" id="presenceOnly">只审核有无手，不提交关键点真值</label>
<label><input type="checkbox" id="checked">我已核对本帧，不是自动批准教师输出</label>
<button id="save">保存此帧复核</button><button id="rejectROI">ROI错了，退回复核</button><button id="ungradable">看不清 / 无法判断</button><p id="notice"></p>
</div></div><script>
const queue=__DATA__,saved=new Map(__SAVED__.map(r=>[r.sample_id,r])),$=id=>document.getElementById(id);
let index=0,points=[],visible=[],active=0,bitmap=new Image();
const edges=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
const names=['腕点','拇指掌根','拇指近节','拇指远节','拇指尖','食指掌指关节','食指近关节','食指远关节','食指尖','中指掌指关节','中指近关节','中指远关节','中指尖','无名指掌指关节','无名指近关节','无名指远关节','无名指尖','小指掌指关节','小指近关节','小指远关节','小指尖'];
for(let i=0;i<21;i++)$('point').add(new Option(`${i} ${names[i]}`,String(i)));
function draw(){const c=$('canvas').getContext('2d');c.clearRect(0,0,512,512);if(!bitmap.complete||!bitmap.naturalWidth)return;c.drawImage(bitmap,0,0,512,512);
 if(!$('overlay').checked)return;
 c.lineWidth=2;c.strokeStyle='#36e09a';for(const [a,b] of edges)if(points[a]&&points[b]&&visible[a]&&visible[b]){
 c.beginPath();c.moveTo(points[a][0]*511,points[a][1]*511);c.lineTo(points[b][0]*511,points[b][1]*511);c.stroke();}
 points.forEach((p,i)=>{if(!p||!visible[i])return;c.fillStyle=i===active?'#ffb000':'#22dd88';c.beginPath();c.arc(p[0]*511,p[1]*511,i===active?6:4,0,Math.PI*2);c.fill();c.fillStyle='white';c.fillText(String(i),p[0]*511+5,p[1]*511-5);});}
function show(){if(!queue.length){$('notice').textContent='复核队列为空';return;}
 const r=queue[index],s=saved.get(r.sample_id);points=structuredClone(s?.landmarks_xy??r.initial_xy??Array(21).fill(null));
 visible=s?.visible?.slice()??r.initial_visible?.slice()??points.map(p=>p!==null);active=0;$('point').value='0';$('visible').checked=visible[0];
 $('presence').value=['ungradable','roi_rejected'].includes(s?.status)?'':(s?String(Number(s.presence)):(r.kind==='teacher_positive'?'1':''));
 $('roi').value=s?.roi_status??'';
 $('handedness').value=s?.handedness===null||s?.handedness===undefined?'':String(s.handedness);
 $('scenario').value=s?.scenario??'general';$('presenceOnly').checked=!!s&&s.landmarks_xy===null&&s.presence;
 $('checked').checked=s?.status==='accepted'&&!r.audit_note;if(s?.reviewer)$('reviewer').value=s.reviewer;
 $('meta').textContent=`${index+1}/${queue.length} | ${r.sample_id} | ${r.split} | ${r.split_group} | ${r.kind}`;
 $('purpose').textContent=r.kind==='unknown_candidate'?'本项：随机候选区域，用于审核有手/无手，可能只有背景、脸或部分手。':'本项：教师自动定位的单手ROI，绿色点可能出错；右侧红色腕点帮助确认目标手。';
 $('audit').textContent=r.audit_note??'';
 $('source').textContent=`原图 ${r.source_size?.join('×')??'未记录'}，ROI原生边长 ${Math.round(r.ROI_side_source_pixels??0)}px；源帧 ${r.source_frame}, ${r.source_timestamp_s.toFixed(3)}s。放大显示不会补出细节。`;
 $('context').src=r.context;const pending=new Image();bitmap=pending;pending.onload=()=>{if(bitmap===pending)draw();};pending.src=r.image;
 $('count').textContent=`已保存 ${saved.size} 帧`;$('notice').textContent='';}
$('point').onchange=()=>{active=Number($('point').value);$('visible').checked=visible[active];draw();};
$('overlay').onchange=draw;
$('visible').onchange=()=>{visible[active]=$('visible').checked;if(visible[active]&&!points[active])visible[active]=false;draw();};
$('canvas').onclick=e=>{const box=$('canvas').getBoundingClientRect(),p=[Math.max(0,Math.min(1,(e.clientX-box.left)/box.width*512/511)),Math.max(0,Math.min(1,(e.clientY-box.top)/box.height*512/511))];
 let nearest=-1,dist=.025;points.forEach((q,i)=>{if(q&&visible[i]){let d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<dist){nearest=i;dist=d;}}});
 if(nearest>=0&&nearest!==active){active=nearest;$('point').value=String(active);}else{points[active]=p;visible[active]=true;}
 $('visible').checked=visible[active];draw();};
$('prev').onclick=()=>{index=(index+queue.length-1)%queue.length;show();};$('next').onclick=()=>{index=(index+1)%queue.length;show();};
$('save').onclick=()=>{const reviewer=$('reviewer').value.trim(),value=$('presence').value,presence=value==='1',only=$('presenceOnly').checked;
 if($('roi').value==='wrong'){$('rejectROI').onclick();return;}
 if(!$('roi').value){$('notice').textContent='请先审核ROI范围；裁剪错了可直接退回，不要编造关键点。';return;}
 if(!reviewer||value===''||!$('checked').checked){$('notice').textContent='请填写复核者、判断有无手并确认已核对。';return;}
 if(presence&&!only&&visible.filter(Boolean).length<2){$('notice').textContent='关键点真值至少需要两个可见点，或选择只审核有无手。';return;}
 saved.set(queue[index].sample_id,{sample_id:queue[index].sample_id,status:'accepted',roi_status:$('roi').value,annotation_origin:'human',human_verified:true,reviewer,presence,
 handedness:presence&&$('handedness').value!==''?Number($('handedness').value):null,scenario:$('scenario').value,
 landmarks_xy:presence&&!only?points.map((p,i)=>visible[i]?p:null):null,visible:presence&&!only?visible.slice():Array(21).fill(false)});
 $('notice').textContent='此帧已存到内存；离开前请导出 JSONL。';$('count').textContent=`已保存 ${saved.size} 帧`;};
$('rejectROI').onclick=()=>{const reviewer=$('reviewer').value.trim();if(!reviewer){$('notice').textContent='请填写复核者';return;}
 saved.set(queue[index].sample_id,{sample_id:queue[index].sample_id,status:'roi_rejected',roi_status:'wrong',annotation_origin:'human',human_verified:true,reviewer,reason:'wrong_crop_or_target',presence:null,landmarks_xy:null});
 $('notice').textContent='已退回ROI；不作为无手或关键点真值。原裁剪不会被改写，请导出JSONL。';$('count').textContent=`已保存 ${saved.size} 帧`;};
$('ungradable').onclick=()=>{const reviewer=$('reviewer').value.trim();if(!reviewer){$('notice').textContent='请填写复核者';return;}
 saved.set(queue[index].sample_id,{sample_id:queue[index].sample_id,status:'ungradable',annotation_origin:'human',human_verified:true,reviewer,reason:'blur_small_or_uncertain',presence:null,landmarks_xy:null});
 $('notice').textContent='已标无法判断，不会作为有手、无手或坐标真值；请导出后继续。';$('count').textContent=`已保存 ${saved.size} 帧`;};
$('download').onclick=()=>{if(!saved.size){$('notice').textContent='还没有已复核帧';return;}const blob=new Blob([[...saved.values()].map(v=>JSON.stringify(v)).join('\n')+'\n'],{type:'application/x-ndjson'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='hand_review_annotations.jsonl';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('import').onchange=async e=>{try{const ids=new Set(queue.map(r=>r.sample_id));for(const line of (await e.target.files[0].text()).split(/\r?\n/)){if(!line.trim())continue;const r=JSON.parse(line);if(!ids.has(r.sample_id)||!['accepted','ungradable','roi_rejected'].includes(r.status))throw Error('ID 或状态不匹配');saved.set(r.sample_id,r);}show();}catch(error){$('notice').textContent=String(error);}};
show();
</script></html>'''.replace('__DATA__',data).replace('__SAVED__',saved_data)
    (directory/'index.html').write_text(html,encoding='utf-8')
    return len(selected)
