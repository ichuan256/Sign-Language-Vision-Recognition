"""ROI failures must not become negatives; review navigation must preserve human work."""
import json
from pathlib import Path
import shutil
import subprocess
import cv2
import numpy as np
import pytest
from vision.keypoints.student_data import apply_reviews
from vision.keypoints.student_review import write_review
from vision.keypoints.review_geometry import roi_polygon,review_context,source_affine


@pytest.mark.parametrize('status,roi_status',[('roi_rejected','wrong'),('accepted','wrong')])
def test_bad_crop_never_becomes_negative_or_coordinate_truth(tmp_path,status,roi_status):
    y=np.ones((1,65),np.float32);m=np.ones_like(y)
    review=dict(sample_id='a',status=status,roi_status=roi_status,reviewer='human',annotation_origin='human',
        human_verified=True,presence=False,landmarks_xy=None)
    path=tmp_path/'reviews.jsonl';path.write_text(json.dumps(review))
    yy,mm,records=apply_reviews(y,m,[dict(sample_id='a',pose_source='teacher')],path)
    assert not mm.any() and yy[0,63]==1 and m.all()
    assert records[0]['quality_status']=='human_roi_rejected'
    assert records[0]['pose_source']==records[0]['presence_source']=='none'


def test_roi_polygon_and_context_use_same_affine_without_changing_frame():
    matrix=cv2.getRotationMatrix2D((40,50),22,1.3);matrix[:,2]+=[20,10]
    polygon,_=roi_polygon(matrix)
    assert np.allclose(polygon@matrix[:,:2].T+matrix[:,2],[[0,0],[127,0],[127,127],[0,127]])
    frame=np.zeros((240,320,3),np.uint8)
    image=review_context(frame,matrix,[[.5,.5]]*21,width=160)
    assert image.shape==(120,160,3) and image[:,:,2].max()>0 and not frame.any()
    with pytest.raises(ValueError,match='invertible'):roi_polygon(np.zeros((2,3)))


def test_historical_affine_precision_is_preserved_for_pixel_reproduction():
    record=dict(kind='teacher_positive',affine_source_to_roi=[[1,0,.123456789],[0,1,0]])
    assert source_affine(record).dtype==np.float64
    assert source_affine(dict(record,kind='unknown_candidate')).dtype==np.float32
    assert source_affine(dict(record,affine_dtype='float32')).dtype==np.float32


def review_records():
    return [dict(sample_id=s,split='train',split_group='g',kind=k,initial_xy=xy,
        source_frame=i,source_timestamp_s=float(i),source_size=[1920,1080],ROI_side_source_pixels=200,
        image='a.jpg',context='context.jpg') for i,(s,k,xy) in enumerate([
            ('a','teacher_positive',[[.5,.5]]*21),('b','unknown_candidate',None)])]


def test_prefill_requires_unique_ids_in_unchanged_queue(tmp_path):
    with pytest.raises(ValueError,match='unique IDs'):
        write_review(tmp_path,review_records(),2,annotations=[dict(sample_id='elsewhere')])


def test_rendered_review_handlers_keep_prefill_and_reject_wrong_roi(tmp_path):
    node=shutil.which('node')
    if not node:pytest.skip('Node needed to exercise rendered review JavaScript')
    records=review_records();annotations=[dict(sample_id='a',status='accepted',reviewer='human',presence=True,
        landmarks_xy=[[.5,.5]]*21,visible=[True]*21)]
    write_review(tmp_path,records,2,annotations=annotations,preserve_order=True)
    runner=tmp_path/'exercise.js'
    runner.write_text(r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8'),script=html.split('<script>')[1].split('</script>')[0];
const elements={},images=[];let draws=0;
const graphics=new Proxy({}, {get:(_,name)=>name==='drawImage'?()=>draws++:()=>{}});
const get=id=>elements[id]??=( {value:'',checked:id==='overlay',textContent:'',add:()=>{},getContext:()=>graphics});
class Picture{constructor(){images.push(this);this.complete=true;this.naturalWidth=512;}}
const context=vm.createContext({document:{getElementById:get},Image:Picture,Option:function(){},structuredClone});
vm.runInContext(script,context);
assert.equal(vm.runInContext('saved.size',context),1);
assert.equal(get('presence').value,'1');
const oldImage=images.at(-1);get('next').onclick();const currentImage=images.at(-1);
oldImage.onload();assert.equal(draws,0); // stale image must not redraw another frame
currentImage.onload();assert.equal(draws,1);
get('roi').value='usable';get('reviewer').value='human';get('presence').value='0';get('checked').checked=true;
get('save').onclick();
assert.equal(vm.runInContext("saved.get('b').presence",context),false);
assert.equal(vm.runInContext("saved.get('b').landmarks_xy",context),null);
get('prev').onclick();get('roi').value='wrong';get('save').onclick();
assert.equal(vm.runInContext("saved.get('a').status",context),'roi_rejected');
assert.equal(vm.runInContext("saved.get('a').presence",context),null);
assert.equal(vm.runInContext("saved.get('a').landmarks_xy",context),null);
get('next').onclick();get('ungradable').onclick();
assert.equal(vm.runInContext("saved.get('b').status",context),'ungradable');
get('prev').onclick();assert.equal(get('presence').value,'');
assert.equal(vm.runInContext('saved.size',context),2);
console.log('Review handlers passed');
''',encoding='utf-8')
    result=subprocess.run([node,str(runner),str(tmp_path/'index.html')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
